# Conexão e Inicialização do Banco SQLite - Aurora Siger
import sqlite3
import math
import csv

from config import CAMINHO_BANCO, CAMINHO_SQL
from datetime import datetime, timezone
from pathlib import Path

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

    # Definindo as colunas obrigatórias do CSV.
    campos_csv = {
        "modulo_codigo",
        "modulo_nome",
        "modulo_tipo",
        "modulo_critico",
        "sensor_codigo",
        "sensor_tipo",
        "sensor_unidade",
        "ciclo",
        "instante",
        "valor"
    }

    novas_leituras = 0

    # Guarda os metadados para detectar contradições no CSV.
    modulos_csv = {}
    sensores_csv = {}

    # Abrindo o CSV sem alterar o banco.
    with Path(caminho_csv).open(
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:

        leitor = csv.DictReader(arquivo)

        # Confirmando que o cabeçalho está correto.
        if (
            leitor.fieldnames is None
            or len(leitor.fieldnames) != len(campos_csv)
            or set(leitor.fieldnames) != campos_csv
        ):
            raise ValueError(
                "O CSV não possui as colunas esperadas."
            )

        # Iniciando uma transação protegida.
        conexao.execute("SAVEPOINT importacao_sifsm")

        try:
            # Percorrendo todas as linhas do arquivo.
            for numero_linha, linha in enumerate(
                leitor, start=2
            ):

                # Verificando linhas com colunas ausentes ou extras.
                if (
                    None in linha
                    or any(
                        linha[campo] is None
                        for campo in campos_csv
                    )
                ):
                    raise ValueError(
                        f"Linha {numero_linha}: colunas inválidas."
                    )

                # Removendo espaços desnecessários.
                dados = {
                    campo: linha[campo].strip()
                    for campo in campos_csv
                }

                # Validando os campos de texto obrigatórios.
                campos_texto = (
                    "modulo_codigo",
                    "modulo_nome",
                    "modulo_tipo",
                    "sensor_codigo",
                    "sensor_tipo",
                    "sensor_unidade",
                    "instante"
                )

                for campo in campos_texto:
                    if not dados[campo]:
                        raise ValueError(
                            f"Linha {numero_linha}: "
                            f"campo '{campo}' vazio."
                        )

                # Validando a criticidade do módulo.
                if dados["modulo_critico"] not in ("0", "1"):
                    raise ValueError(
                        f"Linha {numero_linha}: "
                        "criticidade inválida."
                    )

                critico = int(dados["modulo_critico"])

                # Validando o ciclo.
                try:
                    ciclo = int(dados["ciclo"])
                except ValueError:
                    raise ValueError(
                        f"Linha {numero_linha}: ciclo inválido."
                    ) from None

                if ciclo <= 0 or str(ciclo) != dados["ciclo"]:
                    raise ValueError(
                        f"Linha {numero_linha}: ciclo inválido."
                    )

                # Validando a medição.
                try:
                    valor = float(dados["valor"])
                except ValueError:
                    raise ValueError(
                        f"Linha {numero_linha}: valor inválido."
                    ) from None

                if not math.isfinite(valor):
                    raise ValueError(
                        f"Linha {numero_linha}: "
                        "valor não finito."
                    )

                # Validando o instante ISO 8601 com fuso.
                instante = dados["instante"]

                try:
                    data = datetime.fromisoformat(
                        instante.replace("Z", "+00:00")
                    )
                except ValueError:
                    raise ValueError(
                        f"Linha {numero_linha}: "
                        "instante inválido."
                    ) from None

                if data.tzinfo is None:
                    raise ValueError(
                        f"Linha {numero_linha}: "
                        "instante sem fuso horário."
                    )

                codigo_modulo = dados["modulo_codigo"]
                codigo_sensor = dados["sensor_codigo"]

                # Verificando consistência dentro do CSV.
                info_modulo = (
                    dados["modulo_nome"],
                    dados["modulo_tipo"],
                    critico
                )

                info_sensor = (
                    codigo_modulo,
                    dados["sensor_tipo"],
                    dados["sensor_unidade"]
                )

                if (
                    codigo_modulo in modulos_csv
                    and modulos_csv[codigo_modulo] != info_modulo
                ):
                    raise ValueError(
                        f"Linha {numero_linha}: "
                        "dados contraditórios do módulo."
                    )

                if (
                    codigo_sensor in sensores_csv
                    and sensores_csv[codigo_sensor] != info_sensor
                ):
                    raise ValueError(
                        f"Linha {numero_linha}: "
                        "dados contraditórios do sensor."
                    )

                modulos_csv[codigo_modulo] = info_modulo
                sensores_csv[codigo_sensor] = info_sensor

                # Procurando o módulo pelo código.
                modulo = conexao.execute(
                    """
                    SELECT id
                    FROM modulos
                    WHERE codigo = ?
                    """,
                    (codigo_modulo,)
                ).fetchone()

                if modulo is None:
                    cursor = conexao.execute(
                        """
                        INSERT INTO modulos
                            (codigo, nome, tipo, critico, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            codigo_modulo,
                            dados["modulo_nome"],
                            dados["modulo_tipo"],
                            critico,
                            "ativo"
                        )
                    )

                    modulo_id = cursor.lastrowid
                else:
                    modulo_id = modulo["id"]

                # Procurando o sensor pelo código.
                sensor = conexao.execute(
                    """
                    SELECT id, modulo_id, tipo, unidade
                    FROM sensores
                    WHERE codigo = ?
                    """,
                    (codigo_sensor,)
                ).fetchone()

                if sensor is None:
                    cursor = conexao.execute(
                        """
                        INSERT INTO sensores
                            (codigo, modulo_id, tipo, unidade, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            codigo_sensor,
                            modulo_id,
                            dados["sensor_tipo"],
                            dados["sensor_unidade"],
                            "ativo"
                        )
                    )

                    sensor_id = cursor.lastrowid
                else:
                    # Impede associar um sensor existente
                    # a outro módulo ou outra grandeza.
                    if (
                        sensor["modulo_id"] != modulo_id
                        or sensor["tipo"] != dados["sensor_tipo"]
                        or sensor["unidade"] != dados["sensor_unidade"]
                    ):
                        raise ValueError(
                            f"Linha {numero_linha}: "
                            "sensor incompatível com o banco."
                        )

                    sensor_id = sensor["id"]

                # Verificando se a leitura já existe.
                leitura = conexao.execute(
                    """
                    SELECT valor, instante
                    FROM leituras
                    WHERE sensor_id = ? AND ciclo = ?
                    """,
                    (sensor_id, ciclo)
                ).fetchone()

                if leitura is not None:
                    # Aceitando apenas a repetição exata.
                    if (
                        leitura["valor"] != valor
                        or leitura["instante"] != instante
                    ):
                        raise ValueError(
                            f"Linha {numero_linha}: "
                            "leitura já existente com outros dados."
                        )

                    continue

                # Inserindo uma leitura nova.
                conexao.execute(
                    """
                    INSERT INTO leituras
                        (sensor_id, ciclo, instante, valor)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        sensor_id,
                        ciclo,
                        instante,
                        valor
                    )
                )

                novas_leituras += 1

        except Exception:
            # Desfazendo tudo que foi importado.
            conexao.execute(
                "ROLLBACK TO SAVEPOINT importacao_sifsm"
            )
            conexao.execute(
                "RELEASE SAVEPOINT importacao_sifsm"
            )
            raise

        else:
            # Confirmando a importação bem-sucedida.
            conexao.execute(
                "RELEASE SAVEPOINT importacao_sifsm"
            )

    return novas_leituras


### CRUD DOS MÓDULOS

# Cadastra módulo e retorna seu ID (int)
def cadastrar_modulo(conexao, dados):
    # Verificando se os dados estão em formato de dicionário.
    if not isinstance(dados, dict):
        raise TypeError("Os dados devem ser um dicionário.")
    
    # Verifica os campos obrigatórios
    for campo in ("codigo", "nome", "tipo"):
        valor = dados.get(campo)

        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(
                f"O campo '{campo}' deve conter um texto válido."
            )
        
    # Verifica se a criticidade é booleana
    critico = dados.get("critico", 0)

    if type(critico) not in (int, bool) or critico not in (0, 1):
        raise ValueError("A criticidade deve ser 0 ou 1.")
    
    # Verifica o status operacional
    status = dados.get("status", "ativo")

    if status not in ("ativo", "inativo", "manutencao"):
        raise ValueError("Status do módulo inválido.")
    
    # Executa a operação SQL utilizando parâmetros
    cursor = conexao.execute(
        """
        INSERT INTO modulos
            (codigo, nome, tipo, critico, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            dados["codigo"].strip(),
            dados["nome"].strip(),
            dados["tipo"].strip(),
            int(critico),
            status
        )
    )

    # Confirma a gravação no banco
    conexao.commit()

    # Retorna o identificador do registro criado
    return cursor.lastrowid

# Retorna uma lista de dicionários dos módulos
def listar_modulos(conexao):
    cursor = conexao.execute(
        """
        SELECT
            id,
            codigo,
            nome,
            tipo,
            critico,
            status
        FROM modulos
        ORDER BY id ASC
        """
    )

    registros = cursor.fetchall()

    modulos = [dict(registro) for registro in registros]

    return modulos

# Retorna um dicionário ou None, se não encontrado
def buscar_modulo_por_codigo(conexao, codigo):
    # Verifica se o código informado é válido
    if not isinstance(codigo, str) or not codigo.strip():
        raise ValueError(
            "O código deve ser um texto não vazio."
        )
    
    # Consulta o módulo utilizando um parâmetro SQL
    cursor = conexao.execute(
        """
        SELECT
            id,
            codigo,
            nome,
            tipo,
            critico,
            status
        FROM modulos
        WHERE codigo = ?
        """,
        (codigo.strip(),)
    )

    # Recupera somente o primeiro resultado
    registro = cursor.fetchone()

    # Retorna None quando não encontra o módulo
    if registro is None:
        return None
    
    return dict(registro)

# Retorna True se excluído; False se não existir
def atualizar_modulo(conexao, modulo_id, alteracoes):
    # Validando o identificador do módulo
    if type(modulo_id) is not int or modulo_id <= 0:
        raise ValueError("O ID do módulo deve ser um inteiro positivo.")
    
    # Validando o dicionário de alterações
    if not isinstance(alteracoes, dict) or not alteracoes:
        raise ValueError("Informe um dicionário com as alterações.")
    
    # Definindo os campos que podem ser atualizados
    campos_permitidos = {
        "codigo",
        "nome",
        "tipo",
        "critico",
        "status"
    }

    campos_invalidos = set(alteracoes) - campos_permitidos

    if campos_invalidos:
        raise ValueError(f"Campos não permitidos: {campos_invalidos}")
    
    # Validando e normalizando os valores recebidos
    dados_validados = {}

    for campo, valor in alteracoes.items():
        if campo in ("codigo", "nome", "tipo"):
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"O campo '{campo}' deve conter texto válido.")
            
            dados_validados[campo] = valor.strip()

        elif campo == "critico":
            if type(valor) not in (int, bool) or valor not in (0, 1):
                raise ValueError("A criticidade deve ser 0 ou 1.")
            
            dados_validados[campo] = int(valor)

        elif campo == "status":
            if not isinstance(valor, str) or valor not in ("ativo", "inativo", "manutencao"):
                raise ValueError("Status do módulo inválido.")
            
            dados_validados[campo] = valor

    # Construindo somente as colunas autorizadas
    atribuicoes = ", ".join(
        f"{campo} = ?"
        for campo in dados_validados
    )

    parametros = list(dados_validados.values())
    parametros.append(modulo_id)

    # Executando o UPDATE com parâmetros
    cursor = conexao.execute(
        f"""
        UPDATE modulos
        SET {atribuicoes}
        WHERE id = ?
        """,
        parametros
    )

    # Verificando quantos registros foram encontrados
    registros_afetados = cursor.rowcount

    # Confirmando a transação
    conexao.commit()

    return registros_afetados > 0              

