# Conexão e Inicialização do Banco SQLite - Aurora Siger
import sqlite3

from config import CAMINHO_BANCO, CAMINHO_SQL

### ABRINDO CONEXÃO

# Abre e retorna uma conexão com o banco SQLite
def abrir_conexao(caminho_banco=None):

    # Usando o banco oficial, caso outro caminho não seja informado
    caminho = caminho_banco if caminho_banco is not None else CAMINHO_BANCO

    # Abrindo o banco; cria o arquivo se ele não existir
    conexao = sqlite3.connect(str(caminho))

    # Permite acessar os resultados pelo nome das colunas
    conexao.row_factory = sqlite3.Row

    # Ativa a verificação das chaves estrangeiras
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao

### INICIALIZANDO O BANCO DE DADOS

# Executa o arquivo SQL e cria as tabelas necessárias
def inicializar_banco(conexao):

    # Lê as instruções SQL armazenadas no arquivo
    script_sql = CAMINHO_SQL.read_text(encoding="utf-8")

    # Executando as instruções do arquivo SQL
    conexao.executescript(script_sql)

### IMPORTAÇÃO DE DADOS

# Importando os dados simulados sem duplicar registros
def carregar_csv_inicial(conexao, caminho_csv):
    raise NotImplementedError("Importação CSV pendente.")

### CRUD DOS MÓDULOS

# Cadastra módulo e retorna seu ID (int)
def cadastrar_modulo(conexao, dados):
    raise NotImplementedError("Cadastro pendente.")

# Retorna uma lista de dicionários dos módulos
def listar_modulos(conexao):
    raise NotImplementedError("Listagem pendente.")

# Retorna um dicionário ou None, se não encontrado
def buscar_modulo_por_codigo(conexao, codigo):
    raise NotImplementedError("Busca pendente.")

# Retorna True se excluído; False se não existir
def atualizar_modulo(conexao, modulo_id, alteracoes):
    raise NotImplementedError("Atualização pendente.")

# Retorna True se excluído; False se não existir
def excluir_modulo(conexao, modulo_id):
    raise NotImplementedError("Exclusão pendente.")

### SENSORES E LEITURAS

# Cadastra sensor e retorna seu ID (int)
def cadastrar_sensor(conexao, dados):
    raise NotImplementedError("Cadastro de sensor pendente.")

# Retorna uma lsita de dicionários dos sensores
def listar_sensores(conexao):
    raise NotImplementedError("Listagem de sensores pendente.")

# Registra uma leitura e retorna seu ID (int)
def registrar_leitura(conexao, dados):
    raise NotImplementedError("Registro de leitura pendente.")

# Retorna leituras enriquecidas em list[dict] 
# se o ciclo for None, consulta todos os ciclos
def consultar_leituras(conexao, ciclo=None):
    raise NotImplementedError("Consulta de leituras pendente.")

# Retorna consumo e geração agregados por ciclo
def obter_serie_energia(conexao):
    raise NotImplementedError("Série energética pendente.")

### SOLICITAÇÕES E ALERTAS

# Cadastra solicitações e retorna seu ID (int)
def registrar_solicitacao(conexao, dados):
    raise NotImplementedError("Solicitação pendente.")

# Retorna solicitações ordenadas pelo ID
def listar_solicitacoes(conexao, status="pendente"):
    raise NotImplementedError("Listagem de solicitações pendente.")

# Registra alertas e retorna a quantidade de novos
def registrar_alertas(conexao, alertas):
    raise NotImplementedError("Registro de alertas pendentes.")