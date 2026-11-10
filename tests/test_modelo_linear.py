"""Avaliação temporal, mínimos quadrados e extrapolação do consumo."""

from copy import deepcopy
import inspect
from math import sqrt
import unittest

from config import HORIZONTE_PREVISAO_CICLOS
from modelo_linear import avaliar_e_prever_consumo


def criar_serie(quantidade=10):
    return [
        {"ciclo": ciclo, "consumo_kw": 1 + 2 * ciclo, "geracao_kw": 4}
        for ciclo in range(1, quantidade + 1)
    ]


class TestModeloLinear(unittest.TestCase):
    def test_contrato_e_assinatura(self):
        self.assertEqual(list(inspect.signature(avaliar_e_prever_consumo).parameters),
                         ["serie_energia", "horizonte_ciclos"])
        resultado = avaliar_e_prever_consumo(criar_serie())
        self.assertEqual(set(resultado), {"coeficientes", "metricas", "previsoes", "limitacoes"})
        self.assertEqual(set(resultado["coeficientes"]), {"intercepto_kw", "inclinacao_kw_por_ciclo"})
        self.assertEqual(set(resultado["metricas"]), {
            "quantidade_total", "quantidade_treino", "quantidade_teste",
            "consumo_minimo_kw", "consumo_maximo_kw", "consumo_medio_kw",
            "mae_kw", "rmse_kw", "r2", "mae_referencia_kw", "consumo_medio_treino_kw",
            "quantidade_previsoes_negativas_teste",
        })
        self.assertEqual(len(resultado["previsoes"]), HORIZONTE_PREVISAO_CICLOS)
        self.assertTrue(all(isinstance(texto, str) for texto in resultado["limitacoes"]))

    def test_coeficientes_e_previsoes_conhecidos(self):
        resultado = avaliar_e_prever_consumo(criar_serie(), 3)
        self.assertAlmostEqual(resultado["coeficientes"]["intercepto_kw"], 1)
        self.assertAlmostEqual(resultado["coeficientes"]["inclinacao_kw_por_ciclo"], 2)
        self.assertEqual(resultado["previsoes"], [
            {"ciclo": 11, "consumo_previsto_kw": 23, "extrapolacao": True},
            {"ciclo": 12, "consumo_previsto_kw": 25, "extrapolacao": True},
            {"ciclo": 13, "consumo_previsto_kw": 27, "extrapolacao": True},
        ])
        self.assertAlmostEqual(resultado["metricas"]["mae_kw"], 0)
        self.assertAlmostEqual(resultado["metricas"]["rmse_kw"], 0)
        self.assertAlmostEqual(resultado["metricas"]["r2"], 1)

    def test_minimos_quadrados_com_variacao_e_metricas_manuais(self):
        serie = criar_serie()
        # Resíduos no treino somam zero e têm soma ponderada por ciclo zero.
        for linha, residuo in zip(serie, [1, -2, 1, 0, 0, 0, 0, 0, 3, -1]):
            linha["consumo_kw"] += residuo
        resultado = avaliar_e_prever_consumo(serie)
        self.assertAlmostEqual(resultado["coeficientes"]["intercepto_kw"], 1)
        self.assertAlmostEqual(resultado["coeficientes"]["inclinacao_kw_por_ciclo"], 2)
        metricas = resultado["metricas"]
        # Teste: real=[22,20], previsto=[19,21]; baseline média do treino=10.
        self.assertAlmostEqual(metricas["mae_kw"], 2)
        self.assertAlmostEqual(metricas["rmse_kw"], sqrt(5))
        self.assertAlmostEqual(metricas["r2"], -4)
        self.assertAlmostEqual(metricas["mae_referencia_kw"], 11)
        self.assertAlmostEqual(metricas["consumo_medio_treino_kw"], 10)
        self.assertEqual(metricas["quantidade_previsoes_negativas_teste"], 0)
        self.assertEqual(metricas["consumo_minimo_kw"], 3)
        self.assertEqual(metricas["consumo_maximo_kw"], 22)
        self.assertAlmostEqual(metricas["consumo_medio_kw"], 12.2)

    def test_divisao_24_ciclos_e_ausencia_de_vazamento(self):
        serie = criar_serie(24)
        original = avaliar_e_prever_consumo(serie)
        for linha in serie[19:]:
            linha["consumo_kw"] += 100
        alterado = avaliar_e_prever_consumo(list(reversed(serie)))
        self.assertEqual(alterado["metricas"]["quantidade_total"], 24)
        self.assertEqual(alterado["metricas"]["quantidade_treino"], 19)
        self.assertEqual(alterado["metricas"]["quantidade_teste"], 5)
        self.assertEqual(original["coeficientes"], alterado["coeficientes"])
        self.assertEqual(original["previsoes"], alterado["previsoes"])
        self.assertEqual(original["metricas"]["consumo_medio_treino_kw"],
                         alterado["metricas"]["consumo_medio_treino_kw"])
        self.assertNotEqual(alterado["metricas"]["consumo_medio_treino_kw"],
                            alterado["metricas"]["consumo_medio_kw"])
        self.assertAlmostEqual(alterado["metricas"]["mae_kw"], 100)
        self.assertAlmostEqual(alterado["metricas"]["mae_referencia_kw"], 124)

    def test_arredondamento_da_divisao_cronologica(self):
        for quantidade, treino, teste in ((10, 8, 2), (11, 8, 3), (24, 19, 5)):
            with self.subTest(quantidade=quantidade):
                metricas = avaliar_e_prever_consumo(criar_serie(quantidade))["metricas"]
                self.assertEqual(metricas["quantidade_treino"], treino)
                self.assertEqual(metricas["quantidade_teste"], teste)

    def test_resposta_constante_no_teste_r2_indefinido(self):
        serie = criar_serie()
        serie[-1]["consumo_kw"] = serie[-2]["consumo_kw"] = 20
        resultado = avaliar_e_prever_consumo(serie)
        self.assertIsNone(resultado["metricas"]["r2"])
        self.assertAlmostEqual(resultado["metricas"]["mae_kw"], 1)
        self.assertTrue(any("R²" in texto and "constante" in texto for texto in resultado["limitacoes"]))

    def test_serie_inteira_constante(self):
        serie = criar_serie()
        for linha in serie:
            linha["consumo_kw"] = 0.1
        resultado = avaliar_e_prever_consumo(serie)
        self.assertAlmostEqual(resultado["coeficientes"]["inclinacao_kw_por_ciclo"], 0)
        self.assertAlmostEqual(resultado["coeficientes"]["intercepto_kw"], 0.1)
        self.assertIsNone(resultado["metricas"]["r2"])
        self.assertAlmostEqual(resultado["metricas"]["mae_referencia_kw"], 0)

    def test_previsao_negativa_e_sinalizada_sem_corte(self):
        serie = criar_serie()
        for linha in serie:
            linha["consumo_kw"] = 10 - linha["ciclo"]
        resultado = avaliar_e_prever_consumo(serie, 2)
        self.assertEqual([r["consumo_previsto_kw"] for r in resultado["previsoes"]], [-1, -2])
        self.assertIn("negativ", " ".join(resultado["limitacoes"]).lower())

    def test_conta_negativas_no_teste_sem_mascarar_erro_ou_reajustar(self):
        serie = [
            {"ciclo": ciclo, "consumo_kw": max(0, 8 - ciclo), "geracao_kw": 0}
            for ciclo in range(1, 11)
        ]
        resultado = avaliar_e_prever_consumo(serie)
        self.assertEqual(resultado["metricas"]["quantidade_previsoes_negativas_teste"], 2)
        self.assertEqual(resultado["metricas"]["consumo_medio_treino_kw"], 3.5)
        self.assertEqual(resultado["coeficientes"], {
            "intercepto_kw": 8.0, "inclinacao_kw_por_ciclo": -1.0,
        })
        self.assertEqual(resultado["metricas"]["mae_kw"], 1.5)
        self.assertEqual(resultado["previsoes"][0]["consumo_previsto_kw"], -3)

    def test_limitacoes_de_interpretacao(self):
        textos = " ".join(avaliar_e_prever_consumo(criar_serie())["limitacoes"]).lower()
        for termo in ("simulados", "observações", "temporal", "extrapolação", "intercepto", "causalidade"):
            self.assertIn(termo, textos)

    def test_ordena_sem_alterar_entrada(self):
        serie = list(reversed(criar_serie()))
        copia = deepcopy(serie)
        self.assertEqual(avaliar_e_prever_consumo(serie), avaliar_e_prever_consumo(criar_serie()))
        self.assertEqual(serie, copia)

    def test_lacunas_usa_identificadores_e_ultimo_ciclo(self):
        serie = criar_serie()
        for linha in serie:
            linha["ciclo"] *= 3
            linha["consumo_kw"] = 1 + 2 * linha["ciclo"]
        resultado = avaliar_e_prever_consumo(serie, 2)
        self.assertAlmostEqual(resultado["coeficientes"]["inclinacao_kw_por_ciclo"], 2)
        self.assertEqual([r["ciclo"] for r in resultado["previsoes"]], [31, 32])
        self.assertEqual([r["consumo_previsto_kw"] for r in resultado["previsoes"]], [63, 65])

    def test_aceita_gerador(self):
        self.assertEqual(avaliar_e_prever_consumo(iter(criar_serie())), avaliar_e_prever_consumo(criar_serie()))

    def test_rejeita_dados_insuficientes(self):
        for quantidade in (0, 1, 2, 9):
            with self.subTest(quantidade=quantidade), self.assertRaisesRegex(ValueError, "10 observações"):
                avaliar_e_prever_consumo(criar_serie(quantidade))

    def test_rejeita_horizonte_invalido(self):
        for horizonte in (0, -1, True, False, 1.0, "3", None, float("nan"), float("inf")):
            with self.subTest(horizonte=horizonte), self.assertRaisesRegex(ValueError, "horizonte_ciclos"):
                avaliar_e_prever_consumo(criar_serie(), horizonte)

    def test_rejeita_duplicatas(self):
        serie = criar_serie()
        serie[-1]["ciclo"] = 1
        with self.assertRaisesRegex(ValueError, "ciclo.*duplicado"):
            avaliar_e_prever_consumo(serie)

    def test_rejeita_campos_ausentes(self):
        for campo in ("ciclo", "consumo_kw", "geracao_kw"):
            serie = criar_serie()
            del serie[0][campo]
            with self.subTest(campo=campo), self.assertRaisesRegex(ValueError, campo):
                avaliar_e_prever_consumo(serie)

    def test_rejeita_ciclos_invalidos(self):
        for valor in (0, -1, True, False, 1.5, "1", None, float("nan"), float("inf")):
            serie = criar_serie()
            serie[0]["ciclo"] = valor
            with self.subTest(valor=valor), self.assertRaisesRegex(ValueError, "ciclo"):
                avaliar_e_prever_consumo(serie)

    def test_rejeita_potencias_invalidas_inclusive_no_teste(self):
        for campo in ("consumo_kw", "geracao_kw"):
            for valor in (-1, True, False, "2", None, 1j, float("nan"), float("inf")):
                serie = criar_serie()
                serie[-1][campo] = valor
                with self.subTest(campo=campo, valor=valor), self.assertRaisesRegex(ValueError, campo):
                    avaliar_e_prever_consumo(serie)

    def test_rejeita_estrutura_invalida(self):
        for serie in (None, 1, True, "", {}, [None] * 10):
            with self.subTest(serie=serie), self.assertRaises(ValueError):
                avaliar_e_prever_consumo(serie)


if __name__ == "__main__":
    unittest.main()