# Retorna True se excluído; False se não existir
def excluir_modulo(conexao, modulo_id):
    
    # Validando o identificador informado
    if type(modulo_id) is not int or modulo_id <= 0:
        raise ValueError(
            "O ID do módulo deve ser um inteiro positivo."
        )
    
    # Executando a exclusão utilizando SQL parametrizado
    cursor = conexao.execute(
        """
        DELETE FROM modulos
        WHERE id = ?
        """,
        (modulo_id,)
    )

    # Verificando se algum registro foi excluído
    registros_afetados = cursor.rowcount

    # Confirmando a operação no banco
    conexao.commit()

    # Informando se a exclusão ocorreu
    return registros_afetados > 0

### SENSORES E LEITURAS

# Cadastra sensor e retorna seu ID (int)
def cadastrar_sensor(conexao, dados):
    
    # Verifica se os dados são um dicionário
    if not isinstance(dados, dict):
        raise TypeError("Os dados do sensor devem ser um dicionário.")
    
    # Validando os campos obrigatórios de texto
    for campo in ("codigo", "tipo", "unidade"):
        valor = dados.get(campo)

        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"O campo '{campo}' deve conter texto válido.")
    
    # Verificando se o ID do módulo é válido
    modulo_id = dados.get("modulo_id")

    if type(modulo_id) is not int or modulo_id <= 0:
        raise ValueError("O ID do módulo deve ser um inteiro positivo.")
    
    # Verificando o status operacional do sensor
    status = dados.get("status", "ativo")

    if status not in ("ativo", "inativo", "invalido"):
        raise ValueError("O status do sensor é inválido.")
    
    # Cadastrando o sensor utilizando SQL parametrizado
    cursor = conexao.execute(
        """
        INSERT INTO sensores
            (codigo, modulo_id, tipo, unidade, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            dados["codigo"].strip(),
            modulo_id,
            dados["tipo"].strip(),
            dados["unidade"].strip(),
            status
        )
    )

    # Confirmando a gravação
    conexao.commit()

    # Retornando o ID criado
    return cursor.lastrowid

# Retorna uma lsita de dicionários dos sensores
def listar_sensores(conexao):
    cursor = conexao.execute(
        """
        SELECT
            id,
            codigo,
            modulo_id,
            tipo,
            unidade,
            status
        FROM sensores
        ORDER BY id ASC
        """
    )

    registros = cursor.fetchall()

    sensores = [dict(registro) for registro in registros]

    return sensores

# Registra uma leitura e retorna seu ID (int)
def registrar_leitura(conexao, dados):
    
    # Validando o formato dos dados recebidos
    if not isinstance(dados, dict):
        raise TypeError("Os dados da leitura devem ser um dicionário.")
    
    # Validando o identificador do sensor
    sensor_id = dados.get("sensor_id")

    if type(sensor_id) is not int or sensor_id <= 0:
        raise ValueError("O ID do sensor deve ser um inteiro positivo.")
    
    # Validando o número do ciclo
    ciclo = dados.get("ciclo")

    if type(ciclo) is not int or ciclo <= 0:
        raise ValueError("O ciclo deve ser um inteiro positivo.")
    
    # Validando a data e hora da medição
    instante = dados.get("instante")

    if not isinstance(instante, str) or not instante.strip():
        raise ValueError("O instante deve conter uma data e hora válidas.")
    
    instante = instante.strip()

    try:
        datetime.fromisoformat(
            instante.replace("Z", "+00:00")
        )
    except ValueError:
        raise ValueError("O instante deve utilizar o formato ISO 8601.") from None 
    
    # Validando o valor numérico medido
    valor = dados.get("valor")

    if type(valor) not in (int, float):
        raise ValueError("O valor da leitura deve ser numérico.")
    
    if not math.isfinite(valor): #math.isfinite para aceitar apenas valores numéricos finitos
        raise ValueError("O valor da leitura deve ser finito.")
    
    # Inserindo a leitura no banco
    cursor = conexao.execute(
        """
        INSERT INTO leituras
            (sensor_id, ciclo, instante, valor)
        VALUES (?, ?, ?, ?)
        """,
        (
            sensor_id,
            ciclo,
            instante,
            float(valor)
        )
    )

    # Confirmando a operação
    conexao.commit()

    return cursor.lastrowid

# Retorna leituras enriquecidas em list[dict] 
# se o ciclo for None, consulta todos os ciclos
def consultar_leituras(conexao, ciclo=None):
    
    # Validando o ciclo, quando informado
    if ciclo is not None:
        if type(ciclo) is not int or ciclo <= 0:
            raise ValueError("O ciclo deve ser um inteiro positivo.")
        
    # Construindo a consulta com os relacionamentos
    consulta = """
        SELECT
            l.id AS leitura_id,
            l.sensor_id,
            s.codigo AS sensor_codigo,
            s.tipo AS sensor_tipo,
            s.status AS sensor_status,
            m.id AS modulo_id,
            m.codigo AS modulo_codigo,
            m.critico AS modulo_critico,
            m.status AS modulo_status,
            l.ciclo,
            l.instante,
            l.valor,
            s.unidade
        FROM leituras AS l
        JOIN sensores AS s
            ON l.sensor_id = s.id
        JOIN modulos AS m
            ON s.modulo_id = m.id
    """

    parametros = ()

    # Adicionando o filtro apenas quando necessário
    if ciclo is not None:
        consulta += " WHERE l.ciclo = ?"
        parametros = (ciclo,)

    # Definindo uma ordem previsível
    consulta += """
        ORDER BY l.ciclo ASC, l.sensor_id ASC, l.id ASC
    """

    # Recuperando os registros
    registros = conexao.execute(
        consulta,
        parametros
    ).fetchall()

    # Transformando os resultados em dicionários
    leituras = []

    for registro in registros:
        leitura = dict(registro)

        # Convertendo o campo de criticidade para booleano
        leitura["modulo_critico"] = bool(
            leitura["modulo_critico"]
        )

        leituras.append(leitura)

    return leituras

# Retorna consumo e geração agregados por ciclo
def obter_serie_energia(conexao):
    cursor = conexao.execute(
        """
        SELECT
            l.ciclo,
            SUM(
                CASE
                    WHEN s.tipo = 'consumo_kw'
                    THEN l.valor
                    ELSE 0
                END
            ) AS consumo_kw,

            SUM(
                CASE
                    WHEN s.tipo = 'geracao_kw'
                    THEN l.valor
                    ELSE 0
                END
            ) AS geracao_kw

        FROM leituras AS l

        JOIN sensores AS s
            ON l.sensor_id = s.id
        
        WHERE s.tipo IN ('consumo_kw', 'geracao_kw')

        GROUP BY l.ciclo
        ORDER BY l.ciclo ASC
        """
    )

    registros = cursor.fetchall()

    serie_energia = []

    for registro in registros:
        serie_energia.append({
            "ciclo": registro["ciclo"],
            "consumo_kw": float(registro["consumo_kw"]),
            "geracao_kw": float(registro["geracao_kw"])
        })

    return serie_energia

### SOLICITAÇÕES E ALERTAS

# Cadastra solicitações e retorna seu ID (int)
def registrar_solicitacao(conexao, dados):

    # Validando o formato dos dados.
    if not isinstance(dados, dict):
        raise TypeError(
            "Os dados devem ser um dicionário."
        )

    # Validando o módulo relacionado.
    modulo_id = dados.get("modulo_id")

    if type(modulo_id) is not int or modulo_id <= 0:
        raise ValueError(
            "O ID do módulo deve ser um inteiro positivo."
        )

    # Validando a descrição.
    descricao = dados.get("descricao")

    if (
        not isinstance(descricao, str)
        or not descricao.strip()
    ):
        raise ValueError(
            "A descrição deve conter texto válido."
        )

    descricao = descricao.strip()

    # Validando a prioridade.
    prioridade = dados.get("prioridade")

    if prioridade not in ("baixa", "media", "alta"):
        raise ValueError(
            "A prioridade deve ser baixa, media ou alta."
        )

    # Validando o status.
    status = dados.get("status", "pendente")

    if status not in (
        "pendente",
        "em_atendimento",
        "concluida"
    ):
        raise ValueError(
            "O status da solicitação é inválido."
        )

    # Definindo a data de criação.
    criado_em = dados.get("criado_em")

    if criado_em is None:
        criado_em = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
    else:
        if (
            not isinstance(criado_em, str)
            or not criado_em.strip()
        ):
            raise ValueError(
                "A data de criação é inválida."
            )

        criado_em = criado_em.strip()

        try:
            data = datetime.fromisoformat(
                criado_em.replace("Z", "+00:00")
            )
        except ValueError:
            raise ValueError(
                "A data deve utilizar o formato ISO 8601."
            ) from None

        if data.tzinfo is None:
            raise ValueError(
                "A data deve informar o fuso horário."
            )

    # Inserindo a solicitação no banco.
    cursor = conexao.execute(
        """
        INSERT INTO solicitacoes
            (
                modulo_id,
                descricao,
                prioridade,
                status,
                criado_em
            )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            modulo_id,
            descricao,
            prioridade,
            status,
            criado_em
        )
    )

    # Confirmando a gravação.
    conexao.commit()

    return cursor.lastrowid

