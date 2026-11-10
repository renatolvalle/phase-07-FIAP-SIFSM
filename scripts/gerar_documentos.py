"""Reconstrói relatório, circuito e evidências a partir dos modelos reais.

Uso: python -X utf8 -B scripts/gerar_documentos.py
Só escreve os artefatos nomeados; nunca abre o SQLite local.
"""

import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from analise_integrada import executar_analise_integrada
from banco_dados import abrir_conexao, carregar_csv_inicial, inicializar_banco
from config import CAPACIDADE_BATERIA_KWH, CARGA_INICIAL_KWH, HORAS_POR_CICLO
from monitoramento import gerar_tabela_verdade, gerar_tabela_verdade_bloqueio
from simulacao_computacional import simular_balanco_energetico
from scripts.empacotar import FONTES_ANALISE, normalizar_conteudo

# Dependências editoriais não são carregadas pela aplicação principal.
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

AUTORES = (
    "Alexandre Niewelt — RM 570614", "Danilo Fernandes — RM 570057",
    "Renato Nascimento — RM 570266", "Renato Valle — RM 572352",
)
TITULO = "SISTEMA INTEGRADO DE FUTURO SUSTENTÁVEL EM MARTE"
LARGURA = A4[0] - 5 * cm
AZUL = colors.HexColor("#153B50")
VERDE = colors.HexColor("#087F8C")
CLARO = colors.HexColor("#EEF5F5")


def sha256(caminho):
    caminho = Path(caminho)
    return hashlib.sha256(normalizar_conteudo(caminho.name, caminho.read_bytes())).hexdigest()


def coletar_resultados():
    """Importa exclusivamente o CSV fornecido em banco efêmero e fecha a conexão."""
    conexao = abrir_conexao(":memory:")
    try:
        inicializar_banco(conexao)
        carregar_csv_inicial(conexao, RAIZ / "dados_aurora_siger.csv")
        resultado = executar_analise_integrada(conexao)
    finally:
        conexao.close()
    serie = [
        {k: r[k] for k in ("ciclo", "consumo_kw", "geracao_kw")}
        for r in resultado["simulacao"]["historico"]
    ]
    estresse = simular_balanco_energetico(
        [{**r, "geracao_kw": r["geracao_kw"] * 0.7} for r in serie]
    )
    return {
        "origem": "CSV simulado do projeto; SQLite em memória, sem banco local.",
        "parametros": {"capacidade_kwh": CAPACIDADE_BATERIA_KWH,
                       "carga_inicial_kwh": CARGA_INICIAL_KWH,
                       "horas_por_ciclo": HORAS_POR_CICLO},
        "fontes_sha256": {nome: sha256(RAIZ / nome) for nome in FONTES_ANALISE},
        "normalizacao_hash": "SHA-256 do texto com finais de linha LF.",
        "resultado": resultado, "estresse_geracao_menos_30_pct": estresse,
    }


