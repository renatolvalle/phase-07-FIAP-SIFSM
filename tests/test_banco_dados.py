# Testes automatizados do Banco de Dados (DB) do Sistema Aurora Siger
# O teste verifica a estrutura SQLite e suas regras de integridade

import sqlite3
import unittest
import csv
import tempfile

from banco_dados import (
    abrir_conexao,
    inicializar_banco,
    cadastrar_modulo,
    listar_modulos,
    buscar_modulo_por_codigo,
    atualizar_modulo,
    excluir_modulo,
    cadastrar_sensor,
    registrar_leitura,
    listar_sensores,
    consultar_leituras,
    obter_serie_energia,
    carregar_csv_inicial,
    registrar_solicitacao,
    listar_solicitacoes,
    registrar_alertas
)
from pathlib import Path
from gerar_dados_iniciais import gerar_csv_inicial

# Testes da conexão e estrutura do banco SQLite
class TestBancoDados(unittest.TestCase):
    # Prepara um banco temporário para cada teste
    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)

        inicializar_banco(self.conexao)

    # Verifica a existência das cinco tabelas
    def test_criacao_das_tabelas(self):
        registros = self.conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        tabelas = {registro["name"] for registro in registros}

        esperadas = {
            "modulos",
            "sensores",
            "leituras",
            "alertas",
            "solicitacoes"
        }

        self.assertEqual(tabelas, esperadas)

    # Verifica se as foreign keys estão habilitadas
    def test_chaves_estrangeiras_ativas(self):
        resultado = self.conexao.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        self.assertEqual(resultado, 1)

    # O campo critico aceita somente 0 ou 1
    def test_rejeitar_criticidade_invalida(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conexao.execute(
                """
                INSERT INTO modulos
                    (codigo, nome, tipo, critico)
                VALUES (?, ?, ?, ?)
                """,
                ("MOD_TESTE", "Módulo Teste", "energia", 2)
            )
    
    # Dois módulos não podem possuir o mesmo código
    def test_rejeitar_codigo_duplicado(self):
        dados = ("MOD-001", "Habitação", "habitacao")

        self.conexao.execute(
            """
            INSERT INTO modulos (codigo, nome, tipo)
            VALUES (?, ?, ?)
            """,
            dados
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.conexao.execute(
                """
                INSERT INTO modulos (codigo, nome, tipo)
                VALUES (?, ?, ?)
                """,
                dados
            )

    # Um sensor não pode apontar para um módulo inexistente
    def test_rejeitar_sensor_sem_modulo(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conexao.execute(
                """
                INSERT INTO sensores
                    (codigo, modulo_id, tipo, unidade)
                VALUES (?, ?, ?, ?)
                """,
                ("SEN-TESTE", 999, "consumo_kw", "kW")
            )
    
    # Inicializar novamente não deve apagar dados
    def test_inicializacao_repetida(self):
        self.conexao.execute(
            """
            INSERT INTO modulos (codigo, nome, tipo)
            VALUES (?, ?, ?)
            """,
            ("MOD-TESTE", "Módulo Teste", "energia")
        )

        inicializar_banco(self.conexao)

        resultado = self.conexao.execute(
            "SELECT COUNT(*) FROM modulos"
        ).fetchone()[0]

        self.assertEqual(resultado, 1)
        
    # Verifica se o cadastro cria um módulo válido.
    def test_cadastrar_modulo(self):
        dados = {
            "codigo": "MOD-HAB-01",
            "nome": "Habitação",
            "tipo": "habitacao",
            "critico": 1,
            "status": "ativo"
        }

        identificador = cadastrar_modulo(self.conexao, dados)

        self.assertIsInstance(identificador, int)

        registro = self.conexao.execute(
            "SELECT * FROM modulos WHERE id = ?",
            (identificador,)
        ).fetchone()

        self.assertEqual(registro["codigo"], "MOD-HAB-01")
        self.assertEqual(registro["critico"], 1)

    # Não permite cadastrar módulo sem código
    def test_cadastrar_modulo_invalido(self):
        dados = {
            "codigo": "",
            "nome": "Habitação",
            "tipo": "habitacao"
        }

        with self.assertRaises(ValueError):
            cadastrar_modulo(self.conexao, dados)

    # Não permite códigos de módulo duplicados
    def test_cadastrar_modulo_duplicado(self):
        dados = {
            "codigo": "MOD-HAB-01",
            "nome": "Habitação",
            "tipo": "habitacao"
        }

        cadastrar_modulo(self.conexao, dados)

        with self.assertRaises(sqlite3.IntegrityError):
            cadastrar_modulo(self.conexao, dados)

    # Uma tabela vazia deve retornar uma lista vazia
    def test_listar_modulos_vazio(self):
        resultado = listar_modulos(self.conexao)

        self.assertEqual(resultado, [])

    # Verifica listagem, formato e ordem dos módulos
    def test_listar_modulos_cadastrados(self):
        primeiro_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        segundo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-01",
                "nome": "Energia",
                "tipo": "energia"
            }
        )

        resultado = listar_modulos(self.conexao)

        self.assertEqual(len(resultado), 2)

        self.assertEqual(
            [modulo["id"] for modulo in resultado],
            [primeiro_id, segundo_id]
        )

        self.assertTrue(
            all(isinstance(modulo, dict) for modulo in resultado)
        )

        self.assertEqual(
            resultado[0]["codigo"],
            "MOD-HAB-01"
        )

        self.assertEqual(
            resultado[1]["codigo"],
            "MOD-ENE-01"
        )

    # Busca o módulo previamente cadastrado
    def test_buscar_modulo_existente(self):
        cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-AGR-01",
                "nome": "Agricultura",
                "tipo": "agricultura",
                "critico": 0
            }
        )

        resultado = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-AGR-01"
        )

        self.assertIsInstance(resultado, dict)
        self.assertEqual(resultado["nome"], "Agricultura")
        self.assertEqual(resultado["critico"], 0)

    # A busca sem resultado deve retornar None
    def test_buscar_modulo_inexistente(self):
        resultado = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-INEXISTENTE"
        )

        self.assertIsNone(resultado)

    # A busca não deve aceitar um código vazio
    def test_buscar_modulo_codigo_invalido(self):
        with self.assertRaises(ValueError):
            buscar_modulo_por_codigo(
                self.conexao,
                "   "
            )

    # Atualiazndo campos e preservando os demais dados
    def test_atualizar_modulo_existente(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao",
                "critico": 1,
                "status": "ativo"
            }
        )

        resultado = atualizar_modulo(
            self.conexao,
            modulo_id,
            {
                "nome": "Habitação Principal",
                "status": "manutencao"
            }
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao, "MOD-HAB-01"
        )

        self.assertTrue(resultado)
        self.assertEqual(modulo["id"], modulo_id)
        self.assertEqual(modulo["nome"], "Habitação Principal")
        self.assertEqual(modulo["status"], "manutencao")
        self.assertEqual(modulo["critico"], 1)

    # Retorna False se o ID não existir
    def test_atualizar_modulo_inexistente(self):
        resultado = atualizar_modulo(
            self.conexao,
            9999,
            {"nome": "Novo Nome"}
        )

        self.assertFalse(resultado)

    # Não permite uma atualização vazia
    def test_atualizar_modulo_sem_alteracoes(self):
        with self.assertRaises(ValueError):
            atualizar_modulo(
                self.conexao,
                1,
                {}
            )

    # Impede alterações em campos não autorizados
    def test_atualizar_modulo_campo_proibido(self):
        with self.assertRaises(ValueError):
            atualizar_modulo(
                self.conexao,
                1,
                {"id": 500}
            )

    # Valida status, criticidade e textos obrigatórios
    def test_atualizar_modulo_valores_invalidos(self):
        casos_invalidos = [
            {"status": "desconhecido"},
            {"critico": 3},
            {"nome": "   "}
        ]

        for alteracoes in casos_invalidos:
            with self.subTest(alteracoes=alteracoes):
                with self.assertRaises(ValueError):
                    atualizar_modulo(
                        self.conexao,
                        1,
                        alteracoes
                    )

    # O banco impede códigos duplicados.
    def test_atualizar_modulo_codigo_duplicado(self):
        cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        segundo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-01",
                "nome": "Energia",
                "tipo": "Energia"
            }
        )

        with self.assertRaises(sqlite3.IntegrityError):
            atualizar_modulo(
                self.conexao,
                segundo_id,
                {"codigo": "MOD-HAB-01"}
            )

    # Exclui um módulo existente sem dependências 
    def test_excluir_modulo_existente(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-TEMP-01",
                "nome": "Laboratório Temporário",
                "tipo": "laboratorio"
            }
        )

        resultado = excluir_modulo(
            self.conexao,
            modulo_id
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-TEMP-01"
        )

        self.assertTrue(resultado)
        self.assertIsNone(modulo)

    # Retorna False quando o módulo não existe
    def test_excluir_modulo_inexistente(self):
        resultado = excluir_modulo(
            self.conexao,
            9999
        )

        self.assertFalse(resultado)

    # Rejeita IDs inválidos
    def test_excluir_modulo_id_invalido(self):
        identificadores_invalidos = [
            0,
            -1,
            "5",
            True,
            None
        ]

        for modulo_id in identificadores_invalidos:
            with self.subTest(modulo_id=modulo_id):
                with self.assertRaises(ValueError):
                    excluir_modulo(
                        self.conexao,
                        modulo_id
                    )
    
    # Impede a exclusão com sensor vinculado
    def test_excluir_modulo_com_sensor(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        # Cria um sensor associado ao módulo
        self.conexao.execute(
            """
            INSERT INTO sensores
                (codigo, modulo_id, tipo, unidade, status)
            VALUEs (?, ?, ?, ?, ?)
            """,
            (
                "SEN-HAB-01",
                modulo_id,
                "consumo_kw",
                "kW",
                "ativo"
            )
        )

        self.conexao.commit()

        # O SQLite deve bloquear a exclusão
        with self.assertRaises(sqlite3.IntegrityError):
            excluir_modulo(
                self.conexao,
                modulo_id
            )

        # O módulo deve continuar cadastrado
        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-HAB-01"
        )

        self.assertIsNotNone(modulo)
    
    # Impede exclusão com solicitação vinculada
    def test_excluir_modulo_com_solicitacoes(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-01",
                "nome": "Energia",
                "tipo": "energia"
            }
        )

        # Cria uma solicitação associada ao módulo
        self.conexao.execute(
            """
            INSERT INTO solicitacoes
                (
                    modulo_id,
                    descricao,
                    prioridade,
                    status,
                    criado_em
                )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                modulo_id,
                "Verificar funcionamento do módulo.",
                "alta",
                "pendente",
                "2026-11-06T12:00:00Z"
            )
        )

        self.conexao.commit()

        # A exclusão deve ser bloqueada
        with self.assertRaises(sqlite3.IntegrityError):
            excluir_modulo(
                self.conexao,
                modulo_id
            )
        
        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-ENE-01"
        )

        self.assertIsNotNone(modulo)

    # Verifica o cadastrao de um sensor válido
    def test_cadastrar_sensor(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        sensor_id = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-HAB-CONS-01",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        registro = self.conexao.execute(
            "SELECT * FROM sensores WHERE id = ?",
            (sensor_id,)
        ).fetchone()

        self.assertIsInstance(sensor_id, int)
        self.assertEqual(registro["modulo_id"], modulo_id)
        self.assertEqual(registro["status"], "ativo")

    # Impede o sensor vinculado ao módulo inexistente
    def test_cadastrar_sensor_modulo_inexistente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            cadastrar_sensor(
                self.conexao,
                {
                    "codigo": "SEN-TESTE",
                    "modulo_id": 9999,
                    "tipo": "consumo_kw",
                    "unidade": "kW"
                }
            )

    # Não permite dois sensores com o mesmo código
    def test_cadastrar_sensor_codigo_duplicado(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-01",
                "nome": "Energia",
                "tipo": "energia"
            }
        )

        dados = {
            "codigo": "SEN-ENE-01",
            "modulo_id": modulo_id,
            "tipo": "geracao_kw",
            "unidade": "kW"
        }

        cadastrar_sensor(self.conexao, dados)

        with self.assertRaises(sqlite3.IntegrityError):
            cadastrar_sensor(self.conexao, dados)

    # Rejeitando campos obrigatórios e status inválidos
    def test_cadastrar_sensor_dados_invalidos(self):
        casos_invalidos = [
            {
                "codigo": "",
                "modulo_id": 1,
                "tipo": "consumo_kw",
                "unidade": "kW"
            },
            {
                "codigo": "SEN-01",
                "modulo_id": 0,
                "tipo": "consumo_kw",
                "unidade": "kW"
            },
            {
                "codigo": "SEN-01",
                "modulo_id": 1,
                "tipo": "",
                "unidade": "kW"
            },
            {
                "codigo": "SEN-01",
                "modulo_id": 1,
                "tipo": "consumo_kw",
                "unidade": "kW",
                "status": "desconhecido"
            }
        ]

        for dados in casos_invalidos:
            with self.subTest(dados=dados):
                with self.assertRaises(ValueError):
                    cadastrar_sensor(self.conexao, dados)

    # Registra uma leitura vinculada a um sensor
    def test_registrar_leitura(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        sensor_id = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-HAB-01",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        leitura_id = registrar_leitura(
            self.conexao,
            {
                "sensor_id": sensor_id,
                "ciclo": 1,
                "instante": "2026-11-07T12:00:00Z",
                "valor": 3.1
            }
        )

        registro = self.conexao.execute(
            "SELECT * FROM leituras WHERE id = ?",
            (leitura_id,)
        ).fetchone()

        self.assertEqual(registro["sensor_id"], sensor_id)
        self.assertEqual(registro["ciclo"], 1)
        self.assertAlmostEqual(registro["valor"], 3.1)

    # Impede leitura vinculada a sensor inexistente
    def test_registrar_leitura_sensor_inexistente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            registrar_leitura(
                self.conexao,
                {
                    "sensor_id": 9999,
                    "ciclo": 1,
                    "instante": "2026-11-07T12:00:00Z",
                    "valor": 3.1
                }
            )

    # Rejeita ciclos, instantes e valores inválidos
    def test_registrar_leitura_dados_invalidos(self):
        dados_validos = {
            "sensor_id": 1,
            "ciclo": 1,
            "instante": "2026-11-07T12:00:00Z",
            "valor": 3.1
        }

        casos_invalidos = [
            {"sensor_id": 0},
            {"ciclo": 0},
            {"ciclo": True},
            {"instante": "data-invalida"},
            {"valor": "3.1"},
            {"valor": float("nan")},
            {"valor": float("inf")}
        ]

        for alteracao in casos_invalidos:
            dados = {**dados_validos, **alteracao}

            with self.subTest(alteracao=alteracao):
                with self.assertRaises(ValueError):
                    registrar_leitura(self.conexao, dados)

    # Impede duas leituras ao mesmo sensor no mesmo ciclo
    def test_registrar_leitura_duplicada(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        sensor_id = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-HAB-01",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        dados = {
            "sensor_id": sensor_id,
            "ciclo": 1,
            "instante": "2026-11-07T12:00:00Z",
            "valor": 3.1
        }

        registrar_leitura(self.conexao, dados)

        with self.assertRaises(sqlite3.IntegrityError):
            registrar_leitura(self.conexao, dados)

    # Sensores diferentes podem registrar o mesmo ciclo
    def test_leituras_mesmo_ciclo_sensores_diferentes(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-01",
                "nome": "Energia",
                "tipo": "energia"
            }
        )

        sensor_consumo = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-CONS-01",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        sensor_geracao = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-GER-01",
                "modulo_id": modulo_id,
                "tipo": "geracao_kw",
                "unidade": "kW"
            }
        )

        for sensor_id, valor in [
            (sensor_consumo, 3.1),
            (sensor_geracao, 4.2)
        ]:
            registrar_leitura(
                self.conexao,
                {
                    "sensor_id": sensor_id,
                    "ciclo": 1,
                    "instante": "2026-11-07T12:00:00Z",
                    "valor": valor
                }
            )

        quantidade = self.conexao.execute(
            "SELECT COUNT(*) FROM leituras WHERE ciclo = 1"
        ).fetchone()[0]

        self.assertEqual(quantidade, 2)

    # Prepara módulos, sensores e leituras para os testes
    def preparar_cenario_consultas(self):
        modulo_energia = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-01",
                "nome": "Energia",
                "tipo": "energia",
                "critico": 1
            }
        )

        modulo_habitacao = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao",
                "critico": 1 
            }
        )

        sensores = {}

        configuracoes = [
            (
                "consumo",
                "SEN-ENE-CONS",
                modulo_energia,
                "consumo_kw",
                "kW"
            ),
                        (
                "geracao",
                "SEN-ENE-GER",
                modulo_energia,
                "geracao_kw",
                "kW"
            ),
                        (
                "temperatura",
                "SEN-ENE-TEMP",
                modulo_energia,
                "temperatura",
                "°C"
            ),
                        (
                "habitacao",
                "SEN-HAB-CONS",
                modulo_habitacao,
                "consumo_kw",
                "kW"
            ),
        ]

        for nome, codigo, modulo_id, tipo, unidade in configuracoes:
            sensores[nome] = cadastrar_sensor(
                self.conexao,
                {
                    "codigo": codigo,
                    "modulo_id": modulo_id,
                    "tipo": tipo,
                    "unidade": unidade 
                }
            )

        medicoes = [
            ("consumo", 1, 2.0),
            ("geracao", 1, 5.0),
            ("temperatura", 1, -8.0),
            ("habitacao", 1, 1.5),
            ("consumo", 2, 3.0),
            ("geracao", 2, 4.0),
            ("temperatura", 2, -6.0),
            ("habitacao", 2, 0.5)
        ]

        for nome, ciclo, valor in medicoes:
            registrar_leitura(
                self.conexao,
                {
                    "sensor_id": sensores[nome],
                    "ciclo": ciclo,
                    "instante": "2026-11-09T12:00:00Z",
                    "valor": valor
                }
            )

        return {
            "modulo_energia": modulo_energia,
            "modulo_habitacao": modulo_habitacao,
            "sensores": sensores
        }
    
    # Sem sensores, a listagem retorna uma lista vazia
    def test_listar_sensores_vazio(self):
        resultado = listar_sensores(self.conexao)

        self.assertEqual(resultado, [])

    # Retorna sensores como dicionários ordenados por ID
    def test_listar_sensores_ordenados(self):
        self.preparar_cenario_consultas()

        resultado = listar_sensores(self.conexao)

        self.assertEqual(len(resultado), 4)
        self.assertTrue(
            all(isinstance(sensor, dict) for sensor in resultado)
        )

        identificadores = [
            sensor["id"] for sensor in resultado
        ]

        self.assertEqual(
            identificadores,
            sorted(identificadores)
        )

        self.assertEqual(
            resultado[0]["codigo"],
            "SEN-ENE-CONS"
        )

    # Sem leituras, a consulta retorna lista vazia
    def test_consultar_leituras_vazio(self):
        resultado = consultar_leituras(self.conexao)

        self.assertEqual(resultado, [])

    # Verifica os dados reunidos pelas três tabelas
    def test_consultar_leituras_enriquecidas(self):
        self.preparar_cenario_consultas()

        resultado = consultar_leituras(self.conexao)

        self.assertEqual(len(resultado), 8)

        primeira = resultado[0]

        self.assertEqual(
            primeira["sensor_codigo"],
            "SEN-ENE-CONS"
        )

        self.assertEqual(
            primeira["sensor_tipo"],
            "consumo_kw"
        )

        self.assertEqual(
            primeira["modulo_codigo"],
            "MOD-ENE-01"
        )

        self.assertIs(primeira["modulo_critico"], True)
        self.assertEqual(primeira["unidade"], "kW")
        self.assertAlmostEqual(primeira["valor"], 2.0)

    # Filtra as leituras pelo ciclo informado
    def test_consultar_leituras_por_ciclo(self):
        self.preparar_cenario_consultas()

        resultado = consultar_leituras(
            self.conexao,
            ciclo=2
        )

        self.assertEqual(len(resultado), 4)

        self.assertTrue(
            all(leitura["ciclo"] == 2 for leitura in resultado)
        )

    # Rejeita ciclos inválidos
    def test_consultar_leituras_ciclo_invalido(self):
        casos_invalidos = [0, -1, "1", True, 1.5]

        for ciclo in casos_invalidos:
            with self.subTest(ciclo=ciclo):
                with self.assertRaises(ValueError):
                    consultar_leituras(
                        self.conexao,
                        ciclo=ciclo
                    )

    # Um ciclo sem registros retorna lista vazia
    def test_consultar_leituras_ciclo_ausente(self):
        self.preparar_cenario_consultas()

        resultado = consultar_leituras(
            self.conexao,
            ciclo=999
        )

        self.assertEqual(resultado, [])

    # Sem leituras energéticas, retorna lista vazia
    def test_obter_serie_energia_vazia(self):
        resultado = obter_serie_energia(self.conexao)

        self.assertEqual(resultado, [])

    def test_obter_serie_energia_agregada(self):
        self.preparar_cenario_consultas()

        resultado = obter_serie_energia(self.conexao)

        self.assertEqual(len(resultado), 2)

        self.assertEqual(resultado[0]["ciclo"], 1)
        self.assertAlmostEqual(resultado[0]["consumo_kw"], 3.5)
        self.assertAlmostEqual(resultado[0]["geracao_kw"], 5.0)

        self.assertEqual(resultado[1]["ciclo"], 2)
        self.assertAlmostEqual(resultado[1]["consumo_kw"], 3.5)
        self.assertAlmostEqual(resultado[1]["geracao_kw"], 4.0)

    # Mudanças de status não apagam leituras anteriores
    def test_obter_serie_energia_preserva_historico(self):
        dados = self.preparar_cenario_consultas()

        atualizar_modulo(
            self.conexao,
            dados["modulo_energia"],
            {"status" : "inativo"}
        )

        self.conexao.execute(
            """
            UPDATE sensores
            SET status = "inativo"
            WHERE id = ?
            """,
            (dados["sensores"]["habitacao"],)
        )

        self.conexao.commit()

        resultado = obter_serie_energia(self.conexao)

        self.assertEqual(len(resultado), 2)
        self.assertAlmostEqual(resultado[0]["consumo_kw"], 3.5)
        self.assertAlmostEqual(resultado[0]["geracao_kw"], 5.0)

    # Gera um CSV isolado para os testes
    def criar_csv_temporario(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)

        caminho = Path(diretorio.name) / "dados_teste.csv"

        gerar_csv_inicial(caminho)

        return caminho

    # Altera uma medição para testar erros de importação
    def alterar_valor_csv(self, caminho, indice, novo_valor):
        with caminho.open(
            newline="",
            encoding="utf-8"
        ) as arquivo:
            leitor = csv.DictReader(arquivo)
            colunas = leitor.fieldnames
            linhas = list(leitor)

        linhas[indice]["valor"] = novo_valor

        with caminho.open(
            mode="w",
            newline="",
            encoding="utf-8"
        ) as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=colunas
            )

            escritor.writeheader()
            escritor.writerows(linhas)

    # Importa cinco módulos, dez sensores e 320 leituras
    def test_importar_csv_banco_vazio(self):
        caminho = self.criar_csv_temporario()

        quantidade = carregar_csv_inicial(
            self.conexao, caminho
        )

        self.assertEqual(quantidade, 320)

        for tabela, esperado in (
            ("modulos", 5),
            ("sensores", 10),
            ("leituras", 320)
        ):
            total = self.conexao.execute(
                f"SELECT COUNT(*) FROM {tabela}"
            ).fetchone()[0]

            self.assertEqual(total, esperado)

        serie = obter_serie_energia(self.conexao)
        self.assertEqual(len(serie), 32)

    # Uma segunda importação não deve duplicar dados
    def test_importar_csv_duas_vezes(self):
        caminho = self.criar_csv_temporario()

        primeira = carregar_csv_inicial(
            self.conexao, caminho
        )

        segunda = carregar_csv_inicial(
            self.conexao, caminho
        )

        total = self.conexao.execute(
            "SELECT COUNT(*) FROM leituras"
        ).fetchone()[0]

        self.assertEqual(primeira, 320)
        self.assertEqual(segunda, 0)
        self.assertEqual(total, 320)

    def test_importar_csv_inexistente(self):
        """Um arquivo inexistente deve produzir erro."""

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "inexistente.csv"

            with self.assertRaises(FileNotFoundError):
                carregar_csv_inicial(
                    self.conexao, caminho
                )

    # A importação rejeita colunas incorretas
    def test_importar_csv_cabecalho_invalido(self):
        caminho = self.criar_csv_temporario()

        caminho.write_text(
            "sensor_codigo,ciclo,valor\n"
            "SEN-01,1,3.1\n",
            encoding="utf-8"
        )

        with self.assertRaises(ValueError):
            carregar_csv_inicial(
                self.conexao, caminho
            )

    # Um erro no meio do CSV desfaz toda a importação
    def test_importar_csv_rollback(self):
        caminho = self.criar_csv_temporario()

        # Introduz uma medição inválida após várias linhas.
        self.alterar_valor_csv(
            caminho, indice=200, novo_valor="invalido"
        )

        with self.assertRaises(ValueError):
            carregar_csv_inicial(
                self.conexao, caminho
            )

        for tabela in ("modulos", "sensores", "leituras"):
            total = self.conexao.execute(
                f"SELECT COUNT(*) FROM {tabela}"
            ).fetchone()[0]

            self.assertEqual(total, 0)

    # Não sobrescreve uma leitura já registrada
    def test_importar_csv_leitura_conflitante(self):
        caminho = self.criar_csv_temporario()

        carregar_csv_inicial(self.conexao, caminho)

        valor_original = self.conexao.execute(
            """
            SELECT valor FROM leituras
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()[0]

        # Altera o valor do primeiro registro do CSV.
        self.alterar_valor_csv(
            caminho, indice=0, novo_valor="999"
        )

        with self.assertRaises(ValueError):
            carregar_csv_inicial(
                self.conexao, caminho
            )

        valor_final = self.conexao.execute(
            """
            SELECT valor FROM leituras
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()[0]

        self.assertEqual(valor_final, valor_original)

    # Cadastra um módulo para os testes de solicitações
    def criar_modulo_para_solicitacoes(self):
        return cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-TESTE-01",
                "nome": "Módulo de Testes",
                "tipo": "laboratorio"
            }
        )

    # Cria quatro chamados para testar a listagem
    def criar_solicitacoes_exemplo(self):
        modulo_id = self.criar_modulo_para_solicitacoes()
        identificadores = []

        exemplos = [
            ("Primeiro chamado", "baixa", "pendente"),
            ("Segundo chamado", "alta", "pendente"),
            ("Terceiro chamado", "media", "pendente"),
            ("Chamado finalizado", "baixa", "concluida")
        ]

        for descricao, prioridade, status in exemplos:
            identificador = registrar_solicitacao(
                self.conexao,
                {
                    "modulo_id": modulo_id,
                    "descricao": descricao,
                    "prioridade": prioridade,
                    "status": status
                }
            )

            identificadores.append(identificador)

        return identificadores

    # Cria módulo, sensor e leitura para os testes
    def criar_sensor_para_alertas(self):
        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao",
                "critico": 1
            }
        )

        sensor_id = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-HAB-CONS-01",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        registrar_leitura(
            self.conexao,
            {
                "sensor_id": sensor_id,
                "ciclo": 1,
                "instante": "2026-11-09T12:00:00Z",
                "valor": 3.1
            }
        )

        return sensor_id

    # Monta um alerta de consumo crítico
    def criar_alerta_exemplo(self, sensor_id, ciclo=1):
        return {
            "sensor_id": sensor_id,
            "ciclo": ciclo,
            "regra_codigo": "CONSUMO_CRITICO",
            "nivel": "alto",
            "mensagem": "Consumo elevado em módulo crítico."
        }

    # Registra um chamado com status pendente
    def test_registrar_solicitacao_valida(self):
        modulo_id = self.criar_modulo_para_solicitacoes()

        solicitacao_id = registrar_solicitacao(
            self.conexao,
            {
                "modulo_id": modulo_id,
                "descricao": " Verificar ventilação. ",
                "prioridade": "alta"
            }
        )

        registro = self.conexao.execute(
            "SELECT * FROM solicitacoes WHERE id = ?",
            (solicitacao_id,)
        ).fetchone()

        self.assertIsInstance(solicitacao_id, int)
        self.assertEqual(registro["modulo_id"], modulo_id)
        self.assertEqual(registro["descricao"], "Verificar ventilação.")
        self.assertEqual(registro["prioridade"], "alta")
        self.assertEqual(registro["status"], "pendente")
        self.assertTrue(registro["criado_em"])

    # Rejeita informações imcompatíveis com o contrato
    def test_registrar_solicitacao_dados_invalidos(self):
        modulo_id = self.criar_modulo_para_solicitacoes()

        dados_validos = {
            "modulo_id": modulo_id,
            "descricao": "Inspecionar módulo",
            "prioridade": "alta"
        }

        casos_invalidos = [
            {"modulo_id": 0},
            {"modulo_id": True},
            {"descricao": "   "},
            {"prioridade": "urgente"},
            {"status": "desconhecido"},
            {"criado_em": "data-invalida"},
            {"criado_em": "2026-11-09T12:00:00"}
        ]

        for alteracao in casos_invalidos:
            dados = {**dados_validos, **alteracao}

            with self.subTest(alteracao=alteracao):
                with self.assertRaises(ValueError):
                    registrar_solicitacao(self.conexao, dados)

    # Impede chamados para módulos inexistentes
    def test_registrar_solicitacao_modulo_inexistente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            registrar_solicitacao(
                self.conexao,
                {
                    "modulo_id": 9999,
                    "descricao": "Verificar módulo",
                    "prioridade": "alta"
                }
            )

    # Lista chamados pendentes na ordem de cadastro
    def test_listar_solicitacoes_pendentes_fifo(self):
        identificadores = self.criar_solicitacoes_exemplo()

        resultado = listar_solicitacoes(self.conexao)

        self.assertEqual(len(resultado), 3)

        self.assertEqual(
            [item["id"] for item in resultado],
            identificadores[:3]
        )

        self.assertTrue(
            all(item["status"] == "pendente" for item in resultado)
        )

    # Permite consultar todas solicitações ou somente as concluídas
    def test_listar_solicitacoes_todos_status(self):
        self.criar_solicitacoes_exemplo()

        todas = listar_solicitacoes(
            self.conexao,
            status=None
        )

        concluidas = listar_solicitacoes(
            self.conexao,
            status="concluida"
        )

        self.assertEqual(len(todas), 4)
        self.assertEqual(len(concluidas), 1)
        self.assertEqual(
            concluidas[0]["descricao"],
            "Chamado finalizado"
        )

    # Rejeita um status desconhecido
    def test_listar_solicitacoes_filtro_invalido(self):
        with self.assertRaises(ValueError):
            listar_solicitacoes(
                self.conexao,
                status="cancelada"
            )

    # Insere um alerta e retorna a quantidade criada
    def test_registrar_alerta_valido(self):
        sensor_id = self.criar_sensor_para_alertas()

        alerta = self.criar_alerta_exemplo(sensor_id)

        quantidade = registrar_alertas(
            self.conexao,
            [alerta]
        )

        registro = self.conexao.execute(
            "SELECT * FROM alertas"
        ).fetchone()

        self.assertEqual(quantidade, 1)
        self.assertEqual(registro["sensor_id"], sensor_id)
        self.assertEqual(registro["nivel"], "alto")
        self.assertEqual(registro["status"], "aberto")

    # Não duplica nem reabre um alerta já registrado
    def test_registrar_alerta_idempotente(self):
        sensor_id = self.criar_sensor_para_alertas()
        alerta = self.criar_alerta_exemplo(sensor_id)

        primeira = registrar_alertas(
            self.conexao,
            [alerta]
        )

        self.conexao.execute(
            "UPDATE alertas SET status = 'resolvido'"
        )
        self.conexao.commit()

        segunda = registrar_alertas(
            self.conexao,
            [alerta]
        )

        registro = self.conexao.execute(
            "SELECT status FROM alertas"
        ).fetchone()

        self.assertEqual(primeira, 1)
        self.assertEqual(segunda, 0)
        self.assertEqual(registro["status"], "resolvido")

    # Impede alterar silenciosamente um alerta existente
    def test_registrar_alerta_conflitante(self):
        sensor_id = self.criar_sensor_para_alertas()
        alerta = self.criar_alerta_exemplo(sensor_id)

        registrar_alertas(self.conexao, [alerta])

        conflitante = {
            **alerta,
            "mensagem": "Mensagem diferente."
        }

        with self.assertRaises(ValueError):
            registrar_alertas(
                self.conexao,
                [conflitante]
            )

        registro = self.conexao.execute(
            "SELECT mensagem FROM alertas"
        ).fetchone()

        self.assertEqual(
            registro["mensagem"],
            alerta["mensagem"]
        )

    # Um erro deve desfazer todas as inserções do lote
    def test_registrar_alertas_rollback(self):
        sensor_id = self.criar_sensor_para_alertas()

        alerta_valido = self.criar_alerta_exemplo(sensor_id)

        alerta_invalido = {
            **alerta_valido,
            "ciclo": 2,
            "nivel": "urgente"
        }

        with self.assertRaises(ValueError):
            registrar_alertas(
                self.conexao,
                [alerta_valido, alerta_invalido]
            )

        quantidade = self.conexao.execute(
            "SELECT COUNT(*) FROM alertas"
        ).fetchone()[0]

        self.assertEqual(quantidade, 0)

    # Não permite alertas vinculados a sensor inexistente
    def test_registrar_alerta_sensor_inexistente(self):
        alerta = self.criar_alerta_exemplo(
            sensor_id=9999
        )

        with self.assertRaises(sqlite3.IntegrityError):
            registrar_alertas(
                self.conexao,
                [alerta]
            )

if __name__ == "__main__":
    unittest.main()