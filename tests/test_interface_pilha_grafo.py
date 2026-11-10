"""Etapa 03.3.B.2 — Testes de integração da pilha e do grafo no Menu 3.

Executar: python3 -B -m unittest discover -s tests -p 'test_interface_pilha_grafo.py' -v
"""

import io
import sqlite3
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from banco_dados import abrir_conexao, inicializar_banco, cadastrar_modulo
from estruturas_dados import PilhaHistorico
from codigo_fonte import (
    exibir_pilha_historico,
    exibir_grafo_dependencias,
    menu_estruturas_dados,
)


class TestInterfacePilhaGrafo(unittest.TestCase):
    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)
        inicializar_banco(self.conexao)

    def executar(self, funcao, *args, entradas=None):
        saida = io.StringIO()
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            patch("builtins.input", side_effect=entradas or []),
            redirect_stdout(saida),
        ):
            funcao(*args)
        return saida.getvalue()

    def criar_modulo(self, codigo, nome=None):
        return cadastrar_modulo(self.conexao, {
            "codigo": codigo,
            "nome": nome or codigo,
            "tipo": "infraestrutura",
        })

    def test_pilha_vazia_e_opcao_desfazer(self):
        historico = PilhaHistorico()
        saida = self.executar(exibir_pilha_historico, historico,
                              entradas=["2", "3", "0"])
        self.assertIn("Pilha vazia: nenhuma ação registrada", saida)
        self.assertIn("Pilha vazia: nada a desfazer", saida)
        self.assertEqual(len(historico), 0)

    def test_pilha_empilhar_e_listar_em_ordem_lifo(self):
        historico = PilhaHistorico()
        saida = self.executar(
            exibir_pilha_historico, historico,
            entradas=["1", "Inspecionar bateria", "energia",
                      "1", "Verificar sensor", "manutencao", "2", "0"],
        )
        self.assertEqual([r["acao"] for r in historico.listar()],
                         ["Verificar sensor", "Inspecionar bateria"])
        trecho = saida.rsplit("Histórico (mais recente primeiro):", 1)[-1]
        self.assertLess(trecho.index("Verificar sensor"), trecho.index("Inspecionar bateria"))

    def test_pilha_desfazer_remove_somente_ultimo_registro(self):
        historico = PilhaHistorico()
        historico.empilhar("primeira", instante="t1")
        historico.empilhar("segunda", instante="t2")
        saida = self.executar(exibir_pilha_historico, historico,
                              entradas=["3", "DESFAZER", "0"])
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico.topo()["acao"], "primeira")
        self.assertIn("Registro removido somente da pilha: segunda", saida)
        self.assertIn("Nenhuma ação do banco de dados foi revertida", saida)

    def test_pilha_cancelamento_preserva_registro(self):
        historico = PilhaHistorico()
        historico.empilhar("primeira", instante="t1")
        saida = self.executar(exibir_pilha_historico, historico,
                              entradas=["3", "NAO", "0"])
        self.assertEqual(len(historico), 1)
        self.assertIn("Desfazer cancelado", saida)

    def test_pilha_rejeita_acao_sem_texto(self):
        historico = PilhaHistorico()
        saida = self.executar(exibir_pilha_historico, historico,
                              entradas=["1", "   ", "detalhe", "0"])
        self.assertEqual(len(historico), 0)
        self.assertIn("Dados inválidos", saida)

    def test_pilha_permanece_entre_visitas_dentro_do_menu3(self):
        # Ao entrar de novo na opção 4, a mesma pilha deve ser usada.
        saida = self.executar(
            menu_estruturas_dados, self.conexao,
            entradas=["4", "1", "Verificar energia", "prioridade alta", "0",
                      "4", "2", "0", "0"],
        )
        self.assertIn("Histórico (mais recente primeiro):", saida)
        self.assertIn("Verificar energia", saida)

    def test_grafo_sem_modulos(self):
        saida = self.executar(exibir_grafo_dependencias, self.conexao)
        self.assertIn("Nenhum módulo cadastrado", saida)

    def test_grafo_falha_energia_propagacao_direta_e_indireta(self):
        for codigo in ("MOD-ENE-01", "MOD-HAB-01", "MOD-AGR-01",
                       "MOD-COM-01", "MOD-LAB-01"):
            self.criar_modulo(codigo)
        antes = self.conexao.total_changes
        saida = self.executar(exibir_grafo_dependencias, self.conexao,
                              entradas=["MOD-ENE-01"])
        self.assertIn("Total de módulos afetados: 4", saida)
        for codigo in ("MOD-HAB-01", "MOD-AGR-01", "MOD-COM-01"):
            self.assertIn(f"{codigo} - {codigo} (direto)", saida)
        self.assertIn("MOD-LAB-01 - MOD-LAB-01 (indireto)", saida)
        self.assertEqual(antes, self.conexao.total_changes)

    def test_grafo_falha_agricultura_afeta_so_laboratorio(self):
        self.criar_modulo("MOD-AGR-01")
        self.criar_modulo("MOD-LAB-01")
        saida = self.executar(exibir_grafo_dependencias, self.conexao,
                              entradas=["MOD-AGR-01"])
        self.assertIn("Total de módulos afetados: 1", saida)
        self.assertIn("MOD-LAB-01 - MOD-LAB-01 (direto)", saida)

    def test_grafo_modulos_faltantes_nao_sao_inventados(self):
        self.criar_modulo("MOD-ENE-01")
        self.criar_modulo("MOD-HAB-01")
        saida = self.executar(exibir_grafo_dependencias, self.conexao,
                              entradas=["MOD-ENE-01"])
        self.assertIn("Total de módulos afetados: 1", saida)
        self.assertNotIn("MOD-AGR-01 ->", saida)
        self.assertNotIn("MOD-LAB-01 ->", saida)

    def test_grafo_modulo_isolado_e_suportado(self):
        self.criar_modulo("MOD-OUT-99", "Módulo auxiliar")
        saida = self.executar(exibir_grafo_dependencias, self.conexao,
                              entradas=["MOD-OUT-99"])
        self.assertIn("Nenhuma dependência do cenário ilustrativo", saida)
        self.assertIn("Total de módulos afetados: 0", saida)

    def test_grafo_codigo_ausente_ou_invalido(self):
        self.criar_modulo("MOD-ENE-01")
        for codigo in ("", "MOD-INEXISTENTE"):
            with self.subTest(codigo=codigo):
                saida = self.executar(exibir_grafo_dependencias, self.conexao,
                                      entradas=[codigo])
                self.assertIn("Dados inválidos", saida)

    def test_grafo_erro_sql_e_tratado(self):
        self.conexao.close()
        saida = self.executar(exibir_grafo_dependencias, self.conexao)
        self.assertIn("Erro ao consultar os módulos", saida)

    def test_submenu_encaminha_opcoes_4_e_5(self):
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.exibir_pilha_historico") as pilha,
            patch("codigo_fonte.exibir_grafo_dependencias") as grafo,
            patch("builtins.input", side_effect=["4", "5", "0"]),
        ):
            menu_estruturas_dados(self.conexao)

        pilha.assert_called_once()
        self.assertIsInstance(pilha.call_args.args[0], PilhaHistorico)
        grafo.assert_called_once_with(self.conexao)


if __name__ == "__main__":
    unittest.main()
