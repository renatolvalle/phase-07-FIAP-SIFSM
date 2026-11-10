# Análise integrada — SIFSM

## Objetivo e execução

`executar_analise_integrada(conexao)` conecta os módulos da equipe usando os dados
do SQLite recebido. Retorna os seis campos definidos em `CONTRATOS.md`; não usa
dados sintéticos de substituição nem mantém outra implementação dos modelos.

Para demonstrar com o CSV fornecido, sem tocar no banco local:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B analise_integrada.py
```

A demonstração cria um banco em memória, inicializa o esquema, importa o CSV,
analisa, fecha essa conexão e imprime JSON. O comando não gera arquivos. Para a
aplicação, fornecer uma conexão aberta por `banco_dados.abrir_conexao`, com esquema
e dados já preparados; o chamador continua responsável por fechá-la.

## Fluxo e estruturas

1. `consultar_leituras`: obtém leituras enriquecidas, em ordem de ciclo/sensor.
2. `listar_sensores` + `construir_indice_sensores`: constrói hash por código.
   `buscar_sensor_hash` localiza cada sensor durante a validação das leituras;
   não é necessário percorrer a lista de sensores a cada busca. A construção é
   linear e a busca é O(1) em média. O índice é retornado nos indicadores.
3. Valida medidas/unidades e cobertura antes da agregação. `obter_serie_energia`
   continua sendo a única consulta que agrega potência por ciclo.
4. `avaliar_consumo_critico` aplica R1 (consumo acima do limite AND módulo crítico)
   aos sensores/módulos ativos. `avaliar_bloqueio_operacao` aplica R2 (sensor inválido
   OR módulo em manutenção); bloqueios são diagnósticos nos indicadores.
5. `listar_solicitacoes` + `montar_fila_solicitacoes`: organiza os registros
   pendentes em deque FIFO por ID. Retorna uma lista na mesma ordem para facilitar
   transporte em JSON. Não remove itens nem altera seu status. Prioridade não
   muda a ordem de chegada. A fila vazia significa que não há pendentes cadastrados.
6. `simular_balanco_energetico`: integra potência média × duração em horas,
   preservando capacidade, déficit e excedente da bateria ideal.
7. `avaliar_e_prever_consumo`: regressão simples ciclo → consumo, ajuste nos
   primeiros 80% e métricas nos últimos 20%; somente com pelo menos 10 ciclos.
8. `gerar_recomendacoes`: usa os indicadores, alertas e os dois resultados reais;
   retorna sugestões e ressalvas com supervisão humana obrigatória. A regressão
   só fundamenta pico/tendência se superar a referência por MAE e não produzir
   negativas no teste/futuro; do contrário, a sugestão usa a média do treino
   explicitamente identificada como referência, quando disponível.

Listas armazenam leituras, histórico e previsões. Não há necessidade de inserir
pilha ou grafo artificialmente nesse fluxo: o enunciado exige uso coerente, não
uso de todas as estruturas estudadas. Os módulos especializados não recebem SQL.

## Dados, unidades e ausência de registros

- A série representa a soma dos sensores de consumo/geração com leituras, em
  todos os módulos. A média informada é a média desses totais por ciclo, em kW,
  não a média entre sensores. A cobertura não prova medição de toda a colônia real.
- `consumo_kw`/`geracao_kw`: potências médias durante cada ciclo. `E = P × Δt` em
  kWh, com duração de `config.py`. SoC em %. Não se usa trapézio para essas médias.
- Exige-se kW, valores finitos não negativos, ambos os tipos de potência e o mesmo
  conjunto de sensores energéticos observados em cada ciclo energético. Uma
  leitura negativa não pode ser escondida pela soma de outras leituras positivas.
- Falta de leitura em um ciclo gera `ValueError`, inclusive se outros sensores do
  mesmo tipo ainda estiverem presentes. A consulta isolada retorna zero para uma
  grandeza ausente; a validação anterior impede interpretá-lo como medição real.
- Sensores cadastrados sem nenhuma leitura ficam fora da soma, com aviso explícito.
  Para analisar períodos com mudança real de cobertura, será necessário evoluir
  o recorte temporal e os metadados; hoje a análise rejeita cobertura variável.
- Ciclos inteiramente ausentes não são interpolados. Os identificadores restantes
  mantêm suas distâncias na regressão, mas cada linha representa apenas um ciclo
  de duração na simulação. O resultado informa essa limitação.
- Sem série energética: `simulacao={}`, `previsao={}`, sem campos de média. Zero
  realmente medido é válido; ausência de dados não é consumo zero nem atendimento
  de 100%. De 1 a 9 ciclos: simulação válida, previsão vazia e motivo explícito.
- Não se mascara falha numérica, banco sem esquema ou conexão fechada como
  indisponibilidade por poucas observações: a exceção original é propagada.

## Histórico, regras e persistência

A série histórica inclui dispositivos hoje inativos, inválidos ou em manutenção,
conforme a consulta já implementada pela equipe. R1/R2 usam os status atuais,
pois não existe histórico de mudanças de status. Um bloqueio atual não apaga
leituras anteriores; também não autoriza operação com base nos resultados.

A análise é **somente de leitura**, incluindo nos casos de erro. Não faz commit,
rollback, importação automática, cadastro de solicitações nem gravação de alertas.
Repetições com os mesmos dados produzem o mesmo resultado e não duplicam registros.
Uma transação que já estava aberta pertence ao chamador e permanece aberta.
Em uso concorrente, cabe ao chamador providenciar uma transação de leitura
consistente; o fluxo não cria um snapshot próprio.

Se a aplicação decidir persistir os alertas calculados, a chamada é separada:

```python
from banco_dados import registrar_alertas

