"""Verifica a execução explícita e as evidências da demonstração local."""

import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from demonstracao_energia import criar_serie_demonstracao, executar_demonstracao


class TestDemonstracaoEnergia(unittest.TestCase):
    def test_base_didatica_reproduzivel_com_variacao(self):
        serie = criar_serie_demonstracao()
        self.assertEqual(len(serie), 24)
        self.assertEqual(serie, criar_serie_demonstracao())
        diferencas = [b["consumo_kw"] - a["consumo_kw"] for a, b in zip(serie, serie[1:])]
        self.assertGreater(max(diferencas) - min(diferencas), 0.1)
        serie[0]["consumo_kw"] = 999
        self.assertNotEqual(serie, criar_serie_demonstracao())

    def test_importacao_sem_arquivos_saida_ou_biblioteca_grafica(self):
        raiz = Path(__file__).resolve().parents[1]
        codigo = (
            f"import sys; sys.path.insert(0, {str(raiz)!r}); "
            "import simulacao_computacional, modelo_linear, demonstracao_energia; "
            "assert 'matplotlib' not in sys.modules"
        )
        with tempfile.TemporaryDirectory() as temporario:
            processo = subprocess.run(
                [sys.executable, "-B", "-c", codigo], cwd=temporario,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(processo.returncode, 0, processo.stderr)
            self.assertEqual(processo.stdout, "")
            self.assertEqual(processo.stderr, "")
            self.assertEqual(list(Path(temporario).iterdir()), [])

    @unittest.skipUnless(importlib.util.find_spec("matplotlib"), "Instale requirements.txt para verificar os gráficos.")
    def test_gera_quatro_pngs_json_coerente_e_fecha_figuras(self):
        with tempfile.TemporaryDirectory() as temporario:
            destino = Path(temporario) / "evidencias"
            resultado = executar_demonstracao(destino)
            self.assertEqual(len(resultado["arquivos"]), 5)
            imagens = list(destino.glob("*.png"))
            self.assertEqual(len(imagens), 4)
            for caminho in imagens:
                conteudo = caminho.read_bytes()
                self.assertEqual(conteudo[:8], b"\x89PNG\r\n\x1a\n")
                largura, altura = struct.unpack(">II", conteudo[16:24])
                self.assertGreater(largura, 800)
                self.assertGreater(altura, 400)
            salvo = json.loads((destino / "demonstracao_energia.json").read_text(encoding="utf-8"))
            self.assertEqual(salvo, resultado["dados"])
            base, estresse = salvo["simulacao_base"]["resumo"], salvo["simulacao_estresse"]["resumo"]
            self.assertEqual(base["consumo_total_kwh"], estresse["consumo_total_kwh"])
            self.assertAlmostEqual(estresse["geracao_total_kwh"], base["geracao_total_kwh"] * 0.7)
            self.assertGreater(estresse["deficit_total_kwh"], base["deficit_total_kwh"])
            self.assertEqual(salvo["regressao"]["metricas"]["quantidade_treino"], 19)
            import matplotlib.pyplot as plt
            self.assertEqual(plt.get_fignums(), [])


if __name__ == "__main__":
    unittest.main()
