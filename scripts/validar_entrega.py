"""Confere o conteúdo do ZIP antes de extraí-lo; opcionalmente ensaia cópia isolada."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
from posixpath import dirname, join, normpath
import re
import subprocess
import sys
import tempfile
import zipfile

try:
    from .empacotar import ARQUIVOS, FONTES_ANALISE, RAIZ, validar_url_video
except ImportError:
    from empacotar import ARQUIVOS, FONTES_ANALISE, RAIZ, validar_url_video

LIMITE_BYTES = 100 * 1024 * 1024


def conferir_zip(caminho, final=False):
    """Rejeita entradas extras, duplicadas, caminhos perigosos e manifesto divergente."""
    with zipfile.ZipFile(caminho) as z:
        infos = z.infolist()
        nomes = [i.filename for i in infos]
        if len(nomes) > 200 or sum(i.file_size for i in infos) > LIMITE_BYTES:
            raise ValueError("Pacote excede os limites de tamanho/quantidade de arquivos.")
        if len(set(n.casefold() for n in nomes)) != len(nomes):
            raise ValueError("Nomes duplicados no ZIP.")
        esperados = set(ARQUIVOS) | {"manifesto_entrega.json"}
        if "link_video.txt" in nomes:
            esperados.add("link_video.txt")
        if set(nomes) != esperados:
            raise ValueError(f"Conteúdo inesperado ou ausente: {sorted(set(nomes) ^ esperados)}")
        for info in infos:
            if (info.flag_bits & 1 or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("Entradas criptografadas ou links simbólicos não são aceitos.")
        if z.testzip() is not None:
            raise ValueError("CRC inválido no pacote.")
        conteudos = {nome: z.read(nome) for nome in nomes}
    manifesto = json.loads(conteudos["manifesto_entrega.json"])
    if not isinstance(manifesto, dict):
        raise ValueError("O manifesto deve ser um objeto JSON.")
    hashs = {nome: hashlib.sha256(valor).hexdigest() for nome, valor in conteudos.items()
             if nome != "manifesto_entrega.json"}
    if manifesto.get("formato_manifesto") != 1 or manifesto.get("arquivos_sha256") != hashs:
        raise ValueError("Manifesto/SHA-256 divergente do conteúdo efetivo.")
    video = "link_video.txt" in conteudos
    if manifesto.get("video_url_incluida") is not video:
        raise ValueError("Situação do vídeo divergente do conteúdo.")
    if video:
        validar_url_video(conteudos["link_video.txt"].decode("utf-8"))
    elif final:
        raise ValueError("Entrega final incompleta: falta link_video.txt.")
    for nome, valor in conteudos.items():
        if nome.endswith(".py"):
            ast.parse(valor.decode("utf-8-sig"), filename=nome)
    evidencia = json.loads(conteudos["graficos_ou_imagens/resultado_integrado.json"])
    if (not isinstance(evidencia, dict) or not isinstance(evidencia.get("fontes_sha256"), dict)
            or set(evidencia["fontes_sha256"]) != set(FONTES_ANALISE)):
        raise ValueError("Lista de fontes da evidência inválida ou incompleta.")
    for nome, digest in evidencia["fontes_sha256"].items():
        if nome not in hashs or hashs[nome] != digest:
            raise ValueError(f"Evidência desatualizada em relação a {nome}.")
    # Verifica figuras e links relativos do Markdown incluído no pacote.
    for nome, valor in conteudos.items():
        if not nome.endswith(".md"):
            continue
        for alvo in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", valor.decode("utf-8-sig")):
            if re.match(r"^[a-zA-Z]+:", alvo) or alvo.startswith("#"):
                continue
            arquivo = normpath(join(dirname(nome), alvo.split("#", 1)[0]))
            # O ZIP externo não contém a si próprio; os links de download ficam no GitHub.
            if arquivo not in conteudos:
                raise ValueError(f"Link local ausente no pacote: {nome} → {alvo}")
    return manifesto, conteudos


def ensaiar(conteudos, python=sys.executable):
    """Extrai apenas arquivos já conferidos em um novo diretório efêmero."""
    with tempfile.TemporaryDirectory(prefix="sifsm-ensaio-") as tmp:
        pasta = Path(tmp)
        for nome, valor in conteudos.items():
            destino = pasta / nome
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(valor)
        sequencia = "1\n9\nIMPORTAR\n\n0\n7\n\n8\n\n0\n"
        resultado = subprocess.run(
            [str(python), "-X", "utf8", "-B", "codigo_fonte.py"], input=sequencia,
            text=True, encoding="utf-8", cwd=pasta, capture_output=True, timeout=60,
        )
        if resultado.returncode or "92.29" not in resultado.stdout or "5.344" not in resultado.stdout:
            raise ValueError(f"Ensaio CLI não reproduziu os resultados: {resultado.stderr}\n{resultado.stdout[-4000:]}")
        teste = subprocess.run(
            [str(python), "-X", "utf8", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
            text=True, encoding="utf-8", cwd=pasta, capture_output=True, timeout=180,
        )
        if teste.returncode or "skipped=" in teste.stderr:
            raise ValueError(f"Suíte extraída falhou ou pulou testes:\n{teste.stderr[-8000:]}")
        return {"cli": "OK — importação, análise e informações técnicas",
                "testes": teste.stderr.splitlines()[-4:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", nargs="?", type=Path, default=RAIZ / "entrega/sifsm-entrega.zip")
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--executar", action="store_true", help="Executa código do pacote após conferência.")
    args = parser.parse_args()
    try:
        manifesto, conteudos = conferir_zip(args.zip, args.final)
        print(f"Manifesto, sintaxe, fontes das evidências e {len(conteudos)} arquivos: OK.")
        if args.executar:
            print(json.dumps(ensaiar(conteudos), ensure_ascii=False, indent=2))
        if not manifesto["video_url_incluida"]:
            print("Pendências humanas: gravação e publicação/link do vídeo. Não é entrega acadêmica completa.")
    except (ValueError, OSError, KeyError, SyntaxError, zipfile.BadZipFile,
            subprocess.TimeoutExpired) as erro:
        parser.exit(1, f"Validação reprovada: {erro}\n")


if __name__ == "__main__":
    main()
