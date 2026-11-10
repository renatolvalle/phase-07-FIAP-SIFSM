# **SIFSM - Contratos de Integração v1.0**

## **Objetivo**

Definir as interfaces compartilhadas entre os módulos Python do SIFSM.

Os integrantes deverão implementar as funcionalidades respeitando as assinaturas e os formatos estabelecidos.

Alterações nos contratos deverão ser comunicadas e aprovadas pela equipe.

## **Banco de Dados**

Banco utilizado: SQLite.

Tabelas:
- modulos
- sensores
- leituras
- alertas
- solicitacoes

A conexão é aberta por `banco_dados.py`; `codigo_fonte.main()` controla o ciclo de
vida da aplicação e garante o fechamento. `main.py` encaminha para essa mesma função.

Todas as conexões deverão utilizar a verificação de chaves estrangeiras.

## **Formato dos Dados**

A comunicação entre os módulos deverá priorizar listas e dicionários Python.

Exemplo de leitura enriquecida:

```python
{
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
  "unidade": "kW"

}
```

Exemplo de série energética:

```python
[
  {
    "ciclo": 1,
    "consumo_kw": 5.4,
    "geracao_kw": 3.2 
  }
]
```

## **Contratos por Módulo**

### banco_dados.py

|              Função               |    Retorno     |
|-----------------------------------|----------------|
| abrir_conexao(caminho_banco=None) | Conexão SQLite |
| inicializar_banco(conexao)        |     None       |
| carregar_csv_inicial(conexao, caminho_csv) |  int  |
| cadastrar_modulo(conexao, dados)   |      int       |
| listar_modulos(conexao)           |   list[dict]   |
| buscar_modulo_por_codigo(conexao, codigo) | dict ou None |
| atualizar_modulo(conexao, modulo_id, alteracoes) | bool |
| excluir_modulo(conexao, modulo_id) |    bool       |
| cadastrar_sensor(conexao, dados)  |     int        |
| listar_sensores(conexao)          |   list[dict]   |
| registrar_leitura(conexao,dados)  |      int       |
| consultar_leituras(conexao, ciclo=None) | list[dict] |
| obter_serie_energia(conexao)      |   list[dict]   |
| registrar_solicitacao(conexao, dados) |    int     |
| listar_solicitacoes(conexao, status="pendente") | list[dict] |
| registrar_alertas(conexao, alertas) |      int     |

### monitoramento.py

- `avaliar_consumo_critico(leituras, limite_kw=...)` -> list[dict].
- `gerar_tabela_verdade()` -> list[dict].

**Regra principal:** consumo elevado AND módulo crítico.

### estruturas_dados.py

- `construir_indice_sensores(sensores)` -> dict.
- `buscar_sensor_hash(indice, codigo)` -> dict ou None.
- `montar_fila_solicitacoes(solicitacoes)` -> collections.deque.

### simulacao_computacional.py

- `simular_balanco_energetico(serie_energia, capacidade_kwh=..., carga_inicial_kwh=..., horas_por_ciclo=...)` -> dict.

O retorno conterá as chaves `historico` e `resumo`.

### modelo_linear.py

- `avaliar_e_prever_consumo(serie_energia, horizonte_ciclos=...)` -> dict.

O retorno conterá `coeficientes`, `metricas`, `previsoes` e `limitacoes`.

Complemento aditivo de 10/11/2026 para avaliação das recomendações, autorizado
na revisão da Etapa 2 (sem alterar assinatura ou chaves principais):

- `metricas.consumo_medio_treino_kw`: média de consumo calculada exclusivamente
  nos registros de treino, em kW; é o valor constante da referência usada no teste.
  Não se confunde com `metricas.consumo_medio_kw`, que descreve toda a série.
- `metricas.quantidade_previsoes_negativas_teste`: inteiro >= 0, quantidade de
  estimativas fisicamente inválidas da reta no período de teste.

Coeficientes, MAE, RMSE, R² e `previsoes` continuam sendo **da regressão original**,
mesmo quando ela não é escolhida nas recomendações. A escolha não altera o modelo,
não reajusta no teste e não substitui suas previsões pela média silenciosamente.

### agents.py

- `rotear_solicitacao(texto)` -> str.
- `gerar_recomendacoes(indicadores, alertas, simulacao, previsao)` -> dict.

`agents.py` é o nome efetivo do módulo (referido como `agentes.py` no plano
original). As recomendações não executam ações operacionais automaticamente,
não abrem conexão SQL, não registram ordens e não inserem solicitações em fila.
Eventual cadastro cabe à camada de integração/persistência, após validação humana.

