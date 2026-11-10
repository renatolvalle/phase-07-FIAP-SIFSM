# **SIFSM - Documentação: Monitoramento e Estruturas de Dados**

- **Responsável:** Renato Valle
- **Arquivos implementados:** `monitoramento.py`, `estruturas_dados.py`; interface em `codigo_fonte.py`
- **Artefato:** [circuito_logico.pdf](../circuito_logico.pdf), AND/OR e tabelas verdade, representação digital sem hardware
- **Testes:** `tests/test_monitoramento.py`, `tests/test_estruturas_dados.py`
- **Itens do enunciado atendidos:** 1.2 (circuitos lógicos, sensores simulados e automação) e 1.3 (estruturas de dados)

---

## **1. Regras lógicas (item 1.2)**

Os módulos de `monitoramento.py` e `estruturas_dados.py` não acessam o banco de dados. Eles recebem listas e dicionários (leituras enriquecidas, conforme `CONTRATOS.md`) e devolvem listas e dicionários.

### **1.1 Regra R1 - Consumo crítico (porta AND)**

| Item | Descrição |
|---|---|
| Decisão | Acionar alerta se o consumo estiver alto **e** o módulo for crítico. |
| Expressão booleana | `ALERTA = CONSUMO_ALTO AND MODULO_CRITICO` |
| `CONSUMO_ALTO` | 1 se o valor lido pelo sensor de consumo (`consumo_kw`) for **maior** que o limite (`LIMITE_CONSUMO_CRITICO_KW = 2.5` kW, em `config.py`). |
| `MODULO_CRITICO` | 1 se `modulos.critico = 1`. |
| Função | `avaliar_consumo_critico(leituras, limite_kw)` |
| Saída | `list[dict]` com `sensor_id`, `ciclo`, `regra_codigo` (`R1_CONSUMO_CRITICO`), `nivel` (`alto`), `mensagem`, `status` (`aberto`) e `criado_em`. |

| CONSUMO_ALTO | MODULO_CRITICO | ALERTA |
|:-:|:-:|:-:|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

Somente sensores e módulos com status `ativo` são avaliados, e somente sensores do tipo `consumo_kw` entram na regra. A função `gerar_tabela_verdade()` devolve essa tabela como `list[dict]`.

### **1.2 Regra R2 - Bloqueio de operação (porta OR)**

| Item | Descrição |
|---|---|
| Decisão | Bloquear uma operação se houver sensor em estado inválido **ou** módulo em manutenção. |
| Expressão booleana | `BLOQUEIO = SENSOR_INVALIDO OR MODULO_MANUTENCAO` |
| `SENSOR_INVALIDO` | 1 se `sensores.status = 'invalido'`. |
| `MODULO_MANUTENCAO` | 1 se `modulos.status = 'manutencao'`. |
| Função | `avaliar_bloqueio_operacao(leitura)` |
| Saída | `dict` com `permitido` (bool) e `motivos` (`list[str]`). |

| SENSOR_INVALIDO | MODULO_MANUTENCAO | BLOQUEIO |
|:-:|:-:|:-:|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 1 |

A função `gerar_tabela_verdade_bloqueio()` devolve essa tabela como `list[dict]`.
A R2 retorna um diagnóstico com motivos, não cadastra alertas. Um módulo em
manutenção pode ter sensores; isso não altera a expressão OR. `permitido=True`
significa apenas ausência dessas duas condições, não autorização geral de segurança.

### **1.3 Representação lógica**

As expressões e tabelas verdade acima representam as portas AND (R1) e OR (R2)
e são exibidas pela opção 2 da aplicação quando há leituras. Os testes conferem
a coerência com as funções. O [PDF](../circuito_logico.pdf) foi preparado na Etapa 4,
com filtro de elegibilidade da R1 explicitado e sem simular acionamento físico.
As tabelas são geradas pelas mesmas funções deste módulo.

### **1.4 Decisões técnicas**

- **Valor igual ao limite não é "elevado".** A comparação é estrita (`valor > limite_kw`).
- **A R1 e a R2 são complementares.** A R1 só avalia o que está `ativo`, e a R2 trata os casos de sensor `invalido` e módulo em `manutencao`.
- **Tratamento de erros.** Limite inválido, leitura sem campo obrigatório ou valor não numérico levantam `ValueError` com mensagem clara. Listas vazias retornam listas vazias.

