# Testes Automatizados das Estruturas de Dados do Sistema Aurora Siger
# O teste verifica hash, fila, pilha e grafo

import unittest
from collections import deque

from estruturas_dados import (
    GrafoModulos,
    PilhaHistorico,
    atender_proxima_solicitacao,
    buscar_sensor_hash,
    construir_grafo_modulos,
    construir_indice_sensores,
    montar_fila_solicitacoes,
)

# Testes da tabela hash de sensores
class TestIndiceSensores(unittest.TestCase):
    def setUp(self):
        self.sensores = [
            {"id": 1, "codigo": "SEN-ENE-01", "tipo": "geracao_kw"},
            {"id": 2, "codigo": "SEN-HAB-01", "tipo": "consumo_kw"},
        ]

    # O índice usa o código como chave
    def test_construir_indice(self):
        indice = construir_indice_sensores(self.sensores)

        self.assertEqual(set(indice), {"SEN-ENE-01", "SEN-HAB-01"})
        self.assertEqual(indice["SEN-HAB-01"]["id"], 2)

    # Busca por código existente retorna o sensor
    def test_buscar_sensor_existente(self):
        indice = construir_indice_sensores(self.sensores)
        self.assertEqual(buscar_sensor_hash(indice, "SEN-ENE-01")["id"], 1)

    # Busca sem resultado retorna None
    def test_buscar_sensor_inexistente(self):
        indice = construir_indice_sensores(self.sensores)
        self.assertIsNone(buscar_sensor_hash(indice, "SEN-XXX"))

    # Lista vazia gera índice vazio
    def test_lista_vazia(self):
        self.assertEqual(construir_indice_sensores([]), {})

    # Código repetido sinaliza erro
    def test_codigo_repetido(self):
        with self.assertRaises(ValueError):
            construir_indice_sensores(self.sensores + [{"id": 3, "codigo": "SEN-ENE-01"}])

    # Sensor sem código sinaliza erro
    def test_sensor_sem_codigo(self):
        with self.assertRaises(ValueError):
            construir_indice_sensores([{"id": 1}])

# Testes da fila de solicitações
class TestFilaSolicitacoes(unittest.TestCase):
    # A fila é uma deque ordenada pelo ID, mesmo com a entrada desordenada
    def test_ordem_de_chegada(self):
        entrada = [{"id": 3}, {"id": 1}, {"id": 2}]
        fila = montar_fila_solicitacoes(entrada)

        self.assertIsInstance(fila, deque)
        self.assertEqual([s["id"] for s in fila], [1, 2, 3])

    # A lista original não é alterada
    def test_nao_altera_a_entrada(self):
        entrada = [{"id": 3}, {"id": 1}]
        montar_fila_solicitacoes(entrada)

        self.assertEqual([s["id"] for s in entrada], [3, 1])

    # Lista vazia gera fila vazia
    def test_lista_vazia(self):
        self.assertEqual(len(montar_fila_solicitacoes([])), 0)

    # Solicitação sem ID sinaliza erro
    def test_solicitacao_sem_id(self):
        with self.assertRaises(ValueError):
            montar_fila_solicitacoes([{"descricao": "sem id"}])

    # Atender retira sempre a mais antiga (FIFO)
    def test_atender_proxima(self):
        fila = montar_fila_solicitacoes([{"id": 2}, {"id": 1}])

        self.assertEqual(atender_proxima_solicitacao(fila)["id"], 1)
        self.assertEqual(atender_proxima_solicitacao(fila)["id"], 2)
        self.assertIsNone(atender_proxima_solicitacao(fila))

