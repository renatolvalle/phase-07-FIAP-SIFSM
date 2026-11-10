"""Orquestração de leitura do SIFSM: banco, regras, estruturas e modelos.

O chamador fornece e mantém a conexão. A análise não grava alertas, não cria
solicitações nem controla equipamentos; decisões continuam sob supervisão humana.
"""

import sqlite3
from math import fsum, isfinite

import banco_dados
from agents import gerar_recomendacoes
from estruturas_dados import (
    buscar_sensor_hash,
    construir_indice_sensores,
    montar_fila_solicitacoes,
)
from modelo_linear import avaliar_e_prever_consumo
from monitoramento import avaliar_bloqueio_operacao, avaliar_consumo_critico
from simulacao_computacional import simular_balanco_energetico


def _validar_cobertura_energetica(leituras, indice_sensores):
    """Impede que ausência de medição ou unidade errada se torne potência zero.

    Cada ciclo energético deve conter consumo e geração, com a mesma cobertura
    dos sensores energéticos observados na base. Sensores sem qualquer leitura
    são sinalizados separadamente, pois não se conhece seu período de operação.
    """
    sensores_por_ciclo = {}
    tipos_observados = set()
    sensores_observados = set()
    for leitura in leituras:
        sensor = buscar_sensor_hash(indice_sensores, leitura["sensor_codigo"])
        if sensor is None or sensor["id"] != leitura["sensor_id"]:
            raise ValueError("Leitura sem sensor correspondente no índice de sensores.")
        if leitura["sensor_tipo"] not in ("consumo_kw", "geracao_kw"):
            continue
        valor = leitura["valor"]
        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not isfinite(valor)
            or valor < 0
        ):
            raise ValueError(
                f"Potência inválida no sensor {sensor['codigo']}, ciclo {leitura['ciclo']}."
            )
        if sensor["unidade"] != "kW":
            raise ValueError(f"O sensor energético {sensor['codigo']} deve usar kW.")
        codigo = sensor["codigo"]
        sensores_observados.add(codigo)
        tipos_observados.add(leitura["sensor_tipo"])
        sensores_por_ciclo.setdefault(leitura["ciclo"], set()).add(codigo)

    if sensores_observados and tipos_observados != {"consumo_kw", "geracao_kw"}:
        raise ValueError("Série incompleta: são necessárias leituras de consumo e geração.")
    for ciclo, sensores in sensores_por_ciclo.items():
        ausentes = sensores_observados - sensores
        if ausentes:
            raise ValueError(
                f"Série incompleta no ciclo {ciclo}: faltam leituras de "
                f"{', '.join(sorted(ausentes))}. Ausência não significa potência zero."
            )
    return sensores_observados


