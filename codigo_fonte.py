# Sistema Integrado de Futuro Sustentável em Marte (SIFSM)
import os
import sqlite3
import csv
import sys
from math import isfinite

from config import(
    NOME_SISTEMA,
    SIGLA_SISTEMA,
    NOME_COLONIA,
    CAMINHO_CSV,
    CAPACIDADE_BATERIA_KWH,
    CARGA_INICIAL_KWH,
    HORAS_POR_CICLO,
    LIMITE_CONSUMO_CRITICO_KW,
    HORIZONTE_PREVISAO_CICLOS
) 

from banco_dados import (
    abrir_conexao,
    inicializar_banco,
    listar_modulos,
    cadastrar_modulo,
    buscar_modulo_por_codigo,
    atualizar_modulo,
    excluir_modulo,
    listar_sensores,
    consultar_leituras,
    obter_serie_energia,
    carregar_csv_inicial,
    registrar_alertas,
    registrar_solicitacao,
    listar_solicitacoes
)

from monitoramento import (
    avaliar_consumo_critico,
    avaliar_bloqueio_operacao,
    gerar_tabela_verdade,
    gerar_tabela_verdade_bloqueio
)

from estruturas_dados import (
    construir_indice_sensores,
    buscar_sensor_hash,
    montar_fila_solicitacoes,
    atender_proxima_solicitacao,
    PilhaHistorico,
    GrafoModulos
)

from simulacao_computacional import simular_balanco_energetico
from analise_integrada import executar_analise_integrada
from agents import demonstrar_agentes, rotear_solicitacao

# Função de limpar o terminal
def limpar_tela():
    # Preserva saídas redirecionadas e não chama comandos de terminal nos testes.
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")

# Exibindo o cabeçalho principal do sistema
def exibir_cabecalho():
    print("=" * 60)
    print(f"----| {NOME_SISTEMA} |----")
    print(f"--------------| {SIGLA_SISTEMA} - COLÔNIA {NOME_COLONIA} |--------------")
    print("=" * 60)

# Função para pressionar "ENTER" antes de voltar ao menu
def pausar():
    input("\nPressione 'ENTER' para continuar.")

