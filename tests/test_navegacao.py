"""Navegação unificada: dados reais, falhas, repetição e entradas isoladas da CLI."""

import io
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from unittest.mock import patch

import banco_dados
import codigo_fonte
import main
from config import CAMINHO_CSV, DIRETORIO_BASE


class TestNavegacaoIntegrada(unittest.TestCase):
    def setUp(self):
        self.conexao = banco_dados.abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)
        banco_dados.inicializar_banco(self.conexao)

    def executar(self, funcao, entradas=()):
        saida = io.StringIO()
        with (
            patch("codigo_fonte.limpar_tela"),
            patch("codigo_fonte.pausar"),
            patch("builtins.input", side_effect=entradas),
            redirect_stdout(saida),
        ):
            funcao(self.conexao)
        return saida.getvalue()

    def importar(self):
        banco_dados.carregar_csv_inicial(self.conexao, CAMINHO_CSV)

    def criar_serie(self, consumos):
        modulo_id = banco_dados.cadastrar_modulo(self.conexao, {
            "codigo": "MOD-TESTE", "nome": "Teste", "tipo": "energia", "critico": 1,
        })
        sensores = [banco_dados.cadastrar_sensor(self.conexao, {
            "codigo": tipo, "modulo_id": modulo_id, "tipo": tipo, "unidade": "kW",
        }) for tipo in ("consumo_kw", "geracao_kw")]
        for ciclo, consumo in enumerate(consumos, 1):
            for sensor_id, valor in zip(sensores, (consumo, 2.0)):
                banco_dados.registrar_leitura(self.conexao, {
                    "sensor_id": sensor_id, "ciclo": ciclo, "valor": valor,
                    "instante": "2026-11-10T12:00:00Z",
                })

    def test_main_encaminha_para_a_mesma_funcao(self):
        self.assertIs(main.main, codigo_fonte.main)

    def test_todas_as_opcoes_encaminham_e_sao_repetiveis(self):
        nomes = (
            "menu_dados", "exibir_monitoramento_sensores", "menu_estruturas_dados",
            "exibir_simulacao_computacional", "exibir_modelo_linear", "exibir_agentes",
            "exibir_sustentabilidade", "exibir_informacoes_tecnicas",
        )
        from contextlib import ExitStack

        with ExitStack() as pilha:
            funcoes = [pilha.enter_context(patch.object(codigo_fonte, nome)) for nome in nomes]
            saida = self.executar(codigo_fonte.menu_principal, list("12345678123456780"))
        for funcao in funcoes:
            self.assertEqual(funcao.call_count, 2)
            funcao.assert_called_with(self.conexao)
        self.assertNotIn("Funcionalidade em Desenvolvimento", saida)

    def test_opcoes_invalidas_retornam_ao_menu(self):
        for funcao in (codigo_fonte.menu_principal, codigo_fonte.menu_dados,
                       codigo_fonte.menu_estruturas_dados):
            with self.subTest(funcao=funcao.__name__):
                saida = self.executar(funcao, ["", "abc", "99", "0"])
                self.assertIn("inválida", saida)

    def test_voltar_dos_submenus_nao_fecha_conexao(self):
        self.executar(codigo_fonte.menu_principal, ["1", "0", "3", "0", "0"])
        self.assertEqual(self.conexao.execute("SELECT 1").fetchone()[0], 1)

    def test_regressao_csv_preserva_metricas_e_explicita_referencia(self):
        self.importar()
        saida = self.executar(codigo_fonte.exibir_modelo_linear)
        for texto in ("treino: 25", "teste posterior: 7", "0.2766813 kW",
                      "0.2722857 kW", "-0.0193275", "5.3440 kW", "Ciclo 33: 5.2824615",
                      "BRUTAS", "extrapolação", "Estimativa de referência", "sem ganho preditivo",
                      "porcentagem", "ciclo zero", "kW por ciclo"):
            self.assertIn(texto, saida)

    def test_regressao_sem_dados_nao_inventa_resultados(self):
        saida = self.executar(codigo_fonte.exibir_modelo_linear)
        self.assertIn("Previsão indisponível", saida)
        self.assertNotIn("MAE:", saida)
        self.assertNotIn("Ciclo 33", saida)

    def test_serie_curta_tem_simulacao_mas_nao_regressao(self):
        self.criar_serie([6.0])
        saida = self.executar(codigo_fonte.exibir_sustentabilidade)
        self.assertIn("Energia consumida: 6.00 kWh", saida)
        self.assertIn("Previsão indisponível", saida)
        self.assertIn("1 ciclos", saida)

    def test_r2_indefinido_e_sinalizado_sem_converter_em_zero(self):
        self.criar_serie([1.0] * 10)
        saida = self.executar(codigo_fonte.exibir_modelo_linear)
        self.assertIn("R²: indefinido (teste constante)", saida)
        self.assertNotIn("R²: 0.0000000", saida)

    def test_previsoes_negativas_nao_sao_cortadas_ou_endossadas(self):
        self.criar_serie([float(10 - i) for i in range(1, 11)])
        saida = self.executar(codigo_fonte.exibir_modelo_linear)
        self.assertIn("Ciclo 11: -1.0000000 kW", saida)
        self.assertIn("negativ", saida)
        self.assertIn("Estimativa de referência", saida)

    def test_sustentabilidade_csv_resultados_independentes_conhecidos(self):
        self.importar()
        saida = self.executar(codigo_fonte.exibir_sustentabilidade)
        for texto in ("Módulos: 5", "Sensores: 10", "Leituras: 320", "Ciclos energéticos: 32",
                      "não gravados): 19", "171.05 kWh", "66.76 kWh", "92.29 kWh", "46.05%",
                      "SoC final: 0.00%", "média somente do treino: 5.3440 kW",
                      "privacidade", "Sustentabilidade digital", "Responsabilidade social"):
            self.assertIn(texto, saida)

    def test_sustentabilidade_vazia_nao_afirma_atendimento(self):
        saida = self.executar(codigo_fonte.exibir_sustentabilidade)
        self.assertIn("Módulos: 0", saida)
        self.assertIn("Simulação indisponível", saida)
        self.assertIn("IMPORTAR", saida)
        self.assertNotIn("100.00%", saida)
        self.assertNotIn("Atendimento simulado", saida)

    def test_fila_da_analise_reflete_cadastro_sem_atender(self):
        self.importar()
        solicitacao_id = banco_dados.registrar_solicitacao(self.conexao, {
            "modulo_id": banco_dados.listar_modulos(self.conexao)[0]["id"],
            "descricao": "Verificar consumo", "prioridade": "alta",
        })
        saida = self.executar(codigo_fonte.exibir_sustentabilidade)
        self.assertIn("Solicitações pendentes na fila FIFO: 1", saida)
        self.assertIn(f"Primeira na fila: ID {solicitacao_id}", saida)
        self.assertEqual(len(banco_dados.listar_solicitacoes(self.conexao)), 1)

    def test_telas_analiticas_nao_modificam_banco(self):
        self.importar()
        antes = list(self.conexao.iterdump())
        for funcao in (codigo_fonte.exibir_modelo_linear, codigo_fonte.exibir_sustentabilidade,
                       codigo_fonte.exibir_simulacao_computacional,
                       codigo_fonte.exibir_informacoes_tecnicas):
            with self.subTest(funcao=funcao.__name__):
                self.executar(funcao)
                self.assertEqual(list(self.conexao.iterdump()), antes)

    def test_informacoes_tecnicas_coerentes_com_implementacao(self):
        saida = self.executar(codigo_fonte.exibir_informacoes_tecnicas)
        for texto in ("codigo_fonte.py", "main.py", "SQLite", "20 kWh", "12 kWh", "1 h",
                      "CPU", "GPU/NPU/TPU", "latência nula", "não usadas", "sem IA generativa",
                      "sem histórico de status", "proteger o arquivo"):
            self.assertIn(texto, saida)
        self.assertIn("Nenhum corte de cargas", saida)

    def test_agentes_demonstracao_repetivel_e_sem_cadastro(self):
        self.importar()
        antes = list(self.conexao.iterdump())
        primeira = self.executar(codigo_fonte.exibir_agentes, [""])
        segunda = self.executar(codigo_fonte.exibir_agentes, [""])
        self.assertEqual(primeira, segunda)
        self.assertIn("guardrail", primeira)
        self.assertEqual(list(self.conexao.iterdump()), antes)

    def test_agentes_consulta_critica_bloqueada_inclusive_por_manutencao(self):
        saida = self.executar(codigo_fonte.exibir_agentes,
                             ["Desligar suporte vital por falha e manutenção"])
        resposta = saida.rsplit("Ação bloqueada pelo guardrail", 1)[-1]
        self.assertIn("autorização manual", resposta)
        self.assertIn("Nenhuma ação executada", resposta)
        self.assertEqual(banco_dados.listar_solicitacoes(self.conexao, None), [])

    def test_agentes_texto_so_pontuacao_e_erro_compreensivel(self):
        self.assertIn("Solicitação inválida", self.executar(codigo_fonte.exibir_agentes, ["!!!"]))

    def test_erro_sqlite_nas_telas_retornavel(self):
        self.conexao.close()
        for funcao in (codigo_fonte.exibir_modelo_linear, codigo_fonte.exibir_sustentabilidade,
                       codigo_fonte.exibir_simulacao_computacional):
            with self.subTest(funcao=funcao.__name__):
                self.assertIn("Erro ao consultar", self.executar(funcao))

    def test_cobertura_parcial_e_rejeitada_em_todas_telas_analiticas(self):
        self.importar()
        self.conexao.execute("DELETE FROM leituras WHERE id = (SELECT MIN(id) FROM leituras)")
        self.conexao.commit()
        for funcao in (codigo_fonte.exibir_modelo_linear, codigo_fonte.exibir_sustentabilidade,
                       codigo_fonte.exibir_simulacao_computacional):
            with self.subTest(funcao=funcao.__name__):
                saida = self.executar(funcao)
                self.assertIn("Série incompleta", saida)
                self.assertNotIn("Energia consumida:", saida)

    def test_unidade_errada_e_rejeitada_no_monitoramento(self):
        self.importar()
        self.conexao.execute("UPDATE sensores SET unidade = 'W' WHERE tipo = 'consumo_kw'")
        saida = self.executar(codigo_fonte.exibir_monitoramento_sensores, [""])
        self.assertIn("Dados inválidos", saida)
        self.assertEqual(self.conexao.execute("SELECT COUNT(*) FROM alertas").fetchone()[0], 0)

    def test_erro_numerico_nao_vira_sucesso_e_menu_continua(self):
        with patch("codigo_fonte.executar_analise_integrada", side_effect=OverflowError("teste")):
            saida = self.executar(codigo_fonte.menu_principal, ["5", "7", "8", "0"])
        self.assertIn("Dados inválidos para a regressão", saida)
        self.assertIn("Dados inválidos para a análise", saida)
        self.assertIn("INFORMAÇÕES TÉCNICAS", saida)