def br(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def gerar_graficos(dados, destino):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    resultado = dados["resultado"]
    historico = resultado["simulacao"]["historico"]
    x = [r["ciclo"] for r in historico]
    y = [r["consumo_kw"] for r in historico]
    estilo = {"font.family": "DejaVu Sans", "font.size": 10,
              "axes.spines.top": False, "axes.spines.right": False,
              "axes.labelcolor": "#153B50", "axes.edgecolor": "#627780",
              "legend.frameon": False, "savefig.facecolor": "white"}

    def salvar(fig, nome):
        try:
            fig.savefig(destino / nome, dpi=200, bbox_inches="tight",
                        metadata={"Software": "SIFSM", "Author": "Equipe SIFSM"})
        finally:
            plt.close(fig)

    with plt.rc_context(estilo):
        from matplotlib.patches import FancyBboxPatch
        fig, eixo = plt.subplots(figsize=(8.4, 5.3), layout="constrained")
        eixo.set(xlim=(0, 1), ylim=(0, 1))
        eixo.axis("off")
        for i, (titulo, detalhe) in enumerate((
            ("01 / DADOS", "CSV simulado → SQLite | CRUD e importação explícitos"),
            ("02 / VALIDAÇÃO", "Consultas, hash, R1/R2 e FIFO | Cobertura e unidades"),
            ("03 / MODELOS", "Bateria ideal e regressão temporal | Somente leitura"),
            ("04 / REVISÃO", "Recomendações e limitações | Supervisão humana"),
        )):
            y0 = .81 - i * .24
            eixo.add_patch(FancyBboxPatch((.02, y0), .96, .16,
                                          boxstyle="round,pad=0.01", facecolor="#153B50", linewidth=0))
            eixo.text(.05, y0 + .105, titulo, color="#8FE1DF", weight="bold", fontsize=10)
            eixo.text(.05, y0 + .045, detalhe, color="white", fontsize=10)
            if i < 3:
                eixo.annotate("", (.5, y0 - .065), (.5, y0 - .015),
                              arrowprops={"arrowstyle": "->", "color": "#087F8C", "lw": 1.5})
        salvar(fig, "arquitetura.png")

        fig, eixos = plt.subplots(2, 1, figsize=(8.4, 6.7), layout="constrained")
        eixos[0].plot(x, y, color="#A8472D", marker="o", ms=3, label="Consumo")
        eixos[0].plot(x, [r["geracao_kw"] for r in historico], color="#087F8C",
                      marker="s", ms=3, label="Geração")
        eixos[0].set(ylabel="Potência média (kW)", xlabel="Ciclo (1 h por registro)")
        eixos[0].legend(ncols=2, loc="upper right")
        for sim, nome, cor, linha in (
            (resultado["simulacao"], "Base", "#087F8C", "-"),
            (dados["estresse_geracao_menos_30_pct"], "Geração −30%", "#A8472D", "--"),
        ):
            eixos[1].plot([0] + x, [CARGA_INICIAL_KWH] + [
                r["energia_final_kwh"] for r in sim["historico"]
            ], label=nome, color=cor, linestyle=linha, marker="o", ms=3)
        eixos[1].axhline(CAPACIDADE_BATERIA_KWH, color="#627780", linestyle=":",
                        label="Capacidade")
        eixos[1].set(ylabel="Energia da bateria (kWh)",
                     xlabel="Ciclo concluído (0 = estado inicial)", ylim=(-0.5, 21))
        eixos[1].legend(ncols=3, loc="upper right")
        for eixo in eixos:
            eixo.grid(alpha=0.18)
            eixo.set_axisbelow(True)
        salvar(fig, "csv_energia.png")

        reg = resultado["previsao"]
        corte = reg["metricas"]["quantidade_treino"]
        coef = reg["coeficientes"]
        reta = [coef["intercepto_kw"] + coef["inclinacao_kw_por_ciclo"] * c for c in x]
        futuros = [p["ciclo"] for p in reg["previsoes"]]
        previstos = [p["consumo_previsto_kw"] for p in reg["previsoes"]]
        fig, eixos = plt.subplots(2, 1, figsize=(8.4, 6.7), layout="constrained")
        eixo = eixos[0]
        eixo.scatter(x[:corte], y[:corte], color="#087F8C", s=20, label="Treino 1–25")
        eixo.scatter(x[corte:], y[corte:], color="#A8472D", marker="s", s=24,
                     label="Teste 26–32")
        eixo.plot(x + futuros, reta + previstos, color="#153B50", linestyle="--",
                  label="Reta do treino")
        eixo.scatter(futuros, previstos, color="#153B50", marker="x", label="Futuro bruto")
        eixo.axhline(reg["metricas"]["consumo_medio_treino_kw"], color="#777777",
                     linestyle=":", label="Média do treino")
        eixo.axvline(25.5, color="#777777", linewidth=0.8)
        eixo.set(ylabel="Consumo médio (kW)", xlabel="Ciclo")
        eixo.legend(ncols=2, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.32))
        eixos[1].bar(x[corte:], [a - b for a, b in zip(y[corte:], reta[corte:])],
                      color="#A8472D", width=0.55)
        eixos[1].axhline(0, color="#153B50", linewidth=0.8)
        eixos[1].set(ylabel="Resíduo real − previsto (kW)", xlabel="Ciclo de teste",
                     xticks=x[corte:])
        for eixo in eixos:
            eixo.grid(alpha=0.18)
            eixo.set_axisbelow(True)
        salvar(fig, "csv_regressao.png")


