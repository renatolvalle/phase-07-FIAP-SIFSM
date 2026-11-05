# Configurações Compartilhadas do Sistema Aurora Siger
from pathlib import Path # Manipular arquivos e diretórios entre plataformas

### IDENTIFICAÇÃO DO SISTEMA
NOME_SISTEMA = "SISTEMA INTEGRADO DE FUTURO SUSTENTÁVEL EM MARTE"
SIGLA_SISTEMA = "SIFSM"
NOME_COLONIA = "AURORA SIGER"

### CAMINHOS DOS ARQUIVOS

# Diretório onde o config.py está localizado
DIRETORIO_BASE = Path(__file__).resolve().parent

# Arquivos utilizados pelo projeto
CAMINHO_BANCO = DIRETORIO_BASE / "aurora_siger.db"
CAMINHO_SQL = DIRETORIO_BASE / "banco_aurora_siger.sql"
CAMINHO_CSV = DIRETORIO_BASE / "dados_aurora_siger.csv"

### PARÂMETROS OPERACIONAIS

# Limite simulado para classificação de consumo elevado
LIMITE_CONSUMO_CRITICO_KW = 2.5

# Duração de cada ciclo simulado, em horas
HORAS_POR_CICLO = 1.0

### PARÂMETROS DA SIMULAÇÃO

# Capacidade total da bateria, em kWh
CAPACIDADE_BATERIA_KWH = 20.0

# Energia armazenada no início da simulação
CARGA_INICIAL_KWH = 12.0

# Número de ciclos previstos pelo modelo linear
HORIZONTE_PREVISAO_CICLOS = 3