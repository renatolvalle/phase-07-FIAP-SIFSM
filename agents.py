"""Agentes determinísticos de apoio à decisão, sem execução ou persistência.

O roteamento por palavras-chave simula handoffs, não compreensão de linguagem
natural. Toda sugestão depende de validação humana; nenhum agente controla
equipamentos, grava ordens ou abre conexões com o banco.
"""

from math import isfinite
import re
import unicodedata


MENSAGEM_BLOQUEIO = (
    "Ação bloqueada pelo guardrail: solicitações sobre suporte vital ou sistemas "
    "críticos exigem supervisão humana e autorização manual. Nenhuma ação executada."
)


def _normalizar_texto(texto):
    if not isinstance(texto, str):
        raise ValueError("A solicitação deve ser um texto não vazio.")
    texto = unicodedata.normalize("NFKD", texto.casefold())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = " ".join(re.findall(r"[a-z0-9]+", texto))
    if not texto:
        raise ValueError("A solicitação deve ser um texto não vazio.")
    return texto


def _solicitacao_critica(texto_normalizado):
    # Política conservadora: qualquer menção a estes sistemas requer avaliação
    # humana, inclusive consultas ou negações. Não tenta inferir autorização.
    return bool(re.search(
        r"\b(suporte vital|modulos? criticos?|sistemas? criticos?)\b",
        texto_normalizado,
    ))


class Agente:
    def __init__(self, nome, especialidade):
        self.nome = nome
        self.especialidade = especialidade

    def processar(self, dados):
        raise NotImplementedError("O agente deve implementar seu processamento.")


class AgenteTriador(Agente):
    def __init__(self, agentes_disponiveis):
        super().__init__("Triador", "Roteamento")
        self.agentes = agentes_disponiveis

    def processar(self, dados):
        texto = _normalizar_texto(dados)
        # O bloqueio antecede qualquer handoff, independentemente do especialista.
        if _solicitacao_critica(texto):
            return MENSAGEM_BLOQUEIO
        palavras = set(texto.split())
        if palavras & {"energia", "bateria", "consumo"}:
            return self.agentes["energia"].processar(dados)
        if palavras & {"falha", "manutencao", "reparo"}:
            return self.agentes["manutencao"].processar(dados)
        return "Solicitação fora do escopo. Necessária intervenção humana. Nenhuma ação executada."


class AgenteEnergia(Agente):
    def __init__(self):
        super().__init__("Especialista em Energia", "Gestão de Consumo")

    def processar(self, dados):
        # Protege também quem chama o especialista diretamente, sem o triador.
        if _solicitacao_critica(_normalizar_texto(dados)):
            return MENSAGEM_BLOQUEIO
        return (
            "Recomendação de energia: avaliar o consumo e a possibilidade de reduzir "
            "cargas apenas em módulos não críticos, após validação humana. "
            "Nenhuma ação executada."
        )


class AgenteManutencao(Agente):
    def __init__(self):
        super().__init__("Especialista em Manutenção", "Reparos")

    def processar(self, dados):
        if _solicitacao_critica(_normalizar_texto(dados)):
            return MENSAGEM_BLOQUEIO
        return (
            "Recomendação de manutenção: submeter a inspeção à equipe responsável. "
            "Nenhuma ordem registrada ou inserida em fila; o cadastro depende da "
            "camada de integração e de validação humana."
        )


agentes_colonia = {
    "energia": AgenteEnergia(),
    "manutencao": AgenteManutencao(),
}
sistema_ia = AgenteTriador(agentes_colonia)


def rotear_solicitacao(texto):
    """Retorna orientação textual; entrada vazia ou não textual gera ValueError."""
    return sistema_ia.processar(texto)


def _validar_dicionario(valor, nome):
    if not isinstance(valor, dict):
        raise ValueError(f"{nome} deve ser um dicionário.")
    return valor


def _validar_lista(valor, nome, tipo):
    if not isinstance(valor, list) or any(not isinstance(item, tipo) for item in valor):
        raise ValueError(f"{nome} deve ser uma lista de {tipo.__name__}.")
    return valor


def _numero_opcional(dados, campo, minimo=None, maximo=None, inteiro=False):
    """Ausência significa indisponibilidade, nunca zero ou situação normal."""
    if campo not in dados:
        return None
    valor = dados[campo]
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{campo} deve ser um número finito.")
    try:
        finito = isfinite(valor)
    except OverflowError:
        finito = False
    if not finito or (inteiro and not isinstance(valor, int)):
        raise ValueError(f"{campo} deve ser um número finito" + (" inteiro." if inteiro else "."))
    if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
        raise ValueError(f"{campo} está fora do intervalo permitido.")
    return valor


