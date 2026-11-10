"""Integração real com SQLite em memória; nunca acessa o banco local da colônia."""

import contextlib
import csv
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import analise_integrada
import banco_dados
from agents import gerar_recomendacoes
from config import CAMINHO_CSV, DIRETORIO_BASE, HORAS_POR_CICLO
from estruturas_dados import buscar_sensor_hash
from modelo_linear import avaliar_e_prever_consumo
from simulacao_computacional import simular_balanco_energetico


class TestAnaliseIntegrada(unittest.TestCase):
    def setUp(self):
        self.conexao = banco_dados.abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)
        banco_dados.inicializar_banco(self.conexao)

    def carregar_csv(self):
        return banco_dados.carregar_csv_inicial(self.conexao, CAMINHO_CSV)

    def analisar(self):
        return analise_integrada.executar_analise_integrada(self.conexao)

    def criar_serie(self, quantidade=10, consumo=lambda ciclo: 2 + ciclo, geracao=1):
        modulo_id = banco_dados.cadastrar_modulo(self.conexao, {
            "codigo": "MOD-TESTE", "nome": "Teste", "tipo": "habitacao", "critico": 1,
        })
        for tipo in ("consumo_kw", "geracao_kw"):
            sensor_id = banco_dados.cadastrar_sensor(self.conexao, {
                "codigo": tipo, "modulo_id": modulo_id, "tipo": tipo, "unidade": "kW",
            })
            for ciclo in range(1, quantidade + 1):
                banco_dados.registrar_leitura(self.conexao, {
                    "sensor_id": sensor_id, "ciclo": ciclo,
                    "instante": "2026-11-03T12:00:00Z",
                    "valor": consumo(ciclo) if tipo == "consumo_kw" else geracao,
                })
        return modulo_id

    def test_csv_real_fluxo_completo_e_contrato(self):
        self.assertEqual(self.carregar_csv(), 320)
        resultado = self.analisar()
        self.assertEqual(set(resultado), {
            "indicadores", "alertas", "simulacao", "previsao", "recomendacoes", "limitacoes",
        })
        indicadores = resultado["indicadores"]
        for chave, esperado in (
            ("quantidade_modulos", 5), ("quantidade_sensores", 10),
            ("quantidade_leituras", 320), ("quantidade_ciclos", 32),
            ("quantidade_alertas", 19), ("quantidade_solicitacoes_pendentes", 0),
        ):
            self.assertEqual(indicadores[chave], esperado)
        self.assertEqual(len(resultado["alertas"]), 19)
        self.assertEqual(len(resultado["simulacao"]["historico"]), 32)
        self.assertEqual(len(resultado["previsao"]["previsoes"]), 3)
        self.assertEqual(resultado["previsao"]["metricas"]["quantidade_treino"], 25)
        self.assertEqual(resultado["previsao"]["metricas"]["quantidade_teste"], 7)
        self.assertGreater(resultado["previsao"]["metricas"]["mae_kw"],
                           resultado["previsao"]["metricas"]["mae_referencia_kw"])
        self.assertIn("não superou a referência", " ".join(resultado["limitacoes"]))
        energia = " ".join(resultado["recomendacoes"]["energia"])
        self.assertIn("Estimativa de referência pela média do treino", energia)
        self.assertNotIn("Pico de consumo previsto", energia)
        self.assertNotIn("Tendência de aumento", energia)
        self.assertTrue(resultado["recomendacoes"]["supervisao_humana"])
        self.assertTrue(resultado["limitacoes"])
        self.assertEqual(len(resultado["limitacoes"]), len(set(resultado["limitacoes"])))
        json.dumps(resultado, allow_nan=False)

    def test_csv_totais_e_media_da_colonia_calculados_independentemente(self):
        self.carregar_csv()
        with CAMINHO_CSV.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        consumo = sum(float(r["valor"]) for r in linhas if r["sensor_tipo"] == "consumo_kw")
        geracao = sum(float(r["valor"]) for r in linhas if r["sensor_tipo"] == "geracao_kw")
        resultado = self.analisar()
        self.assertAlmostEqual(resultado["indicadores"]["consumo_medio_kw"], consumo / 32)
        self.assertAlmostEqual(resultado["indicadores"]["geracao_media_kw"], geracao / 32)
        resumo = resultado["simulacao"]["resumo"]
        self.assertAlmostEqual(resumo["consumo_total_kwh"], consumo * HORAS_POR_CICLO)
        self.assertAlmostEqual(resumo["geracao_total_kwh"], geracao * HORAS_POR_CICLO)

    def test_modelos_e_recomendacoes_reutilizam_resultados_reais(self):
        self.carregar_csv()
        serie = banco_dados.obter_serie_energia(self.conexao)
        resultado = self.analisar()
        self.assertEqual(resultado["simulacao"], simular_balanco_energetico(serie))
        self.assertEqual(resultado["previsao"], avaliar_e_prever_consumo(serie))
        self.assertEqual(resultado["recomendacoes"], gerar_recomendacoes(
            resultado["indicadores"], resultado["alertas"],
            resultado["simulacao"], resultado["previsao"],
        ))

    def test_referencia_csv_calculada_apenas_no_treino_sem_alterar_regressao(self):
        self.carregar_csv()
        serie = banco_dados.obter_serie_energia(self.conexao)
        corte = len(serie) * 4 // 5
        media_treino = sum(r["consumo_kw"] for r in serie[:corte]) / corte
        resultado = self.analisar()
        metricas = resultado["previsao"]["metricas"]
        self.assertAlmostEqual(metricas["consumo_medio_treino_kw"], media_treino)
        self.assertNotAlmostEqual(media_treino, metricas["consumo_medio_kw"])
        self.assertAlmostEqual(metricas["mae_kw"], 0.2766813186813189)
        self.assertAlmostEqual(metricas["mae_referencia_kw"], 0.27228571428571435)
        self.assertAlmostEqual(metricas["r2"], -0.019327507692308732)
        self.assertAlmostEqual(resultado["previsao"]["previsoes"][0]["consumo_previsto_kw"],
                               5.282461538461538)
        self.assertIn(f"média do treino: {media_treino:g} kW",
                      " ".join(resultado["recomendacoes"]["energia"]))

    def test_serie_conhecida_unidades_coeficientes_e_balanco(self):
        self.criar_serie()
        resultado = self.analisar()
        resumo = resultado["simulacao"]["resumo"]
        self.assertAlmostEqual(resumo["consumo_total_kwh"], 75)
        self.assertAlmostEqual(resumo["geracao_total_kwh"], 10)
        self.assertAlmostEqual(resumo["energia_final_kwh"], 0)
        self.assertAlmostEqual(resumo["deficit_total_kwh"], 53)
        self.assertAlmostEqual(resultado["previsao"]["coeficientes"]["intercepto_kw"], 2)
        self.assertAlmostEqual(resultado["previsao"]["coeficientes"]["inclinacao_kw_por_ciclo"], 1)
        self.assertAlmostEqual(resultado["previsao"]["metricas"]["mae_kw"], 0)
        self.assertEqual([p["consumo_previsto_kw"] for p in resultado["previsao"]["previsoes"]],
                         [13, 14, 15])
        energia = " ".join(resultado["recomendacoes"]["energia"])
        self.assertIn("Pico de consumo previsto de 15 kW", energia)
        self.assertIn("Tendência de aumento", energia)
        self.assertNotIn("Estimativa de referência pela média do treino", energia)

    def test_alterar_dados_altera_analise_sem_dados_sinteticos(self):
        self.criar_serie()
        antes = self.analisar()
        self.conexao.execute("UPDATE leituras SET valor = valor * 2 WHERE sensor_id = 1")
        depois = self.analisar()
        self.assertEqual(depois["indicadores"]["consumo_medio_kw"],
                         2 * antes["indicadores"]["consumo_medio_kw"])
        self.assertEqual(depois["previsao"]["coeficientes"]["inclinacao_kw_por_ciclo"], 2)

    def test_indice_hash_encontra_sensores_do_csv(self):
        self.carregar_csv()
        indice = self.analisar()["indicadores"]["indice_sensores"]
        for sensor in banco_dados.listar_sensores(self.conexao):
            self.assertEqual(buscar_sensor_hash(indice, sensor["codigo"]), sensor)
        self.assertIsNone(buscar_sensor_hash(indice, "INEXISTENTE"))

    def test_fila_apenas_pendentes_por_chegada_sem_atender_ou_priorizar(self):
        modulo_id = self.criar_serie()
        ids = []
        for prioridade, status in (("baixa", "pendente"), ("alta", "concluida"),
                                   ("alta", "pendente"), ("media", "em_atendimento")):
            ids.append(banco_dados.registrar_solicitacao(self.conexao, {
                "modulo_id": modulo_id, "descricao": "Revisar sensor",
                "prioridade": prioridade, "status": status,
            }))
        antes = banco_dados.listar_solicitacoes(self.conexao, status=None)
        indicadores = self.analisar()["indicadores"]
        self.assertEqual([r["id"] for r in indicadores["fila_solicitacoes"]], [ids[0], ids[2]])
        self.assertEqual(indicadores["quantidade_solicitacoes_pendentes"], 2)
        self.assertEqual(banco_dados.listar_solicitacoes(self.conexao, status=None), antes)

    def test_execucoes_repetidas_nao_escrevem_nem_duplicam(self):
        self.carregar_csv()
        antes = list(self.conexao.iterdump())
        comandos = []
        self.conexao.set_trace_callback(comandos.append)
        resultado = self.analisar()
        self.assertEqual(resultado, self.analisar())
        self.conexao.set_trace_callback(None)
        self.assertTrue(all(c.lstrip().upper().startswith("SELECT") for c in comandos))
        self.assertEqual(list(self.conexao.iterdump()), antes)
        self.assertEqual(self.conexao.execute("SELECT COUNT(*) FROM alertas").fetchone()[0], 0)
        self.assertEqual(self.conexao.execute("SELECT COUNT(*) FROM solicitacoes").fetchone()[0], 0)

    def test_persistencia_explicita_externa_permanece_idempotente(self):
        self.carregar_csv()
        alertas = self.analisar()["alertas"]
        self.assertEqual(banco_dados.registrar_alertas(self.conexao, alertas), 19)
        self.assertEqual(banco_dados.registrar_alertas(self.conexao, self.analisar()["alertas"]), 0)
        self.assertEqual(self.conexao.execute("SELECT COUNT(*) FROM alertas").fetchone()[0], 19)

    def test_nao_confirma_nem_desfaz_transacao_do_chamador(self):
        self.criar_serie()
        self.conexao.execute("UPDATE modulos SET nome = 'Pendente'")
        self.analisar()
        self.assertTrue(self.conexao.in_transaction)
        self.conexao.rollback()
        self.assertEqual(banco_dados.listar_modulos(self.conexao)[0]["nome"], "Teste")

    def test_banco_vazio_nao_inventa_zero_medias_ou_previsoes(self):
        resultado = self.analisar()
        self.assertEqual(resultado["simulacao"], {})
        self.assertEqual(resultado["previsao"], {})
        self.assertEqual(resultado["alertas"], [])
        self.assertEqual(resultado["indicadores"]["quantidade_leituras"], 0)
        self.assertNotIn("consumo_medio_kw", resultado["indicadores"])
        self.assertNotIn("geracao_media_kw", resultado["indicadores"])
        self.assertIn("Sem leituras energéticas", " ".join(resultado["limitacoes"]))
        self.assertTrue(resultado["recomendacoes"]["limitacoes"])

    def test_apenas_leituras_nao_energeticas_nao_inventam_energia(self):
        self.criar_serie(quantidade=1)
        self.conexao.execute("UPDATE sensores SET tipo = 'temperatura', unidade = '°C'")
        resultado = self.analisar()
        self.assertEqual(resultado["indicadores"]["quantidade_leituras"], 2)
        self.assertEqual(resultado["indicadores"]["quantidade_ciclos"], 0)
        self.assertEqual(resultado["simulacao"], {})
        self.assertEqual(resultado["previsao"], {})

    def test_nove_ciclos_simula_sem_regressao_ou_metricas_fabricadas(self):
        self.criar_serie(quantidade=9)
        resultado = self.analisar()
        self.assertEqual(len(resultado["simulacao"]["historico"]), 9)
        self.assertEqual(resultado["previsao"], {})
        self.assertIn("9 ciclos", " ".join(resultado["limitacoes"]))

    def test_um_ciclo_simula(self):
        self.criar_serie(quantidade=1)
        resultado = self.analisar()
        self.assertEqual(resultado["simulacao"]["resumo"]["quantidade_ciclos"], 1)
        self.assertEqual(resultado["previsao"], {})

    def test_zero_medido_e_diferente_de_ausencia(self):
        self.criar_serie(consumo=lambda ciclo: 0, geracao=0)
        resultado = self.analisar()
        self.assertEqual(resultado["indicadores"]["consumo_medio_kw"], 0)
        self.assertEqual(resultado["simulacao"]["resumo"]["deficit_total_kwh"], 0)
        self.assertIsNone(resultado["previsao"]["metricas"]["r2"])
        self.assertEqual(len(resultado["previsao"]["previsoes"]), 3)
        self.assertIn("R²", " ".join(resultado["limitacoes"]))
        self.assertIn("média do treino: 0 kW", " ".join(resultado["recomendacoes"]["energia"]))
        self.assertNotIn("Pico de consumo previsto", " ".join(resultado["recomendacoes"]["energia"]))

    def test_previsao_negativa_preservada_e_sinalizada(self):
        self.criar_serie(consumo=lambda ciclo: 10 - ciclo)
        resultado = self.analisar()
        self.assertLess(resultado["previsao"]["previsoes"][0]["consumo_previsto_kw"], 0)
        self.assertIn("negativ", " ".join(resultado["limitacoes"]).lower())
        self.assertIn("Estimativa de referência pela média do treino",
                      " ".join(resultado["recomendacoes"]["energia"]))
        self.assertNotIn("Pico de consumo previsto", " ".join(resultado["recomendacoes"]["energia"]))

    def test_lacunas_nao_geram_amostras_ou_energia_artificial(self):
        self.criar_serie()
        self.conexao.execute("DELETE FROM leituras WHERE ciclo = 5")
        resultado = self.analisar()
        self.assertEqual(resultado["indicadores"]["quantidade_ciclos"], 9)
        self.assertEqual(resultado["simulacao"]["resumo"]["consumo_total_kwh"], 68)
        self.assertIn("lacunas", " ".join(resultado["limitacoes"]))

    def test_rejeita_grandeza_ausente_em_toda_base(self):
        self.criar_serie()
        self.conexao.execute("DELETE FROM leituras WHERE sensor_id = 2")
        with self.assertRaisesRegex(ValueError, "consumo e geração"):
            self.analisar()

    def test_rejeita_sensor_ausente_em_um_ciclo(self):
        self.criar_serie()
        self.conexao.execute("DELETE FROM leituras WHERE sensor_id = 2 AND ciclo = 3")
        with self.assertRaisesRegex(ValueError, "ciclo 3"):
            self.analisar()

    def test_rejeita_cobertura_parcial_mesmo_com_ambas_grandezas(self):
        self.carregar_csv()
        leitura = banco_dados.consultar_leituras(self.conexao)[0]
        self.conexao.execute("DELETE FROM leituras WHERE id = ?",
                             (leitura["leitura_id"],))
        with self.assertRaisesRegex(ValueError, "Série incompleta"):
            self.analisar()

    def test_sensor_cadastrado_sem_leituras_sinaliza_cobertura(self):
        modulo_id = self.criar_serie()
        banco_dados.cadastrar_sensor(self.conexao, {
            "codigo": "SEM-LEITURAS", "modulo_id": modulo_id,
            "tipo": "consumo_kw", "unidade": "kW",
        })
        resultado = self.analisar()
        self.assertIn("SEM-LEITURAS", " ".join(resultado["limitacoes"]))
        self.assertEqual(resultado["indicadores"]["consumo_medio_kw"], 7.5)

    def test_potencia_negativa_nao_e_mascarada_pela_soma(self):
        self.carregar_csv()
        self.conexao.execute("UPDATE leituras SET valor = -0.01 WHERE id = 1")
        with self.assertRaisesRegex(ValueError, "Potência inválida"):
            self.analisar()

    def test_rejeita_infinito_e_texto_no_banco(self):
        self.criar_serie()
        for valor in (float("inf"), "invalido"):
            with self.subTest(valor=valor):
                self.conexao.execute("UPDATE leituras SET valor = ? WHERE id = 1", (valor,))
                with self.assertRaisesRegex(ValueError, "Potência inválida"):
                    self.analisar()

    def test_rejeita_unidade_incompativel(self):
        self.criar_serie()
        self.conexao.execute("UPDATE sensores SET unidade = 'W' WHERE id = 1")
        with self.assertRaisesRegex(ValueError, "deve usar kW"):
            self.analisar()

    def test_status_atual_nao_exclui_historico_mas_afeta_regras(self):
        self.criar_serie()
        antes = self.analisar()
        self.assertEqual(len(antes["alertas"]), 10)
        self.conexao.execute("UPDATE sensores SET status = 'invalido' WHERE id = 1")
        self.conexao.execute("UPDATE modulos SET status = 'manutencao'")
        depois = self.analisar()
        self.assertEqual(depois["simulacao"], antes["simulacao"])
        self.assertEqual(depois["alertas"], [])
        self.assertEqual(len(depois["indicadores"]["bloqueios_operacionais"]), 20)
        self.assertIn("R2 identificou", " ".join(depois["limitacoes"]))

    def test_rejeita_conexao_ausente_ou_de_tipo_errado(self):
        for conexao in (None, object(), {}, ":memory:"):
            with self.subTest(conexao=conexao), self.assertRaises(TypeError):
                analise_integrada.executar_analise_integrada(conexao)

    def test_conexao_exige_row_factory_do_contrato(self):
        self.conexao.row_factory = None
        with self.assertRaisesRegex(ValueError, "sqlite3.Row"):
            self.analisar()

    def test_conexao_fechada_propaga_erro_sqlite(self):
        self.conexao.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            self.analisar()

    def test_banco_sem_esquema_propaga_erro_sem_inicializacao_automatica(self):
        with contextlib.closing(banco_dados.abrir_conexao(":memory:")) as conexao:
            with self.assertRaises(sqlite3.OperationalError):
                analise_integrada.executar_analise_integrada(conexao)
            self.assertEqual(conexao.execute("SELECT name FROM sqlite_master").fetchall(), [])

    def test_erro_do_modelo_nao_e_confundido_com_poucos_dados(self):
        self.criar_serie()
        with patch.object(analise_integrada, "avaliar_e_prever_consumo",
                          side_effect=ValueError("Falha numérica")):
            with self.assertRaisesRegex(ValueError, "Falha numérica"):
                self.analisar()
        self.assertEqual(self.conexao.execute("SELECT COUNT(*) FROM alertas").fetchone()[0], 0)

    def test_demonstracao_integrada_usa_csv_e_memoria(self):
        resultado = analise_integrada.demonstrar_analise_integrada()
        self.assertEqual(resultado["indicadores"]["quantidade_leituras"], 320)
        self.assertEqual(resultado["indicadores"]["quantidade_ciclos"], 32)
        self.assertEqual(self.conexao.execute("SELECT COUNT(*) FROM leituras").fetchone()[0], 0)


