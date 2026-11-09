"""Balanço energético com bateria ideal da colônia Aurora Siger.

Responsável: Danilo Fernandes.
Potências médias em kW são integradas por retângulos: energia = potência × horas.
"""

from math import fsum, isfinite
from numbers import Integral, Real

from config import CAPACIDADE_BATERIA_KWH, CARGA_INICIAL_KWH, HORAS_POR_CICLO


def _validar_numero(valor, nome):
    """Converte um número real finito para float; booleanos não são medidas."""
    if isinstance(valor, bool) or not isinstance(valor, Real):
        raise ValueError(f"{nome} deve ser um número real finito, sem booleanos.")
    try:
        numero = float(valor)
    except OverflowError as erro:
        raise ValueError(f"{nome} deve ser representável como número finito.") from erro
    if not isfinite(numero):
        raise ValueError(f"{nome} deve ser um número finito.")
    return numero


def _validar_inteiro_positivo(valor, nome):
    if isinstance(valor, bool) or not isinstance(valor, Integral) or valor <= 0:
        raise ValueError(f"{nome} deve ser um inteiro positivo, sem booleanos.")
    return int(valor)


def _preparar_serie(serie_energia):
    """Validação comum dos módulos analíticos; copia e ordena sem preencher lacunas."""
    if isinstance(serie_energia, (str, bytes, dict)):
        raise ValueError("serie_energia deve ser um iterável de dicionários.")
    try:
        registros = iter(serie_energia)
    except TypeError as erro:
        raise ValueError("serie_energia deve ser um iterável de dicionários.") from erro
    serie = []
    ciclos = set()
    for posicao, registro in enumerate(registros, start=1):
        if not isinstance(registro, dict):
            raise ValueError(f"Registro {posicao} deve ser um dicionário.")
        for campo in ("ciclo", "consumo_kw", "geracao_kw"):
            if campo not in registro:
                raise ValueError(f"Registro {posicao}: campo obrigatório ausente: {campo}.")
        ciclo = _validar_inteiro_positivo(registro["ciclo"], "ciclo")
        if ciclo in ciclos:
            raise ValueError(f"ciclo {ciclo} duplicado na série energética.")
        ciclos.add(ciclo)
        linha = {"ciclo": ciclo}
        for campo in ("consumo_kw", "geracao_kw"):
            valor = _validar_numero(registro[campo], f"{campo} do ciclo {ciclo}")
            if valor < 0:
                raise ValueError(f"{campo} do ciclo {ciclo} não pode ser negativo.")
            linha[campo] = valor
        serie.append(linha)
    return sorted(serie, key=lambda linha: linha["ciclo"])


def _somar_finito(valores, nome):
    try:
        total = fsum(valores)
    except OverflowError as erro:
        raise ValueError(f"{nome} excede o intervalo numérico finito.") from erro
    return _validar_numero(total, nome)


def simular_balanco_energetico(
    serie_energia,
    capacidade_kwh=CAPACIDADE_BATERIA_KWH,
    carga_inicial_kwh=CARGA_INICIAL_KWH,
    horas_por_ciclo=HORAS_POR_CICLO,
):
    """Retorna histórico por ciclo e resumo da bateria ideal, em kWh e SoC (%).

    Cada registro contém ciclo inteiro positivo e potências médias não negativas
    em consumo_kw/geracao_kw. Lacunas nos identificadores não adicionam tempo.
    Série vazia preserva a carga inicial. Dados inválidos geram ValueError.
    A entrada não é modificada. Não há perdas, reserva ou limite de potência.
    """
    capacidade_kwh = _validar_numero(capacidade_kwh, "capacidade_kwh")
    carga_inicial_kwh = _validar_numero(carga_inicial_kwh, "carga_inicial_kwh")
    horas_por_ciclo = _validar_numero(horas_por_ciclo, "horas_por_ciclo")
    if capacidade_kwh <= 0:
        raise ValueError("capacidade_kwh deve ser maior que zero.")
    if not 0 <= carga_inicial_kwh <= capacidade_kwh:
        raise ValueError("carga_inicial_kwh deve estar entre zero e capacidade_kwh.")
    if horas_por_ciclo <= 0:
        raise ValueError("horas_por_ciclo deve ser maior que zero.")
    serie = _preparar_serie(serie_energia)
    energia = carga_inicial_kwh
    soc_minimo = energia / capacidade_kwh * 100
    historico = []

    for registro in serie:
        consumo = _validar_numero(registro["consumo_kw"] * horas_por_ciclo, "consumo_kwh")
        geracao = _validar_numero(registro["geracao_kw"] * horas_por_ciclo, "geracao_kwh")
        inicial = energia
        carga = descarga = deficit = excedente = 0.0
        if geracao >= consumo:
            saldo = geracao - consumo
            espaco = capacidade_kwh - inicial
            carga = min(saldo, espaco)
            excedente = saldo - carga
            energia = capacidade_kwh if saldo >= espaco else inicial + carga
        else:
            demanda = consumo - geracao
            descarga = min(demanda, inicial)
            deficit = demanda - descarga
            energia = inicial - descarga
        soc_final = energia / capacidade_kwh * 100
        soc_minimo = min(soc_minimo, soc_final)
        historico.append({
            **registro,
            "consumo_kwh": consumo,
            "geracao_kwh": geracao,
            "energia_inicial_kwh": inicial,
            "energia_final_kwh": energia,
            "soc_inicial_pct": inicial / capacidade_kwh * 100,
            "soc_final_pct": soc_final,
            "carga_recebida_kwh": carga,
            "descarga_fornecida_kwh": descarga,
            "deficit_nao_atendido_kwh": deficit,
            "excedente_nao_armazenado_kwh": excedente,
        })

    resumo = {
        "quantidade_ciclos": len(historico),
        "pico_consumo_kw": max((r["consumo_kw"] for r in serie), default=0.0),
        "pico_geracao_kw": max((r["geracao_kw"] for r in serie), default=0.0),
        "energia_inicial_kwh": carga_inicial_kwh,
        "energia_final_kwh": energia,
        "soc_minimo_pct": soc_minimo,
        "soc_final_pct": energia / capacidade_kwh * 100,
    }
    campos_totais = {
        "consumo_total_kwh": "consumo_kwh",
        "geracao_total_kwh": "geracao_kwh",
        "carga_recebida_total_kwh": "carga_recebida_kwh",
        "descarga_fornecida_total_kwh": "descarga_fornecida_kwh",
        "deficit_total_kwh": "deficit_nao_atendido_kwh",
        "excedente_total_kwh": "excedente_nao_armazenado_kwh",
    }
    for total, campo in campos_totais.items():
        resumo[total] = _somar_finito((r[campo] for r in historico), total)
    consumo_total = resumo["consumo_total_kwh"]
    # Sem demanda, adota-se 100% de atendimento por convenção, inclusive na série vazia.
    resumo["atendimento_percentual"] = (
        (1 - resumo["deficit_total_kwh"] / consumo_total) * 100
        if consumo_total else 100.0
    )
    return {"historico": historico, "resumo": resumo}
