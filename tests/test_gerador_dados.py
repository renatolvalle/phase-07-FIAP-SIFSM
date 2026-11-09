# Testes Automatizados do Gerador de Dados do Sistema Aurora Siger

import csv
import math
import tempfile
import unittest

from pathlib import Path

from gerar_dados_iniciais import (
    CAMPOS_CSV,
    gerar_csv_inicial
)


class TestGeradorDados(unittest.TestCase):

    # Cria um diretório temporário para cada teste
    def setUp(self):

        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)

        self.caminho_csv = (
            Path(self.diretorio.name) / "dados_teste.csv"
        )

    # Lê os registros do CSV temporário
    def ler_dados(self):
        with self.caminho_csv.open(
            newline="",
            encoding="utf-8"
        ) as arquivo:
            leitor = csv.DictReader(arquivo)

            return leitor.fieldnames, list(leitor)

    # Verifica 320 leituras e o cabeçalho esperado
    def test_quantidade_e_colunas(self):
        quantidade = gerar_csv_inicial(self.caminho_csv)

        colunas, registros = self.ler_dados()

        self.assertEqual(quantidade, 320)
        self.assertEqual(len(registros), 320)
        self.assertEqual(colunas, CAMPOS_CSV)

    # Confirma os 10 sensores distribuídos em 32 ciclos
    def test_sensores_e_ciclos(self):
        gerar_csv_inicial(self.caminho_csv)

        _, registros = self.ler_dados()

        sensores = {
            registro["sensor_codigo"]
            for registro in registros
        }

        ciclos = {
            int(registro["ciclo"])
            for registro in registros
        }

        self.assertEqual(len(sensores), 10)
        self.assertEqual(ciclos, set(range(1, 33)))

        for ciclo in ciclos:
            quantidade = sum(
                int(registro["ciclo"]) == ciclo
                for registro in registros
            )

            self.assertEqual(quantidade, 10)

    # Verifica valores numéricos e geração determinística
    def test_valores_finitos_e_reprodutiveis(self):
        gerar_csv_inicial(self.caminho_csv)

        primeira_versao = self.caminho_csv.read_bytes()

        _, registros = self.ler_dados()

        for registro in registros:
            valor = float(registro["valor"])

            self.assertTrue(math.isfinite(valor))

        gerar_csv_inicial(self.caminho_csv)

        segunda_versao = self.caminho_csv.read_bytes()

        self.assertEqual(
            primeira_versao,
            segunda_versao
        )


if __name__ == "__main__":
    unittest.main()