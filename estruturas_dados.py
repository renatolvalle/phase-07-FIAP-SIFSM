"""
Organização dos Dados Operacionais da Colônia da Aurora Siger
Responsável: Renato Valle
Estruturas implementadas:
    - Tabela Hash (dict) para Localizar Sensores
    - Fila (deque) de Solicitações da Tripulação, ordem de chegada (FIFO)
    - Pilha de Histórico de Ações, com desfazer (LIFO)
    - Grafo de Dependência entre Módulos, com análise de impacto

Este módulo não acessa o banco de dados: ele recebe listas e dicionários.
"""

from collections import deque
from datetime import datetime, timezone

### TABELA HASH DE SENSORES

def construir_indice_sensores(sensores):
    """Cria um dicionário indexado pelo código dos sensores.

    Parâmetro:
        sensores: list[dict]

    Retorno:
        dict com codigo como chave e sensor como valor

    Exceções:
        ValueError: sensor sem código ou código repetido.
    """
    indice = {}

    for sensor in sensores:
        try:
            codigo = sensor["codigo"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("Sensor inválido: campo 'codigo' ausente.")

        if codigo in indice:
            raise ValueError(f"Código de sensor repetido: '{codigo}'.")

        indice[codigo] = sensor

    return indice

def buscar_sensor_hash(indice, codigo):
    """Busca um sensor pelo seu código.

    Retorno:
        dict do sensor encontrado ou None
    """
    return indice.get(codigo)

### FILA DE SOLICITAÇÕES

def montar_fila_solicitacoes(solicitacoes):
    """Organiza solicitações por ordem de chegada

    Parâmetro:
        solicitacoes: list[dict] com identificadores

    Retorno:
        collections.deque ordenada pelo ID (FIFO).

    Exceções:
        ValueError: solicitação sem ID.
    """
    for solicitacao in solicitacoes:
        try:
            solicitacao["id"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("Solicitação inválida: campo 'id' ausente.")

    return deque(sorted(solicitacoes, key=lambda solicitacao: solicitacao["id"]))

def atender_proxima_solicitacao(fila):
    """Remove e retorna a solicitação mais antiga da fila, ou None se vazia."""
    if not fila:
        return None

    return fila.popleft()

### PILHA DE HISTÓRICO DE AÇÕES

class PilhaHistorico:
    """Pilha (LIFO) com o histórico de ações do sistema.

    A última ação registrada fica no topo. desfazer() remove e devolve essa
    ação, para que quem chamou possa reverter o seu efeito.
    """

    def __init__(self):
        self._itens = []

    # Registra uma ação no topo da pilha e devolve o registro criado
    def empilhar(self, acao, detalhe="", instante=None):
        if not isinstance(acao, str) or not acao.strip():
            raise ValueError("A ação do histórico deve ser um texto não vazio.")

        if instante is None:
            instante = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        registro = {"acao": acao.strip(), "detalhe": detalhe, "instante": instante}
        self._itens.append(registro)
        return registro

    # Remove e devolve a ação mais recente; None se a pilha estiver vazia
    def desfazer(self):
        if not self._itens:
            return None

        return self._itens.pop()

    # Consulta a ação mais recente sem removê-la; None se estiver vazia
    def topo(self):
        if not self._itens:
            return None

        return self._itens[-1]

    # Lista as ações da mais recente para a mais antiga
    def listar(self):
        return list(reversed(self._itens))

    def esta_vazia(self):
        return not self._itens

    def __len__(self):
        return len(self._itens)

### GRAFO DE DEPENDÊNCIA ENTRE MÓDULOS

class GrafoModulos:
    """Grafo dirigido de dependências entre módulos da colônia.

    A aresta vai do fornecedor para o dependente. Exemplo: se a agricultura
    depende da energia, a aresta é energia -> agricultura. Se a energia
    falhar, a agricultura (e quem depende dela) é afetada.
    """

    def __init__(self):
        self._dependentes = {}

    @staticmethod
    def _validar_codigo(codigo):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError("O código do módulo deve ser um texto não vazio.")

    # Garante que o módulo existe no grafo, mesmo sem dependências
    def adicionar_modulo(self, codigo):
        self._validar_codigo(codigo)
        self._dependentes.setdefault(codigo, [])

    # Registra que 'modulo' depende de 'fornecedor'
    def adicionar_dependencia(self, modulo, fornecedor):
        self._validar_codigo(modulo)
        self._validar_codigo(fornecedor)

        if modulo == fornecedor:
            raise ValueError("Um módulo não pode depender de si mesmo.")

        self.adicionar_modulo(modulo)
        self.adicionar_modulo(fornecedor)

        if modulo not in self._dependentes[fornecedor]:
            self._dependentes[fornecedor].append(modulo)

    # Lista os módulos do grafo
    def modulos(self):
        return list(self._dependentes)

    # Módulos que dependem diretamente de 'codigo'
    def dependentes_diretos(self, codigo):
        return list(self._dependentes.get(codigo, []))

    def modulos_afetados(self, modulo_falho):
        """Lista todos os módulos afetados pela falha de 'modulo_falho'.

        Percorre o grafo em largura (BFS), incluindo dependências indiretas,
        sem repetir módulos e sem incluir o próprio módulo com falha.

        Exceções:
            KeyError: módulo inexistente no grafo.
        """
        if modulo_falho not in self._dependentes:
            raise KeyError(f"Módulo '{modulo_falho}' não existe no grafo.")

        afetados = []
        visitados = {modulo_falho}
        fila = deque([modulo_falho])

        while fila:
            atual = fila.popleft()

            for dependente in self._dependentes[atual]:
                if dependente not in visitados:
                    visitados.add(dependente)
                    afetados.append(dependente)
                    fila.append(dependente)

        return afetados

def construir_grafo_modulos(dependencias):
    """Monta um GrafoModulos a partir de pares (modulo, fornecedor).

    Parâmetro:
        dependencias: list[tuple[str, str]], onde o primeiro módulo depende
        do segundo.
    """
    grafo = GrafoModulos()

    for modulo, fornecedor in dependencias:
        grafo.adicionar_dependencia(modulo, fornecedor)

    return grafo