def estilos():
    corpo = ParagraphStyle("Corpo", fontName="Times-Roman", fontSize=12, leading=18,
                           alignment=TA_JUSTIFY, firstLineIndent=1.25 * cm,
                           spaceAfter=0, allowWidows=0, allowOrphans=0)
    return {
        "corpo": corpo,
        "titulo": ParagraphStyle("Titulo", parent=corpo, fontName="Times-Bold",
                                  firstLineIndent=0, alignment=TA_LEFT,
                                  spaceBefore=18, spaceAfter=18, keepWithNext=True),
        "subtitulo": ParagraphStyle("Subtitulo", parent=corpo, fontName="Times-Bold",
                                     firstLineIndent=0, alignment=TA_LEFT,
                                     spaceBefore=18, spaceAfter=18, keepWithNext=True),
        "centro": ParagraphStyle("Centro", parent=corpo, alignment=TA_CENTER,
                                  firstLineIndent=0, spaceAfter=18),
        "legenda": ParagraphStyle("Legenda", fontName="Times-Roman", fontSize=10,
                                   leading=12, spaceBefore=6, spaceAfter=6),
        "tabela": ParagraphStyle("Celula", fontName="Times-Roman", fontSize=10,
                                  leading=12),
        "codigo": ParagraphStyle("Codigo", fontName="Courier", fontSize=9,
                                  leading=12, spaceBefore=6, spaceAfter=6),
        "referencia": ParagraphStyle("Referencia", parent=corpo, leading=12,
                                      firstLineIndent=0, alignment=TA_LEFT, spaceAfter=12),
    }


def markup(texto):
    """Subconjunto explícito de Markdown; não interpreta HTML arbitrário."""
    texto = escape(texto)
    texto = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", texto)
    return texto