class TestCicloVidaAplicacao(unittest.TestCase):
    def executar_main(self, entradas=(), inicializacao=None):
        conexao = banco_dados.abrir_conexao(":memory:")
        self.addCleanup(conexao.close)
        saida = io.StringIO()
        with (
            patch("codigo_fonte.abrir_conexao", return_value=conexao),
            patch("codigo_fonte.inicializar_banco", side_effect=inicializacao),
            patch("builtins.input", side_effect=entradas),
            patch("codigo_fonte.limpar_tela"),
            redirect_stdout(saida),
        ):
            retorno = codigo_fonte.main()
        with self.assertRaises(sqlite3.ProgrammingError):
            conexao.execute("SELECT 1")
        return retorno, saida.getvalue()

    def test_saida_normal_fecha_conexao(self):
        self.assertEqual(self.executar_main(["0"])[0], 0)

    def test_eof_fecha_conexao(self):
        retorno, saida = self.executar_main([EOFError()])
        self.assertEqual(retorno, 0)
        self.assertIn("Entrada encerrada", saida)

    def test_ctrl_c_no_submenu_fecha_conexao(self):
        self.assertEqual(self.executar_main(["1", KeyboardInterrupt()])[0], 0)

    def test_eof_na_pausa_fecha_conexao(self):
        self.assertEqual(self.executar_main(["8", EOFError()])[0], 0)

    def test_inicializacao_falha_fecha_conexao_e_retorna_erro(self):
        retorno, saida = self.executar_main(inicializacao=sqlite3.OperationalError("falha"))
        self.assertEqual(retorno, 1)
        self.assertIn("Não foi possível inicializar", saida)

    def test_abertura_falha_sem_tentar_navegar(self):
        with (
            patch("codigo_fonte.abrir_conexao", side_effect=OSError("sem acesso")),
            patch("codigo_fonte.menu_principal") as menu,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(codigo_fonte.main(), 1)
        menu.assert_not_called()

    def test_erro_inesperado_propaga_mas_fecha_conexao(self):
        conexao = banco_dados.abrir_conexao(":memory:")
        self.addCleanup(conexao.close)
        with (
            patch("codigo_fonte.abrir_conexao", return_value=conexao),
            patch("codigo_fonte.menu_principal", side_effect=RuntimeError("inesperado")),
            self.assertRaisesRegex(RuntimeError, "inesperado"),
        ):
            codigo_fonte.main()
        with self.assertRaises(sqlite3.ProgrammingError):
            conexao.execute("SELECT 1")


class TestEntradasCLI(unittest.TestCase):
    def executar_copia(self, arquivo, entrada):
        """Config usa caminhos absolutos ao módulo: copiar é o isolamento real do banco."""
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            for origem in [*DIRETORIO_BASE.glob("*.py"),
                           DIRETORIO_BASE / "banco_aurora_siger.sql", CAMINHO_CSV]:
                shutil.copy2(origem, base / origem.name)
            processo = subprocess.run(
                [sys.executable, "-X", "utf8", "-B", str(base / arquivo)],
                input=entrada, cwd=pasta, capture_output=True, text=True,
                encoding="utf-8", timeout=30,
            )
            self.assertEqual(processo.returncode, 0, processo.stderr)
            self.assertEqual(processo.stderr, "")
            with closing(banco_dados.abrir_conexao(base / "aurora_siger.db")) as conexao:
                totais = {t: conexao.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                          for t in ("modulos", "sensores", "leituras", "alertas", "solicitacoes")}
            self.assertFalse((base / "graficos_ou_imagens").exists())
            self.assertFalse((base / "__pycache__").exists())
            return processo.stdout, totais

    def test_ambas_entradas_demonstram_fluxo_completo_em_copia_isolada(self):
        # Inclui importação, regras/persistência repetida, estruturas, modelos,
        # agentes repetidos, análise e retorno. Não abre o banco do repositório.
        entradas = [
            "1", "9", "IMPORTAR", "", "0",
            "2", "", "REGISTRAR", "", "2", "", "REGISTRAR", "",
            "3", "1", "SEN-HAB-CONS-01", "",
            "2", "1", "Verificar consumo", "alta", "",
            "3", "SIMULAR", "", "0",
            "4", "", "5", "",
            "6", "Desligar suporte vital por falha", "", "6", "manutenção", "",
            "7", "", "8", "", "0",
        ]
        for arquivo in ("codigo_fonte.py", "main.py"):
            with self.subTest(arquivo=arquivo):
                saida, totais = self.executar_copia(arquivo, "\n".join(entradas) + "\n")
                self.assertEqual(totais, {"modulos": 5, "sensores": 10, "leituras": 320,
                                          "alertas": 19, "solicitacoes": 1})
                for texto in ("Novos alertas registrados: 19", "Novos alertas registrados: 0",
                              "Sensor encontrado via tabela hash", "O banco NÃO foi alterado",
                              "92.29 kWh", "0.2766813 kW", "5.3440 kW", "SIFSM - Encerrado!"):
                    self.assertIn(texto, saida)
                self.assertEqual(saida.count("=== AGENTES SIMULADOS E GUARDRAILS ==="), 2)
                self.assertNotIn("Funcionalidade em Desenvolvimento", saida)

    def test_cli_eof_no_menu_encerra_sem_traceback(self):
        for arquivo in ("codigo_fonte.py", "main.py"):
            with self.subTest(arquivo=arquivo):
                saida, totais = self.executar_copia(arquivo, "")
                self.assertIn("Entrada encerrada", saida)
                self.assertTrue(all(total == 0 for total in totais.values()))

    def test_importar_entradas_e_silencioso_sem_banco_ou_dependencias_pesadas(self):
        with tempfile.TemporaryDirectory() as pasta:
            processo = subprocess.run(
                [sys.executable, "-X", "utf8", "-B", "-c", (
                    "from unittest.mock import patch; import sys; "
                    "p = patch('sqlite3.connect', side_effect=AssertionError('abriu banco')); p.start(); "
                    "import main, codigo_fonte; "
                    "assert main.main is codigo_fonte.main; "
                    "assert not {'numpy', 'pandas', 'matplotlib'} & set(sys.modules)"
                )], cwd=pasta, env=dict(os.environ, PYTHONPATH=str(DIRETORIO_BASE)),
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            self.assertEqual(processo.returncode, 0, processo.stderr)
            self.assertEqual(processo.stdout, "")
            self.assertEqual(processo.stderr, "")
            self.assertEqual(list(Path(pasta).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
