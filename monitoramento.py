"""
Monitoramento dos Sensores da Colônia da Aurora Siger
Responsável: Renato Valle
Funcionalidades:
    - Identificar Consumo Energético Elevado
    - Aplicar Regras Booleanas (R1 e R2)
    - Gerar Alertas Operacionais
    - Apresentar Tabelas Verdade

Regras implementadas:
    R1: ALERTA   = CONSUMO_ALTO AND MODULO_CRITICO
    R2: BLOQUEIO = SENSOR_INVALIDO OR MODULO_MANUTENCAO

Este módulo não acessa o banco de dados: ele recebe listas e dicionários
(leituras enriquecidas) e devolve listas e dicionários.
"""

from config import LIMITE_CONSUMO_CRITICO_KW

### CONSTANTES DAS REGRAS

# Código gravado no campo regra_codigo da tabela alertas
REGRA_CONSUMO_CRITICO = "R1_CONSUMO_CRITICO"

# Tipo do sensor de consumo (conforme o contrato de leitura enriquecida)
TIPO_SENSOR_CONSUMO = "consumo_kw"

# Expressões booleanas, usadas na documentação e no circuito lógico
EXPRESSAO_R1 = "ALERTA = CONSUMO_ALTO AND MODULO_CRITICO"
EXPRESSAO_R2 = "BLOQUEIO = SENSOR_INVALIDO OR MODULO_MANUTENCAO"

# Campos que cada regra exige na leitura enriquecida
_CAMPOS_R1 = (
    "sensor_id", "sensor_tipo", "sensor_status", "modulo_critico",
    "modulo_status", "ciclo", "instante", "valor",
)
_CAMPOS_R2 = ("sensor_status", "modulo_status")

### FUNÇÕES AUXILIARES

# Lê um campo da leitura; se faltar, sinaliza erro com mensagem clara
def _obter_campo(leitura, campo):
    try:
        return leitura[campo]
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"Leitura inválida: campo '{campo}' ausente.")

# Confere se todos os campos obrigatórios existem na leitura
def _validar_campos(leitura, campos):
    for campo in campos:
        _obter_campo(leitura, campo)

# Confere se um número é válido (bool não é aceito como número)
def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)

### REGRA R1: CONSUMO CRÍTICO

def avaliar_consumo_critico(leituras, limite_kw=LIMITE_CONSUMO_CRITICO_KW):
    """ Avalia a regra booleana de consumo crítico.

    Parâmetros:
        leituras: list[dict] com leituras enriquecidas.
        limite_kw: limite de potência para gerar alerta

    Retorno:
        list[dict] com alertas identificados, no formato aceito por
        registrar_alertas: sensor_id, ciclo, regra_codigo, nivel,
        mensagem, status e criado_em.

    Regra:
        Consumo elevado AND módulo crítico

    Observação:
        Somente sensores e módulos ativos serão avaliados.
        Consumo elevado significa valor MAIOR que limite_kw.
        Leituras de sensores que não sejam de consumo são ignoradas.

    Exceções:
        ValueError: limite inválido, leitura sem campo obrigatório ou
        valor de consumo que não seja número.
    """
    if not _eh_numero(limite_kw) or limite_kw < 0:
        raise ValueError("O limite de consumo deve ser um número maior ou igual a zero.")

    alertas = []

    for leitura in leituras:
        _validar_campos(leitura, _CAMPOS_R1)

        # Somente sensores de consumo entram na regra
        if leitura["sensor_tipo"] != TIPO_SENSOR_CONSUMO:
            continue

        # Somente sensores e módulos ativos são avaliados
        if leitura["sensor_status"] != "ativo" or leitura["modulo_status"] != "ativo":
            continue

        valor = leitura["valor"]
        if not _eh_numero(valor):
            raise ValueError(
                f"Leitura inválida: valor '{valor}' não é numérico "
                f"(sensor_id={leitura['sensor_id']}, ciclo={leitura['ciclo']})."
            )

        consumo_alto = valor > limite_kw
        modulo_critico = bool(leitura["modulo_critico"])

        # Regra R1: consumo elevado AND módulo crítico
        if consumo_alto and modulo_critico:
            alertas.append({
                "sensor_id": leitura["sensor_id"],
                "ciclo": leitura["ciclo"],
                "regra_codigo": REGRA_CONSUMO_CRITICO,
                "nivel": "alto",
                "mensagem": (
                    f"Consumo de {valor} kW acima do limite de {limite_kw} kW "
                    f"em módulo crítico."
                ),
                "status": "aberto",
                "criado_em": leitura["instante"],
            })

    return alertas

def gerar_tabela_verdade():
    """Retorna as quatro combinações da regra AND.

    Retorno:
        list[dict] com consumo_alto, modulo_critico e alerta
    """
    tabela = []

    for consumo_alto in (False, True):
        for modulo_critico in (False, True):
            tabela.append({
                "consumo_alto": consumo_alto,
                "modulo_critico": modulo_critico,
                "alerta": consumo_alto and modulo_critico,
            })

    return tabela

### REGRA R2: BLOQUEIO DE OPERAÇÃO

def avaliar_bloqueio_operacao(leitura):
    """Avalia a regra booleana de bloqueio de operação.

    Parâmetro:
        leitura: dict com sensor_status e modulo_status.

    Retorno:
        dict com:
            permitido: False se a operação deve ser bloqueada
            motivos: list[str] com as causas do bloqueio (vazia se liberada)

    Regra:
        Sensor inválido OR módulo em manutenção

    Observação:
        Não grava alerta: um módulo em manutenção não tem sensor associado.

    Exceções:
        ValueError: leitura sem sensor_status ou modulo_status.
    """
    _validar_campos(leitura, _CAMPOS_R2)

    sensor_invalido = leitura["sensor_status"] == "invalido"
    modulo_manutencao = leitura["modulo_status"] == "manutencao"

    motivos = []
    if sensor_invalido:
        motivos.append("Sensor em estado inválido.")
    if modulo_manutencao:
        motivos.append("Módulo em manutenção.")

    return {
        "permitido": not (sensor_invalido or modulo_manutencao),
        "motivos": motivos,
    }

def gerar_tabela_verdade_bloqueio():
    """Retorna as quatro combinações da regra OR.

    Retorno:
        list[dict] com sensor_invalido, modulo_manutencao e bloqueio
    """
    tabela = []

    for sensor_invalido in (False, True):
        for modulo_manutencao in (False, True):
            tabela.append({
                "sensor_invalido": sensor_invalido,
                "modulo_manutencao": modulo_manutencao,
                "bloqueio": sensor_invalido or modulo_manutencao,
            })

    return tabela
