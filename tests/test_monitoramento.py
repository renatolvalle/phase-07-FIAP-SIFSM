# Testes Automatizados do Monitoramento do Sistema Aurora Siger
# O teste verifica as regras booleanas R1 (consumo crítico) e R2 (bloqueio)

import unittest

from monitoramento import (
    avaliar_bloqueio_operacao,
    avaliar_consumo_critico,
    gerar_tabela_verdade,
    gerar_tabela_verdade_bloqueio,
)

# Cria uma leitura enriquecida válida; os campos podem ser sobrescritos
def criar_leitura(**alteracoes):
    leitura = {
        "sensor_id": 3,
        "sensor_codigo": "SEN-HAB-CONS-01",
        "sensor_tipo": "consumo_kw",
        "sensor_status": "ativo",
        "modulo_id": 2,
        "modulo_codigo": "MOD-HAB-01",
        "modulo_critico": True,
        "modulo_status": "ativo",
        "ciclo": 1,
        "instante": "2026-11-03T12:00:00Z",
        "valor": 3.1,
        "unidade": "kW",
    }
    leitura.update(alteracoes)
    return leitura

# Testes da regra R1: consumo elevado AND módulo crítico
class TestConsumoCritico(unittest.TestCase):
    # Consumo acima do limite em módulo crítico gera alerta
    def test_gera_alerta_com_consumo_alto_e_modulo_critico(self):
        alertas = avaliar_consumo_critico([criar_leitura(valor=3.1)], limite_kw=2.5)

        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["sensor_id"], 3)
        self.assertEqual(alertas[0]["ciclo"], 1)
        self.assertEqual(alertas[0]["regra_codigo"], "R1_CONSUMO_CRITICO")
        self.assertEqual(alertas[0]["nivel"], "alto")
        self.assertEqual(alertas[0]["status"], "aberto")
        self.assertEqual(alertas[0]["criado_em"], "2026-11-03T12:00:00Z")

    # O alerta tem exatamente os campos esperados pela tabela alertas
    def test_campos_do_alerta(self):
        alerta = avaliar_consumo_critico([criar_leitura()], limite_kw=2.5)[0]

        self.assertEqual(
            set(alerta),
            {"sensor_id", "ciclo", "regra_codigo", "nivel",
             "mensagem", "status", "criado_em"},
        )

    # Consumo abaixo do limite não gera alerta
    def test_sem_alerta_com_consumo_baixo(self):
        self.assertEqual(
            avaliar_consumo_critico([criar_leitura(valor=1.0)], limite_kw=2.5), []
        )

    # Consumo exatamente igual ao limite não é considerado elevado
    def test_valor_igual_ao_limite_nao_gera_alerta(self):
        self.assertEqual(
            avaliar_consumo_critico([criar_leitura(valor=2.5)], limite_kw=2.5), []
        )

    # Módulo não crítico não gera alerta, mesmo com consumo alto
    def test_sem_alerta_em_modulo_nao_critico(self):
        leitura = criar_leitura(modulo_critico=False, valor=9.0)
        self.assertEqual(avaliar_consumo_critico([leitura], limite_kw=2.5), [])

    # Criticidade vinda do banco como inteiro (0 ou 1) também funciona
    def test_criticidade_como_inteiro(self):
        self.assertEqual(
            len(avaliar_consumo_critico([criar_leitura(modulo_critico=1)], 2.5)), 1
        )
        self.assertEqual(
            avaliar_consumo_critico([criar_leitura(modulo_critico=0)], 2.5), []
        )

    # Sensor ou módulo que não esteja ativo não é avaliado
    def test_ignora_sensor_ou_modulo_nao_ativo(self):
        leituras = [
            criar_leitura(sensor_status="inativo"),
            criar_leitura(sensor_status="invalido"),
            criar_leitura(modulo_status="inativo"),
            criar_leitura(modulo_status="manutencao"),
        ]
        self.assertEqual(avaliar_consumo_critico(leituras, limite_kw=2.5), [])

    # Sensores que não medem consumo são ignorados
    def test_ignora_sensor_que_nao_e_de_consumo(self):
        leitura = criar_leitura(sensor_tipo="temperatura", valor=40.0, unidade="°C")
        self.assertEqual(avaliar_consumo_critico([leitura], limite_kw=2.5), [])

    # Lista vazia retorna lista vazia
    def test_lista_vazia(self):
        self.assertEqual(avaliar_consumo_critico([], limite_kw=2.5), [])

    # Várias leituras geram um alerta por leitura que satisfaz a regra
    def test_varias_leituras(self):
        leituras = [
            criar_leitura(sensor_id=1, ciclo=1, valor=3.0),
            criar_leitura(sensor_id=1, ciclo=2, valor=1.0),
            criar_leitura(sensor_id=1, ciclo=3, valor=4.0),
        ]
        alertas = avaliar_consumo_critico(leituras, limite_kw=2.5)

        self.assertEqual([alerta["ciclo"] for alerta in alertas], [1, 3])

    # Sem informar o limite, usa o valor de config.py
    def test_limite_padrao_do_config(self):
        self.assertEqual(len(avaliar_consumo_critico([criar_leitura(valor=2.6)])), 1)
        self.assertEqual(avaliar_consumo_critico([criar_leitura(valor=2.4)]), [])

    # Limite inválido sinaliza erro
    def test_limite_invalido(self):
        for limite in (-1, "2.5", None, True):
            with self.subTest(limite=limite):
                with self.assertRaises(ValueError):
                    avaliar_consumo_critico([criar_leitura()], limite_kw=limite)

    # Leitura sem campo obrigatório sinaliza erro
    def test_leitura_sem_campo_obrigatorio(self):
        leitura = criar_leitura()
        del leitura["modulo_critico"]

        with self.assertRaises(ValueError):
            avaliar_consumo_critico([leitura], limite_kw=2.5)

    # Valor não numérico sinaliza erro
    def test_valor_nao_numerico(self):
        with self.assertRaises(ValueError):
            avaliar_consumo_critico([criar_leitura(valor="alto")], limite_kw=2.5)

    # A tabela verdade do AND tem quatro linhas e o resultado correto
    def test_tabela_verdade_and(self):
        tabela = gerar_tabela_verdade()

        self.assertEqual(len(tabela), 4)
        self.assertEqual(
            [(l["consumo_alto"], l["modulo_critico"], l["alerta"]) for l in tabela],
            [
                (False, False, False),
                (False, True, False),
                (True, False, False),
                (True, True, True),
            ],
        )

    # A tabela verdade é coerente com a função avaliar_consumo_critico
    def test_tabela_verdade_coerente_com_a_regra(self):
        for linha in gerar_tabela_verdade():
            with self.subTest(linha=linha):
                valor = 3.0 if linha["consumo_alto"] else 1.0
                leitura = criar_leitura(
                    valor=valor, modulo_critico=linha["modulo_critico"]
                )
                gerou_alerta = bool(avaliar_consumo_critico([leitura], limite_kw=2.5))

                self.assertEqual(gerou_alerta, linha["alerta"])

