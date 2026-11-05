""" 
Organização dos Dados Operacionais da Colônia da Aurora Siger
Responsável: Renato Valle
Funcionalidades planejadas:
    - Fila de Solicitações da Tripulação
    - Tabela Hash para Localizar Sensores
    - Lista de Registros e Alertas
    - Organização de Informações Operacionais
"""

def construir_indice_sensores(sensores):
    """Cria um dicionário indexado pelo código dos sensores.

    Parâmetro:
        sensores: list[dict]

    Retorno:
        dict com codigo como chave e sensor como valor
    """
    raise NotImplementedError("Índice hash pendente.")

def buscar_sensor_hash(indice, codigo):
    """Busca um sensor pelo seu código.

    Retorno:
        dict do senswor encontrado ou None
    """
    raise NotImplementedError("Busca hash pendente.")

def montar_fila_solicitacoes(solicitacoes):
    """Organiza solicitações por ordem de chegada

    Parâmetro:
        solicitacoes: list[dict] com identificadores

    Retorno:
        collections.deque ordenada pelo ID (FIFO).
    """
    raise NotImplementedError("Fila pendente.")