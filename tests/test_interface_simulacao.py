"""Testes da interface de simulação com os contratos e o SQLite reais."""

import io
import sqlite3
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from banco_dados import (
    abrir_conexao,
    inicializar_banco,
    cadastrar_modulo,
    cadastrar_sensor,
    registrar_leitura,
)
from codigo_fonte import exibir_simulacao_computacional, menu_principal


class TestInterfaceSimulacao(unittest.TestCase):
    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)
        inicializar_banco(self.conexao)

    def preparar_serie(self, ciclos):
        """Cria um sensor de consumo e outro de geração em cada ciclo."""
        modulo_id = cadastrar_modulo(self.conexao, {
            "codigo": "MOD-SIM-01", "nome": "Simulação", "tipo": "energia"
        })
        consumo_id = cadastrar_sensor(self.conexao, {
            "codigo": "SEN-SIM-CONS", "modulo_id": modulo_id,
            "tipo": "consumo_kw", "unidade": "kW"
        })
        geracao_id = cadastrar_sensor(self.conexao, {
            "codigo": "SEN-SIM-GER", "modulo_id": modulo_id,
            "tipo": "geracao_kw", "unidade": "kW"
        })
        for ciclo, consumo, geracao in ciclos:
            for sensor_id, valor in ((consumo_id, consumo), (geracao_id, geracao)):
                registrar_leitura(self.conexao, {
                    "sensor_id": sensor_id, "ciclo": ciclo,
                    "instante": "2026-11-09T12:00:00Z", "valor": valor,
                })

    def executar_interface(self):
        saida = io.StringIO()
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.pausar") as pausar,
            redirect_stdout(saida),
        ):
            exibir_simulacao_computacional(self.conexao)
        pausar.assert_called_once()
        return saida.getvalue()

    def test_sem_dados_nao_simula(self):
        saida = self.executar_interface()
        self.assertIn("Nenhum dado energético disponível", saida)
        self.assertIn("Importe os dados iniciais", saida)

    def test_base_utiliza_dados_do_sqlite(self):
        self.preparar_serie([(1, 6, 4), (2, 2, 5)])
        saida = self.executar_interface()
        self.assertIn("Ciclos analisados: 2", saida)
        self.assertIn("Energia consumida: 8.00 kWh", saida)
        self.assertIn("Energia gerada: 9.00 kWh", saida)
        self.assertIn("Ciclo 2:", saida)

    def test_estresse_reduz_apenas_geracao(self):
        self.preparar_serie([(1, 6, 10)])
        saida = self.executar_interface()
        self.assertIn("--- CENÁRIO-BASE ---", saida)
        self.assertIn("--- ESTRESSE: GERAÇÃO -30% ---", saida)
        self.assertEqual(saida.count("Energia consumida: 6.00 kWh"), 2)
        self.assertIn("Energia gerada: 10.00 kWh", saida)
        self.assertIn("Energia gerada: 7.00 kWh", saida)

    def test_deficit_e_bateria_esgotada(self):
        self.preparar_serie([(1, 10, 0), (2, 10, 0), (3, 10, 0)])
        saida = self.executar_interface()
        self.assertIn("Déficit não atendido: 18.00 kWh", saida)
        self.assertIn("Energia final da bateria: 0.00 kWh", saida)
        self.assertIn("SoC final: 0.00%", saida)
        self.assertIn("A demanda não foi totalmente atendida", saida)

    def test_nao_modifica_o_banco(self):
        self.preparar_serie([(1, 6, 4), (2, 2, 5)])
        antes = self.conexao.iterdump()
        dump_antes = list(antes)
        self.executar_interface()
        self.assertEqual(list(self.conexao.iterdump()), dump_antes)

    def test_erro_de_consulta_tratado(self):
        with patch("analise_integrada.banco_dados.obter_serie_energia", side_effect=sqlite3.OperationalError("erro de teste")):
            saida = self.executar_interface()
        self.assertIn("Erro ao consultar a série energética", saida)

    def test_dados_invalidos_tratados(self):
        with patch("analise_integrada.banco_dados.obter_serie_energia", return_value=[
            {"ciclo": 1, "consumo_kw": -2, "geracao_kw": 3}
        ]):
            saida = self.executar_interface()
        self.assertIn("Dados inválidos para a simulação", saida)

    def test_menu_principal_opcao_4(self):
        saida = io.StringIO()
        with (
            patch("builtins.input", side_effect=["4", "0"]),
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.exibir_cabecalho"),
            patch("codigo_fonte.exibir_simulacao_computacional") as simular,
            redirect_stdout(saida),
        ):
            menu_principal(self.conexao)
        simular.assert_called_once_with(self.conexao)
        self.assertNotIn("Funcionalidade em Desenvolvimento", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
