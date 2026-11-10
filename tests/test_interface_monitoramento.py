"""Interface de monitoramento: integração de regras R1 e R2 ao banco."""
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from banco_dados import (abrir_conexao, inicializar_banco, cadastrar_modulo,
                         cadastrar_sensor, registrar_leitura)
from codigo_fonte import exibir_monitoramento_sensores, menu_principal


class TestInterfaceMonitoramento(unittest.TestCase):
    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)
        inicializar_banco(self.conexao)

    def criar_dados(self, modulo_status="ativo", sensor_status="ativo", valor=3.4,
                    critico=1):
        modulo_id = cadastrar_modulo(self.conexao, {
            "codigo": "MOD-MON-01", "nome": "Monitorado", "tipo": "energia",
            "critico": critico, "status": modulo_status
        })
        sensor_id = cadastrar_sensor(self.conexao, {
            "codigo": "SEN-MON-01", "modulo_id": modulo_id,
            "tipo": "consumo_kw", "unidade": "kW", "status": sensor_status
        })
        registrar_leitura(self.conexao, {
            "sensor_id": sensor_id, "ciclo": 1,
            "instante": "2026-11-09T12:00:00Z", "valor": valor
        })
        return sensor_id

    def executar(self, entradas):
        saida = io.StringIO()
        with (patch("builtins.input", side_effect=entradas),
              patch("codigo_fonte.limpar_tela"),
              patch("codigo_fonte.exibir_cabecalho"),
              patch("codigo_fonte.pausar"),
              redirect_stdout(saida)):
            exibir_monitoramento_sensores(self.conexao)
        return saida.getvalue()

    def n_alertas(self):
        return self.conexao.execute("SELECT COUNT(*) FROM alertas").fetchone()[0]

    def test_sem_leituras(self):
        self.assertIn("Nenhuma leitura encontrada", self.executar([""]))

    def test_ciclo_invalido(self):
        for valor in ("abc", "0", "-3"):
            with self.subTest(valor=valor):
                self.assertIn("Dados inválidos", self.executar([valor]))

    def test_r1_tabelas_verdade_sem_gravar(self):
        self.criar_dados()
        saida = self.executar(["1", ""])
        self.assertIn("Alertas R1 identificados: 1", saida)
        self.assertIn("Tabela verdade R1", saida)
        self.assertIn("Tabela verdade R2", saida)
        self.assertEqual(self.n_alertas(), 0)

    def test_confirmacao_registra_sem_duplicar(self):
        self.criar_dados()
        saida = self.executar(["1", "REGISTRAR"])
        self.assertIn("Novos alertas registrados: 1", saida)
        self.assertEqual(self.n_alertas(), 1)
        saida2 = self.executar(["1", "REGISTRAR"])
        self.assertIn("Novos alertas registrados: 0", saida2)
        self.assertEqual(self.n_alertas(), 1)

    def test_cancelamento_nao_grava(self):
        self.criar_dados()
        self.assertIn("Alertas não registrados", self.executar(["1", "CANCELAR"]))
        self.assertEqual(self.n_alertas(), 0)

    def test_r2_sensor_invalido(self):
        self.criar_dados(sensor_status="invalido")
        saida = self.executar(["1"])
        self.assertIn("Alertas R1 identificados: 0", saida)
        self.assertIn("Bloqueios R2 identificados: 1", saida)
        self.assertIn("Sensor em estado inválido", saida)

    def test_r2_modulo_manutencao(self):
        self.criar_dados(modulo_status="manutencao")
        saida = self.executar(["1"])
        self.assertIn("Bloqueios R2 identificados: 1", saida)
        self.assertIn("Módulo em manutenção", saida)
        self.assertEqual(self.n_alertas(), 0)

    def test_filtro_ciclo(self):
        sensor_id = self.criar_dados()
        registrar_leitura(self.conexao, {
            "sensor_id": sensor_id, "ciclo": 2,
            "instante": "2026-11-09T13:00:00Z", "valor": 1.0
        })
        saida = self.executar(["2"])
        self.assertIn("Leituras analisadas: 1", saida)
        self.assertIn("Alertas R1 identificados: 0", saida)

    def test_menu_principal_opcao2(self):
        with (patch("builtins.input", side_effect=["2", "0"]),
              patch("codigo_fonte.limpar_tela"),
              patch("codigo_fonte.exibir_cabecalho"),
              patch("codigo_fonte.exibir_monitoramento_sensores") as monitor,
              redirect_stdout(io.StringIO())):
            menu_principal(self.conexao)
        monitor.assert_called_once_with(self.conexao)

if __name__ == "__main__":
    unittest.main()
