class Agente:
    def __init__(self, nome, especialidade):
        self.nome = nome
        self.especialidade = especialidade

    def processar(self, dados):
        pass

class AgenteTriador(Agente):
    def __init__(self, agentes_disponiveis):
        super().__init__("Triador", "Roteamento")
        self.agentes = agentes_disponiveis

    def processar(self, dados):
        if "energia" in dados.lower() or "bateria" in dados.lower():
            return self.agentes["energia"].processar(dados)
        elif "falha" in dados.lower() or "manutencao" in dados.lower():
            return self.agentes["manutencao"].processar(dados)
        return "Solicitação não compreendida pelos guardrails. Necessária intervenção humana."

class AgenteEnergia(Agente):
    def __init__(self):
        super().__init__("Especialista em Energia", "Gestao de Consumo")

    def processar(self, dados):
        if "desligar suporte vital" in dados.lower():
            return "Ação bloqueada pelo Guardrail: Suporte vital requer autorização manual."
        return "Análise de energia concluída. Reduzindo carga de módulos não críticos."

class AgenteManutencao(Agente):
    def __init__(self):
        super().__init__("Especialista em Manutenção", "Reparos")

    def processar(self, dados):
        return "Ordem de serviço gerada e inserida na fila de manutenção da Aurora Siger."

agentes_colonia = {
    "energia": AgenteEnergia(),
    "manutencao": AgenteManutencao()
}

sistema_ia = AgenteTriador(agentes_colonia)

solicitacoes = [
    "Alerta de bateria baixa no módulo 3",
    "Falha no sensor de umidade da estufa",
    "Desligar suporte vital do laboratório",
    "Status da produção agrícola"
]

for req in solicitacoes:
    resposta = sistema_ia.processar(req)
    print(f"[{req}] -> {resposta}")



def rotear_solicitacao(solicitacao):
    """Função de contrato para o roteamento de IA."""
    return sistema_ia.processar(solicitacao)

def gerar_recomendacoes():
    """Função de contrato para geração de recomendações dos agentes."""
    return ["Reduzir consumo em módulos não críticos", "Manter monitoramento ativo"]