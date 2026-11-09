# Testes Automatizados da Interface do Menu de Dados do Sistema Aurora Siger
import io
import unittest
import csv
import tempfile

from contextlib import redirect_stdout
from unittest.mock import patch
from pathlib import Path
from gerar_dados_iniciais import gerar_csv_inicial

from banco_dados import (
    abrir_conexao,
    inicializar_banco,
    cadastrar_modulo,
    buscar_modulo_por_codigo,
    cadastrar_sensor,
    registrar_leitura
)

from codigo_fonte import (
    exibir_listagem_modulos,
    exibir_cadastro_modulo,
    exibir_busca_modulo,
    exibir_atualizacao_modulo,
    exibir_exclusao_modulo,
    exibir_listagem_sensores,
    exibir_consulta_leituras,
    exibir_serie_energia,
    exibir_importacao_dados,
    menu_dados
)


class TestInterfaceDados(unittest.TestCase):

    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)

        inicializar_banco(self.conexao)

    # Apresenta mensagem quando não existe módulos
    def test_listagem_vazia(self):

        saida = io.StringIO()

        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_listagem_modulos(self.conexao)

        self.assertIn(
            "Nenhum módulo cadastrado.",
            saida.getvalue()
        )

    # Apresenta os dados de um módulo cadastrado
    def test_listagem_modulo_existente(self):

        cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        saida = io.StringIO()

        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_listagem_modulos(self.conexao)

        self.assertIn(
            "MOD-HAB-01",
            saida.getvalue()
        )

        self.assertIn(
            "Habitação",
            saida.getvalue()
        )

    # A opção zero retorna do submenu normalmente
    def test_submenu_voltar(self):

        with (
            patch("builtins.input", return_value="0"),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho")
        ):
            resultado = menu_dados(self.conexao)

        self.assertIsNone(resultado)

    # Cadastra um módulo utilizando entradas simuladas
    def test_cadastro_interface_sucesso(self):

        entradas = [
            "MOD-UI-01",
            "Módulo de Interface",
            "laboratorio",
            "1",
            "ativo"
        ]

        saida = io.StringIO()

        with (
            patch("builtins.input", side_effect=entradas),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_cadastro_modulo(self.conexao)

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-UI-01"
        )

        self.assertIsNotNone(modulo)
        self.assertEqual(modulo["nome"], "Módulo de Interface")
        self.assertEqual(modulo["critico"], 1)
        self.assertEqual(modulo["status"], "ativo")

        self.assertIn(
            "Módulo cadastrado com sucesso",
            saida.getvalue()
        )

    # A interface apresenta erro para código duplicado
    def test_cadastro_interface_codigo_duplicado(self):

        cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-UI-01",
                "nome": "Módulo Original",
                "tipo": "laboratorio"
            }
        )

        entradas = [
            "MOD-UI-01",
            "Módulo Duplicado",
            "laboratorio",
            "0",
            "ativo"
        ]

        saida = io.StringIO()

        with (
            patch("builtins.input", side_effect=entradas),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_cadastro_modulo(self.conexao)

        quantidade = self.conexao.execute(
            "SELECT COUNT(*) FROM modulos"
        ).fetchone()[0]

        self.assertEqual(quantidade, 1)
        self.assertIn(
            "Não foi possível cadastrar",
            saida.getvalue()
        )

    # Rejeita criticidade diferente de zero ou um
    def test_cadastro_interface_criticidade_invalida(self):

        entradas = [
            "MOD-UI-02",
            "Módulo de Teste",
            "laboratorio",
            "2"
        ]

        saida = io.StringIO()

        with (
            patch("builtins.input", side_effect=entradas),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_cadastro_modulo(self.conexao)

        quantidade = self.conexao.execute(
            "SELECT COUNT(*) FROM modulos"
        ).fetchone()[0]

        self.assertEqual(quantidade, 0)
        self.assertIn(
            "Dados inválidos",
            saida.getvalue()
        )

    # Apresenta os dados de um módulo encontrado
    def test_busca_interface_existente(self):

        cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao",
                "critico": 1
            }
        )

        saida = io.StringIO()

        with (
            patch(
                "builtins.input",
                return_value="MOD-HAB-01"
            ),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_busca_modulo(self.conexao)

        self.assertIn(
            "Módulo encontrado",
            saida.getvalue()
        )

        self.assertIn(
            "Habitação",
            saida.getvalue()
        )

    # Apresenta mensagem quando o código não existe
    def test_busca_interface_inexistente(self):

        saida = io.StringIO()

        with (
            patch(
                "builtins.input",
                return_value="MOD-INEXISTENTE"
            ),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            exibir_busca_modulo(self.conexao)

        self.assertIn(
            "Nenhum módulo encontrado",
            saida.getvalue()
        )

    # Confirma que as opções 2 e 3 chamam as funções corretas
    def test_submenu_cadastro_e_busca(self):

        with (
            patch(
                "builtins.input",
                side_effect=["2", "3", "0"]
            ),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch(
                "codigo_fonte.exibir_cadastro_modulo"
            ) as cadastro,
            patch(
                "codigo_fonte.exibir_busca_modulo"
            ) as busca
        ):
            menu_dados(self.conexao)

        cadastro.assert_called_once_with(self.conexao)
        busca.assert_called_once_with(self.conexao)

    # Executa uma tela com entradas simuladas
    def executar_interface(self, funcao, entradas):

        saida = io.StringIO()

        with (
            patch("builtins.input", side_effect=entradas),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            redirect_stdout(saida)
        ):
            funcao(self.conexao)

        return saida.getvalue()

    # Atualiza somente os campos informados
    def test_atualizacao_interface_sucesso(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-UI-ALTER-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        saida = self.executar_interface(
            exibir_atualizacao_modulo,
            [
                str(modulo_id),
                "",
                "Habitação Principal",
                "",
                "",
                "manutencao"
            ]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-UI-ALTER-01"
        )

        self.assertEqual(
            modulo["nome"],
            "Habitação Principal"
        )
        self.assertEqual(modulo["status"], "manutencao")
        self.assertEqual(modulo["tipo"], "habitacao")

        self.assertIn(
            "Módulo atualizado com sucesso",
            saida
        )

    # Não executa UPDATE quando nada é informado
    def test_atualizacao_interface_sem_alteracoes(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-UI-01",
                "nome": "Módulo Original",
                "tipo": "laboratorio"
            }
        )

        saida = self.executar_interface(
            exibir_atualizacao_modulo,
            [str(modulo_id), "", "", "", "", ""]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-UI-01"
        )

        self.assertEqual(
            modulo["nome"],
            "Módulo Original"
        )
        self.assertIn(
            "Nenhuma alteração informada",
            saida
        )

    # Informa quando o ID não existe
    def test_atualizacao_interface_inexistente(self):

        saida = self.executar_interface(
            exibir_atualizacao_modulo,
            ["9999"]
        )

        self.assertIn("Módulo não encontrado", saida)

    # Impede atualização para um código já cadastrado
    def test_atualizacao_interface_codigo_duplicado(self):

        cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-A-01",
                "nome": "Módulo A",
                "tipo": "laboratorio"
            }
        )

        segundo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-B-01",
                "nome": "Módulo B",
                "tipo": "laboratorio"
            }
        )

        saida = self.executar_interface(
            exibir_atualizacao_modulo,
            [
                str(segundo_id),
                "MOD-A-01",
                "",
                "",
                "",
                ""
            ]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-B-01"
        )

        self.assertIsNotNone(modulo)
        self.assertIn(
            "Não foi possível atualizar",
            saida
        )

    # Rejeita status operacional desconhecido
    def test_atualizacao_interface_status_invalido(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-UI-01",
                "nome": "Módulo",
                "tipo": "laboratorio"
            }
        )

        saida = self.executar_interface(
            exibir_atualizacao_modulo,
            [
                str(modulo_id),
                "",
                "",
                "",
                "",
                "desconhecido"
            ]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-UI-01"
        )

        self.assertEqual(modulo["status"], "ativo")
        self.assertIn("Dados inválidos", saida)

    # Exclui um módulo após confirmação explícita
    def test_exclusao_interface_sucesso(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-UI-EXC-01",
                "nome": "Módulo Temporário",
                "tipo": "laboratorio"
            }
        )

        saida = self.executar_interface(
            exibir_exclusao_modulo,
            [str(modulo_id), "EXCLUIR"]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-UI-EXC-01"
        )

        self.assertIsNone(modulo)
        self.assertIn(
            "Módulo excluído com sucesso",
            saida
        )

    # Preserva o módulo quando não há confirmação
    def test_exclusao_interface_cancelada(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-UI-EXC-02",
                "nome": "Módulo Permanente",
                "tipo": "laboratorio"
            }
        )

        saida = self.executar_interface(
            exibir_exclusao_modulo,
            [str(modulo_id), "NAO"]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-UI-EXC-02"
        )

        self.assertIsNotNone(modulo)
        self.assertIn("Exclusão cancelada", saida)

    # Impede exclusão de módulo com sensor associado
    def test_exclusao_interface_com_sensor(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-HAB-01",
                "nome": "Habitação",
                "tipo": "habitacao"
            }
        )

        cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-HAB-01",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        saida = self.executar_interface(
            exibir_exclusao_modulo,
            [str(modulo_id), "EXCLUIR"]
        )

        modulo = buscar_modulo_por_codigo(
            self.conexao,
            "MOD-HAB-01"
        )

        self.assertIsNotNone(modulo)
        self.assertIn(
            "Não foi possível excluir",
            saida
        )

    # Verifica o encaminhamento das opções 4 e 5 do submenu
    def test_submenu_atualizar_e_excluir(self):

        with (
            patch(
                "builtins.input",
                side_effect=["4", "5", "0"]
            ),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch(
                "codigo_fonte.exibir_atualizacao_modulo"
            ) as atualizacao,
            patch(
                "codigo_fonte.exibir_exclusao_modulo"
            ) as exclusao
        ):
            menu_dados(self.conexao)

        atualizacao.assert_called_once_with(self.conexao)
        exclusao.assert_called_once_with(self.conexao)

    # Cria sensores e leituras para testar as consultas
    def preparar_medicoes_interface(self):

        modulo_id = cadastrar_modulo(
            self.conexao,
            {
                "codigo": "MOD-ENE-TESTE",
                "nome": "Energia de Teste",
                "tipo": "energia",
                "critico": 1
            }
        )

        sensor_consumo = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-CONS-TESTE",
                "modulo_id": modulo_id,
                "tipo": "consumo_kw",
                "unidade": "kW"
            }
        )

        sensor_geracao = cadastrar_sensor(
            self.conexao,
            {
                "codigo": "SEN-GER-TESTE",
                "modulo_id": modulo_id,
                "tipo": "geracao_kw",
                "unidade": "kW"
            }
        )

        medicoes = [
            (1, 2.0, 4.0),
            (2, 3.0, 1.0)
        ]

        for ciclo, consumo, geracao in medicoes:

            for sensor_id, valor in (
                (sensor_consumo, consumo),
                (sensor_geracao, geracao)
            ):

                registrar_leitura(
                    self.conexao,
                    {
                        "sensor_id": sensor_id,
                        "ciclo": ciclo,
                        "instante": "2026-11-09T12:00:00Z",
                        "valor": valor
                    }
                )

    # Informa quando não existem sensores
    def test_interface_sensores_vazio(self):

        saida = self.executar_interface(
            exibir_listagem_sensores,
            []
        )

        self.assertIn(
            "Nenhum sensor cadastrado",
            saida
        )

    # Apresenta os sensores existentes
    def test_interface_sensores_cadastrados(self):

        self.preparar_medicoes_interface()

        saida = self.executar_interface(
            exibir_listagem_sensores,
            []
        )

        self.assertIn(
            "Total de sensores: 2",
            saida
        )

        self.assertIn(
            "SEN-CONS-TESTE",
            saida
        )

        self.assertIn(
            "SEN-GER-TESTE",
            saida
        )

    # Apresenta mensagem quando não há leituras
    def test_interface_leituras_vazio(self):

        saida = self.executar_interface(
            exibir_consulta_leituras,
            [""]
        )

        self.assertIn(
            "Nenhuma leitura encontrada",
            saida
        )

    # Consulta leituras sem informar o ciclo
    def test_interface_leituras_todos_ciclos(self):

        self.preparar_medicoes_interface()

        saida = self.executar_interface(
            exibir_consulta_leituras,
            [""]
        )

        self.assertIn(
            "4 leitura(s) encontrada(s)",
            saida
        )

        self.assertIn("Ciclo: 1", saida)
        self.assertIn("Ciclo: 2", saida)

    # Apresenta somente as medições do ciclo 2
    def test_interface_leituras_filtrar_ciclo(self):

        self.preparar_medicoes_interface()

        saida = self.executar_interface(
            exibir_consulta_leituras,
            ["2"]
        )

        self.assertIn(
            "2 leitura(s) encontrada(s)",
            saida
        )

        self.assertIn("Ciclo: 2", saida)
        self.assertNotIn("Ciclo: 1", saida)

    # Rejeita filtros inválidos
    def test_interface_leituras_ciclo_invalido(self):

        for entrada in ("abc", "0", "-3"):
            with self.subTest(entrada=entrada):

                saida = self.executar_interface(
                    exibir_consulta_leituras,
                    [entrada]
                )

                self.assertIn(
                    "Dados inválidos",
                    saida
                )

    # Informa quando não existem dados energéticos
    def test_interface_energia_vazia(self):

        saida = self.executar_interface(
            exibir_serie_energia,
            []
        )

        self.assertIn(
            "Nenhum dado energético disponível",
            saida
        )

    # Apresenta corretamente os saldos por ciclo
    def test_interface_energia_saldos(self):

        self.preparar_medicoes_interface()

        saida = self.executar_interface(
            exibir_serie_energia,
            []
        )

        self.assertIn(
            "Total de ciclos energéticos: 2",
            saida
        )

        self.assertIn(
            "Consumo: 2.00 kW",
            saida
        )

        self.assertIn(
            "Geração: 4.00 kW",
            saida
        )

        self.assertIn(
            "Saldo: +2.00 kW",
            saida
        )

        self.assertIn(
            "Saldo: -2.00 kW",
            saida
        )

        self.assertIn("Superávit", saida)
        self.assertIn("Déficit", saida)

    # Verifica o encaminhamento das opções 6, 7 e 8 do submenu
    def test_submenu_consultas(self):

        with (
            patch(
                "builtins.input",
                side_effect=["6", "7", "8", "0"]
            ),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch(
                "codigo_fonte.exibir_listagem_sensores"
            ) as listar,
            patch(
                "codigo_fonte.exibir_consulta_leituras"
            ) as leituras,
            patch(
                "codigo_fonte.exibir_serie_energia"
            ) as energia
        ):
            menu_dados(self.conexao)

        listar.assert_called_once_with(self.conexao)
        leituras.assert_called_once_with(self.conexao)
        energia.assert_called_once_with(self.conexao)

    # Gera um CSV temporário para os testes
    def criar_csv_para_interface(self):

        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)

        caminho = Path(diretorio.name) / "dados_teste.csv"

        gerar_csv_inicial(caminho)

        return caminho

    # Importa os dados e apresenta os totais
    def test_interface_importacao_sucesso(self):

        caminho = self.criar_csv_para_interface()

        with patch("codigo_fonte.CAMINHO_CSV", caminho):
            saida = self.executar_interface(
                exibir_importacao_dados,
                ["IMPORTAR"]
            )

        total = self.conexao.execute(
            "SELECT COUNT(*) FROM leituras"
        ).fetchone()[0]

        self.assertEqual(total, 320)
        self.assertIn(
            "Novas leituras importadas: 320",
            saida
        )
        self.assertIn("Módulos: 5", saida)
        self.assertIn("Sensores: 10", saida)
        self.assertIn("Leituras: 320", saida)

    # Uma segunda importação não duplica leituras
    def test_interface_importacao_repetida(self):

        caminho = self.criar_csv_para_interface()

        with patch("codigo_fonte.CAMINHO_CSV", caminho):

            self.executar_interface(
                exibir_importacao_dados,
                ["IMPORTAR"]
            )

            saida = self.executar_interface(
                exibir_importacao_dados,
                ["IMPORTAR"]
            )

        total = self.conexao.execute(
            "SELECT COUNT(*) FROM leituras"
        ).fetchone()[0]

        self.assertEqual(total, 320)
        self.assertIn(
            "Novas leituras importadas: 0",
            saida
        )

    # Não importa dados sem confirmação
    def test_interface_importacao_cancelada(self):

        caminho = self.criar_csv_para_interface()

        with patch("codigo_fonte.CAMINHO_CSV", caminho):
            saida = self.executar_interface(
                exibir_importacao_dados,
                ["CANCELAR"]
            )

        total = self.conexao.execute(
            "SELECT COUNT(*) FROM leituras"
        ).fetchone()[0]

        self.assertEqual(total, 0)
        self.assertIn("Importação cancelada", saida)

    # Apresenta orientação quando o CSV não existe
    def test_interface_importacao_arquivo_ausente(self):

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "nao_existe.csv"

            with patch("codigo_fonte.CAMINHO_CSV", caminho):
                saida = self.executar_interface(
                    exibir_importacao_dados,
                    []
                )

        self.assertIn(
            "Arquivo CSV não encontrado",
            saida
        )

        self.assertIn(
            "gerar_dados_iniciais.py",
            saida
        )

    # Rejeita um arquivo com cabeçalho incorreto
    def test_interface_importacao_csv_invalido(self):

        caminho = self.criar_csv_para_interface()

        caminho.write_text(
            "sensor_codigo,ciclo,valor\n"
            "SEN-01,1,3.1\n",
            encoding="utf-8"
        )

        with patch("codigo_fonte.CAMINHO_CSV", caminho):
            saida = self.executar_interface(
                exibir_importacao_dados,
                ["IMPORTAR"]
            )

        total = self.conexao.execute(
            "SELECT COUNT(*) FROM leituras"
        ).fetchone()[0]

        self.assertEqual(total, 0)
        self.assertIn("Dados inválidos no CSV", saida)

    # Um CSV com erro não deixa importação parcial
    def test_interface_importacao_rollback(self):

        caminho = self.criar_csv_para_interface()

        with caminho.open(
            newline="",
            encoding="utf-8"
        ) as arquivo:
            leitor = csv.DictReader(arquivo)
            colunas = leitor.fieldnames
            linhas = list(leitor)

        # Introduz um erro depois de várias leituras válidas.
        linhas[200]["valor"] = "invalido"

        with caminho.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=colunas
            )
            escritor.writeheader()
            escritor.writerows(linhas)

        with patch("codigo_fonte.CAMINHO_CSV", caminho):
            saida = self.executar_interface(
                exibir_importacao_dados,
                ["IMPORTAR"]
            )

        for tabela in ("modulos", "sensores", "leituras"):
            total = self.conexao.execute(
                f"SELECT COUNT(*) FROM {tabela}"
            ).fetchone()[0]

            self.assertEqual(total, 0)

        self.assertIn("Dados inválidos no CSV", saida)

    # A opção 9 chama a interface de importação
    def test_submenu_importacao(self):
        with (
            patch(
                "builtins.input",
                side_effect=["9", "0"]
            ),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch(
                "codigo_fonte.exibir_importacao_dados"
            ) as importacao
        ):
            menu_dados(self.conexao)

        importacao.assert_called_once_with(self.conexao)

if __name__ == "__main__":
    unittest.main()