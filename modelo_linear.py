""" 
Apoio a Decisões Sustentáveis por Meio de Regressão Linear na Colônia da Aurora Siger
Responsável: Danilo Fernandes
Funcionalidades planejadas:
    - Realizar Análise Exploratória de Dados
    - Treinar Modelo de Regressão Linear
    - Estimar Consumo Energético Futuro
    - Calcular Métricas de Avaliação
    - Interpretar Coeficientes e Previsões
"""

from config import HORIZONTE_PREVISAO_CICLOS

def avaliar_e_prever_consumo(serie_energia, horizonte_ciclos=HORIZONTE_PREVISAO_CICLOS):
    """Treina, avaliar e utiliza regressão linear

    Parâmetros:
        serie_energia: list[dict] de dados energéticos
        horizonte_ciclos: quantidade de ciclos futuros

    Retorno:
        dict contendo:
            coeficientes: dict
            metricas: dict
            previsoes: list[dict]
            limitacoes: list[str]

    Variáveis:
        X: ciclo de operação
        y: consumo_kw

    Avaliação:
        Separação cronológica entre treino e teste
    """
    raise NotImplementedError("Modelo linear ainda não implementado.")