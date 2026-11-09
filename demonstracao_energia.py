"""Demonstração reproduzível da simulação e regressão; responsável: Danilo Fernandes.

Execute explicitamente: python -B demonstracao_energia.py
Importar este módulo não carrega Matplotlib nem grava arquivos.
"""

import argparse
import json
from pathlib import Path

from config import CAPACIDADE_BATERIA_KWH, DIRETORIO_BASE, HORAS_POR_CICLO
from modelo_linear import avaliar_e_prever_consumo
from simulacao_computacional import simular_balanco_energetico


def criar_serie_demonstracao():
    """Retorna 24 ciclos sintéticos com tendência e variação determinística."""
    variacoes = [-0.25, 0.10, 0.20, -0.10, 0.05, -0.15, 0.30, -0.05]
    geracoes = [
        7.0, 7.2, 7.4, 7.6, 7.8, 8.0, 8.2, 7.8,
        6.8, 5.5, 4.0, 3.5, 3.0, 2.8, 2.5, 2.8,
        3.5, 4.5, 5.5, 6.5, 7.5, 8.0, 8.2, 7.8,
    ]
    return [
        {
            "ciclo": ciclo,
            "consumo_kw": round(4.5 + 0.12 * ciclo + variacoes[(ciclo - 1) % 8], 2),
            "geracao_kw": geracao,
        }
        for ciclo, geracao in enumerate(geracoes, start=1)
    ]


def _gerar_graficos(serie, simulacao, estresse, regressao, diretorio):
    # Importação tardia: cálculos e testes numéricos não dependem de Matplotlib.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    caminhos = []

    def salvar(figura, nome):
        caminho = diretorio / nome
        figura.savefig(caminho, dpi=160, bbox_inches="tight")
        caminhos.append(caminho)

    ciclos = [r["ciclo"] for r in serie]
    consumo = [r["consumo_kw"] for r in serie]
    geracao = [r["geracao_kw"] for r in serie]
    estilo = {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    with plt.rc_context(estilo):
        figura, eixo = plt.subplots(figsize=(11, 5), layout="constrained")
        try:
            eixo.bar([c - 0.2 for c in ciclos], consumo, width=0.4, color="#b44d27", label="Consumo")
            eixo.bar([c + 0.2 for c in ciclos], geracao, width=0.4, color="#257766", label="Geração")
            eixo.set(title="Aurora Siger | potências médias por ciclo — dados simulados",
                     xlabel=f"Ciclo ({HORAS_POR_CICLO:g} h por ciclo)", ylabel="Potência média (kW)")
            eixo.set_xticks(ciclos[::2])
            eixo.grid(axis="y", alpha=0.2)
            eixo.set_axisbelow(True)
            eixo.legend(ncols=2)
            salvar(figura, "potencias_por_ciclo.png")
        finally:
            plt.close(figura)

        figura, eixos = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout="constrained")
        try:
            estados = [0] + ciclos
            for resultado, nome, cor, marcador in (
                (simulacao, "Base", "#257766", "o"),
                (estresse, "Geração reduzida em 30%", "#b44d27", "s"),
            ):
                energia = [resultado["resumo"]["energia_inicial_kwh"]]
                energia += [r["energia_final_kwh"] for r in resultado["historico"]]
                eixos[0].plot(estados, energia, marker=marcador, markersize=4, color=cor, label=nome)
                eixos[1].plot(estados, [e / CAPACIDADE_BATERIA_KWH * 100 for e in energia],
                              marker=marcador, markersize=4, color=cor, label=nome)
            eixos[0].axhline(CAPACIDADE_BATERIA_KWH, color="#666666", linestyle="--", label="Capacidade")
            eixos[0].set(title="Bateria ideal | estados inicial e finais — dados simulados",
                         ylabel="Energia armazenada (kWh)", ylim=(-0.5, CAPACIDADE_BATERIA_KWH + 1))
            eixos[1].set(xlabel="Ciclo concluído (0 = estado inicial)", ylabel="Estado de carga (%)",
                         ylim=(-2, 105))
            eixos[0].legend(ncols=3)
            for eixo in eixos:
                eixo.grid(alpha=0.2)
            salvar(figura, "bateria_e_soc.png")
        finally:
            plt.close(figura)

        corte = regressao["metricas"]["quantidade_treino"]
        coeficientes = regressao["coeficientes"]
        intercepto = coeficientes["intercepto_kw"]
        inclinacao = coeficientes["inclinacao_kw_por_ciclo"]
        ajustados = [intercepto + inclinacao * ciclo for ciclo in ciclos]
        futuros = [r["ciclo"] for r in regressao["previsoes"]]
        previstos = [r["consumo_previsto_kw"] for r in regressao["previsoes"]]
        figura, eixo = plt.subplots(figsize=(11, 5), layout="constrained")
        try:
            eixo.scatter(ciclos[:corte], consumo[:corte], color="#257766", label=f"Treino ({corte})")
            eixo.scatter(ciclos[corte:], consumo[corte:], color="#b44d27", marker="s",
                         label=f"Teste ({len(serie) - corte})")
            eixo.plot(ciclos[:corte], ajustados[:corte], color="#257766", label="Reta ajustada no treino")
            eixo.plot(ciclos[corte - 1:] + futuros, ajustados[corte - 1:] + previstos,
                      color="#6556a3", linestyle="--", label="Extrapolação do ajuste")
            eixo.scatter(futuros, previstos, marker="x", s=65, color="#6556a3", label="Previsão futura")
            eixo.axvline((ciclos[corte - 1] + ciclos[corte]) / 2, color="#777777", linestyle=":")
            eixo.set(title="Regressão ciclo → consumo | separação cronológica — dados simulados",
                     xlabel="Ciclo", ylabel="Consumo médio (kW)")
            eixo.grid(alpha=0.2)
            eixo.legend(ncols=2)
            salvar(figura, "regressao_consumo.png")
        finally:
            plt.close(figura)

        figura, eixo = plt.subplots(figsize=(9, 4), layout="constrained")
        try:
            residuos = [real - previsto for real, previsto in zip(consumo[corte:], ajustados[corte:])]
            eixo.bar(ciclos[corte:], residuos, color="#b44d27", width=0.6)
            eixo.axhline(0, color="#444444", linewidth=1)
            eixo.set(title="Resíduos somente no teste | real − previsto",
                     xlabel="Ciclo de teste", ylabel="Resíduo (kW)")
            eixo.set_xticks(ciclos[corte:])
            eixo.grid(axis="y", alpha=0.2)
            eixo.set_axisbelow(True)
            salvar(figura, "residuos_teste.png")
        finally:
            plt.close(figura)
    return caminhos


