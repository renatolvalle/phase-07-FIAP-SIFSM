# Relatório Técnico - Sistema Integrado de Futuro Sustentável em Marte (SIFSM)

## Contexto da Solução
O Sistema Integrado de Futuro Sustentável em Marte (SIFSM) foi desenvolvido para gerenciar os recursos, a infraestrutura e as decisões operacionais da colônia Aurora Siger. O sistema integra banco de dados relacional, regras lógicas de automação, estruturas de dados otimizadas, simulações computacionais, modelagem preditiva e inteligência artificial para garantir a sobrevivência, a segurança e a sustentabilidade da tripulação.

---

## 1. Organização de Dados e CRUD
A gestão de dados da Aurora Siger é estruturada em um banco de dados relacional (compatível com Oracle/SQL) composto por tabelas dedicadas ao monitoramento dos módulos vitais, sensores ambientais e registros de consumo.
* **Tabelas Principais:** `tb_modulos` (armazena ID, nome do módulo, status operacional e nível de criticidade) e `tb_sensores_leituras` (armazena ID do sensor, tipo de leitura como temperatura, umidade ou energia, e valor atual).
* **Operações CRUD e Tratamento de Erros:** O sistema implementa um módulo em Python que executa o cadastro (`INSERT`), listagem (`SELECT`), alteração (`UPDATE`) e exclusão (`DELETE`) de registros. Blocos de exceção (`try`, `except`, `else`, `finally`) foram aplicados rigorosamente para capturar entradas inválidas do usuário, falhas de conexão com o banco de dados e inconsistências operacionais sem interromper o fluxo da aplicação.

---

## 2. Circuitos Lógicos e Automação
O SIFSM traduz regras de sobrevivência da colônia em lógica booleana e circuitos digitais simulados. 
* **Regra de Decisão:** Caso um módulo seja considerado crítico e seu consumo energético ultrapasse o limite seguro, o sistema aciona automaticamente um alerta operacional e corta cargas não essenciais. Em termos booleanos: $Alerta = Crtico \land ConsumoAlto$.
* **Automação Embarcada:** A lógica foi concebida para integração com microcontroladores (Arduino e simulação conceitual via Tinkercad), utilizando sensores de umidade, temperatura e atuadores (LEDs de sinalização e relés de corte de energia) para demonstrar como decisões computacionais de software se convertem em respostas físicas de hardware.

---

## 3. Estruturas de Dados Aplicadas
Para lidar com a complexidade e o volume de informações em tempo real na colônia, o SIFSM emprega estruturas de dados fundamentais:
* **Fila (Queue):** Utilizada para gerenciar a ordem de atendimento das solicitações da tripulação e chamados de manutenção, garantindo uma política de atendimento justa (First-In, First-Out).
* **Pilha (Stack):** Empregada para registrar o histórico de ações executadas no sistema, permitindo a reversão (*undo*) de etapas administrativas.
* **Tabela Hash (Dicionários):** Utilizada para o mapeamento e busca rápida de códigos de sensores e módulos da colônia com complexidade $O(1)$.

---

## 4. Simulação Computacional e Integração Matemática
A simulação computacional modela a variação do estado de carga das baterias e o consumo energético dos módulos habitacionais e agrícolas ao longo do tempo.
* **Variáveis e Fenômeno:** Utilizando bibliotecas como NumPy e Matplotlib, o script simula ciclos de geração solar e consumo contínuo de oxigênio e energia.
* **Integração Matemática:** Conceitos de integração numérica foram aplicados para calcular a área sob a curva de consumo energético, permitindo estimar o consumo acumulado e prever o tempo restante de autonomia das reservas de energia da colônia antes de esgotamento total.

---

## 5. Modelagem Linear e Tomada de Decisão
Para apoiar o planejamento preditivo de recursos, foi construído um modelo de regressão linear simples e múltipla.
* **Análise Exploratória:** O modelo correlaciona variáveis ambientais externas e o nível de ocupação dos módulos com a demanda energética diária.
* **Avaliação:** Através da interpretação dos coeficientes e métricas de erro, o sistema consegue estimar com precisão a demanda de recursos para os ciclos seguintes, subsidiando cortes preventivos e otimizando a distribuição de água e eletricidade.

---

## 6. Integração de IA e Sistemas Multiagentes
A inteligência artificial do SIFSM opera por meio de uma arquitetura multiagentes que reduz a carga cognitiva da tripulação:
* **Agente Triador e Especialistas:** Um Agente Triador recebe as solicitações brutas e executa o *handoff* para agentes especialistas (como o Agente de Energia e o Agente de Manutenção).
* **Guardrails e Segurança:** Funções determinísticas e *guardrails* rígidos impedem que a IA tome decisões críticas de suporte à vida sem autorização humana expressa. As respostas utilizam um fluxo conceitual RAG (*Retrieval-Augmented Generation*), consultando diretamente a base de dados oficial da colônia.

---

## 7. Arquiteturas Modernas e Processamento
A infraestrutura computacional da Aurora Siger adota computação heterogênea para otimizar o consumo energético local:
* **Edge Computing vs. Servidores Centrais:** O monitoramento contínuo de sensores de baixa complexidade roda diretamente em microcontroladores na borda (*edge*), economizando largura de banda. Tarefas pesadas, como simulações e modelos preditivos, são direcionadas a aceleradores (GPUs/TPUs) em servidores centrais.
* **Hierarquia de Memória:** Dados críticos de emergência são mantidos em cache de alta velocidade (SRAM) para garantir latência nula, enquanto dados históricos de longo prazo são direcionados a storages secundários, mitigando o calor e o desperdício de energia no data center marciano.

---

## 8. Soluções Sustentáveis, Cidadania Digital e Impacto Socioambiental
A vertente socioambiental e sustentável do SIFSM apoia-se em quatro pilares fundamentais:
* **Prevenção de Desperdícios:** A simulação e os modelos lineares evitam erros físicos dispendiosos em Marte, preservando minérios e baterias.
* **Resiliência Autônoma:** Redes inteligentes e automações baseadas em lógica booleana mantêm a colônia segura mesmo durante falhas graves de comunicação.
* **Cidadania e Privacidade de Dados:** O tratamento de dados pessoais e de consumo da tripulação evita vieses discriminatórios ou punições automatizadas por uso de recursos.
* **Mitigação de Impacto Térmico:** A arquitetura heterogênea equilibra o custo energético do processamento intensivo de IA para que ele não concorra de forma predatória com os sistemas de suporte à vida.