# Testes da pilha de histórico
class TestPilhaHistorico(unittest.TestCase):
    def setUp(self):
        self.pilha = PilhaHistorico()

    # Pilha nova está vazia
    def test_pilha_vazia(self):
        self.assertTrue(self.pilha.esta_vazia())
        self.assertEqual(len(self.pilha), 0)
        self.assertIsNone(self.pilha.topo())
        self.assertIsNone(self.pilha.desfazer())
        self.assertEqual(self.pilha.listar(), [])

    # Empilhar devolve o registro e o coloca no topo
    def test_empilhar(self):
        registro = self.pilha.empilhar("alerta_resolvido", "alerta 7", "2026-11-03T12:00:00Z")

        self.assertEqual(
            registro,
            {"acao": "alerta_resolvido", "detalhe": "alerta 7",
             "instante": "2026-11-03T12:00:00Z"},
        )
        self.assertEqual(self.pilha.topo(), registro)
        self.assertEqual(len(self.pilha), 1)

    # Sem informar o instante, ele é preenchido automaticamente
    def test_instante_automatico(self):
        registro = self.pilha.empilhar("manutencao_iniciada")
        self.assertRegex(registro["instante"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    # Desfazer remove na ordem inversa da inserção (LIFO)
    def test_desfazer_em_ordem_lifo(self):
        self.pilha.empilhar("a", instante="t1")
        self.pilha.empilhar("b", instante="t2")
        self.pilha.empilhar("c", instante="t3")

        self.assertEqual(self.pilha.desfazer()["acao"], "c")
        self.assertEqual(self.pilha.desfazer()["acao"], "b")
        self.assertEqual(self.pilha.topo()["acao"], "a")
        self.assertEqual(len(self.pilha), 1)

    # Listar mostra da mais recente para a mais antiga
    def test_listar(self):
        self.pilha.empilhar("a", instante="t1")
        self.pilha.empilhar("b", instante="t2")

        self.assertEqual([r["acao"] for r in self.pilha.listar()], ["b", "a"])

    # Ação vazia ou inválida sinaliza erro
    def test_acao_invalida(self):
        for acao in ("", "   ", None, 5):
            with self.subTest(acao=acao):
                with self.assertRaises(ValueError):
                    self.pilha.empilhar(acao)

# Testes do grafo de dependência entre módulos
class TestGrafoModulos(unittest.TestCase):
    def setUp(self):
        # energia -> agricultura -> habitacao; energia -> laboratorio
        self.grafo = construir_grafo_modulos([
            ("agricultura", "energia"),
            ("laboratorio", "energia"),
            ("habitacao", "agricultura"),
        ])

    # Falha na energia afeta todos os dependentes, diretos e indiretos
    def test_impacto_em_cadeia(self):
        self.assertEqual(
            self.grafo.modulos_afetados("energia"),
            ["agricultura", "laboratorio", "habitacao"],
        )

    # Falha em módulo intermediário afeta só quem depende dele
    def test_impacto_intermediario(self):
        self.assertEqual(self.grafo.modulos_afetados("agricultura"), ["habitacao"])

    # Módulo sem dependentes não afeta ninguém
    def test_modulo_folha(self):
        self.assertEqual(self.grafo.modulos_afetados("habitacao"), [])

    # Dependentes diretos
    def test_dependentes_diretos(self):
        self.assertEqual(self.grafo.dependentes_diretos("energia"), ["agricultura", "laboratorio"])
        self.assertEqual(self.grafo.dependentes_diretos("inexistente"), [])

    # Módulo inexistente sinaliza erro
    def test_modulo_inexistente(self):
        with self.assertRaises(KeyError):
            self.grafo.modulos_afetados("inexistente")

    # Dependência repetida não duplica a aresta
    def test_dependencia_repetida(self):
        self.grafo.adicionar_dependencia("agricultura", "energia")
        self.assertEqual(self.grafo.dependentes_diretos("energia").count("agricultura"), 1)

    # Ciclos não geram laço infinito nem repetem módulos
    def test_ciclo(self):
        grafo = construir_grafo_modulos([("a", "b"), ("b", "a")])
        self.assertEqual(grafo.modulos_afetados("a"), ["b"])

    # Dependência de si mesmo ou código inválido sinaliza erro
    def test_entradas_invalidas(self):
        with self.assertRaises(ValueError):
            self.grafo.adicionar_dependencia("energia", "energia")
        with self.assertRaises(ValueError):
            self.grafo.adicionar_modulo("")
        with self.assertRaises(ValueError):
            self.grafo.adicionar_dependencia("x", None)

    # Módulo isolado pode existir sem dependências
    def test_modulo_isolado(self):
        grafo = GrafoModulos()
        grafo.adicionar_modulo("comunicacao")

        self.assertEqual(grafo.modulos(), ["comunicacao"])
        self.assertEqual(grafo.modulos_afetados("comunicacao"), [])

if __name__ == "__main__":
    unittest.main()
