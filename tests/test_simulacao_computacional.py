"""Testes do balanço energético com resultados calculados manualmente."""

from copy import deepcopy
import unittest

from config import CAPACIDADE_BATERIA_KWH, CARGA_INICIAL_KWH, HORAS_POR_CICLO
from simulacao_computacional import simular_balanco_energetico


def criar_ciclo(ciclo=1, consumo_kw=6, geracao_kw=4):
    return {"ciclo": ciclo, "consumo_kw": consumo_kw, "geracao_kw": geracao_kw}


class TestSimulacaoEnergetica(unittest.TestCase):
    def test_exemplo_manual_e_campos_do_historico(self):
        resultado = simular_balanco_energetico([criar_ciclo()], 20, 12, 1)
        self.assertEqual(set(resultado), {"historico", "resumo"})
        self.assertEqual(resultado["historico"], [{
            "ciclo": 1, "consumo_kw": 6, "geracao_kw": 4,
            "consumo_kwh": 6, "geracao_kwh": 4,
            "energia_inicial_kwh": 12, "energia_final_kwh": 10,
            "soc_inicial_pct": 60, "soc_final_pct": 50,
            "carga_recebida_kwh": 0, "descarga_fornecida_kwh": 2,
            "deficit_nao_atendido_kwh": 0, "excedente_nao_armazenado_kwh": 0,
        }])

    def test_parametros_padrao_do_config(self):
        resultado = simular_balanco_energetico([criar_ciclo()])
        explicito = simular_balanco_energetico(
            [criar_ciclo()], CAPACIDADE_BATERIA_KWH, CARGA_INICIAL_KWH,
            HORAS_POR_CICLO,
        )
        self.assertEqual(resultado, explicito)

    def test_equilibrio_preserva_carga(self):
        linha = simular_balanco_energetico([criar_ciclo(1, 5, 5)])["historico"][0]
        self.assertEqual(linha["energia_final_kwh"], CARGA_INICIAL_KWH)
        self.assertEqual(linha["carga_recebida_kwh"], 0)
        self.assertEqual(linha["descarga_fornecida_kwh"], 0)

    def test_integracao_com_duracao_fracionaria(self):
        linha = simular_balanco_energetico([criar_ciclo()], 20, 12, 0.25)["historico"][0]
        self.assertEqual(linha["consumo_kwh"], 1.5)
        self.assertEqual(linha["geracao_kwh"], 1)
        self.assertEqual(linha["energia_final_kwh"], 11.5)

    def test_carregamento(self):
        linha = simular_balanco_energetico([criar_ciclo(1, 2, 5)], 20, 12, 2)["historico"][0]
        self.assertEqual(linha["carga_recebida_kwh"], 6)
        self.assertEqual(linha["energia_final_kwh"], 18)
        self.assertEqual(linha["soc_final_pct"], 90)

    def test_saturacao_registra_excedente(self):
        linha = simular_balanco_energetico([criar_ciclo(1, 1, 10)], 20, 18)["historico"][0]
        self.assertEqual(linha["energia_final_kwh"], 20)
        self.assertEqual(linha["carga_recebida_kwh"], 2)
        self.assertEqual(linha["excedente_nao_armazenado_kwh"], 7)

    def test_esgotamento_registra_deficit(self):
        linha = simular_balanco_energetico([criar_ciclo(1, 10, 1)], 20, 2)["historico"][0]
        self.assertEqual(linha["energia_final_kwh"], 0)
        self.assertEqual(linha["descarga_fornecida_kwh"], 2)
        self.assertEqual(linha["deficit_nao_atendido_kwh"], 7)

    def test_bateria_inicialmente_cheia_ou_vazia(self):
        for inicial, consumo, geracao, deficit, excedente in (
            (20, 1, 10, 0, 9), (0, 10, 1, 9, 0),
        ):
            with self.subTest(inicial=inicial):
                linha = simular_balanco_energetico(
                    [criar_ciclo(1, consumo, geracao)], 20, inicial,
                )["historico"][0]
                self.assertEqual(linha["energia_final_kwh"], inicial)
                self.assertEqual(linha["deficit_nao_atendido_kwh"], deficit)
                self.assertEqual(linha["excedente_nao_armazenado_kwh"], excedente)

    def test_conservacao_limites_e_encadeamento(self):
        serie = [criar_ciclo(i, (i * 7) % 23, (i * 11) % 29) for i in range(1, 101)]
        resultado = simular_balanco_energetico(serie, 20, 12, 0.7)
        anterior = 12
        for linha in resultado["historico"]:
            with self.subTest(ciclo=linha["ciclo"]):
                self.assertEqual(linha["energia_inicial_kwh"], anterior)
                self.assertGreaterEqual(linha["energia_final_kwh"], 0)
                self.assertLessEqual(linha["energia_final_kwh"], 20)
                self.assertAlmostEqual(
                    linha["energia_inicial_kwh"] + linha["geracao_kwh"]
                    + linha["deficit_nao_atendido_kwh"],
                    linha["energia_final_kwh"] + linha["consumo_kwh"]
                    + linha["excedente_nao_armazenado_kwh"],
                )
                anterior = linha["energia_final_kwh"]

    def test_resumo_manual_e_atendimento(self):
        serie = [criar_ciclo(1, 2, 10), criar_ciclo(2, 12, 0), criar_ciclo(3, 0, 2)]
        resumo = simular_balanco_energetico(serie, 10, 5)["resumo"]
        esperado = {
            "quantidade_ciclos": 3, "consumo_total_kwh": 14, "geracao_total_kwh": 12,
            "pico_consumo_kw": 12, "pico_geracao_kw": 10,
            "energia_inicial_kwh": 5, "energia_final_kwh": 2,
            "soc_minimo_pct": 0, "soc_final_pct": 20,
            "carga_recebida_total_kwh": 7, "descarga_fornecida_total_kwh": 10,
            "deficit_total_kwh": 2, "excedente_total_kwh": 3,
            "atendimento_percentual": 100 * 12 / 14,
        }
        self.assertEqual(set(resumo), set(esperado))
        for campo, valor in esperado.items():
            self.assertAlmostEqual(resumo[campo], valor, msg=campo)

    def test_soc_minimo_inclui_estado_inicial(self):
        resumo = simular_balanco_energetico([criar_ciclo(1, 0, 10)], 20, 2)["resumo"]
        self.assertEqual(resumo["soc_minimo_pct"], 10)

    def test_consumo_zero_convencao_de_atendimento(self):
        resumo = simular_balanco_energetico([criar_ciclo(1, 0, 4)])["resumo"]
        self.assertEqual(resumo["consumo_total_kwh"], 0)
        self.assertEqual(resumo["atendimento_percentual"], 100)

    def test_serie_vazia_preserva_estado(self):
        resultado = simular_balanco_energetico([], 20, 12)
        self.assertEqual(resultado["historico"], [])
        resumo = resultado["resumo"]
        for campo in ("quantidade_ciclos", "consumo_total_kwh", "geracao_total_kwh",
                      "pico_consumo_kw", "pico_geracao_kw", "deficit_total_kwh",
                      "excedente_total_kwh", "carga_recebida_total_kwh",
                      "descarga_fornecida_total_kwh"):
            self.assertEqual(resumo[campo], 0, campo)
        self.assertEqual(resumo["energia_inicial_kwh"], 12)
        self.assertEqual(resumo["energia_final_kwh"], 12)
        self.assertEqual(resumo["soc_minimo_pct"], 60)
        self.assertEqual(resumo["soc_final_pct"], 60)
        self.assertEqual(resumo["atendimento_percentual"], 100)

    def test_ordena_copia_e_aceita_lacunas_sem_inventar_ciclos(self):
        serie = [criar_ciclo(9), criar_ciclo(2)]
        original = deepcopy(serie)
        resultado = simular_balanco_energetico(serie, 20, 12)
        self.assertEqual([r["ciclo"] for r in resultado["historico"]], [2, 9])
        self.assertEqual(resultado["resumo"]["energia_final_kwh"], 8)
        self.assertEqual(serie, original)
        resultado["historico"][0]["consumo_kw"] = 999
        self.assertEqual(serie, original)

    def test_aceita_gerador(self):
        serie = (criar_ciclo(i) for i in range(1, 4))
        self.assertEqual(simular_balanco_energetico(serie)["resumo"]["quantidade_ciclos"], 3)

    def test_rejeita_duplicatas(self):
        with self.assertRaisesRegex(ValueError, "ciclo.*duplicado"):
            simular_balanco_energetico([criar_ciclo(), criar_ciclo()])

    def test_rejeita_campos_ausentes(self):
        for campo in criar_ciclo():
            linha = criar_ciclo()
            del linha[campo]
            with self.subTest(campo=campo), self.assertRaisesRegex(ValueError, campo):
                simular_balanco_energetico([linha])

    def test_rejeita_estrutura_invalida(self):
        for serie in (None, 3, True, "", {}, [None], [[1, 6, 4]]):
            with self.subTest(serie=serie), self.assertRaises(ValueError):
                simular_balanco_energetico(serie)

    def test_rejeita_ciclos_invalidos(self):
        for ciclo in (0, -1, 1.0, True, False, "1", None, float("nan"), float("inf")):
            with self.subTest(ciclo=ciclo), self.assertRaisesRegex(ValueError, "ciclo"):
                simular_balanco_energetico([criar_ciclo(ciclo)])

    def test_rejeita_potencias_invalidas(self):
        for campo in ("consumo_kw", "geracao_kw"):
            for valor in (-1, True, False, "6", None, 1j, float("nan"), float("inf"), -float("inf")):
                linha = criar_ciclo()
                linha[campo] = valor
                with self.subTest(campo=campo, valor=valor), self.assertRaisesRegex(ValueError, campo):
                    simular_balanco_energetico([linha])

    def test_rejeita_parametros_invalidos_mesmo_com_serie_vazia(self):
        for campo in ("capacidade_kwh", "carga_inicial_kwh", "horas_por_ciclo"):
            invalidos = [-1, True, False, "2", None, float("nan"), float("inf")]
            invalidos += [21] if campo == "carga_inicial_kwh" else [0]
            for valor in invalidos:
                with self.subTest(campo=campo, valor=valor), self.assertRaisesRegex(ValueError, campo):
                    simular_balanco_energetico([], **{campo: valor})

    def test_rejeita_transbordamento_da_integracao(self):
        with self.assertRaisesRegex(ValueError, "finito"):
            simular_balanco_energetico([criar_ciclo(1, 1e308, 0)], horas_por_ciclo=10)


if __name__ == "__main__":
    unittest.main()