novos = registrar_alertas(conexao, resultado["alertas"])
```

O cadastro existente é idempotente por sensor/ciclo/regra para alertas idênticos;
conflitos são erros, não sobrescritas. O instante calculado é o da leitura; o
instante persistido é o de cadastro. Alertas calculados não representam a consulta
dos alertas antigos da tabela, nem reabrem alertas já tratados.

## Resultado verificado com o CSV fornecido

Com os parâmetros padrão da configuração e o CSV atual:

| Medida | Resultado |
|---|---:|
| Módulos / sensores / leituras | 5 / 10 / 320 |
| Ciclos / alertas R1 calculados | 32 / 19 |
| Consumo médio / geração média | 5,3453125 / 2,08625 kW |
| Consumo / geração acumulados | 171,05 / 66,76 kWh |
| Energia inicial / final | 12 / 0 kWh |
| Déficit não atendido / excedente | 92,29 / 0 kWh |
| Atendimento simulado | 46,0450% |
| Treino / teste | 25 / 7 ciclos |
| Intercepto / inclinação | 5,384 kW / −0,003076923 kW por ciclo |
| MAE / RMSE no teste | 0,2766813 / 0,3016809 kW |
| R² / MAE da referência | −0,0193275 / 0,2722857 kW |
| Média somente do treino (referência constante) | 5,344 kW |
| Previsões dos ciclos 33 / 34 / 35 | 5,2824615 / 5,2793846 / 5,2763077 kW |

O modelo **não supera a referência pela MAE** nesse conjunto. R² negativo não é
percentual de acertos. Esses resultados são preservados e sinalizados pelos
agentes, sem forçar uma avaliação positiva. A recomendação preditiva passa a usar
**5,344 kW por ciclo, a média dos 25 ciclos de treino**, e não o pico da reta.
As previsões dos ciclos 33–35 na tabela/JSON continuam sendo as da regressão,
para inspeção acadêmica; não são as estimativas recomendadas neste conjunto.
O déficit é resultado da bateria
ideal e dos dados simulados, não diagnóstico de um equipamento real. A ligeira
tendência decrescente não demonstra causalidade nem garante demanda futura.

### Política de escolha e abstenção

- Compara-se o MAE da reta com o MAE da média do treino na mesma janela de teste.
  MAE estritamente menor e ausência de previsões negativas no teste/futuro permitem
  sugestão de pico/tendência, sempre para revisão humana e sem garantia futura.
- Empate ou MAE pior: **modelo sem ganho preditivo demonstrado**. A reta não
  fundamenta pico/tendência nas recomendações. Uma previsão fisicamente inválida
  também impede esse uso, ainda que o MAE médio seja menor.
- A alternativa é a média **apenas do treino**, constante em cada ciclo do
  horizonte, não um pico. O modelo agora expõe `consumo_medio_treino_kw` e
  `quantidade_previsoes_negativas_teste` dentro de `metricas`; as chaves principais
  e os resultados anteriores permanecem preservados.
- Sem avaliação completa ou sem previsões: não se recomenda estimativa preditiva.
  Se for necessário recorrer à referência mas a média do treino estiver ausente,
  também há abstenção; não se aproveita a média de toda a série como substituta.
- Não há reajuste ou fabricação de dados. A referência também pode falhar; a
  escolha nessa mesma janela não tem validação independente. Não afirmar que o
  método escolhido garante desempenho futuro ou dimensiona capacidade física.

Essa política altera as sugestões dos agentes, não o retorno bruto da regressão.
Alertas, fila, indicadores e sugestões baseadas no balanço energético observado
permanecem válidos em seu escopo, mesmo quando não se endossa o modelo preditivo.

## Navegação integrada e demonstrações independentes

`codigo_fonte.py` é a entrada principal e `main.py` encaminha à mesma aplicação.
As opções 4, 5 e 7 chamam `executar_analise_integrada(conexao)` e apresentam os
resultados do SQLite; não substituem dados ausentes por uma série demonstrativa.
A opção 7 exibe o fluxo completo, inclusive hash/fila, R1/R2, energia, regressão,
recomendações, impactos e limitações. A opção 4 compara geração −30% com o cenário
base validado. Registro explícito de R1 fica na opção 2; não altera esta análise.
Veja [Navegação](DOC_NAVEGACAO.md).

`simular_consumo_energetico()` e `modelo_linear_previsao()` permanecem auxiliares
independentes: usam os 24 ciclos sintéticos de
`demonstracao_energia.criar_serie_demonstracao` e os mesmos modelos especializados,
sem NumPy/Pandas, gráficos ou banco. Retornam os dicionários dos modelos e imprimem
resultados com unidades. Substituem a antiga senoide/modelagem paralela, mas não
são o fluxo integrado com o CSV nem opções do menu atual.

A ligação dos menus à conexão recebida foi implementada na Etapa 3. Importar
`analise_integrada` ou as entradas não imprime nada nem abre conexões ou bibliotecas gráficas.

## Verificação do escopo

| Referência | Evidência nesta etapa | Complemento da entrega |
|---|---|---|
| Banco e erros — enunciado 1.1 | Consultas reais; testes de conexão/esquema/dados inválidos | CRUD existente continua no menu de dados |
| Lógica — 1.2 | R1/R2 aplicadas às leituras do banco | circuito_logico.pdf preparado na Etapa 4 |
| Estruturas — 1.3 | Hash pesquisado e fila FIFO de registros reais | Menus na Etapa 3; vídeo pendente |
| Simulação e matemática — 1.4 | Modelo compartilhado, E = PΔt, déficit/excedente | Exibição unificada implementada na Etapa 3 |
| Regressão — 1.5 | Exploração, coeficientes, teste temporal, referência e ressalvas | Exibição unificada implementada na Etapa 3 |
| Agentes — 1.6 | Recomendações com os resultados reais e supervisão humana | Roteamento da Etapa 1 e demonstração explícita no menu 6 |
| Arquitetura e socioambiental — 1.7/1.8 | Fluxo local, limites de cobertura, ausência de controle automático | Relatório completo e PDF acadêmico preparados na Etapa 4 |
| Entrega — seção 2 | Exemplo CLI reproduzível e documentação do contrato | ZIP técnico/ensaio na Etapa 4; somente vídeo e publicação/link pendentes |

`PLANO_EQUIPE.md` mantém os responsáveis e registra as branches sequenciais de
finalização. Esta etapa implementa a orquestração; não declara o projeto inteiro
pronto para entrega.

Na Etapa 4, `graficos_ou_imagens/resultado_integrado.json` registra o retorno
completo do CSV e o cenário de geração −30%, com hashes das fontes. Os gráficos
`csv_energia.png` e `csv_regressao.png` usam essa base, não os 24 ciclos da
demonstração independente. O [relatório](relatorio_tecnico.md) consolida resultados
e limitações; [ENTREGA.md](ENTREGA.md) descreve o pacote e as pendências humanas.

Testes específicos:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_analise_integrada.py" -v
```

Cobrem CSV real, cálculos independentes e série manual conhecida, mudança dos
dados, hash/fila, ausência de escritas/transações, persistência explícita idempotente,
vazio, 1/9/10 ciclos, cobertura, unidades, valores inválidos, status atuais,
R² indefinido/previsão negativa, propagação de erros, importação silenciosa,
CLI sem arquivos, regressão melhor/pior/empatada, referência exclusiva do treino,
abstenção sem métricas e repetição dos auxiliares sintéticos. A navegação atual
tem testes próprios em `test_navegacao.py`. Tudo usa bancos em
memória ou diretórios temporários, sem acesso ao banco local.

Validação local da revisão da Etapa 2: **272 testes aprovados** na suíte completa,
dependências sem incompatibilidades (`pip check`), sintaxe e assinaturas contratuais
verificadas. Os oito novos testes desta revisão, além dos cenários reforçados,
cobrem a seleção/abstenção sem alterar os resultados da regressão ou os dados.
Após integração dos menus na Etapa 3: **348 testes aprovados**, incluindo fluxos
das duas entradas em cópias isoladas e comparação dos números exibidos com o CSV.