**Roteamento e guardrails:**

- `texto` deve ser uma string não vazia; entrada inválida gera `ValueError`.
- O triador normaliza caixa, acentos, espaços e pontuação e compara palavras
  inteiras. Energia/bateria/consumo têm precedência sobre falha/manutenção/reparo.
- Antes de qualquer encaminhamento, menções a `suporte vital`, `módulo(s)
  crítico(s)` ou `sistema(s) crítico(s)` são bloqueadas e encaminhadas à supervisão
  humana/autorização manual. Os especialistas também aplicam esse bloqueio em
  chamadas diretas. Não existe parâmetro para autorizar execução automática.
- A política é conservadora: consultas e negações sobre esses sistemas também
  exigem revisão humana. Palavras desconhecidas recebem orientação de intervenção
  humana. Trata-se de simulação por palavras-chave, não de um classificador geral
  de riscos ou de uma barreira suficiente para controlar equipamentos reais.
- Importar o módulo não executa demonstração, menu, acesso ao banco ou impressão.
  `demonstrar_agentes()` exibe e retorna `list[dict]` com `solicitacao` e `resposta`;
  pode ser repetida ou executada com `python -X utf8 -B agents.py`.

**Entradas de `gerar_recomendacoes`:**

| Argumento | Tipo | Campos utilizados |
|---|---|---|
| `indicadores` | `dict` | `quantidade_leituras` (inteiro >= 0), `consumo_medio_kw` (>= 0) |
| `alertas` | `list[dict]` | Quantidade de alertas recebidos para revisão de manutenção |
| `simulacao` | `dict` | `resumo`: `quantidade_ciclos` (inteiro >= 0), `deficit_total_kwh`, `excedente_total_kwh` (>= 0), `soc_final_pct` (0 a 100) |
| `previsao` | `dict` | `coeficientes.inclinacao_kw_por_ciclo` (pode ser negativa), `metricas.mae_kw`, `metricas.mae_referencia_kw` e `metricas.consumo_medio_treino_kw` (>= 0), `metricas.quantidade_previsoes_negativas_teste` (inteiro >= 0), `metricas.r2` (número ou `None`), `previsoes` (`list[dict]` com `consumo_previsto_kw`), `limitacoes` (`list[str]`) |

Os quatro argumentos são obrigatórios. Campos conhecidos são opcionais, sem
substituir ausência por zero; `{}`/`[]` representam resultados indisponíveis.
Campos adicionais dos módulos analíticos são aceitos. Valores fornecidos devem
respeitar os tipos e intervalos acima; números devem ser finitos e não booleanos.
Estruturas/valores inválidos geram `ValueError`. Entradas não são alteradas.

O retorno é `dict` com:

- `energia`: `list[str]` baseada no consumo informado, déficit/excedente e estado
  final simulados; tendência e pico da regressão apenas quando a avaliação permitir,
  ou estimativa constante explicitamente identificada como média do treino;
- `manutencao`: `list[str]` para revisão dos alertas recebidos, sem confirmar cadastro;
- `supervisao_humana`: sempre `True`;
- `limitacoes`: `list[str]` com ausência de dados, restrições operacionais e ressalvas
  da previsão recebida, incluindo valores negativos, R² indefinido e modelo que
  não supera a referência pelo MAE, quando aplicável.

Sem ciclos não se interpreta o estado inicial da bateria como resultado de
operação. Previsões negativas são preservadas na entrada e sinalizadas como
inválidas. Sugestões não atestam segurança operacional.

**Escolha da estimativa nas recomendações:**

1. Sem previsões, não há sugestão preditiva. Sem ambos os MAEs ou sem a contagem
   de negativas no teste, a avaliação é incompleta: não recomendar pico, tendência
   nem referência. Dados de contratos anteriores são aceitos, mas geram essa abstenção.
2. Com avaliação completa, usar pico/tendência da regressão somente se
   `mae_kw < mae_referencia_kw`, nenhuma previsão futura for negativa e a contagem
   de negativas no teste for zero. R² não é um critério adicional de seleção;
   `None` continua sinalizado e não é convertido em 0 ou 1.
3. Em empate ou pior MAE, indicar **modelo sem ganho preditivo demonstrado** e
   suprimir recomendações de pico/tendência da reta. Negativas no teste ou no
   futuro também bloqueiam essas recomendações, mesmo com MAE menor.
4. Nesses casos, se a média do treino estiver disponível, recomendar apenas esse
   valor constante para cada ciclo do horizonte como **estimativa de referência**,
   não como pico, demanda garantida ou capacidade de segurança. Sem a média do
   treino, abster-se; nunca usar a média global para reconstruir a referência.