class TestEntradasAnalise(unittest.TestCase):
    def executar_processo(self, argumentos, entrada=None):
        with tempfile.TemporaryDirectory() as diretorio:
            ambiente = dict(os.environ, PYTHONPATH=str(DIRETORIO_BASE))
            processo = subprocess.run(
                [sys.executable, "-X", "utf8", "-B", *argumentos], input=entrada,
                cwd=diretorio, env=ambiente, capture_output=True, text=True,
                encoding="utf-8", timeout=30,
            )
            self.assertEqual(processo.returncode, 0, processo.stderr)
            self.assertEqual(list(Path(diretorio).iterdir()), [])
            return processo

    def test_importacao_silenciosa_sem_banco_graficos_ou_dependencias_pesadas(self):
        processo = self.executar_processo(["-c", (
            "import analise_integrada, sys; "
            "assert not {'numpy', 'pandas', 'matplotlib', 'codigo_fonte'} & set(sys.modules)"
        )])
        self.assertEqual(processo.stdout, "")
        self.assertEqual(processo.stderr, "")

    def test_cli_integrada_json_valido_sem_arquivos(self):
        processo = self.executar_processo([str(DIRETORIO_BASE / "analise_integrada.py")])
        resultado = json.loads(processo.stdout)
        self.assertEqual(resultado["indicadores"]["quantidade_ciclos"], 32)
        self.assertEqual(len(resultado["alertas"]), 19)

    def test_opcao_existente_do_menu_permanece_repetivel(self):
        processo = self.executar_processo([str(DIRETORIO_BASE / "main.py")], "2\n\n2\n\n4\n")
        self.assertEqual(processo.stdout.count("avaliação fora do treino"), 2)
        self.assertEqual(processo.stdout.count("SoC final:"), 2)

    def test_compatibilidade_reutiliza_mesma_serie_e_modelos(self):
        from demonstracao_energia import criar_serie_demonstracao

        with contextlib.redirect_stdout(io.StringIO()):
            simulacao = analise_integrada.simular_consumo_energetico()
            previsao = analise_integrada.modelo_linear_previsao()
        self.assertEqual(simulacao, simular_balanco_energetico(criar_serie_demonstracao()))
        self.assertEqual(previsao, avaliar_e_prever_consumo(criar_serie_demonstracao()))


if __name__ == "__main__":
    unittest.main()