---

## **2. Estruturas de dados (item 1.3)**

| Estrutura | Implementação | Onde se integra ao sistema |
|---|---|---|
| Tabela hash | `dict` (`construir_indice_sensores`, `buscar_sensor_hash`) | Busca de sensor pelo código |
| Fila | `collections.deque` (`montar_fila_solicitacoes`, `atender_proxima_solicitacao`) | Solicitações da tripulação (`solicitacoes`) |
| Pilha | classe `PilhaHistorico` | Histórico de ações e desfazer |
| Grafo | classe `GrafoModulos` (`construir_grafo_modulos`) | Dependência entre módulos e impacto de falhas |

### **2.1 Tabela hash**

- **Uso:** localizar um sensor pelo código (por exemplo, `SEN-HAB-CONS-01`) sem percorrer a lista inteira.
- **Por que é adequada:** a busca por chave custa O(1) em média, contra O(n) numa lista. O código do sensor é único no banco (`UNIQUE`), então é uma boa chave.
- **Erros:** código repetido ou sensor sem código levanta `ValueError`. Busca sem resultado retorna `None`.

### **2.2 Fila (FIFO)**

- **Uso:** atender as solicitações da tripulação na ordem de chegada, pelo ID.
- **Por que é adequada:** a regra de atendimento é "o primeiro a chegar é o primeiro a ser atendido". Em uma `deque`, retirar do início custa O(1), enquanto numa lista custaria O(n).
- **Observação:** a prioridade (`baixa`, `media`, `alta`) não altera a ordem, conforme definido em `CONTRATOS.md`.

### **2.3 Pilha (LIFO)**

- **Uso:** guardar as ações feitas no sistema (por exemplo, alerta resolvido ou manutenção iniciada).
- **Por que é adequada:** desfazer sempre se aplica à ação mais recente, que é o comportamento de uma pilha. Empilhar, desfazer e consultar o topo custam O(1).
- **Como funciona:** `desfazer()` remove e devolve a ação mais recente. Quem chama é responsável por reverter o efeito dela.

### **2.4 Grafo dirigido**

- **Uso:** representar que um módulo depende de outro (por exemplo, a agricultura depende da energia) e descobrir quais módulos são afetados quando um deles falha.
- **Por que é adequado:** dependências entre módulos formam uma rede, que uma lista ou uma árvore não representa bem (um módulo pode depender de vários, e vários podem depender do mesmo).
- **Como funciona:** a lista de adjacência guarda, para cada módulo, quem depende dele. `modulos_afetados(modulo)` faz uma busca em largura (BFS), custo O(V + E), sem repetir módulos e sem entrar em laço infinito se houver ciclo.
- **Limitação:** o banco não guarda dependências. Elas entram no sistema como dados passados na construção do grafo.

---

## **3. Testes**

Na navegação integrada, opção 2 consulta/calcula R1/R2 e só grava R1 após
`REGISTRAR`. A opção 3 oferece hash, cadastro administrativo de solicitações,
FIFO temporária, pilha demonstrativa e grafo de dependências hipotéticas entre
módulos cadastrados. `SIMULAR` não muda pendências no banco; desfazer na pilha
não reverte operações SQLite. A pilha dura enquanto o submenu 3 estiver aberto;
o grafo é reconstruído em cada consulta. [Guia](DOC_NAVEGACAO.md).

Execução: `python3 -B -m unittest discover -s tests -v`

- `test_monitoramento.py`: R1, R2, tabelas verdade, limites, erros e coerência entre as tabelas e as funções.
- `test_estruturas_dados.py`: hash, fila, pilha e grafo, incluindo casos vazios, entradas inválidas e ciclos.

## **4. Limitações**

- Os dados são simulados e não representam medições reais de Marte.
- O limite de consumo é único (2,5 kW), igual para todos os módulos.
- A R2 avalia uma leitura por vez e não considera o histórico de falhas.
- O histórico (pilha) e o grafo ficam em memória e se perdem ao encerrar o sistema.
