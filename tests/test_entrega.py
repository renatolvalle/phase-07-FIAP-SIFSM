"""Documentos e empacotamento: todo arquivo de teste é escrito em pasta temporária."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import warnings
import zipfile

from scripts.empacotar import ARQUIVOS, RAIZ, montar_zip, selecionar_arquivos, validar_url_video
from scripts.validar_entrega import conferir_zip


class TestURLVideo(unittest.TestCase):
    def test_aceita_watch_e_url_curta(self):
        for url in ("https://www.youtube.com/watch?v=AbCdEf123_-",
                    "https://youtu.be/AbCdEf123_-", "https://m.youtube.com/watch?v=AbCdEf123_-&t=10"):
            self.assertEqual(validar_url_video(url + "\n"), url)

    def test_rejeita_host_falso_http_e_credenciais(self):
        for url in ("http://youtu.be/AbCdEf123_-", "https://youtube.com.example/watch?v=AbCdEf123_-",
                    "https://user@youtu.be/AbCdEf123_-", "https://youtu.be:443/AbCdEf123_-",
                    "https://example.org/watch?v=AbCdEf123_-"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validar_url_video(url)

    def test_rejeita_placeholder_multiplas_urls_e_id_invalido(self):
        for url in ("PENDENTE", "https://youtu.be/curto", "https://www.youtube.com/",
                    "https://youtu.be/AbCdEf123_-\nhttps://youtu.be/AbCdEf123_-",
                    "https://www.youtube.com/watch?v=AbCdEf123_-&v=AbCdEf123_-",
                    "https://youtu.be/AbCdEf123_-#fragmento"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validar_url_video(url)


class TestEmpacotamento(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sifsm-pacote-teste-")
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name) / "projeto"
        for nome in ARQUIVOS:
            destino = self.raiz / nome
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RAIZ / nome, destino)
        self.zip = Path(self.tmp.name) / "entrega.zip"

    def montar(self, final=False):
        return montar_zip(self.zip, self.raiz, final)

    def alterar_zip(self, nome, valor, duplicar=False):
        with zipfile.ZipFile(self.zip) as z:
            conteudo = {i: z.read(i) for i in z.namelist()}
        if not duplicar:
            conteudo[nome] = valor
        with zipfile.ZipFile(self.zip, "w") as z:
            for n, v in conteudo.items():
                z.writestr(n, v)
            if duplicar:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    z.writestr(nome, valor)

    def test_lista_explicita_exclui_arquivos_locais(self):
        for nome in (".env", "aurora_siger.db", "HANDOFF.md", "privado.py"):
            (self.raiz / nome).write_text("não entregar", encoding="utf-8")
        selecionados = selecionar_arquivos(self.raiz)
        self.assertEqual(set(selecionados), set(ARQUIVOS))
        self.assertEqual(len(selecionados), len(set(selecionados)))

    def test_arquivo_obrigatorio_ausente_bloqueia(self):
        (self.raiz / "banco_aurora_siger.sql").unlink()
        with self.assertRaisesRegex(ValueError, "obrigatório ausente"):
            self.montar()
        self.assertFalse(self.zip.exists())

    def test_destino_nao_pode_sobrescrever_fonte(self):
        with self.assertRaisesRegex(ValueError, "substituir"):
            montar_zip(self.raiz / "codigo_fonte.py", self.raiz)

    def test_destino_nao_pode_sobrescrever_banco_local(self):
        banco = self.raiz / "aurora_siger.db"
        banco.write_bytes(b"banco local preservado")
        with self.assertRaisesRegex(ValueError, "extensão .zip"):
            montar_zip(banco, self.raiz)
        self.assertEqual(banco.read_bytes(), b"banco local preservado")

    def test_final_exige_video_sem_placeholder(self):
        with self.assertRaisesRegex(ValueError, "falta link_video"):
            self.montar(final=True)
        (self.raiz / "link_video.txt").write_text("PENDENTE", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.montar()

    def test_video_valido_incluido_mas_sem_alegar_verificacao_youtube(self):
        (self.raiz / "link_video.txt").write_text("https://youtu.be/AbCdEf123_-\n", encoding="utf-8")
        manifesto = self.montar(final=True)
        verificado, conteudo = conferir_zip(self.zip, final=True)
        self.assertTrue(verificado["video_url_incluida"])
        self.assertIn("link_video.txt", conteudo)
        self.assertIn("Somente sintaxe", manifesto["escopo_validacao_video"])

    def test_zip_tecnico_valido_e_final_deliberadamente_reprovado(self):
        self.montar()
        manifesto, conteudo = conferir_zip(self.zip)
        self.assertEqual(len(manifesto["pendencias_humanas"]), 2)
        self.assertFalse(manifesto["video_url_incluida"])
        self.assertEqual(set(conteudo), set(ARQUIVOS) | {"manifesto_entrega.json"})
        with self.assertRaisesRegex(ValueError, "falta link_video"):
            conferir_zip(self.zip, final=True)

    def test_zip_deterministico_e_checksum_correto(self):
        self.montar()
        antes = self.zip.read_bytes()
        self.montar()
        self.assertEqual(self.zip.read_bytes(), antes)
        self.assertTrue(self.zip.with_suffix(".zip.sha256").read_text().startswith(hashlib.sha256(antes).hexdigest()))

    def test_finais_de_linha_nao_mudam_pacote_ou_hash_de_fontes(self):
        self.montar()
        antes = self.zip.read_bytes()
        for nome in ARQUIVOS:
            p = self.raiz / nome
            if p.suffix in {".py", ".md", ".txt", ".sql", ".csv", ".json"}:
                valor = p.read_bytes().replace(b"\r\n", b"\n")
                p.write_bytes(valor.replace(b"\n", b"\r\n"))
        self.montar()
        self.assertEqual(antes, self.zip.read_bytes())
        conferir_zip(self.zip)

    def test_tamper_de_arquivo_e_rejeitado(self):
        self.montar()
        self.alterar_zip("codigo_fonte.py", b"print('alterado')")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            conferir_zip(self.zip)

    def test_caminho_perigoso_e_arquivo_extra_rejeitados(self):
        for nome in ("../escape.py", ".env", "C:/escape.py"):
            self.montar()
            self.alterar_zip(nome, b"inesperado")
            with self.subTest(nome=nome), self.assertRaisesRegex(ValueError, "inesperado"):
                conferir_zip(self.zip)

    def test_entrada_duplicada_rejeitada(self):
        self.montar()
        self.alterar_zip("README.md", b"duplicado", duplicar=True)
        with self.assertRaisesRegex(ValueError, "duplicados"):
            conferir_zip(self.zip)

    def test_evidencia_desatualizada_rejeitada(self):
        with (self.raiz / "config.py").open("a", encoding="utf-8") as f:
            f.write("\n# Mudança posterior à coleta\n")
        self.montar()
        with self.assertRaisesRegex(ValueError, "Evidência desatualizada"):
            conferir_zip(self.zip)

    def test_evidencia_sem_fontes_rejeitada(self):
        arquivo = self.raiz / "graficos_ou_imagens/resultado_integrado.json"
        evidencia = json.loads(arquivo.read_text(encoding="utf-8"))
        evidencia["fontes_sha256"] = {}
        arquivo.write_text(json.dumps(evidencia), encoding="utf-8")
        self.montar()
        with self.assertRaisesRegex(ValueError, "fontes da evidência"):
            conferir_zip(self.zip)

    def test_manifesto_de_tipo_invalido_rejeitado(self):
        self.montar()
        self.alterar_zip("manifesto_entrega.json", b"[]")
        with self.assertRaisesRegex(ValueError, "objeto JSON"):
            conferir_zip(self.zip)

    def test_sintaxe_invalida_rejeitada(self):
        (self.raiz / "main.py").write_text("def inválida(\n", encoding="utf-8")
        self.montar()
        with self.assertRaises(SyntaxError):
            conferir_zip(self.zip)

    def test_link_local_ausente_rejeitado(self):
        with (self.raiz / "README.md").open("a", encoding="utf-8") as f:
            f.write("\n[Arquivo](arquivo-ausente.md)\n")
        self.montar()
        with self.assertRaisesRegex(ValueError, "Link local ausente"):
            conferir_zip(self.zip)

    def test_manifesto_video_incoerente_rejeitado(self):
        manifesto = self.montar()
        manifesto["video_url_incluida"] = True
        self.alterar_zip("manifesto_entrega.json", json.dumps(manifesto).encode())
        with self.assertRaisesRegex(ValueError, "Situação do vídeo"):
            conferir_zip(self.zip)


class TestDocumentacao(unittest.TestCase):
    def test_evidencias_numericas_e_tabelas_do_relatorio(self):
        dados = json.loads((RAIZ / "graficos_ou_imagens/resultado_integrado.json").read_text(encoding="utf-8"))
        resultado = dados["resultado"]
        self.assertEqual(resultado["indicadores"]["quantidade_leituras"], 320)
        self.assertAlmostEqual(resultado["simulacao"]["resumo"]["deficit_total_kwh"], 92.29)
        self.assertAlmostEqual(dados["estresse_geracao_menos_30_pct"]["resumo"]["deficit_total_kwh"], 112.318)
        m = resultado["previsao"]["metricas"]
        self.assertGreater(m["mae_kw"], m["mae_referencia_kw"])
        texto = (RAIZ / "docs/relatorio_tecnico.md").read_text(encoding="utf-8")
        for chave in ("simulacao",):
            resumo = resultado[chave]["resumo"]
            for campo in ("consumo_total_kwh", "geracao_total_kwh", "deficit_total_kwh", "atendimento_percentual"):
                valor = f"{resumo[campo]:.2f}".replace(".", ",")
                self.assertIn(valor, texto)
        for campo in ("mae_kw", "rmse_kw", "mae_referencia_kw", "r2"):
            self.assertIn(f"{m[campo]:.7f}".replace(".", ",").replace("-", "−"), texto)

    def test_assinaturas_pdf_e_png_presentes(self):
        for nome in ("relatorio_tecnico.pdf", "circuito_logico.pdf"):
            self.assertTrue((RAIZ / nome).read_bytes().startswith(b"%PDF-"))
        for nome in ("arquitetura", "csv_energia", "csv_regressao"):
            self.assertTrue((RAIZ / f"graficos_ou_imagens/{nome}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    @unittest.skipUnless(importlib.util.find_spec("pypdf"), "Instale requirements-docs.txt para conferir os PDFs.")
    def test_pdf_paginas_sumario_metadados_e_margens(self):
        from pypdf import PdfReader
        relatorio = PdfReader(RAIZ / "relatorio_tecnico.pdf")
        circuito = PdfReader(RAIZ / "circuito_logico.pdf")
        self.assertEqual(len(circuito.pages), 2)
        self.assertGreater(len(relatorio.pages), 10)
        texto = "\n".join(p.extract_text() for p in relatorio.pages)
        self.assertIn("SUMÁRIO", texto)
        self.assertIn("REFERÊNCIAS", texto)
        self.assertNotIn("tb_modulos", texto)
        self.assertNotIn("\u25a0", texto)
        self.assertGreater(len(relatorio.outline), 8)
        self.assertTrue(any(p.get("/Annots") for p in relatorio.pages[:6]))
        for pdf in (relatorio, circuito):
            self.assertIn("Danilo Fernandes", pdf.metadata.author)
            self.assertEqual(pdf.metadata.producer, "SIFSM")
            for p in pdf.pages:
                self.assertAlmostEqual(float(p.mediabox.width), 595.2756, places=2)
                self.assertAlmostEqual(float(p.mediabox.height), 841.8898, places=2)
        for pdf, inicio, desconto in ((relatorio, 5, 1), (circuito, 0, 0)):
            for i, p in enumerate(pdf.pages):
                cabecalho = []

                def visitar(texto, cm, tm, fonte, tamanho):
                    if tm[5] > 770 and texto.strip():
                        cabecalho.append(texto.strip())

                p.extract_text(visitor_text=visitar)
                self.assertEqual(cabecalho, [str(i + 1 - desconto)] if i >= inicio else [])

    @unittest.skipUnless(importlib.util.find_spec("reportlab"), "Instale requirements-docs.txt.")
    def test_tabela_documental_divergente_bloqueia_pdf(self):
        from scripts.gerar_documentos import coletar_resultados, ler_corpo
        trecho = "| Medida | Base | Geração −30% |\n|---|---|---|\n| Consumo (kWh) | 0 | 0 |"
        with self.assertRaisesRegex(ValueError, "diverge dos modelos"):
            ler_corpo(trecho, coletar_resultados())

    @unittest.skipUnless(importlib.util.find_spec("reportlab"), "Instale requirements-docs.txt para reconstruir os PDFs.")
    def test_documentos_reconstruiveis_e_pdf_deterministico(self):
        from scripts.gerar_documentos import coletar_resultados, gerar_circuito, gerar_relatorio
        with tempfile.TemporaryDirectory(prefix="sifsm-documentos-teste-") as pasta:
            a, b = Path(pasta) / "a.pdf", Path(pasta) / "b.pdf"
            gerar_circuito(a)
            gerar_circuito(b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(a.read_bytes(), (RAIZ / "circuito_logico.pdf").read_bytes())
            dados = coletar_resultados()
            evidencia = json.loads((RAIZ / "graficos_ou_imagens/resultado_integrado.json").read_text(encoding="utf-8"))
            self.assertEqual(dados, evidencia)
            gerar_relatorio(dados, a)
            gerar_relatorio(dados, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(a.read_bytes(), (RAIZ / "relatorio_tecnico.pdf").read_bytes())


if __name__ == "__main__":
    unittest.main()