# Retornando solicitações ordenadas pelo ID

def listar_solicitacoes(conexao, status="pendente"):
    status_permitidos = {
        "pendente",
        "em_atendimento",
        "concluida"
    }

    # Validando o filtro informado.
    if status is not None and status not in status_permitidos:
        raise ValueError(
            "Filtro de status inválido."
        )

    # Montando a consulta.
    consulta = """
        SELECT
            id,
            modulo_id,
            descricao,
            prioridade,
            status,
            criado_em
        FROM solicitacoes
    """

    parametros = ()

    # Aplicando o filtro quando necessário.
    if status is not None:
        consulta += " WHERE status = ?"
        parametros = (status,)

    # Preservando a ordem dos registros.
    consulta += " ORDER BY id ASC"

    registros = conexao.execute(
        consulta,
        parametros
    ).fetchall()

    # Retornando uma lista de dicionários.
    return [dict(registro) for registro in registros]

# Registrando alertas e retorna a quantidade de novos

def registrar_alertas(conexao, alertas):

    # Validando a coleção recebida.
    if not isinstance(alertas, list):
        raise TypeError(
            "Os alertas devem ser enviados em uma lista."
        )

    if not alertas:
        return 0

    novos_alertas = 0

    # Protegendo toda a operação com um savepoint.
    conexao.execute("SAVEPOINT registro_alertas_sifsm")

    try:
        for indice, alerta in enumerate(alertas, start=1):

            # Validando o formato de cada alerta.
            if not isinstance(alerta, dict):
                raise TypeError(
                    f"Alerta {indice}: esperado um dicionário."
                )

            sensor_id = alerta.get("sensor_id")
            ciclo = alerta.get("ciclo")
            regra_codigo = alerta.get("regra_codigo")
            nivel = alerta.get("nivel")
            mensagem = alerta.get("mensagem")

            if type(sensor_id) is not int or sensor_id <= 0:
                raise ValueError(
                    f"Alerta {indice}: sensor_id inválido."
                )

            if type(ciclo) is not int or ciclo <= 0:
                raise ValueError(
                    f"Alerta {indice}: ciclo inválido."
                )

            if (
                not isinstance(regra_codigo, str)
                or not regra_codigo.strip()
            ):
                raise ValueError(
                    f"Alerta {indice}: regra inválida."
                )

            regra_codigo = regra_codigo.strip()

            if nivel not in ("baixo", "medio", "alto"):
                raise ValueError(
                    f"Alerta {indice}: nível inválido."
                )

            if (
                not isinstance(mensagem, str)
                or not mensagem.strip()
            ):
                raise ValueError(
                    f"Alerta {indice}: mensagem inválida."
                )

            mensagem = mensagem.strip()

            # Verificando se o alerta já está cadastrado.
            existente = conexao.execute(
                """
                SELECT nivel, mensagem
                FROM alertas
                WHERE sensor_id = ?
                  AND ciclo = ?
                  AND regra_codigo = ?
                """,
                (sensor_id, ciclo, regra_codigo)
            ).fetchone()

            if existente is not None:
                if (
                    existente["nivel"] != nivel
                    or existente["mensagem"] != mensagem
                ):
                    raise ValueError(
                        f"Alerta {indice}: registro conflitante."
                    )

                # Alerta idêntico: não duplica.
                continue

            # Registrando a data de criação em UTC.
            criado_em = (
                datetime.now(timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z")
            )

            # Inserindo o novo alerta.
            conexao.execute(
                """
                INSERT INTO alertas
                    (
                        sensor_id,
                        ciclo,
                        regra_codigo,
                        nivel,
                        mensagem,
                        status,
                        criado_em
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sensor_id,
                    ciclo,
                    regra_codigo,
                    nivel,
                    mensagem,
                    "aberto",
                    criado_em
                )
            )

            novos_alertas += 1

    except Exception:
        # Desfazendo todos os alertas inseridos neste lote.
        conexao.execute(
            "ROLLBACK TO SAVEPOINT registro_alertas_sifsm"
        )
        conexao.execute(
            "RELEASE SAVEPOINT registro_alertas_sifsm"
        )
        raise

    else:
        # Finalizando o lote sem alterar uma transação externa.
        conexao.execute(
            "RELEASE SAVEPOINT registro_alertas_sifsm"
        )

    return novos_alertas