# Consulta e apresenta os módulos cadastrados
def exibir_listagem_modulos(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== MÓDULOS DA COLÔNIA ===\n")

    try:
        modulos = listar_modulos(conexao)

    except sqlite3.Error as erro:
        print("Erro ao consultar os módulos.")
        print(f"Detalhes: {erro}")

    else:
        if not modulos:
            print("Nenhum módulo cadastrado.")

        else:
            for modulo in modulos:
                print(f"ID: {modulo['id']}")
                print(f"Código: {modulo['codigo']}")
                print(f"Nome: {modulo['nome']}")
                print(f"Tipo: {modulo['tipo']}")

                critico = (
                    "Sim" if modulo["critico"] else "Não"
                )

                print(f"Crítico: {critico}")
                print(f"Status: {modulo['status']}")
                print("-" * 40)

    pausar()

# Solicita os dados e cadastra um módulo na colônia
def exibir_cadastro_modulo(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== CADASTRAR MÓDULO ===\n")

    try:
        # Solicitando os campos de texto.
        codigo = input("Código do módulo: ").strip()
        nome = input("Nome do módulo: ").strip()
        tipo = input("Tipo do módulo: ").strip()

        # Solicitando a criticidade.
        critico_texto = input(
            "Módulo crítico? (1 = Sim, 0 = Não): "
        ).strip()

        if critico_texto not in ("0", "1"):
            raise ValueError(
                "A criticidade deve ser 0 ou 1."
            )

        # Solicitando o status operacional.
        status = input(
            "Status (ativo/inativo/manutencao) "
            "[Enter = ativo]: "
        ).strip().lower()

        if not status:
            status = "ativo"

        # Organizando os dados em um dicionário.
        dados = {
            "codigo": codigo,
            "nome": nome,
            "tipo": tipo,
            "critico": int(critico_texto),
            "status": status
        }

        # Chamando a função de persistência.
        modulo_id = cadastrar_modulo(
            conexao,
            dados
        )

    except (ValueError, TypeError) as erro:
        print(f"\nDados inválidos: {erro}")

    except sqlite3.IntegrityError as erro:
        print("\nNão foi possível cadastrar o módulo.")
        print("Verifique se o código já está cadastrado.")
        print(f"Detalhes: {erro}")

    except sqlite3.Error as erro:
        print("\nErro ao acessar o banco de dados.")
        print(f"Detalhes: {erro}")

    else:
        print("\nMódulo cadastrado com sucesso!")
        print(f"ID gerado: {modulo_id}")
        print(f"Código: {codigo}")

    finally:
        pausar()

# Busca e apresenta um móduo pelo seu código
def exibir_busca_modulo(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== BUSCAR MÓDULO ===\n")

    try:
        # Solicitando o código ao usuário.
        codigo = input(
            "Digite o código do módulo: "
        ).strip()

        # Consultando o banco.
        modulo = buscar_modulo_por_codigo(
            conexao,
            codigo
        )

    except ValueError as erro:
        print(f"\nCódigo inválido: {erro}")

    except sqlite3.Error as erro:
        print("\nErro ao consultar o banco de dados.")
        print(f"Detalhes: {erro}")

    else:
        # Verificando se o módulo foi encontrado.
        if modulo is None:
            print("\nNenhum módulo encontrado.")

        else:
            print("\nMódulo encontrado:\n")

            print(f"ID: {modulo['id']}")
            print(f"Código: {modulo['codigo']}")
            print(f"Nome: {modulo['nome']}")
            print(f"Tipo: {modulo['tipo']}")

            critico = (
                "Sim" if modulo["critico"] else "Não"
            )

            print(f"Crítico: {critico}")
            print(f"Status: {modulo['status']}")

    finally:
        pausar()

# Solicita e valida um identificador de módulo
def solicitar_id_modulo():

    texto = input("Digite o ID do módulo: ").strip()

    try:
        modulo_id = int(texto)
    except ValueError:
        raise ValueError(
            "O ID deve ser um número inteiro positivo."
        ) from None

    if modulo_id <= 0:
        raise ValueError(
            "O ID deve ser um número inteiro positivo."
        )

    return modulo_id

# Atualiza os campos escolhidos pelo usuário
def exibir_atualizacao_modulo(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== ATUALIZAR MÓDULO ===\n")

    try:
        # Solicitando o identificador.
        modulo_id = solicitar_id_modulo()

        # Localizando o módulo na listagem.
        modulos = listar_modulos(conexao)

        modulo = next(
            (
                item for item in modulos
                if item["id"] == modulo_id
            ),
            None
        )

        if modulo is None:
            print("\nMódulo não encontrado.")
            return

        # Apresentando os dados atuais.
        print("\nDados atuais do módulo:")
        print(f"Código: {modulo['codigo']}")
        print(f"Nome: {modulo['nome']}")
        print(f"Tipo: {modulo['tipo']}")
        print(f"Crítico: {modulo['critico']}")
        print(f"Status: {modulo['status']}")

        print(
            "\nPressione Enter para manter "
            "o valor atual de um campo.\n"
        )

        # Solicitando possíveis alterações.
        novo_codigo = input("Novo código: ").strip()
        novo_nome = input("Novo nome: ").strip()
        novo_tipo = input("Novo tipo: ").strip()

        novo_critico = input(
            "Crítico (1 = Sim, 0 = Não): "
        ).strip()

        novo_status = input(
            "Status (ativo/inativo/manutencao): "
        ).strip().lower()

        # Montando o dicionário de alterações.
        alteracoes = {}

        if novo_codigo:
            alteracoes["codigo"] = novo_codigo

        if novo_nome:
            alteracoes["nome"] = novo_nome

        if novo_tipo:
            alteracoes["tipo"] = novo_tipo

        if novo_critico:
            if novo_critico not in ("0", "1"):
                raise ValueError(
                    "A criticidade deve ser 0 ou 1."
                )

            alteracoes["critico"] = int(novo_critico)

        if novo_status:
            alteracoes["status"] = novo_status

        # Verificando se algo foi informado.
        if not alteracoes:
            print("\nNenhuma alteração informada.")
            return

        # Executando a atualização.
        atualizado = atualizar_modulo(
            conexao,
            modulo_id,
            alteracoes
        )

        if atualizado:
            print("\nMódulo atualizado com sucesso!")
        else:
            print("\nMódulo não encontrado.")

    except (ValueError, TypeError) as erro:
        print(f"\nDados inválidos: {erro}")

    except sqlite3.IntegrityError as erro:
        print("\nNão foi possível atualizar o módulo.")
        print("Verifique se o código já está cadastrado.")
        print(f"Detalhes: {erro}")

    except sqlite3.Error as erro:
        print("\nErro ao acessar o banco de dados.")
        print(f"Detalhes: {erro}")

    finally:
        pausar()

# Solicitando confirmação para excluir um módulo
def exibir_exclusao_modulo(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== EXCLUIR MÓDULO ===\n")

    try:
        # Solicitando o identificador.
        modulo_id = solicitar_id_modulo()

        # Procurando o módulo.
        modulos = listar_modulos(conexao)

        modulo = next(
            (
                item for item in modulos
                if item["id"] == modulo_id
            ),
            None
        )

        if modulo is None:
            print("\nMódulo não encontrado.")
            return

        # Apresentando o registro escolhido.
        print("\nMódulo selecionado:")
        print(f"ID: {modulo['id']}")
        print(f"Código: {modulo['codigo']}")
        print(f"Nome: {modulo['nome']}")
        print(f"Status: {modulo['status']}")

        print(
            "\nATENÇÃO: esta operação remove "
            "o módulo do banco de dados."
        )

        # Exigindo confirmação explícita.
        confirmacao = input(
            "\nDigite EXCLUIR para confirmar: "
        ).strip()

        if confirmacao != "EXCLUIR":
            print("\nExclusão cancelada.")
            return

        # Solicitando a exclusão ao banco.
        excluido = excluir_modulo(
            conexao,
            modulo_id
        )

        if excluido:
            print("\nMódulo excluído com sucesso!")
        else:
            print("\nMódulo não encontrado.")

    except (ValueError, TypeError) as erro:
        print(f"\nDados inválidos: {erro}")

    except sqlite3.IntegrityError:
        print("\nNão foi possível excluir o módulo.")
        print(
            "Existem sensores ou solicitações "
            "vinculadas a esse módulo."
        )
        print(
            "Considere alterar seu status "
            "para 'inativo'."
        )

    except sqlite3.Error as erro:
        print("\nErro ao acessar o banco de dados.")
        print(f"Detalhes: {erro}")

    finally:
        pausar()

# Consultando e apresentando os sensores cadastrados
def exibir_listagem_sensores(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== SENSORES DA COLÔNIA ===\n")

    try:
        sensores = listar_sensores(conexao)

    except sqlite3.Error as erro:
        print("Erro ao consultar os sensores.")
        print(f"Detalhes: {erro}")

    else:
        if not sensores:
            print("Nenhum sensor cadastrado.")

        else:
            print(
                f"Total de sensores: {len(sensores)}\n"
            )

            for sensor in sensores:
                print(f"ID: {sensor['id']}")
                print(f"Código: {sensor['codigo']}")
                print(f"Módulo ID: {sensor['modulo_id']}")
                print(f"Tipo: {sensor['tipo']}")
                print(f"Unidade: {sensor['unidade']}")
                print(f"Status: {sensor['status']}")
                print("-" * 40)

    finally:
        pausar()

# Consultando leituras de todos os ciclos ou de um específico
def exibir_consulta_leituras(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== CONSULTAR LEITURAS ===\n")
    print(
        "Pressione Enter para consultar todos os ciclos."
    )

    try:
        # Solicitando um filtro opcional.
        ciclo_texto = input(
            "Informe o ciclo: "
        ).strip()

        ciclo = None

        # Convertendo o ciclo quando informado.
        if ciclo_texto:
            try:
                ciclo = int(ciclo_texto)
            except ValueError:
                raise ValueError(
                    "O ciclo deve ser um inteiro positivo."
                ) from None

            if ciclo <= 0:
                raise ValueError(
                    "O ciclo deve ser um inteiro positivo."
                )

        # Consultando os dados no banco.
        leituras = consultar_leituras(
            conexao,
            ciclo=ciclo
        )

        # Apresentando o resultado.
        if not leituras:
            print("\nNenhuma leitura encontrada.")
            return

        print(
            f"\n{len(leituras)} leitura(s) encontrada(s)."
        )

        # Evita imprimir centenas de registros.
        limite_exibicao = 20

        for leitura in leituras[:limite_exibicao]:
            print("\n" + "-" * 40)
            print(f"Ciclo: {leitura['ciclo']}")
            print(f"Sensor: {leitura['sensor_codigo']}")
            print(f"Módulo: {leitura['modulo_codigo']}")

            print(
                f"Valor: {leitura['valor']:.2f} "
                f"{leitura['unidade']}"
            )

            print(
                f"Status do sensor: "
                f"{leitura['sensor_status']}"
            )

            print(
                f"Status do módulo: "
                f"{leitura['modulo_status']}"
            )

        # Informando se a exibição foi limitada.
        if len(leituras) > limite_exibicao:
            restantes = len(leituras) - limite_exibicao

            print(
                f"\nExibidas as primeiras "
                f"{limite_exibicao} leituras."
            )

            print(
                f"Outras {restantes} leitura(s) "
                "não foram exibidas."
            )

            print(
                "Informe um ciclo específico "
                "para refinar a consulta."
            )

    except ValueError as erro:
        print(f"\nDados inválidos: {erro}")

    except sqlite3.Error as erro:
        print("\nErro ao consultar as leituras.")
        print(f"Detalhes: {erro}")

    finally:
        pausar()

# Apresentando o consumo, a geração e o saldo por ciclo
def exibir_serie_energia(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== SÉRIE ENERGÉTICA DA COLÔNIA ===\n")
    print("Consulta agregada bruta: uma grandeza ausente pode aparecer como zero.")
    print("Use as opções 4, 5 ou 7 do principal para analisar com validação de cobertura/unidades.\n")

    try:
        # Obtendo a série agregada.
        serie = obter_serie_energia(conexao)

    except sqlite3.Error as erro:
        print("Erro ao consultar os dados energéticos.")
        print(f"Detalhes: {erro}")

    else:
        if not serie:
            print("Nenhum dado energético disponível.")

        else:
            print(
                f"Total de ciclos energéticos: {len(serie)}\n"
            )

            # Apresentando os valores de cada ciclo.
            for registro in serie:
                ciclo = registro["ciclo"]
                consumo = registro["consumo_kw"]
                geracao = registro["geracao_kw"]

                saldo = geracao - consumo

                # Classificando o saldo de potência.
                if saldo > 0:
                    situacao = "Superávit"

                elif saldo < 0:
                    situacao = "Déficit"

                else:
                    situacao = "Equilíbrio"

                print(
                    f"Ciclo {ciclo} | "
                    f"Consumo: {consumo:.2f} kW | "
                    f"Geração: {geracao:.2f} kW | "
                    f"Saldo: {saldo:+.2f} kW"
                )

                print(f"Situação: {situacao}")
                print("-" * 40)

    finally:
        pausar()

# Importa o CSV inicial e apresenta um resumo da operação
def exibir_importacao_dados(conexao):

    limpar_tela()
    exibir_cabecalho()

    print("\n=== IMPORTAR DADOS INICIAIS ===\n")

    print(f"Arquivo: {CAMINHO_CSV.name}")

    try:
        # Verificando se o arquivo existe.
        if not CAMINHO_CSV.is_file():
            print("\nArquivo CSV não encontrado.")
            print(f"Caminho esperado: {CAMINHO_CSV}")
            print(
                "\nExecute no terminal: "
                "python3 -B gerar_dados_iniciais.py"
            )
            return

        # Solicitando uma confirmação explícita.
        print(
            "\nA importação cadastrará módulos, "
            "sensores e leituras ainda inexistentes."
        )

        confirmacao = input(
            "Digite IMPORTAR para continuar: "
        ).strip()

        if confirmacao != "IMPORTAR":
            print("\nImportação cancelada.")
            return

        # Executando a importação na camada de persistência.
        novas_leituras = carregar_csv_inicial(
            conexao,
            CAMINHO_CSV
        )

        # Apresentando o resultado da operação.
        print("\nImportação concluída com sucesso!")
        print(f"Novas leituras importadas: {novas_leituras}")

        if novas_leituras == 0:
            print(
                "Nenhuma leitura nova foi adicionada."
            )

        # Consultando os totais atuais do banco.
        total_modulos = len(listar_modulos(conexao))
        total_sensores = len(listar_sensores(conexao))
        total_leituras = len(consultar_leituras(conexao))

        print("\nResumo atual do banco de dados:")
        print(f"Módulos: {total_modulos}")
        print(f"Sensores: {total_sensores}")
        print(f"Leituras: {total_leituras}")

    except (ValueError, TypeError) as erro:
        print("\nDados inválidos no CSV.")
        print(f"Detalhes: {erro}")

    except (OSError, UnicodeError, csv.Error) as erro:
        print("\nNão foi possível ler o arquivo CSV.")
        print(f"Detalhes: {erro}")

    except sqlite3.Error as erro:
        print("\nErro ao importar dados para o SQLite.")
        print(f"Detalhes: {erro}")

    finally:
        pausar()


# Integra o monitoramento lógico aos dados operacionais da colônia.
def exibir_monitoramento_sensores(conexao):

    limpar_tela()
    exibir_cabecalho()
    print("\n=== MONITORAMENTO E REGRAS LÓGICAS ===\n")

    try:
        texto = input("Ciclo (Enter = todos): ").strip()
        ciclo = None

        if texto:
            try:
                ciclo = int(texto)
            except ValueError:
                raise ValueError(
                    "O ciclo deve ser um inteiro positivo."
                ) from None

            if ciclo <= 0:
                raise ValueError(
                    "O ciclo deve ser um inteiro positivo."
                )

        # Consulta as leituras enriquecidas do SQLite.
        leituras = consultar_leituras(conexao, ciclo=ciclo)

        if not leituras:
            print("\nNenhuma leitura encontrada para monitoramento.")
            return

        # R1: consumo elevado AND módulo crítico.
        # O monitoramento pode funcionar sem série completa, mas não deve
        # interpretar outra unidade ou uma medida inválida como potência em kW.
        for leitura in leituras:
            if leitura["sensor_tipo"] == "consumo_kw":
                valor = leitura["valor"]
                if (leitura["unidade"] != "kW" or not isfinite(valor) or valor < 0):
                    raise ValueError("O consumo deve ser finito, não negativo e medido em kW.")
        alertas = avaliar_consumo_critico(leituras)

        print(f"\nLeituras analisadas: {len(leituras)}")
        print(f"R1: consumo > {LIMITE_CONSUMO_CRITICO_KW:g} kW AND módulo crítico (ambos ativos).")
        print(f"Alertas R1 identificados: {len(alertas)}")

        # Limita apenas a apresentação, não o registro.
        for alerta in alertas[:10]:
            print(
                f"Sensor ID {alerta['sensor_id']} | "
                f"Ciclo {alerta['ciclo']} | "
                f"{alerta['mensagem']}"
            )

        if len(alertas) > 10:
            print(
                f"... mais {len(alertas) - 10} "
                "alertas não exibidos."
            )

        # R2: sensor inválido OR módulo em manutenção.
        # Seleciona uma leitura por sensor para evitar
        # contar repetidamente o mesmo bloqueio.
        ultimas_por_sensor = {
            leitura["sensor_id"]: leitura
            for leitura in leituras
        }

        bloqueios = []

        for leitura in ultimas_por_sensor.values():
            resultado = avaliar_bloqueio_operacao(leitura)

            if not resultado["permitido"]:
                bloqueios.append(
                    (leitura, resultado["motivos"])
                )

        print(f"\nBloqueios R2 identificados: {len(bloqueios)}")

        for leitura, motivos in bloqueios:
            print(
                f"Sensor {leitura['sensor_codigo']} / "
                f"Módulo {leitura['modulo_codigo']}: "
                + "; ".join(motivos)
            )

        print(
            "Observação: R2 usa o status atual dos dispositivos, "
            "não um histórico de estados."
        )

        # Demonstra a tabela verdade da regra AND.
        print(
            "\nTabela verdade R1 "
            "(consumo alto, crítico, alerta):"
        )

        for linha in gerar_tabela_verdade():
            print(
                f"{int(linha['consumo_alto'])} "
                f"{int(linha['modulo_critico'])} "
                f"{int(linha['alerta'])}"
            )

        # Demonstra a tabela verdade da regra OR.
        print(
            "\nTabela verdade R2 "
            "(sensor inválido, manutenção, bloqueio):"
        )

        for linha in gerar_tabela_verdade_bloqueio():
            print(
                f"{int(linha['sensor_invalido'])} "
                f"{int(linha['modulo_manutencao'])} "
                f"{int(linha['bloqueio'])}"
            )

        # O usuário decide se deseja persistir os alertas R1.
        if alertas:
            confirmacao = input(
                "\nDigite REGISTRAR para salvar os alertas R1 "
                "(Enter = não salvar): "
            ).strip()

            if confirmacao == "REGISTRAR":
                quantidade = registrar_alertas(
                    conexao,
                    alertas
                )

                print(
                    f"Novos alertas registrados: {quantidade}"
                )

            else:
                print("Alertas não registrados.")

    except (ValueError, TypeError) as erro:
        print(f"\nDados inválidos: {erro}")

    except sqlite3.Error as erro:
        print(f"\nErro de banco no monitoramento: {erro}")

    finally:
        pausar()

# Exibe resultados da simulação numérica a partir dos dados do SQLite.
def exibir_simulacao_computacional(conexao):

    limpar_tela()
    exibir_cabecalho()
    print("\n=== SIMULAÇÃO COMPUTACIONAL ENERGÉTICA ===\n")

    try:
        # Reutiliza a análise validada: ausência parcial de leituras não é zero.
        analise = executar_analise_integrada(conexao)
        resultado_base = analise["simulacao"]

        if not resultado_base:
            print("Nenhum dado energético disponível para simulação.")
            print("Importe os dados iniciais pela opção 9 do submenu de dados.")
            return

        serie = resultado_base["historico"]

        # Cenário hipotético: consumo inalterado, geração reduzida em 30%.
        serie_estresse = [
            {
                "ciclo": registro["ciclo"],
                "consumo_kw": registro["consumo_kw"],
                "geracao_kw": registro["geracao_kw"] * 0.70,
            }
            for registro in serie
        ]
        resultado_estresse = simular_balanco_energetico(serie_estresse)

        base = resultado_base["resumo"]
        estresse = resultado_estresse["resumo"]

        print(f"Ciclos analisados: {base['quantidade_ciclos']}")
        print(f"Duração de cada ciclo: {HORAS_POR_CICLO:.1f} h")
        print(f"Capacidade da bateria: {CAPACIDADE_BATERIA_KWH:.2f} kWh")
        print(f"Carga inicial da bateria: {CARGA_INICIAL_KWH:.2f} kWh")
        print("Bateria ideal: sem perdas e sem limite de potência.\n")
        print("Integração por retângulos: E = soma(P média do ciclo × duração), em kWh.")

        for titulo, resumo in (
            ("CENÁRIO-BASE", base),
            ("ESTRESSE: GERAÇÃO -30%", estresse),
        ):
            print(f"--- {titulo} ---")
            print(f"Energia consumida: {resumo['consumo_total_kwh']:.2f} kWh")
            print(f"Energia gerada: {resumo['geracao_total_kwh']:.2f} kWh")
            print(f"Déficit não atendido: {resumo['deficit_total_kwh']:.2f} kWh")
            print(f"Excedente não armazenado: {resumo['excedente_total_kwh']:.2f} kWh")
            print(f"Energia final da bateria: {resumo['energia_final_kwh']:.2f} kWh")
            print(f"SoC final: {resumo['soc_final_pct']:.2f}%")
            print(f"SoC mínimo: {resumo['soc_minimo_pct']:.2f}%")
            print(f"Atendimento da demanda: {resumo['atendimento_percentual']:.2f}%\n")

        aumento_deficit = estresse["deficit_total_kwh"] - base["deficit_total_kwh"]
        print(f"Diferença do déficit no estresse: {aumento_deficit:+.2f} kWh")

        if base["deficit_total_kwh"] > 0:
            print("A demanda não foi totalmente atendida no cenário-base.")
        else:
            print("A demanda foi atendida no cenário-base simulado.")

        print("\nÚltimos 5 ciclos do cenário-base:")
        for registro in resultado_base["historico"][-5:]:
            print(
                f"Ciclo {registro['ciclo']}: "
                f"consumo {registro['consumo_kw']:.2f} kW | "
                f"geração {registro['geracao_kw']:.2f} kW | "
                f"bateria {registro['energia_final_kwh']:.2f} kWh | "
                f"déficit {registro['deficit_nao_atendido_kwh']:.2f} kWh"
            )

        print("\nResultados simulados, sem atuação física na colônia.")
        print("O cenário de estresse reduz toda a geração agregada, não apenas a solar.")
        _exibir_limitacoes(analise["limitacoes"])

    except (ValueError, TypeError, OverflowError) as erro:
        print(f"\nDados inválidos para a simulação: {erro}")
    except sqlite3.Error as erro:
        print(f"\nErro ao consultar a série energética: {erro}")
    finally:
        pausar()

# Integra a busca em tabela hash, sem consultas SQL diretas na interface.
def exibir_busca_sensor_hash(conexao):
    limpar_tela()
    exibir_cabecalho()
    print("\n=== BUSCA DE SENSORES POR HASH ===\n")

    try:
        sensores = listar_sensores(conexao)
        if not sensores:
            print("Nenhum sensor cadastrado. Importe os dados iniciais.")
            return

        codigo = input("Código do sensor: ").strip()
        if not codigo:
            raise ValueError("Informe um código de sensor não vazio.")

        indice = construir_indice_sensores(sensores)
        encontrado = buscar_sensor_hash(indice, codigo)
        if encontrado is None:
            print("Sensor não encontrado no índice hash.")
        else:
            print("Sensor encontrado via tabela hash:")
            print(f"ID: {encontrado['id']}")
            print(f"Código: {encontrado['codigo']}")
            print(f"Módulo ID: {encontrado['modulo_id']}")
            print(f"Tipo: {encontrado['tipo']}")
            print(f"Unidade: {encontrado['unidade']}")
            print(f"Status: {encontrado['status']}")

    except (ValueError, TypeError) as erro:
        print(f"Dados inválidos: {erro}")
    except sqlite3.Error as erro:
        print(f"Erro ao consultar sensores: {erro}")
    finally:
        pausar()


# Cadastra solicitações reais no SQLite para alimentar a fila FIFO.
def exibir_cadastro_solicitacao(conexao):
    limpar_tela()
    exibir_cabecalho()
    print("\n=== REGISTRAR SOLICITAÇÃO DA TRIPULAÇÃO ===\n")

    try:
        modulos = listar_modulos(conexao)
        if not modulos:
            print("Nenhum módulo cadastrado. Importe os dados iniciais.")
            return

        for modulo in modulos:
            print(f"{modulo['id']} - {modulo['codigo']} ({modulo['nome']})")

        modulo_id = solicitar_id_modulo()
        descricao = input("Descreva a solicitação: ").strip()
        prioridade = input(
            "Prioridade (baixa/media/alta) [Enter = media]: "
        ).strip().lower() or "media"

        solicitacao_id = registrar_solicitacao(
            conexao,
            {
                "modulo_id": modulo_id,
                "descricao": descricao,
                "prioridade": prioridade,
            },
        )
        print(f"Solicitação registrada no SQLite com ID {solicitacao_id}.")
        print("Status inicial: pendente")
        print("Registro administrativo para revisão humana; nenhuma ação operacional executada.")

    except (ValueError, TypeError) as erro:
        print(f"Dados inválidos: {erro}")
    except sqlite3.IntegrityError:
        print("Não foi possível registrar: módulo inexistente no banco.")
    except sqlite3.Error as erro:
        print(f"Erro ao cadastrar solicitação: {erro}")
    finally:
        pausar()


# Mostra e manipula uma fila TEMPORÁRIA montada a partir de solicitações pendentes.
def exibir_fila_solicitacoes(conexao):
    limpar_tela()
    exibir_cabecalho()
    print("\n=== FILA FIFO DE SOLICITAÇÕES PENDENTES ===\n")

    try:
        solicitacoes = listar_solicitacoes(conexao, status="pendente")
        fila = montar_fila_solicitacoes(solicitacoes)
        if not fila:
            print("Nenhuma solicitação pendente na fila.")
            print("Utilize a opção 2 deste submenu para cadastrar uma.")
            return

        print(f"Total de solicitações pendentes: {len(fila)}")
        print("Ordem de chegada: menor ID primeiro (FIFO).")
        for solicitacao in list(fila)[:15]:
            print(
                f"ID {solicitacao['id']} | Módulo {solicitacao['modulo_id']} | "
                f"Prioridade {solicitacao['prioridade']} | "
                f"{solicitacao['descricao']}"
            )
        if len(fila) > 15:
            print(f"Outras {len(fila) - 15} solicitações não exibidas.")

        confirmacao = input(
            "\nDigite SIMULAR para retirar a primeira da fila temporária "
            "(Enter = voltar): "
        ).strip()
        if confirmacao == "SIMULAR":
            proxima = atender_proxima_solicitacao(fila)
            print(f"Próxima solicitação simulada: ID {proxima['id']}.")
            print(f"Itens restantes na fila temporária: {len(fila)}")
            print("O banco NÃO foi alterado; a solicitação continua pendente.")
        else:
            print("Nenhuma simulação de atendimento realizada.")

    except (ValueError, TypeError) as erro:
        print(f"Dados inválidos: {erro}")
    except sqlite3.Error as erro:
        print(f"Erro ao consultar solicitações: {erro}")
    finally:
        pausar()

# Interface da pilha de histórico LIFO.
def exibir_pilha_historico(historico):
    """Demonstra registros e desfazer em memória; não desfaz operações SQL."""
    while True:
        limpar_tela()
        exibir_cabecalho()
        print("\n=== PILHA DE HISTÓRICO (LIFO) ===\n")
        print(f"Registros na pilha: {len(historico)}")
        print("1 - Registrar ação demonstrativa")
        print("2 - Listar histórico (mais recente primeiro)")
        print("3 - Desfazer último registro da pilha")
        print("0 - Voltar ao Menu de Estruturas")
        print("\nA pilha é temporária: não altera nem reverte o SQLite.")

        opcao = input("\nEscolha uma opção: ").strip()
        if opcao == "0":
            return

        try:
            if opcao == "1":
                acao = input("Nome da ação demonstrativa: ").strip()
                detalhe = input("Detalhe (opcional): ").strip()
                registro = historico.empilhar(acao, detalhe)
                print(f"Ação registrada somente na pilha: {registro['acao']}")

            elif opcao == "2":
                registros = historico.listar()
                if not registros:
                    print("Pilha vazia: nenhuma ação registrada.")
                else:
                    print("Histórico (mais recente primeiro):")
                    for registro in registros[:15]:
                        print(
                            f"{registro['instante']} | {registro['acao']} | "
                            f"{registro['detalhe']}"
                        )
                    if len(registros) > 15:
                        print(f"Mais {len(registros) - 15} registro(s) não exibido(s).")

            elif opcao == "3":
                topo = historico.topo()
                if topo is None:
                    print("Pilha vazia: nada a desfazer.")
                else:
                    print(f"Última ação: {topo['acao']}")
                    confirmacao = input(
                        "Digite DESFAZER para remover o registro (Enter = cancelar): "
                    ).strip()
                    if confirmacao == "DESFAZER":
                        removido = historico.desfazer()
                        print(f"Registro removido somente da pilha: {removido['acao']}")
                        print("Nenhuma ação do banco de dados foi revertida.")
                    else:
                        print("Desfazer cancelado; registro preservado.")
            else:
                print("Opção inválida. Tente novamente.")

        except (ValueError, TypeError) as erro:
            print(f"Dados inválidos: {erro}")

        pausar()


# Grafo didático entre módulos cadastrados no SQLite.
def exibir_grafo_dependencias(conexao):
    """Mostra impactos por BFS; arestas hipotéticas não são gravadas no banco."""
    limpar_tela()
    exibir_cabecalho()
    print("\n=== GRAFO DE DEPENDÊNCIAS ENTRE MÓDULOS ===\n")

    try:
        modulos = listar_modulos(conexao)
        if not modulos:
            print("Nenhum módulo cadastrado para construir o grafo.")
            return

        # Todos os módulos do banco entram no grafo, inclusive os isolados.
        grafo = GrafoModulos()
        nomes = {}
        for modulo in modulos:
            codigo = modulo["codigo"]
            grafo.adicionar_modulo(codigo)
            nomes[codigo] = modulo["nome"]

        # Pares: (dependente, fornecedor). EXEMPLO, não relação real do banco.
        dependencias_exemplo = [
            ("MOD-HAB-01", "MOD-ENE-01"),
            ("MOD-AGR-01", "MOD-ENE-01"),
            ("MOD-COM-01", "MOD-ENE-01"),
            ("MOD-LAB-01", "MOD-AGR-01"),
        ]
        arestas = []
        for dependente, fornecedor in dependencias_exemplo:
            if dependente in nomes and fornecedor in nomes:
                grafo.adicionar_dependencia(dependente, fornecedor)
                arestas.append((fornecedor, dependente))

        print("Módulos cadastrados:")
        for codigo, nome in nomes.items():
            print(f"  {codigo} - {nome}")

        print("\nDependências HIPOTÉTICAS (fornecedor -> dependente):")
        if arestas:
            for fornecedor, dependente in arestas:
                print(f"  {fornecedor} -> {dependente}")
        else:
            print("  Nenhuma dependência do cenário ilustrativo está disponível.")

        codigo_falho = input("\nCódigo do módulo com falha simulada: ").strip()
        if not codigo_falho:
            raise ValueError("Informe o código de um módulo.")
        if codigo_falho not in nomes:
            raise ValueError("Módulo não encontrado entre os cadastrados.")

        afetados = grafo.modulos_afetados(codigo_falho)
        diretos = set(grafo.dependentes_diretos(codigo_falho))
        print(f"\nFalha simulada em: {codigo_falho}")
        print(f"Total de módulos afetados: {len(afetados)}")

        if not afetados:
            print("Nenhum módulo dependente afetado no cenário ilustrativo.")
        else:
            for codigo in afetados:
                tipo = "direto" if codigo in diretos else "indireto"
                print(f"  {codigo} - {nomes[codigo]} ({tipo})")

        print("\nAnálise de impacto em memória, sem falhas físicas ou mudanças no SQLite.")

    except (ValueError, TypeError, KeyError) as erro:
        print(f"Dados inválidos: {erro}")
    except sqlite3.Error as erro:
        print(f"Erro ao consultar os módulos: {erro}")
    finally:
        pausar()

# Submenu da opção 3 do Menu Principal.
def menu_estruturas_dados(conexao):
    # A pilha permanece ativa enquanto o usuário estiver neste submenu.
    historico = PilhaHistorico()

    while True:
        limpar_tela()
        exibir_cabecalho()
        print("\n=== ALERTAS E ESTRUTURAS DE DADOS ===\n")
        print("1 - Buscar Sensor Usando Tabela Hash")
        print("2 - Registrar Solicitação da Tripulação")
        print("3 - Consultar e Simular Fila (FIFO)")
        print("4 - Pilha de Histórico (LIFO)")
        print("5 - Grafo de Dependências (BFS)")
        print("Alertas R1: consultar e registrar pela opção 2 do Menu Principal.")
        print("0 - Voltar ao Menu Principal")

        opcao = input("\nEscolha uma opção: ").strip()
        if opcao == "0":
            return
        if opcao == "1":
            exibir_busca_sensor_hash(conexao)
        elif opcao == "2":
            exibir_cadastro_solicitacao(conexao)
        elif opcao == "3":
            exibir_fila_solicitacoes(conexao)
        elif opcao == "4":
            exibir_pilha_historico(historico)
        elif opcao == "5":
            exibir_grafo_dependencias(conexao)
        else:
            print("Opção inválida. Tente novamente.")
            pausar()

# Apresenta o submenu de gerenciamento dos dados
def menu_dados(conexao):

    while True:
        limpar_tela()
        exibir_cabecalho()

        print("\n=== GERENCIAR DADOS DA COLÔNIA ===\n")

        print("1 - Listar Módulos")
        print("2 - Cadastrar Módulo")
        print("3 - Buscar Módulo")
        print("4 - Atualizar Módulo")
        print("5 - Excluir Módulo")
        print("6 - Listar Sensores")
        print("7 - Consultar Leituras")
        print("8 - Consultar Série Energética")
        print("9 - Importar Dados Iniciais")
        print("0 - Voltar ao Menu Principal")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "0":
            return

        elif opcao == "1":
            exibir_listagem_modulos(conexao)
        
        elif opcao == "2":
            exibir_cadastro_modulo(conexao)

        elif opcao == "3":
            exibir_busca_modulo(conexao)

        elif opcao == "4":
            exibir_atualizacao_modulo(conexao)

        elif opcao == "5":
            exibir_exclusao_modulo(conexao)

        elif opcao == "6":
            exibir_listagem_sensores(conexao)

        elif opcao == "7":
            exibir_consulta_leituras(conexao)

        elif opcao == "8":
            exibir_serie_energia(conexao)

        elif opcao == "9":
            exibir_importacao_dados(conexao)

        else:
            print("\nOpção inválida. Tente novamente.")
            pausar()

def _exibir_limitacoes(limitacoes):
    """Apresenta as ressalvas dos módulos, sem descartá-las ou inventar sucesso."""
    print("\nLimitações e interpretação:")
    for limitacao in limitacoes:
        print(f"- {limitacao}")


def _exibir_previsao(previsao):
    """Exibe o resultado bruto da regressão, não a estimativa escolhida pelos agentes."""
    if not previsao:
        print("Previsão indisponível: a regressão exige pelo menos 10 ciclos energéticos.")
        return

    metricas = previsao["metricas"]
    coeficientes = previsao["coeficientes"]
    print("\nRegressão: X = ciclo; y = consumo médio agregado por ciclo, em kW.")
    print(f"Observações: {metricas['quantidade_total']} | treino: {metricas['quantidade_treino']} "
          f"| teste posterior: {metricas['quantidade_teste']}")
    print(f"Consumo mínimo/máximo/médio histórico: {metricas['consumo_minimo_kw']:.4f} / "
          f"{metricas['consumo_maximo_kw']:.4f} / {metricas['consumo_medio_kw']:.4f} kW")
    print(f"Consumo estimado (kW) = {coeficientes['intercepto_kw']:.6f} "
          f"+ ({coeficientes['inclinacao_kw_por_ciclo']:.6f} × ciclo)")
    print("Intercepto: estimativa no ciclo zero, sem significado físico garantido.")
    print("Inclinação: variação estimada em kW por ciclo; associação não é causalidade.")
    print(f"Avaliação fora do treino | MAE: {metricas['mae_kw']:.7f} kW | "
          f"RMSE: {metricas['rmse_kw']:.7f} kW")
    r2 = metricas["r2"]
    print("R²: " + ("indefinido (teste constante)" if r2 is None else f"{r2:.7f}"))
    print("R² não é porcentagem de acertos e pode ser negativo.")
    print(f"MAE da referência: {metricas['mae_referencia_kw']:.7f} kW | "
          f"média somente do treino: {metricas['consumo_medio_treino_kw']:.4f} kW")
    print("Previsões BRUTAS da reta (extrapolação, não garantia nem recomendação):")
    for item in previsao["previsoes"]:
        print(f"Ciclo {item['ciclo']}: {item['consumo_previsto_kw']:.7f} kW (extrapolação)")
    print("A escolha da estimativa para recomendação aparece abaixo, com validação humana.")


def _exibir_recomendacoes(recomendacoes):
    print("\nRecomendações para revisão humana (nenhuma ação executada):")
    for categoria in ("energia", "manutencao"):
        print("Energia:" if categoria == "energia" else "Manutenção:")
        for texto in recomendacoes[categoria]:
            print(f"- {texto}")
    print("Supervisão humana obrigatória; nenhuma ordem ou atendimento automático.")


def exibir_modelo_linear(conexao):
    """Consulta os dados validados e mantém métricas e previsões originais visíveis."""
    limpar_tela()
    exibir_cabecalho()
    print("\n=== MODELO DE REGRESSÃO LINEAR — DADOS DO SQLITE ===\n")
    try:
        resultado = executar_analise_integrada(conexao)
        _exibir_previsao(resultado["previsao"])
        _exibir_recomendacoes(resultado["recomendacoes"])
        _exibir_limitacoes(resultado["limitacoes"])
    except (ValueError, TypeError, OverflowError) as erro:
        print(f"Dados inválidos para a regressão: {erro}")
    except sqlite3.Error as erro:
        print(f"Erro ao consultar dados para a regressão: {erro}")
    finally:
        pausar()


def exibir_agentes(conexao):
    """Demonstração explícita e consulta textual; não cadastra solicitações."""
    limpar_tela()
    exibir_cabecalho()
    print("\n=== AGENTES SIMULADOS E GUARDRAILS ===\n")
    print("Triagem determinística por palavras-chave, sem LLM, RAG ou controle físico.")
    print("Esta tela não consulta o banco. Recomendações com dados: opção 7.")
    try:
        demonstrar_agentes()
        texto = input("\nSua solicitação (Enter = voltar): ").strip()
        if texto:
            print(rotear_solicitacao(texto))
        print("Nenhum registro de solicitação ou ordem criado por esta consulta.")
    except ValueError as erro:
        print(f"Solicitação inválida: {erro}")
    finally:
        pausar()


def exibir_sustentabilidade(conexao):
    """Apresenta o fluxo integrado com dados atuais, unidades e limites explícitos."""
    limpar_tela()
    exibir_cabecalho()
    print("\n=== SUSTENTABILIDADE — ANÁLISE INTEGRADA DO SQLITE ===\n")
    try:
        resultado = executar_analise_integrada(conexao)
        indicadores = resultado["indicadores"]
        print(f"Módulos: {indicadores['quantidade_modulos']} | "
              f"Sensores: {indicadores['quantidade_sensores']} | "
              f"Leituras: {indicadores['quantidade_leituras']} | "
              f"Ciclos energéticos: {indicadores['quantidade_ciclos']}")
        print(f"Alertas R1 calculados (não gravados): {len(resultado['alertas'])}")
        print(f"Ocorrências R2 por leitura, com status atuais: "
              f"{len(indicadores['bloqueios_operacionais'])}")
        print(f"Sensores no índice hash: {len(indicadores['indice_sensores'])}")
        fila = indicadores["fila_solicitacoes"]
        print(f"Solicitações pendentes na fila FIFO: {len(fila)}")
        if fila:
            print(f"Primeira na fila: ID {fila[0]['id']} (não atendida automaticamente).")

        if resultado["simulacao"]:
            resumo = resultado["simulacao"]["resumo"]
            print(f"Potência média histórica de consumo: {indicadores['consumo_medio_kw']:.4f} kW")
            print(f"Potência média histórica de geração: {indicadores['geracao_media_kw']:.4f} kW")
            print(f"Energia consumida: {resumo['consumo_total_kwh']:.2f} kWh | "
                  f"gerada: {resumo['geracao_total_kwh']:.2f} kWh")
            print(f"Bateria final: {resumo['energia_final_kwh']:.2f} kWh | "
                  f"SoC final: {resumo['soc_final_pct']:.2f}%")
            print(f"Déficit não atendido: {resumo['deficit_total_kwh']:.2f} kWh | "
                  f"excedente não armazenado: {resumo['excedente_total_kwh']:.2f} kWh")
            print(f"Atendimento simulado da demanda: {resumo['atendimento_percentual']:.2f}%")
            print("Matemática: E = soma(P média × duração); bateria ideal de capacidade finita.")
        else:
            print("Simulação indisponível: sem leituras energéticas. Ausência não é consumo zero.")
            print("Para começar: opção 1 → 9 → IMPORTAR (CSV simulado fornecido).")
        _exibir_previsao(resultado["previsao"])
        _exibir_recomendacoes(resultado["recomendacoes"])
        print("\nImpactos relacionados ao protótipo:")
        print("- Recursos: déficit e excedente apoiam revisão de consumo e armazenamento, não corte automático.")
        print("- Prevenção de desperdício: comparar cenários antes de dimensionar uma solução real (opção 4).")
        print("- Transparência e privacidade: métricas/limitações visíveis; minimizar dados pessoais nas solicitações.")
        print("- Sustentabilidade digital: processamento local simples, sem exigir aceleradores ou serviços externos.")
        print("- Responsabilidade social: revisar decisões com a tripulação, preservando serviços críticos e inclusão.")
        _exibir_limitacoes(resultado["limitacoes"])
    except (ValueError, TypeError, OverflowError) as erro:
        print(f"Dados inválidos para a análise: {erro}")
    except sqlite3.Error as erro:
        print(f"Erro ao consultar dados para a análise: {erro}")
    finally:
        pausar()


def exibir_informacoes_tecnicas(conexao):
    """Distingue a implementação local de propostas conceituais de infraestrutura."""
    limpar_tela()
    exibir_cabecalho()
    print("\n=== INFORMAÇÕES TÉCNICAS E LIMITAÇÕES ===\n")
    print(f"Execução: Python {sys.version.split()[0]} | SQLite {sqlite3.sqlite_version}")
    print("Entrada principal: codigo_fonte.py; main.py encaminha para a mesma aplicação.")
    print("Persistência: SQLite local; tabelas modulos, sensores, leituras, alertas e solicitacoes.")
    print(f"Configuração: ciclo = {HORAS_POR_CICLO:g} h; bateria = {CAPACIDADE_BATERIA_KWH:g} kWh; "
          f"carga inicial = {CARGA_INICIAL_KWH:g} kWh; horizonte = {HORIZONTE_PREVISAO_CICLOS} ciclos.")
    print(f"R1: consumo > {LIMITE_CONSUMO_CRITICO_KW:g} kW AND módulo crítico, em dispositivos ativos.")
    print("R2: sensor inválido OR módulo em manutenção; diagnóstico pelos status atuais, sem atuação física.")
    print("Estruturas: hash por código; deque FIFO por ID; pilha LIFO temporária; grafo BFS hipotético.")
    print("Simulação: potência média (kW) × duração (h) = energia (kWh), com déficit/excedente explícitos.")
    print("Regressão: treino/teste cronológico 80/20, mínimo de 10 ciclos; MAE/RMSE em kW, R² sem unidade.")
    print("Recomendações: reta só com MAE melhor e sem negativas; senão média do treino ou abstenção.")
    print("Agentes: funções determinísticas com handoffs e guardrails; sem IA generativa, RAG ou automação real.")
    print("\nArquitetura conectada ao protótipo:")
    print("- CPU: consultas SQLite, regras e pequenos modelos sequenciais; suficiente para a demonstração local.")
    print("- Memória: listas/hash/fila mantêm os registros consultados em RAM; bases grandes exigiriam paginação.")
    print("- Hierarquia: cache e RAM são mais rápidos que disco, mas não têm latência nula; leitura/movimentação custa recursos.")
    print("- GPU/NPU/TPU: propostas conceituais para cargas maiores/paralelas, não usadas ou necessárias aqui.")
    print("- Eficiência: medir gargalos de consulta e transferência antes de adicionar aceleração e seu custo energético.")
    print("\nLimites: CSV simulado; cobertura não comprova toda a colônia; sem histórico de status;")
    print("bateria ideal sem perdas/degradação; lacunas não interpoladas; extrapolação sem garantia futura.")
    print("Segurança: não há autenticação/multiusuário; proteger o arquivo local e evitar dados pessoais desnecessários.")
    print("Análises não gravam alertas. Somente REGISTRAR na opção 2 persiste R1; solicitações são registros administrativos.")
    print("Nenhum corte de cargas, comando a equipamento ou autorização operacional é executado pelo protótipo.")
    print("Documentos: README.md, docs/CONTRATOS.md, docs/DOC_NAVEGACAO.md e docs/DOC_ANALISE_INTEGRADA.md.")
    pausar()


# Menu único: todas as opções chamam funções explícitas e podem ser repetidas.
def menu_principal(conexao):
    opcoes = {
        "1": "- Gerenciar Dados da Colônia",
        "2": "- Monitorar Sensores e Regras Lógicas",
        "3": "- Gerenciar Alertas e Estruturas de Dados",
        "4": "- Executar Simulação Computacional",
        "5": "- Executar Modelo de Regressão Linear",
        "6": "- Consultar Agentes Inteligentes",
        "7": "- Analisar Sustentabilidade da Colônia",
        "8": "- Informações Técnicas e Limitações"
    }
    acoes = {
        "1": menu_dados,
        "2": exibir_monitoramento_sensores,
        "3": menu_estruturas_dados,
        "4": exibir_simulacao_computacional,
        "5": exibir_modelo_linear,
        "6": exibir_agentes,
        "7": exibir_sustentabilidade,
        "8": exibir_informacoes_tecnicas,
    }

    while True:
        limpar_tela()
        exibir_cabecalho()

        print("\n-------------| MENU PRINCIPAL |--------------\n")

        for numero, descricao in opcoes.items():
            print(f"[{numero}] {descricao}")

        print("\n[0] - Sair do Sistema")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "0": 
            limpar_tela()
            print("Encerrando o Sistema...")
            print("SIFSM - Encerrado!\n")
            break
        elif opcao in acoes:
            acoes[opcao](conexao)
        else:
            limpar_tela()
            print("ERRO: Opção inválida!")
            print("Digite um número entre 0 e 8.")
            pausar()

# Função principal utilizada para executar o sistema e iniciar o banco
def main():
    """Gerencia uma conexão por sessão e encerra também em EOF ou Ctrl+C."""
    conexao = None
    try:
        try:
            conexao = abrir_conexao()
            inicializar_banco(conexao)
        except (sqlite3.Error, OSError) as erro:
            print("ERRO: Não foi possível inicializar o banco.")
            print(f"Detalhes: {erro}")
            return 1
        menu_principal(conexao)
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada encerrada pelo usuário. SIFSM - Encerrado!")
        return 0
    finally:
        # Fecha inclusive em falhas de inicialização, navegação ou interrupção.
        if conexao is not None:
            conexao.close()

# Condição para saber se o arquivo está sendo executado diretamente
if __name__ == "__main__":
    raise SystemExit(main())
