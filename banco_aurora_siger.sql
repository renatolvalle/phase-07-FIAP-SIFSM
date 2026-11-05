-- Banco: SQLite do Sistema Aurora Siger

-- Habilitando a verificação das chaves estrangeiras nesta conexão
PRAGMA foreign_keys = ON;

------ TABELA DE MÓDULOS
CREATE TABLE IF NOT EXISTS modulos (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    critico INTEGER NOT NULL DEFAULT 0
        CHECK (critico IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'ativo'
        CHECK (status IN ('ativo', 'inativo', 'manutencao'))
);

------ TABELA DE SENSORES
CREATE TABLE IF NOT EXISTS sensores (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    modulo_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    unidade TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ativo'
        CHECK (status IN ('ativo', 'inativo', 'invalido')),

    FOREIGN KEY (modulo_id)
        REFERENCES modulos(id)
        ON DELETE RESTRICT
);

------ TABELA DE LEITURAS
CREATE TABLE IF NOT EXISTS leituras (
    id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    ciclo INTEGER NOT NULL CHECK (ciclo >= 1),
    instante TEXT NOT NULL,
    valor REAL NOT NULL,

    UNIQUE (sensor_id, ciclo),

    FOREIGN KEY (sensor_id)
        REFERENCES sensores(id)
        ON DELETE RESTRICT
);

------ TABELA DE ALERTAS
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    ciclo INTEGER NOT NULL CHECK (ciclo >= 1),
    regra_codigo TEXT NOT NULL,
    nivel TEXT NOT NULL
        CHECK (nivel IN ('baixo', 'medio', 'alto')),
    mensagem TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberto'
        CHECK (status in ('aberto', 'resolvido')),
    criado_em TEXT NOT NULL,

    UNIQUE (sensor_id, ciclo, regra_codigo),

    FOREIGN KEY (sensor_id)
        REFERENCES sensores(id)
        ON DELETE RESTRICT
);

------ TABELA DE SOLICITAÇÕES
CREATE TABLE IF NOT EXISTS solicitacoes (
    id INTEGER PRIMARY KEY,
    modulo_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    prioridade TEXT NOT NULL DEFAULT 'media'
        CHECK (prioridade IN ('baixa', 'media', 'alta')),
    status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'em_atendimento', 'concluida')),
    criado_em TEXT NOT NULL,

    FOREIGN KEY (modulo_id)
        REFERENCES modulos(id)
        ON DELETE RESTRICT
);

------ ÍNDICES PARA CONSULTAS FREQUENTES
CREATE INDEX IF NOT EXISTS idx_sensores_modulo 
    ON sensores(modulo_id);

CREATE INDEX IF NOT EXISTS idx_leituras_ciclo
    ON leituras(ciclo);

CREATE INDEX IF NOT EXISTS idx_alertas_status
    ON alertas(status);

CREATE INDEX IF NOT EXISTS idx_solicitacoes_fila
    ON solicitacoes(status, id);