def executar_demonstracao(diretorio_saida=None):
    """Gera quatro gráficos e um JSON; retorna dados e caminhos dos arquivos.

    Usa os parâmetros operacionais de config.py. O cenário de estresse altera
    somente a geração (-30%), mantendo consumo, capacidade e carga inicial.
    Reexecutar substitui apenas os cinco arquivos de mesmo nome no destino.
    """
    diretorio = Path(diretorio_saida) if diretorio_saida is not None else DIRETORIO_BASE / "graficos_ou_imagens"
    serie = criar_serie_demonstracao()
    serie_estresse = [{**r, "geracao_kw": round(r["geracao_kw"] * 0.7, 3)} for r in serie]
    simulacao = simular_balanco_energetico(serie)
    estresse = simular_balanco_energetico(serie_estresse)
    regressao = avaliar_e_prever_consumo(serie)
    diretorio.mkdir(parents=True, exist_ok=True)
    caminhos = _gerar_graficos(serie, simulacao, estresse, regressao, diretorio)
    dados = {
        "origem": "Dados sintéticos didáticos; não são medições reais de Marte.",
        "serie_base": serie,
        "serie_estresse": serie_estresse,
        "simulacao_base": simulacao,
        "simulacao_estresse": estresse,
        "regressao": regressao,
    }
    caminho_dados = diretorio / "demonstracao_energia.json"
    caminho_dados.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {"dados": dados, "arquivos": caminhos + [caminho_dados]}


def main():
    argumentos = argparse.ArgumentParser(description="Simulação e regressão energética com 24 ciclos sintéticos.")
    argumentos.add_argument("--saida", type=Path, help="Diretório dos gráficos e do JSON de resultados.")
    opcoes = argumentos.parse_args()
    try:
        resultado = executar_demonstracao(opcoes.saida)
    except ImportError:
        argumentos.exit(1, "Instale as dependências no ambiente virtual: python -m pip install -r requirements.txt\n")
    except (OSError, ValueError) as erro:
        argumentos.exit(1, f"Não foi possível gerar a demonstração: {erro}\n")
    dados = resultado["dados"]
    print("DADOS SIMULADOS | potência em kW; energia em kWh; E = P × duração em horas.")
    for chave, nome in (("simulacao_base", "Base"), ("simulacao_estresse", "Estresse (-30% geração)")):
        resumo = dados[chave]["resumo"]
        print(f"{nome}: consumo={resumo['consumo_total_kwh']:.2f} kWh; "
              f"geração={resumo['geracao_total_kwh']:.2f} kWh; "
              f"déficit={resumo['deficit_total_kwh']:.2f} kWh; "
              f"excedente={resumo['excedente_total_kwh']:.2f} kWh; "
              f"atendimento={resumo['atendimento_percentual']:.2f}%.")
    regressao = dados["regressao"]
    coeficientes, metricas = regressao["coeficientes"], regressao["metricas"]
    print(f"Reta: consumo_kw = {coeficientes['intercepto_kw']:.6f} "
          f"+ {coeficientes['inclinacao_kw_por_ciclo']:.6f} × ciclo.")
    print(f"Treino/teste: {metricas['quantidade_treino']}/{metricas['quantidade_teste']}; "
          f"MAE={metricas['mae_kw']:.4f} kW; RMSE={metricas['rmse_kw']:.4f} kW; "
          f"R²={metricas['r2']}; MAE da referência={metricas['mae_referencia_kw']:.4f} kW.")
    for previsao in regressao["previsoes"]:
        print(f"Ciclo {previsao['ciclo']}: {previsao['consumo_previsto_kw']:.4f} kW (extrapolação).")
    print("Bateria ideal: sem perdas, reserva, degradação ou limite de potência.")
    for limitacao in regressao["limitacoes"]:
        print(f"- {limitacao}")
    for caminho in resultado["arquivos"]:
        print(caminho)


if __name__ == "__main__":
    main()
