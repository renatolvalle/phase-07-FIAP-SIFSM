"""Tendência linear de consumo da colônia Aurora Siger com avaliação temporal.

Responsável: Danilo Fernandes.
Ajuste por mínimos quadrados apenas no treino; MAE, RMSE e R² apenas no teste.
"""

from math import sqrt

from config import HORIZONTE_PREVISAO_CICLOS
from simulacao_computacional import (
    _preparar_serie,
    _somar_finito,
    _validar_inteiro_positivo,
    _validar_numero,
)


def _media(valores):
    return _somar_finito(valores, "Soma para a média") / len(valores)


def _ajustar_reta(treino):
    """Calcula b = Σ((x-x̄)(y-ȳ))/Σ((x-x̄)²) e a = ȳ-bx̄."""
    # Deslocar os ciclos antes de convertê-los evita cancelamento desnecessário.
    origem = treino[0]["ciclo"]
    ciclos = [_validar_numero(r["ciclo"] - origem, "Distância entre ciclos") for r in treino]
    consumos = [r["consumo_kw"] for r in treino]
    media_ciclos = _media(ciclos)
    media_consumos = _media(consumos)
    desvios = [ciclo - media_ciclos for ciclo in ciclos]
    denominador = _somar_finito((d * d for d in desvios), "Variância dos ciclos")
    if denominador == 0:
        raise ValueError("Os ciclos de treino devem ter variação numericamente representável.")
    numerador = _somar_finito(
        (d * (y - media_consumos) for d, y in zip(desvios, consumos)),
        "Covariação de ciclo e consumo",
    )
    inclinacao = _validar_numero(numerador / denominador, "Inclinação")
    intercepto = _validar_numero(
        media_consumos - inclinacao * (_validar_numero(origem, "ciclo inicial") + media_ciclos),
        "Intercepto",
    )
    return intercepto, inclinacao, origem, media_ciclos, media_consumos


def _prever(ciclo, ajuste):
    _, inclinacao, origem, media_ciclos, media_consumos = ajuste
    distancia = _validar_numero(ciclo - origem, "Distância do ciclo previsto")
    return _validar_numero(
        media_consumos + inclinacao * (distancia - media_ciclos), "Consumo previsto",
    )


def avaliar_e_prever_consumo(serie_energia, horizonte_ciclos=HORIZONTE_PREVISAO_CICLOS):
    """Estima consumo_kw em função do ciclo, com pelo menos 10 observações.

    Ordena uma cópia, treina nos primeiros floor(0.8*n) registros e avalia nos
    posteriores. Mantém o ajuste do treino para prever após o último ciclo.
    Retorna coeficientes, metricas, previsoes e limitacoes; dados inválidos
    geram ValueError. A geração é validada como parte da série, mas não é preditora.
    Expõe a média do treino e a contagem de negativas no teste para os agentes
    decidirem se usam a reta ou a referência, sem substituir as previsões brutas.
    """
    horizonte_ciclos = _validar_inteiro_positivo(horizonte_ciclos, "horizonte_ciclos")
    serie = _preparar_serie(serie_energia)
    if len(serie) < 10:
        raise ValueError("A regressão exige pelo menos 10 observações para avaliação temporal.")
    # Descrição da base completa; estes valores não participam do ajuste.
    consumos = [r["consumo_kw"] for r in serie]
    exploracao = {
        "consumo_minimo_kw": min(consumos),
        "consumo_maximo_kw": max(consumos),
        "consumo_medio_kw": _media(consumos),
    }
    # Divisão inteira equivale a floor(0.8*n), sem arredondamento de ponto flutuante.
    corte = len(serie) * 4 // 5
    treino, teste = serie[:corte], serie[corte:]
    ajuste = _ajustar_reta(treino)
    intercepto, inclinacao, _, _, media_treino = ajuste
    reais = [r["consumo_kw"] for r in teste]
    estimados = [_prever(r["ciclo"], ajuste) for r in teste]
    residuos = [real - previsto for real, previsto in zip(reais, estimados)]
    soma_erros_quadrados = _somar_finito((r * r for r in residuos), "Soma dos erros quadrados")
    media_teste = _media(reais)
    soma_total_quadrados = _somar_finito(
        ((real - media_teste) * (real - media_teste) for real in reais),
        "Soma dos desvios quadrados do teste",
    )
    # Teste constante torna R² indefinido, inclusive quando a média tem erro binário.
    teste_constante = all(real == reais[0] for real in reais)
    r2 = None
    if not teste_constante and soma_total_quadrados != 0:
        r2 = _validar_numero(1 - soma_erros_quadrados / soma_total_quadrados, "R²")

    metricas = {
        "quantidade_total": len(serie),
        "quantidade_treino": len(treino),
        "quantidade_teste": len(teste),
        **exploracao,
        # A referência é ajustada só no treino; não substituir pela média global.
        "consumo_medio_treino_kw": media_treino,
        "mae_kw": _media([abs(r) for r in residuos]),
        "rmse_kw": sqrt(soma_erros_quadrados / len(teste)),
        "r2": r2,
        "mae_referencia_kw": _media([abs(real - media_treino) for real in reais]),
        "quantidade_previsoes_negativas_teste": sum(valor < 0 for valor in estimados),
    }
    ultimo_ciclo = serie[-1]["ciclo"]
    previsoes = [
        {"ciclo": ciclo, "consumo_previsto_kw": _prever(ciclo, ajuste), "extrapolacao": True}
        for ciclo in range(ultimo_ciclo + 1, ultimo_ciclo + horizonte_ciclos + 1)
    ]
    limitacoes = [
        "Dados simulados, quando utilizados, não representam medições reais de Marte; "
        "a origem dos dados não é identificada automaticamente pela função.",
        "Uma única separação temporal 80/20 não demonstra estabilidade em outros períodos; "
        "o ajuste do treino é mantido nas previsões futuras.",
        "As previsões futuras são extrapolação temporal e não garantem que a tendência continue.",
        "O intercepto estima o consumo no ciclo zero, sem interpretação física garantida.",
        "Associação entre ciclo e consumo não implica causalidade; ocupação, clima e "
        "manutenção não são variáveis do modelo.",
    ]
    if len(serie) < 30:
        limitacoes.append("Poucas observações (menos de 30): a avaliação é exploratória.")
    if r2 is None:
        limitacoes.append(
            "R² indefinido: consumo constante no teste ou variação não representável numericamente."
        )
    if any(valor < 0 for valor in estimados) or any(r["consumo_previsto_kw"] < 0 for r in previsoes):
        limitacoes.append(
            "Há previsão de consumo negativo, fisicamente inválida; os valores foram "
            "preservados para evidenciar a limitação da reta."
        )
    return {
        "coeficientes": {"intercepto_kw": intercepto, "inclinacao_kw_por_ciclo": inclinacao},
        "metricas": metricas,
        "previsoes": previsoes,
        "limitacoes": limitacoes,
    }
