# Sistema Integrado de Futuro Sustentável em Marte (SIFSM)
import os

from config import NOME_SISTEMA, SIGLA_SISTEMA, NOME_COLONIA
from banco_dados import abrir_conexao, inicializar_banco

# Função de limpar o terminal
def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

# Exibindo o cabeçalho principal do sistema
def exibir_cabecalho():
    print("=" * 60)
    print(f"----| {NOME_SISTEMA} |----")
    print(f"--------------| {SIGLA_SISTEMA} - COLÔNIA {NOME_COLONIA} |--------------")
    print("=" * 60)

# Função para pressionar "ENTER" antes de voltar ao menu
def pausar():
    input("\nPressione 'ENTER' para voltar ao Menu Principal.")

# Menu com opções para navegação no sistema
def menu_principal():
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
        elif opcao in opcoes:
            limpar_tela()
            exibir_cabecalho()
            print(f"\n{opcoes[opcao]}")
            print("\nFuncionalidade em Desenvolvimento")
            pausar()
        else:
            limpar_tela()
            print("ERRO: Opção inválida!")
            print("Digite um número entre 0 e 8.")
            pausar()

# Função principal utilizada para executar o sistema e iniciar o banco
def main():
    conexao = None 

    try:
        conexao = abrir_conexao() # Abrindo o banco de dados do SIFSM
        inicializar_banco(conexao) # Executa o SQL para garantir que as tabelas existam
    
    except (sqlite3.Error, OSError) as erro:
        # Tratando falhas do banco ou de acesso aos arquivos
        limpar_tela()
        print("ERRO: Não foi possível inicializar o banco.")
        print(f"Detalhes: {erro}")
    
    else:
        # Executando somente se a inicialização funcionar
        menu_principal()

    finally:
        #FFechando a conexão, inclusive se ocorrer algum erro
        if conexao is not None:
            conexao.close()

# Condição para saber se o arquivo está sendo executado diretamente
if __name__ == "__main__":
    main()