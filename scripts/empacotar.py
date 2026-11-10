"""Monta ZIP determinístico por lista explícita, sem copiar o ambiente local."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import parse_qs, urlsplit
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS = (
    "README.md", "requirements.txt", "requirements-docs.txt",
    "agents.py", "analise_integrada.py", "banco_dados.py", "codigo_fonte.py",
    "config.py", "demonstracao_energia.py", "estruturas_dados.py",
    "gerar_dados_iniciais.py", "main.py", "modelo_linear.py", "monitoramento.py",
    "simulacao_computacional.py", "banco_aurora_siger.sql", "dados_aurora_siger.csv",
    "relatorio_tecnico.pdf", "circuito_logico.pdf",
    "docs/CONTRATOS.md", "docs/DOC_ANALISE_INTEGRADA.md",
    "docs/DOC_MONITORAMENTO_ESTRUTURAS.md", "docs/DOC_NAVEGACAO.md",
    "docs/DOC_SIMULACAO_REGRESSAO.md", "docs/PLANO_EQUIPE.md",
    "docs/relatorio_tecnico.md", "docs/DIRECAO_VISUAL.md",
    "docs/ENTREGA.md", "docs/ROTEIRO_VIDEO.md", "docs/VALIDACAO_ENTREGA.md",
    "scripts/gerar_documentos.py", "scripts/empacotar.py", "scripts/validar_entrega.py",
    "graficos_ou_imagens/bateria_e_soc.png", "graficos_ou_imagens/demonstracao_energia.json",
    "graficos_ou_imagens/potencias_por_ciclo.png", "graficos_ou_imagens/regressao_consumo.png",
    "graficos_ou_imagens/residuos_teste.png", "graficos_ou_imagens/csv_energia.png",
    "graficos_ou_imagens/csv_regressao.png", "graficos_ou_imagens/resultado_integrado.json",
    "graficos_ou_imagens/arquitetura.png",
    "tests/test_agents.py", "tests/test_analise_integrada.py", "tests/test_banco_dados.py",
    "tests/test_contratos.py", "tests/test_demonstracao_energia.py",
    "tests/test_estruturas_dados.py", "tests/test_gerador_dados.py", "tests/test_interface.py",
    "tests/test_interface_estruturas.py", "tests/test_interface_monitoramento.py",
    "tests/test_interface_pilha_grafo.py", "tests/test_interface_simulacao.py",
    "tests/test_modelo_linear.py", "tests/test_monitoramento.py", "tests/test_navegacao.py",
    "tests/test_simulacao_computacional.py", "tests/test_entrega.py",
)
DATA_ZIP = (2026, 11, 10, 0, 0, 0)
FONTES_ANALISE = (
    "agents.py", "analise_integrada.py", "banco_dados.py", "config.py",
    "estruturas_dados.py", "modelo_linear.py", "monitoramento.py",
    "simulacao_computacional.py", "banco_aurora_siger.sql", "dados_aurora_siger.csv",
)
EXTENSOES_TEXTO = {".py", ".md", ".txt", ".sql", ".csv", ".json"}


def normalizar_conteudo(nome, valor):
    """Canonicaliza finais de linha textuais, sem mudar os arquivos da árvore local."""
    return valor.replace(b"\r\n", b"\n") if Path(nome).suffix in EXTENSOES_TEXTO else valor


def validar_url_video(texto):
    """Valida somente formato/ID; não a duração, existência ou visibilidade no YouTube."""
    url = texto.strip()
    if re.search(r"\s", url):
        raise ValueError("link_video.txt deve conter somente uma URL do YouTube.")
    partes = urlsplit(url)
    if (partes.scheme != "https" or partes.username or partes.password or partes.port
            or partes.fragment):
        raise ValueError("O vídeo deve usar uma URL HTTPS simples do YouTube.")
    if partes.hostname == "youtu.be":
        identificador = partes.path.removeprefix("/")
    elif partes.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com") and partes.path == "/watch":
        valores = parse_qs(partes.query).get("v", [])
        identificador = valores[0] if len(valores) == 1 else ""
    else:
        raise ValueError("Host ou caminho de vídeo não aceito.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", identificador):
        raise ValueError("A URL deve conter um ID de vídeo válido com 11 caracteres.")
    return url


def selecionar_arquivos(raiz=RAIZ, final=False):
    raiz = Path(raiz).resolve()
    nomes = list(ARQUIVOS)
    video = raiz / "link_video.txt"
    if video.is_file():
        validar_url_video(video.read_text(encoding="utf-8"))
        nomes.append("link_video.txt")
    elif final:
        raise ValueError("Entrega final bloqueada: falta link_video.txt com o vídeo publicado.")
    for nome in nomes:
        caminho = raiz / nome
        if not caminho.is_file():
            raise ValueError(f"Arquivo obrigatório ausente: {nome}")
        if caminho.is_symlink() or not caminho.resolve().is_relative_to(raiz):
            raise ValueError(f"Referência externa não permitida no pacote: {nome}")
    return sorted(nomes)


def montar_zip(destino, raiz=RAIZ, final=False):
    raiz = Path(raiz).resolve()
    nomes = selecionar_arquivos(raiz, final)
    destino = Path(destino).resolve()
    if destino in {(raiz / n).resolve() for n in nomes}:
        raise ValueError("O destino não pode substituir um arquivo de entrada.")
    if destino.suffix.lower() != ".zip":
        raise ValueError("O destino precisa ter extensão .zip; não substituir bancos ou outros arquivos locais.")
    conteudos = {nome: normalizar_conteudo(nome, (raiz / nome).read_bytes()) for nome in nomes}
    manifesto = {
        "projeto": "SIFSM — Aurora Siger", "formato_manifesto": 1,
        "normalizacao_textual": "Finais de linha LF; arquivos originais não são modificados.",
        "video_url_incluida": "link_video.txt" in nomes,
        "escopo_validacao_video": "Somente sintaxe da URL; duração, publicação Não listado e acesso exigem conferência humana.",
        "pendencias_humanas": (["Gravar demonstração de até 5 minutos.",
                                "Publicar como Não listado no YouTube e fornecer link_video.txt."]
                               if "link_video.txt" not in nomes else []),
        "arquivos_sha256": {nome: hashlib.sha256(valor).hexdigest() for nome, valor in conteudos.items()},
    }
    conteudos["manifesto_entrega.json"] = (json.dumps(
        manifesto, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".zip", delete=False) as f:
            temporario = Path(f.name)
        with zipfile.ZipFile(temporario, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for nome, valor in sorted(conteudos.items()):
                info = zipfile.ZipInfo(nome, date_time=DATA_ZIP)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, valor, compresslevel=9)
        os.replace(temporario, destino)
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()
    digest = hashlib.sha256(destino.read_bytes()).hexdigest()
    destino.with_suffix(destino.suffix + ".sha256").write_text(
        f"{digest}  {destino.name}\n", encoding="ascii", newline="\n")
    return manifesto


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=RAIZ / "entrega/sifsm-entrega.zip")
    parser.add_argument("--final", action="store_true", help="Exige URL em link_video.txt; não consulta o YouTube.")
    args = parser.parse_args()
    try:
        manifesto = montar_zip(args.saida, final=args.final)
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Não foi possível montar a entrega: {erro}\n")
    print(args.saida)
    print("URL incluída; conferir o vídeo no YouTube." if manifesto["video_url_incluida"]
          else "Pacote técnico montado. Pendentes: gravação e publicação/link do vídeo.")


if __name__ == "__main__":
    main()