A comparação usa a janela de teste já existente: é uma escolha exploratória,
não uma avaliação independente do método selecionado nem garantia de desempenho
futuro. Recomendações sobre déficit/excedente observado na simulação continuam
disponíveis independentemente da qualidade preditiva. O consumo médio global
continua descrito como indicador histórico, explicitamente não como previsão.

### analise_integrada.py
- `executar_analise_integrada(conexao)` -> dict.

O retorno conterá `indicadores`, `alertas`, `simulacao`, `previsao`, `recomendacoes` e `limitacoes`.

**Entrada e efeitos:** `conexao` é obrigatória, aberta por `abrir_conexao`, com
`sqlite3.Row`, chaves estrangeiras habilitadas e esquema previamente inicializado.
A função usa apenas consultas de `banco_dados.py`. Não abre/fecha a conexão,
não inicializa tabelas, não importa dados, não faz commit/rollback, não grava
alertas e não cadastra/atende solicitações. Repetir a análise não duplica registros.
O chamador é responsável pelo ciclo de vida e por eventual transação de leitura
consistente caso existam alterações concorrentes.

**Orquestração:** `consultar_leituras` → índice hash de `listar_sensores` e validação
da cobertura → `obter_serie_energia` → R1/R2 → fila de solicitações pendentes →
`simular_balanco_energetico` → `avaliar_e_prever_consumo` → `gerar_recomendacoes`.
Os modelos usam os padrões de `config.py`, sem cálculos analíticos paralelos.

**Campos do retorno:**

| Campo | Conteúdo |
|---|---|
| `indicadores` | `quantidade_leituras`, `quantidade_modulos`, `quantidade_sensores`, `quantidade_ciclos` (energéticos), `quantidade_alertas`, `quantidade_solicitacoes_pendentes`; contagens inteiras |
| `indicadores.consumo_medio_kw`, `indicadores.geracao_media_kw` | Médias dos totais por ciclo da série, não médias de sensores individuais; campos ausentes se não houver energia |
| `indicadores.indice_sensores` | `dict` indexado pelo código, valores de `listar_sensores`; usado na busca/validação das leituras |
| `indicadores.fila_solicitacoes` | `list[dict]` de pendentes, ordenada por ID usando a deque FIFO, sem priorização ou atendimento automático |
| `indicadores.bloqueios_operacionais` | `list[dict]` com `sensor_codigo`, `ciclo` e `motivos` dos bloqueios R2 pelos status atuais; não são novos alertas persistidos |
| `alertas` | Lista produzida por R1 para as leituras consultadas, não a listagem histórica da tabela `alertas` |
| `simulacao` | Retorno integral do modelo de bateria ou `{}` quando não houver série energética |
| `previsao` | Retorno integral da regressão ou `{}` quando houver menos de 10 ciclos |
| `recomendacoes` | Retorno de `gerar_recomendacoes`, com supervisão humana obrigatória |
| `limitacoes` | `list[str]` sem duplicatas: políticas da integração, indisponibilidades e ressalvas dos agentes/modelo |

**Semântica dos dados:** a série soma por ciclo as leituras de `consumo_kw` e
`geracao_kw` de todos os módulos, incluindo histórico de dispositivos hoje
inativos/em manutenção. R1 considera apenas sensores/módulos atualmente ativos;
R2 sinaliza sensor inválido ou módulo em manutenção. O banco não registra status
históricos; bloqueios atuais não apagam medições anteriores nem autorizam operações.

Antes de somar, a análise exige potências finitas não negativas em `kW`, consumo
e geração presentes e cobertura igual dos sensores energéticos observados em
todos os ciclos energéticos. Falta de sensor em um desses ciclos é erro; zero
explicitamente medido é válido. Sensores cadastrados sem nenhuma leitura geram
uma limitação de cobertura, sem imputação. Lacunas completas de ciclos são aceitas
com aviso, sem interpolação nem tempo adicional. A soma representa os sensores
observados, não prova cobertura física de toda a colônia.

**Ausências e erros:** banco vazio ou apenas leituras não energéticas preserva
contagens/estruturas/regras, com `simulacao={}` e `previsao={}` e médias ausentes.
De 1 a 9 ciclos válidos, há simulação e previsão indisponível com justificativa.
Tipo de conexão incorreto gera `TypeError`; fábrica de linhas incompatível,
unidades, cobertura ou medidas inválidas geram `ValueError`. Erros SQLite e erros
numéricos dos modelos propagam; não são convertidos em resultados de sucesso.

