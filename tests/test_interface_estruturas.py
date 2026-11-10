"""Testes da Etapa 03.3.B.1: busca hash e solicitações FIFO pela interface."""

import io
import sqlite3
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from banco_dados import (
    abrir_conexao, inicializar_banco, cadastrar_modulo,
    cadastrar_sensor, registrar_solicitacao, listar_solicitacoes,
)
from codigo_fonte import (
    exibir_busca_sensor_hash, exibir_cadastro_solicitacao,
    exibir_fila_solicitacoes, menu_estruturas_dados, menu_principal,
)


class TestInterfaceEstruturas(unittest.TestCase):
    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)
        inicializar_banco(self.conexao)

    def executar(self, funcao, entradas=None):
        saida = io.StringIO()
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar"),
            patch("builtins.input", side_effect=entradas or []),
            redirect_stdout(saida),
        ):
            funcao(self.conexao)
        return saida.getvalue()

    def criar_modulo(self):
        return cadastrar_modulo(self.conexao, {
            "codigo": "MOD-HAB-01", "nome": "Habitação", "tipo": "habitacao",
            "critico": 1,
        })

    def criar_sensor(self, modulo_id):
        return cadastrar_sensor(self.conexao, {
            "codigo": "SEN-HAB-CONS-01", "modulo_id": modulo_id,
            "tipo": "consumo_kw", "unidade": "kW",
        })

    def criar_solicitacao(self, modulo_id, descricao, prioridade="media"):
        return registrar_solicitacao(self.conexao, {
            "modulo_id": modulo_id, "descricao": descricao,
            "prioridade": prioridade,
        })

    def test_hash_sem_sensores(self):
        saida = self.executar(exibir_busca_sensor_hash)
        self.assertIn("Nenhum sensor cadastrado", saida)

    def test_hash_busca_sensor_existente(self):
        modulo_id = self.criar_modulo()
        self.criar_sensor(modulo_id)
        saida = self.executar(exibir_busca_sensor_hash, ["  SEN-HAB-CONS-01  "])
        self.assertIn("Sensor encontrado via tabela hash", saida)
        self.assertIn("SEN-HAB-CONS-01", saida)
        self.assertIn("consumo_kw", saida)

    def test_hash_sensor_inexistente(self):
        modulo_id = self.criar_modulo()
        self.criar_sensor(modulo_id)
        saida = self.executar(exibir_busca_sensor_hash, ["SEN-NAO-EXISTE"])
        self.assertIn("Sensor não encontrado no índice hash", saida)

    def test_hash_codigo_vazio(self):
        modulo_id = self.criar_modulo()
        self.criar_sensor(modulo_id)
        saida = self.executar(exibir_busca_sensor_hash, ["   "])
        self.assertIn("Dados inválidos", saida)

    def test_cadastro_sem_modulos(self):
        saida = self.executar(exibir_cadastro_solicitacao)
        self.assertIn("Nenhum módulo cadastrado", saida)

    def test_cadastro_solicitacao_persiste_no_banco(self):
        modulo_id = self.criar_modulo()
        saida = self.executar(
            exibir_cadastro_solicitacao,
            [str(modulo_id), "Verificar bateria", "ALTA"],
        )
        self.assertIn("Solicitação registrada no SQLite", saida)
        registros = listar_solicitacoes(self.conexao)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["descricao"], "Verificar bateria")
        self.assertEqual(registros[0]["prioridade"], "alta")
        self.assertEqual(registros[0]["status"], "pendente")

    def test_cadastro_prioridade_padrao(self):
        modulo_id = self.criar_modulo()
        saida = self.executar(exibir_cadastro_solicitacao,
                              [str(modulo_id), "Revisar estufa", ""])
        self.assertIn("Solicitação registrada", saida)
        self.assertEqual(listar_solicitacoes(self.conexao)[0]["prioridade"], "media")

    def test_cadastro_modulo_inexistente_preserva_integridade(self):
        self.criar_modulo()
        saida = self.executar(exibir_cadastro_solicitacao,
                              ["9999", "Revisar", "baixa"])
        self.assertIn("módulo inexistente", saida)
        self.assertEqual(listar_solicitacoes(self.conexao), [])

    def test_cadastro_prioridade_invalida(self):
        modulo_id = self.criar_modulo()
        saida = self.executar(exibir_cadastro_solicitacao,
                              [str(modulo_id), "Revisar", "urgente"])
        self.assertIn("Dados inválidos", saida)
        self.assertEqual(listar_solicitacoes(self.conexao), [])

    def test_fila_vazia(self):
        saida = self.executar(exibir_fila_solicitacoes)
        self.assertIn("Nenhuma solicitação pendente", saida)

    def test_fila_fifo_simulacao_nao_muda_o_banco(self):
        modulo_id = self.criar_modulo()
        primeiro = self.criar_solicitacao(modulo_id, "primeira", "baixa")
        segundo = self.criar_solicitacao(modulo_id, "segunda", "alta")
        saida = self.executar(exibir_fila_solicitacoes, ["SIMULAR"])
        self.assertIn("Total de solicitações pendentes: 2", saida)
        self.assertIn(f"Próxima solicitação simulada: ID {primeiro}", saida)
        self.assertIn("O banco NÃO foi alterado", saida)
        registros = listar_solicitacoes(self.conexao)
        self.assertEqual([r["id"] for r in registros], [primeiro, segundo])
        self.assertEqual([r["status"] for r in registros], ["pendente", "pendente"])
        self.assertLess(saida.index("primeira"), saida.index("segunda"))

    def test_fila_cancelamento(self):
        modulo_id = self.criar_modulo()
        self.criar_solicitacao(modulo_id, "primeira")
        saida = self.executar(exibir_fila_solicitacoes, [""])
        self.assertIn("Nenhuma simulação de atendimento", saida)
        self.assertEqual(len(listar_solicitacoes(self.conexao)), 1)

    def test_submenu_encaminha_opcoes_e_volta(self):
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.exibir_busca_sensor_hash") as busca,
            patch("codigo_fonte.exibir_cadastro_solicitacao") as cadastro,
            patch("codigo_fonte.exibir_fila_solicitacoes") as fila,
            patch("builtins.input", side_effect=["1", "2", "3", "0"]),
        ):
            self.assertIsNone(menu_estruturas_dados(self.conexao))
        busca.assert_called_once_with(self.conexao)
        cadastro.assert_called_once_with(self.conexao)
        fila.assert_called_once_with(self.conexao)

    def test_menu_principal_opcao_3(self):
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.menu_estruturas_dados") as submenu,
            patch("builtins.input", side_effect=["3", "0"]),
        ):
            menu_principal(self.conexao)
        submenu.assert_called_once_with(self.conexao)


if __name__ == "__main__":
    unittest.main()