def executar_analise_integrada(conexao):
    """Retorna indicadores, alertas, simulacao, previsao, recomendacoes e limitacoes.

    Recebe conexão aberta por banco_dados.abrir_conexao, com esquema inicializado.
    Consulta a soma histórica por ciclo sem filtrar status atuais. Não faz SQL,
    commit, rollback ou fechamento de conexão. Nenhum dado sintético é inserido.

    Sem energia: simulacao/previsao vazias e médias ausentes. De 1 a 9 ciclos:
    simulação disponível, previsão vazia com justificativa. Dados inconsistentes
    geram ValueError; conexão de outro tipo gera TypeError; erros SQLite propagam.
    """
    if not isinstance(conexao, sqlite3.Connection):
        raise TypeError("Forneça uma conexão SQLite aberta por banco_dados.abrir_conexao.")
    if conexao.row_factory is not sqlite3.Row:
        raise ValueError("A conexão deve usar sqlite3.Row, como banco_dados.abrir_conexao.")

    leituras = banco_dados.consultar_leituras(conexao)
    sensores = banco_dados.listar_sensores(conexao)
    indice = construir_indice_sensores(sensores)
    observados = _validar_cobertura_energetica(leituras, indice)
    serie = banco_dados.obter_serie_energia(conexao)
    fila = montar_fila_solicitacoes(banco_dados.listar_solicitacoes(conexao))

    # R1 produz alertas apenas para consumo em sensores e módulos hoje ativos.
    alertas = avaliar_consumo_critico(leituras)
    bloqueios = []
    for leitura in leituras:
        bloqueio = avaliar_bloqueio_operacao(leitura)
        if not bloqueio["permitido"]:
            bloqueios.append({
                "sensor_codigo": leitura["sensor_codigo"],
                "ciclo": leitura["ciclo"],
                "motivos": bloqueio["motivos"],
            })

    indicadores = {
        "quantidade_leituras": len(leituras),
        "quantidade_modulos": len(banco_dados.listar_modulos(conexao)),
        "quantidade_sensores": len(sensores),
        "quantidade_ciclos": len(serie),
        "quantidade_alertas": len(alertas),
        "quantidade_solicitacoes_pendentes": len(fila),
        "indice_sensores": indice,
        # A deque organiza a fila; a lista mantém o contrato de transporte simples.
        "fila_solicitacoes": list(fila),
        "bloqueios_operacionais": bloqueios,
    }
    limitacoes = [
        "Análise somente de leitura: alertas calculados não são gravados e a fila "
        "contém apenas solicitações pendentes já cadastradas, sem atendimento automático.",
        "A série soma consumo e geração de todos os módulos com leituras energéticas; "
        "não comprova cobertura de toda a colônia nem identifica a origem dos dados. "
        "O CSV fornecido pelo projeto contém dados simulados.",
        "A agregação histórica inclui sensores e módulos hoje inativos ou em manutenção. "
        "R1 e R2 usam os status atuais; não há histórico de status para reconstituir o passado.",
        "A bateria é ideal, sem perdas, degradação, reserva mínima ou limites de potência. "
        "Cada ciclo representa a duração de config.py; lacunas não acrescentam tempo.",
    ]
    sem_leituras = sorted(
        sensor["codigo"] for sensor in sensores
        if sensor["tipo"] in ("consumo_kw", "geracao_kw")
        and sensor["codigo"] not in observados
    )
    if sem_leituras:
        limitacoes.append(
            "Sensores energéticos cadastrados sem leituras (fora da soma): "
            + ", ".join(sem_leituras) + "."
        )
    if bloqueios:
        limitacoes.append(
            "R2 identificou bloqueios nos status atuais; os valores históricos são "
            "apenas diagnósticos e não autorizam operação dos equipamentos."
        )

    simulacao = {}
    previsao = {}
    if serie:
        simulacao = simular_balanco_energetico(serie)
        # São médias dos totais por ciclo, não médias de sensores individuais.
        indicadores["consumo_medio_kw"] = fsum(r["consumo_kw"] / len(serie) for r in serie)
        indicadores["geracao_media_kw"] = fsum(r["geracao_kw"] / len(serie) for r in serie)
        if any(b["ciclo"] - a["ciclo"] > 1 for a, b in zip(serie, serie[1:])):
            limitacoes.append(
                "Há lacunas entre os ciclos: não foram interpoladas medições nem "
                "simulada energia nos intervalos ausentes."
            )
        # Mesma exigência mínima documentada por avaliar_e_prever_consumo.
        if len(serie) >= 10:
            previsao = avaliar_e_prever_consumo(serie)
        else:
            limitacoes.append(
                f"Previsão indisponível: {len(serie)} ciclos; a regressão exige "
                "pelo menos 10 observações para avaliação temporal."
            )
    else:
        limitacoes.append(
            "Sem leituras energéticas: simulação, previsão e médias indisponíveis. "
            "Ausência de registros não indica consumo zero ou normalidade."
        )

    recomendacoes = gerar_recomendacoes(indicadores, alertas, simulacao, previsao)
    # Inclui ressalvas da qualidade do modelo e da ausência de dados, sem duplicatas.
    limitacoes = list(dict.fromkeys(limitacoes + recomendacoes["limitacoes"]))
    return {
        "indicadores": indicadores,
        "alertas": alertas,
        "simulacao": simulacao,
        "previsao": previsao,
        "recomendacoes": recomendacoes,
        "limitacoes": limitacoes,
    }


def simular_consumo_energetico():
    """Demonstração sintética auxiliar, sem consultar o banco ou os menus."""
    from demonstracao_energia import criar_serie_demonstracao

    resultado = simular_balanco_energetico(criar_serie_demonstracao())
    resumo = resultado["resumo"]
    print("DEMONSTRAÇÃO SINTÉTICA | 24 ciclos, bateria ideal; não consulta o banco.")
    print(f"Consumo: {resumo['consumo_total_kwh']:.2f} kWh; "
          f"geração: {resumo['geracao_total_kwh']:.2f} kWh; "
          f"SoC final: {resumo['soc_final_pct']:.2f}%.")
    return resultado


def modelo_linear_previsao():
    """Demonstração sintética auxiliar com a regressão cronológica do projeto."""
    from demonstracao_energia import criar_serie_demonstracao

    resultado = avaliar_e_prever_consumo(criar_serie_demonstracao())
    coeficientes, metricas = resultado["coeficientes"], resultado["metricas"]
    print("DEMONSTRAÇÃO SINTÉTICA | regressão ciclo → consumo, avaliação fora do treino.")
    print(f"Consumo (kW) = {coeficientes['intercepto_kw']:.4f} + "
          f"{coeficientes['inclinacao_kw_por_ciclo']:.4f} × ciclo.")
    print(f"MAE: {metricas['mae_kw']:.4f} kW; RMSE: {metricas['rmse_kw']:.4f} kW; "
          f"R²: {metricas['r2']}; MAE referência: {metricas['mae_referencia_kw']:.4f} kW.")
    for previsao in resultado["previsoes"]:
        print(f"Ciclo {previsao['ciclo']}: {previsao['consumo_previsto_kw']:.4f} kW "
              "(extrapolação).")
    return resultado


def demonstrar_analise_integrada():
    """Importa o CSV oficial em memória, analisa e fecha apenas essa conexão."""
    from contextlib import closing
    from config import CAMINHO_CSV

    with closing(banco_dados.abrir_conexao(":memory:")) as conexao:
        banco_dados.inicializar_banco(conexao)
        banco_dados.carregar_csv_inicial(conexao, CAMINHO_CSV)
        return executar_analise_integrada(conexao)


if __name__ == "__main__":
    import json

    print(json.dumps(demonstrar_analise_integrada(), ensure_ascii=False, indent=2, allow_nan=False))
