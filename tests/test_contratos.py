# Testes Automatizados dos Contratos de Integração do Sistema Aurora Siger
# O teste verifica as interfaces compartilhadas entre os módulos

import inspect 
import unittest

import banco_dados
import monitoramento 
import estruturas_dados 
import simulacao_computacional 
import modelo_linear 
import agents 
import analise_integrada 

# Verifica a existência e assinatura das funções
class TestContratos(unittest.TestCase):
    # Confirma que os contratos estão disponíveis
    def test_funcoes_obrigatorias(self):
        contratos = {
            banco_dados: [
                "abrir_conexao",
                "inicializar_banco",
                "carregar_csv_inicial",
                "cadastrar_modulo",
                "listar_modulos",
                "buscar_modulo_por_codigo",
                "atualizar_modulo",
                "excluir_modulo",
                "cadastrar_sensor",
                "listar_sensores",
                "registrar_leitura",
                "consultar_leituras",
                "obter_serie_energia",
                "registrar_solicitacao",
                "listar_solicitacoes",
                "registrar_alertas"
            ],
            monitoramento: [
                "avaliar_consumo_critico",
                "gerar_tabela_verdade"
            ],
            estruturas_dados: [
                "construir_indice_sensores",
                "buscar_sensor_hash",
                "montar_fila_solicitacoes"
            ],
            simulacao_computacional: [
                "simular_balanco_energetico"
            ],
            modelo_linear: [
                "avaliar_e_prever_consumo"
            ],
            agents: [
                "rotear_solicitacao",
                "gerar_recomendacoes"
            ],
            analise_integrada: [
                "executar_analise_integrada"
            ]
        }

        for modulo, funcoes in contratos.items():
            for nome in funcoes:
                with self.subTest(
                    modulo=modulo.__name__,
                    funcao=nome
                ):
                    funcao = getattr(modulo, nome, None)
                    self.assertTrue(callable(funcao))

    # Verifica os parâmetros de funções importantes
    def test_assinaturas_compartilhadas(self):
        contratos = [
            (
                banco_dados.consultar_leituras,
                ["conexao", "ciclo"]
            ),
            (
                monitoramento.avaliar_consumo_critico,
                ["leituras", "limite_kw"]
            ),
            (
                estruturas_dados.buscar_sensor_hash,
                ["indice", "codigo"]
            ),
            (
                simulacao_computacional.simular_balanco_energetico,
                [
                    "serie_energia",
                    "capacidade_kwh",
                    "carga_inicial_kwh",
                    "horas_por_ciclo"
                ]
            ),
            (
                analise_integrada.executar_analise_integrada,
                ["conexao"]
            )
        ]

        for funcao, parametros_esperados in contratos:
            with self.subTest(funcao=funcao.__name__):
                assinatura = inspect.signature(funcao)
                parametros = list(assinatura.parameters)

                self.assertEqual(
                    parametros,
                    parametros_esperados
                )

if __name__ == "__main__":
    unittest.main()