def tabela(linhas, larguras=None):
    estilo = estilos()["tabela"]
    linhas = [[Paragraph(markup(str(c)), estilo) for c in linha] for linha in linhas]
    t = Table(linhas, colWidths=larguras or [LARGURA / len(linhas[0])] * len(linhas[0]),
              repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


class Diagrama(Flowable):
    """Ilustração vetorial; texto e traços continuam nítidos em qualquer zoom."""

    def __init__(self, tipo):
        Flowable.__init__(self)
        self.tipo = tipo
        self.width = LARGURA
        self.height = 270 if tipo == "arquitetura" else 150

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(CLARO)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        if self.tipo == "arquitetura":
            etapas = [
                ("01 / DADOS", "CSV simulado → SQLite", "CRUD e importação explícitos"),
                ("02 / VALIDAÇÃO", "Consultas + hash + R1/R2 + FIFO", "Cobertura, unidades e status"),
                ("03 / MODELOS", "Bateria ideal + regressão temporal", "Cálculos compartilhados, sem escrita"),
                ("04 / REVISÃO", "Recomendações + limitações", "Supervisão humana; sem atuação física"),
            ]
            for i, (rotulo, titulo, detalhe) in enumerate(etapas):
                y = 218 - i * 60
                c.setFillColor(AZUL)
                c.roundRect(14, y, self.width - 28, 44, 4, fill=1, stroke=0)
                c.setFillColor(colors.HexColor("#8FE1DF"))
                c.setFont("Helvetica-Bold", 8)
                c.drawString(25, y + 29, rotulo)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(115, y + 26, titulo)
                c.setFont("Helvetica", 9)
                c.drawString(115, y + 11, detalhe)
                if i < 3:
                    self.seta(self.width / 2, y - 2, self.width / 2, y - 14)
        else:
            self.porta(self.tipo)
        c.restoreState()

    def seta(self, x1, y1, x2, y2):
        c = self.canv
        c.setStrokeColor(VERDE)
        c.setLineWidth(1.4)
        c.line(x1, y1, x2, y2)
        if x1 == x2:
            c.line(x2 - 3, y2 + 4, x2, y2)
            c.line(x2 + 3, y2 + 4, x2, y2)
        else:
            c.line(x2 - 4, y2 - 3, x2, y2)
            c.line(x2 - 4, y2 + 3, x2, y2)

    def porta(self, tipo):
        c = self.canv
        rotulos = (("C / Consumo alto", "M / Módulo crítico", "ALERTA", "AND")
                   if tipo == "R1" else
                   ("I / Sensor inválido", "M / Em manutenção", "BLOQUEIO", "OR"))
        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(18, 122, f"{tipo} / DECISÃO DIGITAL")
        c.setFont("Helvetica", 9)
        c.drawString(18, 91, rotulos[0])
        c.drawString(18, 44, rotulos[1])
        c.setStrokeColor(VERDE)
        c.setLineWidth(1.6)
        fim_entrada = 190 if tipo == "R1" else 210
        c.line(127, 94, fim_entrada, 94)
        c.line(127, 47, fim_entrada, 47)
        p = c.beginPath()
        if tipo == "R1":
            p.moveTo(190, 32)
            p.lineTo(225, 32)
            p.curveTo(284, 32, 284, 109, 225, 109)
            p.lineTo(190, 109)
            p.close()
        else:
            p.moveTo(183, 32)
            p.curveTo(209, 32, 248, 35, 278, 70)
            p.curveTo(248, 106, 209, 109, 183, 109)
            p.curveTo(207, 76, 207, 65, 183, 32)
            p.close()
        c.setFillColor(AZUL)
        c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(228, 67, rotulos[3])
        # A curva cúbica AND atinge x=269,25 no centro; não deixar fios soltos.
        self.seta(269.25 if tipo == "R1" else 278, 70.5 if tipo == "R1" else 70,
                  325, 70.5 if tipo == "R1" else 70)
        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(332, 67, rotulos[2])
        c.setFont("Helvetica", 8)
        c.drawString(18, 14, "Classificação em software. Não representa acionamento de equipamento.")


class Documento(BaseDocTemplate):
    def __init__(self, destino, titulo):
        super().__init__(str(destino), pagesize=A4, leftMargin=3 * cm,
                         rightMargin=2 * cm, topMargin=3 * cm, bottomMargin=2 * cm,
                         title=titulo, author="; ".join(a.split(" —")[0] for a in AUTORES),
                         invariant=1)
        # Sem padding: dimensões úteis correspondem exatamente às margens declaradas.
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        # onPageEnd enxerga a marca textual da própria página, em coordenadas absolutas.
        self.addPageTemplates(PageTemplate(id="ABNT", frames=frame, onPageEnd=self.pagina))
        self.textual = False
        self.desconto_capa = 1

    def beforeDocument(self):
        self.textual = False  # multiBuild refaz cada passagem com o mesmo estado.

    def pagina(self, c, doc):
        c.setCreator("Equipe SIFSM | edição técnica")
        c.setProducer("SIFSM")
        if self.textual:
            c.saveState()
            c.setFillColor(colors.black)
            c.setFont("Times-Roman", 10)
            c.drawRightString(A4[0] - 2 * cm, A4[1] - 2 * cm, str(doc.page - self.desconto_capa))
            c.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and getattr(flowable, "secao", False):
            texto = flowable.getPlainText()
            # A primeira folha textual é identificada antes de imprimir a paginação.
            nivel = getattr(flowable, "nivel", 0)
            chave = "secao-" + re.sub(r"[^a-z0-9]+", "-", texto.lower())
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(texto, chave, level=nivel, closed=False)
            self.notify("TOCEntry", (nivel, texto, self.page - 1, chave))


class InicioTextual(Flowable):
    """Aciona paginação na própria primeira folha textual, não só na seguinte."""

    width = height = 0

    def draw(self):
        self._doctemplate.textual = True


def linhas_resultados(dados, tipo):
    """Valores esperados para conferir as tabelas da fonte Markdown antes do PDF."""
    resultado = dados["resultado"]
    if tipo == "energia":
        base = resultado["simulacao"]["resumo"]
        estresse = dados["estresse_geracao_menos_30_pct"]["resumo"]
        campos = [("Consumo (kWh)", "consumo_total_kwh"),
                  ("Geração (kWh)", "geracao_total_kwh"),
                  ("Energia inicial (kWh)", "energia_inicial_kwh"),
                  ("Energia final (kWh)", "energia_final_kwh"),
                  ("Déficit (kWh)", "deficit_total_kwh"),
                  ("Excedente (kWh)", "excedente_total_kwh"),
                  ("Atendimento (%)", "atendimento_percentual")]
        return [["Medida", "Base", "Geração −30%"]] + [
            [nome, br(base[campo]), br(estresse[campo])] for nome, campo in campos
        ]
    m = resultado["previsao"]["metricas"]
    return [["Medida", "Valor"]] + [
        ["Consumo mínimo / máximo (kW)", br(m["consumo_minimo_kw"]) + " / " + br(m["consumo_maximo_kw"])],
        ["Média global descritiva (kW)", br(m["consumo_medio_kw"], 7)],
        ["Média do treino / referência (kW)", br(m["consumo_medio_treino_kw"], 3)],
        ["Treino / teste (ciclos)", f'{m["quantidade_treino"]} / {m["quantidade_teste"]}'],
        ["MAE / RMSE no teste (kW)", br(m["mae_kw"], 7) + " / " + br(m["rmse_kw"], 7)],
        ["MAE da referência (kW)", br(m["mae_referencia_kw"], 7)],
        ["R² (adimensional)", br(m["r2"], 7).replace("-", "−")],
    ]


def capa(rosto=False):
    e = estilos()
    itens = []
    if not rosto:
        itens += [Paragraph("FIAP — CIÊNCIA DA COMPUTAÇÃO", e["centro"]),
                  Paragraph("FASE 07", e["centro"]), Spacer(1, 0.5 * cm)]
    itens += [Paragraph(escape(a), e["centro"]) for a in AUTORES]
    itens += [Spacer(1, 1.5 * cm), Paragraph(f"<b>{TITULO}</b>", e["centro"]),
              Paragraph("Aurora Siger", e["centro"])]
    if rosto:
        natureza = ParagraphStyle("Natureza", parent=e["corpo"], leading=12,
                                   firstLineIndent=0, leftIndent=LARGURA / 2,
                                   alignment=TA_JUSTIFY)
        itens += [Spacer(1, 1.4 * cm), Paragraph(
            "Relatório técnico da atividade integradora da Fase 07 do curso de "
            "Ciência da Computação da FIAP. Protótipo acadêmico de organização "
            "de dados e apoio à decisão sustentável em uma colônia simulada.", natureza)]
    itens += [Spacer(1, 3 * cm if rosto else 5 * cm),
              Paragraph("São Paulo", e["centro"]), Paragraph("2026", e["centro"]), PageBreak()]
    return itens


def ler_corpo(texto, dados):
    """Converte o subconjunto de Markdown usado no relatório e confere suas tabelas."""
    e = estilos()
    linhas = texto.splitlines()
    itens = []
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        i += 1
        if not linha:
            continue
        if linha.startswith("### "):
            p = Paragraph(markup(linha[4:]), e["subtitulo"])
            p.secao, p.nivel = True, 1
            itens.append(p)
        elif linha.startswith("## "):
            if itens:
                itens.append(PageBreak())
            p = Paragraph(markup(linha[3:]), e["titulo"])
            p.secao, p.nivel = True, 0
            itens.append(p)
        elif linha.startswith("!["):
            caminho = RAIZ / "docs" / re.fullmatch(r"!\[.*\]\(([^)]+)\)", linha)[1]
            if caminho.name == "arquitetura.png":
                itens.append(Diagrama("arquitetura"))
            else:
                imagem = Image(str(caminho))
                imagem.drawHeight *= LARGURA / imagem.drawWidth
                imagem.drawWidth = LARGURA
                itens.append(imagem)
        elif linha.startswith("|"):
            bloco = [linha]
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                bloco.append(linhas[i].strip())
                i += 1
            conteudo = [[c.strip() for c in r.strip("|").split("|")] for r in bloco
                        if not re.fullmatch(r"[| :\-]+", r)]
            larguras = ([LARGURA * .24, LARGURA * .76] if len(conteudo[0]) == 2
                        else None)
            if conteudo[0][0] == "Medida" and len(conteudo[0]) == 2:
                larguras = [LARGURA * .62, LARGURA * .38]
            if conteudo[0][0] == "Medida":
                tipo = "energia" if len(conteudo[0]) == 3 else "regressao"
                if conteudo != linhas_resultados(dados, tipo):
                    raise ValueError(f"Tabela {tipo} do relatório diverge dos modelos. Atualize a fonte Markdown.")
            itens.append(tabela(conteudo, larguras))
        elif linha.startswith("```"):
            while i < len(linhas) and not linhas[i].startswith("```"):
                # Cada expressão é curta; longas falham na verificação de geometria.
                itens.append(Paragraph(escape(linhas[i]), e["codigo"]))
                i += 1
            i += 1
        else:
            paragrafo = [linha]
            while i < len(linhas) and linhas[i].strip():
                paragrafo.append(linhas[i].strip())
                i += 1
            texto_p = " ".join(paragrafo)
            tipo = "legenda" if re.match(r"^(Fonte:|Figura \d|Tabela \d|Quadro \d)", texto_p) else "corpo"
            if tipo == "legenda" and not texto_p.startswith("Fonte:"):
                estilo = ParagraphStyle("Rotulo", parent=e[tipo], keepWithNext=True)
            else:
                estilo = e[tipo]
            # Referências têm espaçamento simples e alinhamento à esquerda.
            if itens and any(isinstance(p, Paragraph) and p.getPlainText() == "REFERÊNCIAS" for p in itens):
                estilo = e["referencia"]
            itens.append(Paragraph(markup(texto_p), estilo))
    return itens


def gerar_relatorio(dados, destino):
    fonte = (RAIZ / "docs/relatorio_tecnico.md").read_text(encoding="utf-8")
    resumo = fonte.split("## Resumo\n", 1)[1].split("## Abstract\n", 1)[0].strip()
    abstract = fonte.split("## Abstract\n", 1)[1].split("## 1 INTRODUÇÃO\n", 1)[0].strip()
    corpo = "## 1 INTRODUÇÃO\n" + fonte.split("## 1 INTRODUÇÃO\n", 1)[1]
    e = estilos()
    itens = capa() + capa(rosto=True)
    for titulo, conteudo in (("RESUMO", resumo), ("ABSTRACT", abstract)):
        itens.append(Paragraph(titulo, e["centro"]))
        for p in conteudo.split("\n\n"):
            itens.append(Paragraph(markup(p), e["corpo"]))
            itens.append(Spacer(1, 18))
        itens.append(PageBreak())
    itens.append(Paragraph("SUMÁRIO", e["centro"]))
    sumario = TableOfContents()
    sumario.levelStyles = [
        ParagraphStyle("Sumario0", fontName="Times-Roman", fontSize=12, leading=18,
                       spaceBefore=6, rightIndent=24),
        ParagraphStyle("Sumario1", fontName="Times-Roman", fontSize=12, leading=18,
                       leftIndent=12, rightIndent=24),
    ]
    itens += [sumario, PageBreak(), InicioTextual()] + ler_corpo(corpo, dados)
    doc = Documento(destino, TITULO + ": Aurora Siger")
    doc.multiBuild(itens, canvasmaker=partial(Canvas, invariant=1))


def gerar_circuito(destino):
    e = estilos()
    itens = [InicioTextual()]
    for numero, tipo, titulo, texto, gerador, chaves in (
        (1, "R1", "CONSUMO CRÍTICO / AND",
         "C = valor > 2,5 kW; M = módulo crítico. A = C AND M. Pré-condições: "
         "tipo consumo_kw, sensor ativo e módulo ativo. Igualdade ao limite não é consumo alto. "
         "A porta abaixo representa a regra após o filtro de elegibilidade.",
         gerar_tabela_verdade, ("consumo_alto", "modulo_critico", "alerta")),
        (2, "R2", "CLASSIFICAÇÃO DE BLOQUEIO / OR",
         "I = sensor com status invalido; M = módulo com status manutencao. B = I OR M. "
         "O retorno permitido é NOT B, acompanhado dos motivos. Inatividade não é uma "
         "entrada dessa regra; permitido não é autorização geral de segurança.",
         gerar_tabela_verdade_bloqueio, ("sensor_invalido", "modulo_manutencao", "bloqueio")),
    ):
        if numero > 1:
            itens.append(PageBreak())
        itens += [Paragraph(f"{numero} {titulo}", e["titulo"]),
                  Paragraph(texto, e["corpo"]), Spacer(1, 18),
                  Paragraph(f"Figura {numero} – Representação lógica de {tipo}", e["legenda"]),
                  Diagrama(tipo),
                  Paragraph("Fonte: Equipe SIFSM (2026), monitoramento.py.", e["legenda"]),
                  Spacer(1, 12),
                  Paragraph(f"Tabela {numero} – Tabela verdade de {tipo}", e["legenda"]),
                  tabela([["Entrada 1", "Entrada 2", "Saída"]] + [
                      [str(int(r[k])) for k in chaves] for r in gerador()
                  ]),
                  Paragraph("Fonte: funções gerar_tabela_verdade e gerar_tabela_verdade_bloqueio.", e["legenda"]),
                  Spacer(1, 18)]
        if tipo == "R1":
            detalhe = ("R1 retorna alertas de software. Na aplicação, somente REGISTRAR os persiste, "
                       "sem duplicar sensor/ciclo/regra. Exemplo: 3,1 kW em sensor de consumo ativo "
                       "de módulo crítico ativo gera alerta; 2,5 kW não gera. Não há corte de cargas.")
        else:
            detalhe = ("R2 não grava alertas nem opera equipamentos. No menu de monitoramento, "
                       "conta uma ocorrência por sensor observado; a análise conta por leitura. "
                       "Os status são atuais, não históricos. Não há Arduino, Tinkercad ou atuador "
                       "implantado; trata-se de representação digital das regras Python.")
        itens.append(Paragraph(detalhe, e["corpo"]))
    doc = Documento(destino, "SIFSM — Representação dos circuitos lógicos R1 e R2")
    # Documento autônomo: primeira página = 1, diferente da contagem do relatório.
    doc.desconto_capa = 0
    doc.build(itens, canvasmaker=partial(Canvas, invariant=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    dados = coletar_resultados()
    destino = RAIZ / "graficos_ou_imagens"
    destino.mkdir(exist_ok=True)
    gerar_graficos(dados, destino)
    (destino / "resultado_integrado.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8", newline="\n")
    gerar_relatorio(dados, RAIZ / "relatorio_tecnico.pdf")
    gerar_circuito(RAIZ / "circuito_logico.pdf")
    print("Relatório, circuito e evidências do CSV reconstruídos. Banco local não acessado.")


if __name__ == "__main__":
    main()