def gerar_recomendacoes(indicadores, alertas, simulacao, previsao):
    """Gera dict com energia, manutencao, supervisao_humana e limitacoes.

    Recebe dict/list[dict]/dict/dict; campos conhecidos são opcionais, mas valores
    fornecidos devem ser válidos. Contêineres vazios indicam dados indisponíveis.
    Não altera entradas, não deduz segurança da ausência de dados e não executa
    ações. Os campos consumidos estão descritos em docs/CONTRATOS.md.
    """
    _validar_dicionario(indicadores, "indicadores")
    _validar_lista(alertas, "alertas", dict)
    _validar_dicionario(simulacao, "simulacao")
    _validar_dicionario(previsao, "previsao")
    resumo = _validar_dicionario(simulacao.get("resumo", {}), "simulacao.resumo")
    coeficientes = _validar_dicionario(previsao.get("coeficientes", {}), "previsao.coeficientes")
    metricas = _validar_dicionario(previsao.get("metricas", {}), "previsao.metricas")
    previsoes = _validar_lista(previsao.get("previsoes", []), "previsao.previsoes", dict)
    limitacoes_modelo = _validar_lista(previsao.get("limitacoes", []), "previsao.limitacoes", str)

    quantidade = _numero_opcional(indicadores, "quantidade_leituras", minimo=0, inteiro=True)
    consumo_medio = _numero_opcional(indicadores, "consumo_medio_kw", minimo=0)
    ciclos = _numero_opcional(resumo, "quantidade_ciclos", minimo=0, inteiro=True)
    deficit = _numero_opcional(resumo, "deficit_total_kwh", minimo=0)
    excedente = _numero_opcional(resumo, "excedente_total_kwh", minimo=0)
    soc = _numero_opcional(resumo, "soc_final_pct", minimo=0, maximo=100)
    inclinacao = _numero_opcional(coeficientes, "inclinacao_kw_por_ciclo")
    mae = _numero_opcional(metricas, "mae_kw", minimo=0)
    mae_referencia = _numero_opcional(metricas, "mae_referencia_kw", minimo=0)
    if metricas.get("r2") is not None:
        _numero_opcional(metricas, "r2")

    consumos_previstos = []
    for registro in previsoes:
        consumo = _numero_opcional(registro, "consumo_previsto_kw")
        if consumo is None:
            raise ValueError("Cada previsão deve conter consumo_previsto_kw.")
        consumos_previstos.append(consumo)

    energia = []
    manutencao = []
    limitacoes = [
        "Sugestões determinísticas para validação humana, sem execução automática ou persistência.",
        "Suporte vital e sistemas críticos exigem supervisão humana e autorização manual.",
    ]
    if quantidade is None or quantidade == 0:
        limitacoes.append("Leituras indisponíveis ou ausentes: não é possível atestar a situação operacional.")
    if consumo_medio is not None and quantidade != 0:
        energia.append(f"Usar o consumo médio informado de {consumo_medio:g} kW como referência para revisão humana.")
    if alertas:
        manutencao.append(
            f"Revisar {len(alertas)} alerta(s) recebido(s) com a equipe responsável; "
            "avaliar inspeção sem criar ordem ou inserir solicitação em fila automaticamente."
        )
    if ciclos is None or ciclos == 0:
        limitacoes.append("Quantidade de ciclos simulados ausente ou zero: não há balanço energético validado.")
    else:
        if deficit is not None and deficit > 0:
            energia.append(
                f"Déficit simulado de {deficit:g} kWh: avaliar capacidade e priorização "
                "de cargas não críticas, preservando suporte vital e exigindo validação humana."
            )
        if excedente is not None and excedente > 0:
            energia.append(
                f"Excedente não armazenado de {excedente:g} kWh: avaliar aproveitamento "
                "ou armazenamento antes de propor alterações."
            )
        if soc == 0:
            energia.append("Bateria esgotada ao final da simulação (SoC 0%): solicitar avaliação humana da reserva.")
        if deficit is None:
            limitacoes.append("Déficit da simulação não informado; não se pode concluir atendimento integral.")
    if inclinacao is not None and inclinacao > 0:
        energia.append(
            f"Tendência de aumento de {inclinacao:g} kW por ciclo: revisar o planejamento "
            "energético com supervisão humana; associação não implica causalidade."
        )
    if not consumos_previstos:
        limitacoes.append("Previsão indisponível: obter série suficiente antes de estimar consumo futuro.")
    elif any(consumo < 0 for consumo in consumos_previstos):
        limitacoes.append("Previsão negativa, fisicamente inválida: não usar para decisões operacionais.")
    else:
        energia.append(
            f"Pico de consumo previsto de {max(consumos_previstos):g} kW: avaliar capacidade "
            "de atendimento; extrapolação não garante demanda futura."
        )
    if mae is not None and mae_referencia is not None and mae >= mae_referencia:
        limitacoes.append("O modelo não superou a referência pelo MAE; revisar sua utilidade antes de apoiar decisões.")
    if "r2" in metricas and metricas["r2"] is None:
        limitacoes.append("R² indefinido: não interpretar como porcentagem de acertos.")
    limitacoes.extend(f"Modelo linear: {texto}" for texto in limitacoes_modelo)
    return {
        "energia": energia,
        "manutencao": manutencao,
        "supervisao_humana": True,
        "limitacoes": limitacoes,
    }


def demonstrar_agentes():
    """Exibe e retorna exemplos repetíveis, sem persistir solicitações."""
    solicitacoes = (
        "Alerta de bateria baixa no módulo 3",
        "Manutenção no sensor de umidade da estufa",
        "Desligar suporte vital por falha",
        "Status da produção agrícola",
    )
    print("=== Demonstração de agentes: recomendações sem execução ou persistência ===")
    resultados = []
    for solicitacao in solicitacoes:
        resposta = rotear_solicitacao(solicitacao)
        print(f"[{solicitacao}] -> {resposta}")
        resultados.append({"solicitacao": solicitacao, "resposta": resposta})
    return resultados


if __name__ == "__main__":
    demonstrar_agentes()
