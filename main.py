import sys
import subprocess

def exibir_menu():
    print("\n==============================================")
    print("  SISTEMA INTEGRADO DE FUTURO SUSTENTÁVEL EM MARTE (SIFSM)")
    print("  Colônia Aurora Siger")
    print("===============================================")
    print("1. Executar Operações de Banco de Dados e CRUD")
    print("2. Executar Simulação Computacional e Modelo Linear")
    print("3. Executar Simulação de Agentes de IA e Guardrails")
    print("4. Sair")
    print("===============================================")

def main():
    while True:
        exibir_menu()
        opcao = input("Selecione uma opção (1-4): ").strip()
        
        if opcao == '1':
            print("\n[Aviso] Módulo de Banco de Dados e CRUD acionado.")
            try:
                import codigo_fonte
            except ImportError:
                print("Erro: O arquivo 'codigo_fonte.py' da equipe ainda não foi encontrado.")
            input("\nPressione Enter para voltar ao menu...")
            
        elif opcao == '2':
            print("\n[Executando] Iniciando análise integrada (Simulação e Regressão)...")
            try:
                import analise_integrada
                analise_integrada.simular_consumo_energetico()
                analise_integrada.modelo_linear_previsao()
            except ImportError:
                print("Erro: O arquivo 'analise_integrada.py' não foi encontrado.")
            input("\nPressione Enter para voltar ao menu...")
            
        elif opcao == '3':
            print("\n[Executando] Iniciando simulação de Sistemas Multiagentes e IA...")
            try:
                import agentes_ia_simulacao
            except ImportError:
                print("Erro: O arquivo 'agentes_ia_simulacao.py' não foi encontrado.")
            input("\nPressione Enter para voltar ao menu...")
            
        elif opcao == '4':
            print("\nEncerrando o SIFSM. Boa sorte na missão em Marte!")
            sys.exit(0)
        else:
            print("\nOpção inválida. Selecione um número entre 1 e 4.")

if __name__ == "__main__":
    main()