# Testes da regra R2: sensor inválido OR módulo em manutenção
class TestBloqueioOperacao(unittest.TestCase):
    # Sensor e módulo normais liberam a operação
    def test_operacao_liberada(self):
        resultado = avaliar_bloqueio_operacao(criar_leitura())

        self.assertTrue(resultado["permitido"])
        self.assertEqual(resultado["motivos"], [])

    # Sensor inválido bloqueia
    def test_bloqueia_sensor_invalido(self):
        resultado = avaliar_bloqueio_operacao(criar_leitura(sensor_status="invalido"))

        self.assertFalse(resultado["permitido"])
        self.assertEqual(len(resultado["motivos"]), 1)

    # Módulo em manutenção bloqueia
    def test_bloqueia_modulo_em_manutencao(self):
        resultado = avaliar_bloqueio_operacao(criar_leitura(modulo_status="manutencao"))

        self.assertFalse(resultado["permitido"])
        self.assertEqual(len(resultado["motivos"]), 1)

    # Os dois motivos juntos aparecem na lista
    def test_bloqueia_pelos_dois_motivos(self):
        resultado = avaliar_bloqueio_operacao(
            criar_leitura(sensor_status="invalido", modulo_status="manutencao")
        )

        self.assertFalse(resultado["permitido"])
        self.assertEqual(len(resultado["motivos"]), 2)

    # Sensor inativo ou módulo inativo não entram na regra R2
    def test_inativo_nao_bloqueia(self):
        self.assertTrue(
            avaliar_bloqueio_operacao(criar_leitura(sensor_status="inativo"))["permitido"]
        )
        self.assertTrue(
            avaliar_bloqueio_operacao(criar_leitura(modulo_status="inativo"))["permitido"]
        )

    # Leitura sem os campos de status sinaliza erro
    def test_leitura_sem_campo_obrigatorio(self):
        with self.assertRaises(ValueError):
            avaliar_bloqueio_operacao({"sensor_status": "ativo"})

    # A tabela verdade do OR tem quatro linhas e o resultado correto
    def test_tabela_verdade_or(self):
        tabela = gerar_tabela_verdade_bloqueio()

        self.assertEqual(len(tabela), 4)
        self.assertEqual(
            [(l["sensor_invalido"], l["modulo_manutencao"], l["bloqueio"])
             for l in tabela],
            [
                (False, False, False),
                (False, True, True),
                (True, False, True),
                (True, True, True),
            ],
        )

    # A tabela verdade é coerente com a função avaliar_bloqueio_operacao
    def test_tabela_verdade_coerente_com_a_regra(self):
        for linha in gerar_tabela_verdade_bloqueio():
            with self.subTest(linha=linha):
                leitura = criar_leitura(
                    sensor_status="invalido" if linha["sensor_invalido"] else "ativo",
                    modulo_status="manutencao" if linha["modulo_manutencao"] else "ativo",
                )
                bloqueada = not avaliar_bloqueio_operacao(leitura)["permitido"]

                self.assertEqual(bloqueada, linha["bloqueio"])

if __name__ == "__main__":
    unittest.main()