**Persistência explícita:** caso a aplicação decida guardar alertas, chama
`registrar_alertas(conexao, resultado["alertas"])` separadamente. Essa função já
previne duplicação por `(sensor_id, ciclo, regra_codigo)` e rejeita conflitos.
`criado_em` no alerta calculado é o instante da leitura; na tabela é o instante
de cadastro definido pela persistência. A análise não altera alertas já gravados.

`demonstrar_analise_integrada()` é uma demonstração auxiliar: cria banco em memória,
importa o CSV fornecido e fecha somente essa conexão; retorna o mesmo dicionário.
Executar `analise_integrada.py` imprime esse resultado em JSON. Os auxiliares
`simular_consumo_energetico()` e `modelo_linear_previsao()` preservam as chamadas
sem argumentos de demonstração, imprimem uma série sintética de
24 ciclos e retornam os dicionários dos modelos compartilhados. Não fazem parte
do contrato de análise do banco e não são mais chamados pelos menus.

### codigo_fonte.py e main.py — navegação integrada

- `codigo_fonte.main()` -> `int`: abre uma conexão, inicializa o esquema, chama
  `menu_principal(conexao)` e fecha em `finally`. Retorna 0 ao sair/EOF/Ctrl+C e 1
  quando a inicialização falha; erros inesperados propagam após o fechamento.
- `main.main` referencia essa mesma função. Executar qualquer entrada chama a
  aplicação explicitamente; importar é silencioso e não abre banco/menu.
- Opções 4, 5 e 7 recebem a conexão e usam `executar_analise_integrada`: mesma
  cobertura validada, mesmos modelos, dados ausentes sem substituição sintética.
  A opção 4 também simula geração −30%, a partir do histórico validado, sem escrita.
- A opção 2 consulta leituras com filtro opcional de ciclo, R1/R2 e tabelas
  verdade. R2 conta uma ocorrência por sensor observado, usando seus status atuais;
  a análise integrada conta ocorrências por leitura. Consumo deve estar em kW,
  finito e não negativo. Não exige cobertura energética completa para aplicar R1/R2.
- Apenas `REGISTRAR` na opção 2 chama `registrar_alertas`; repetição idêntica não
  duplica alertas. As demais análises não persistem seus alertas calculados.
- O cadastro de solicitações no submenu 3 é administrativo, por entrada explícita
  do usuário, usando `registrar_solicitacao`; não executa seu conteúdo. FIFO é por
  ID, sem priorização. `SIMULAR` remove apenas da deque temporária, não do banco.
- Pilha demonstrativa e grafo hipotético são locais ao submenu/consulta. Desfazer
  na pilha não reverte SQL. Não há consulta/alteração de status de alertas históricos
  pelo menu; o monitoramento apresenta alertas recalculados das leituras.
- A opção 6 chama `demonstrar_agentes()` em toda visita e permite uma solicitação
  textual opcional via `rotear_solicitacao`; sem cadastro/execução/consulta ao banco.
- Telas analíticas apresentam resultados, interpretação, recomendações e
  limitações sem modificar coeficientes/métricas/previsões ou autorizar operação.

Roteiro, persistência e testes em [DOC_NAVEGACAO.md](DOC_NAVEGACAO.md).

## **Unidades**

|      Grandeza      | Unidade |
|--------------------|---------|
| Potência consumida | kW      |
| Potência gerada    | kW      |
| Energia            | kWh     |
| Temperatura        | °C      |
| Umidade            | %       |
| Luminosidade       | lux     |
| Estado de carga    | %       |

Cada ciclo simulado terá duração padrão de uma hora.

## **Tratamento de Erros**

- **Busca sem resultado:** retornar `None`.
- **Listagem sem registros:** retornar lista vazia.
- **Atualização de registro inexistente:** retornar `False`.
- **Exclusão de registro inexistente:** retornar `False`.
- **Dados inválidos:** sinalizar exceção apropriada.
- **Violação de integridade:** preservar o erro ou convertê-lo em exceção documentada.
- **Função não implementada:** utilizar `NotImplementedError`.

## **Regras de Integração**

1. Não modificar assinaturas compartilhadas sem aprovação.
2. Não criar conexões SQL dentro dos módulos de simulação, monitoramento ou agentes.
3. Não importar `codigo_fonte.py` nos módulos especializados.
4. Centralizar configurações em `config.py`.
5. Manter os formatos de retorno acordados.
6. Adicionar testes às funcionalidades implementadas.

**Versão dos Contratos: 1.0**
