# Simulação energética e regressão linear

**SIFSM — Aurora Siger · Responsável: Danilo Fernandes**

Implementação local dos requisitos de simulação computacional, integração matemática
e modelagem linear. As funções recebem listas de dicionários e podem ser utilizadas
independentemente do banco e do menu.

As assinaturas e chaves principais seguem [CONTRATOS.md](CONTRATOS.md).
Os campos internos são usados por `agents.py` e `analise_integrada.py`, conforme
o complemento de contrato da Etapa 2. A regressão fornece resultados para inspeção;
a política de uso nas recomendações não modifica os coeficientes nem suas métricas.

## 1. Arquivos e execução

| Arquivo | Finalidade |
|---|---|
| `simulacao_computacional.py` | Validação da série, integração de potência e balanço da bateria |
| `modelo_linear.py` | Mínimos quadrados, avaliação cronológica e previsão |
| `demonstracao_energia.py` | Base didática de 24 ciclos, comparação de cenários e gráficos |
| `tests/test_simulacao_computacional.py` | Cálculos manuais, conservação e validações |
| `tests/test_modelo_linear.py` | Coeficientes, métricas, separação temporal e validações |
| `tests/test_demonstracao_energia.py` | Reprodutibilidade, importação e geração das evidências |
| `requirements.txt` | Dependência dos gráficos |
| `graficos_ou_imagens/` | Quatro gráficos PNG e resultados completos em JSON |

### Ambiente virtual

Na raiz do projeto, em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -B demonstracao_energia.py
```

Não é necessário ativar o ambiente nem alterar a política do PowerShell. `-X utf8`
uniformiza a codificação da saída; `-B` evita arquivos de bytecode.
Em Linux/macOS, substituir o executável por `.venv/bin/python`.

Ambiente verificado: **Python 3.12.10, Windows, Matplotlib 3.11.2**.
O NumPy 2.5.4 foi instalado como dependência transitiva do Matplotlib.
`pip check` não identificou dependências incompatíveis.

A simulação e a regressão usam somente a biblioteca padrão do Python. Mínimos
quadrados foram implementados diretamente para tornar as fórmulas verificáveis;
não é necessário instalar uma biblioteca estatística para executar os cálculos.

O destino padrão da demonstração é `graficos_ou_imagens/`, relativo à raiz do
projeto. Para escolher outro destino:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B demonstracao_energia.py --saida graficos_ou_imagens/ensaio
```

Reexecutar substitui os cinco arquivos de mesmo nome no destino. A importação dos
módulos não gera arquivos, abre janelas ou executa a demonstração. Matplotlib é
carregado somente ao gerar os gráficos, com backend `Agg`; cada figura é fechada
em `finally`, inclusive se a gravação falhar.

## 2. Entrada, unidades e validações

```python
serie = [
    {"ciclo": 1, "consumo_kw": 6.0, "geracao_kw": 4.0},
    {"ciclo": 2, "consumo_kw": 2.0, "geracao_kw": 5.0},
]
```

| Campo/grandeza | Interpretação |
|---|---|
| `ciclo` | Inteiro positivo, único; ordena a sequência e é a variável explicativa da regressão |
| `consumo_kw`, `geracao_kw` | Potências **médias durante o ciclo**, em kW |
| `horas_por_ciclo` | Duração constante dos registros, em horas; padrão de `config.py`: 1 h |
| Energia | kWh; potência multiplicada pela duração |
| SoC | Estado de carga: energia armazenada / capacidade × 100, em % |

As duas funções aceitam iteráveis de dicionários, inclusive geradores. Criam e
ordenam uma cópia, sem alterar a entrada. Campos adicionais são ignorados.
As potências devem ser números reais (`numbers.Real`, como `int` e `float`),
finitos e não negativos. Strings numéricas, valores complexos, `None`, booleanos,
NaN e infinito são rejeitados. Ciclos usam inteiros (`numbers.Integral`), sem
aceitar `1.0` ou booleanos. Campos ausentes, duplicatas e estruturas incorretas
também produzem **`ValueError` com mensagem identificando o problema**.

As validações comuns ficam em auxiliares privados de `simulacao_computacional.py`
e são reutilizadas por `modelo_linear.py`. Não há dependência do banco.

Lacunas são aceitas: os ciclos 2 e 9 representam **dois registros**, cada um com
`horas_por_ciclo`; não se cria demanda, geração ou passagem adicional de tempo
para os identificadores ausentes. Na regressão, os valores numéricos 2 e 9 são
preservados como X. Se a lacuna representar horas reais sem medição, a série
precisará ser tratada pelo produtor dos dados antes de uma análise operacional.

Os cálculos usam ponto flutuante: pequenas diferenças binárias são esperadas.
Não se arredondam os retornos analíticos; apenas a apresentação e a construção
da base didática. Transbordamentos detectados de produtos, somas, coeficientes
ou previsões são rejeitados, em vez de retornar infinitos.

## 3. Simulação e integração matemática

```python
simular_balanco_energetico(
    serie_energia,
    capacidade_kwh=CAPACIDADE_BATERIA_KWH,
    carga_inicial_kwh=CARGA_INICIAL_KWH,
    horas_por_ciclo=HORAS_POR_CICLO,
)
```

Os padrões vêm de `config.py`: bateria de **20 kWh**, energia inicial de **12 kWh**
e duração de **1 hora por ciclo**. Exige-se capacidade e duração positivas, e
carga inicial entre zero e a capacidade, inclusive.

### Integral da potência

Para cada intervalo de duração Δt:

```text
consumo_kwh = consumo_kw × Δt
geracao_kwh = geracao_kw × Δt
energia acumulada ≈ Σ P_i Δt
```

É a soma de áreas de retângulos. Para médias exatas dos intervalos, `P_i Δt`
reproduz a energia do intervalo. O balanço da bateria continua sendo um modelo
agregado, pois não conhece a ordem das oscilações dentro de cada ciclo.

Não se usa a regra dos trapézios: ela trataria os valores como amostras
instantâneas nas bordas, diferente da semântica adotada. Subdividir uma mesma
média sem novas observações não melhora a resolução dos dados.

### Atualização do estado

Seja `E_inicial` a energia armazenada no início do registro:

```text
Se geração >= consumo:
    saldo = geração - consumo
    carga_recebida = min(saldo, capacidade - E_inicial)
    excedente = saldo - carga_recebida
    E_final = E_inicial + carga_recebida
    déficit = 0

Se consumo > geração:
    demanda = consumo - geração
    descarga_fornecida = min(demanda, E_inicial)
    déficit = demanda - descarga_fornecida
    E_final = E_inicial - descarga_fornecida
    excedente = 0
```

Todas as parcelas acima são energias em kWh. A geração atende o consumo do
próprio ciclo antes da bateria. O estado fica em `[0, capacidade]`, e o saldo
que não cabe na bateria ou não pode ser fornecido é contabilizado explicitamente.

A identidade de conservação, verificada nos testes, é:

```text
E_inicial + geração + déficit = E_final + consumo + excedente
```

O déficit no lado esquerdo é uma compensação **contábil da demanda não atendida**,
não uma fonte física de energia. A energia realmente atendida é `consumo - déficit`.
O estado final de um ciclo é o estado inicial do seguinte. Cada uma das N linhas
contém ambos os estados, preservando os N+1 estados sem acrescentar um ciclo fictício.

### Retorno

Chaves principais: **`historico`** (lista) e **`resumo`** (dicionário).

Cada linha de `historico` contém:

| Campos | Unidade/significado |
|---|---|
| `ciclo` | Identificador original |
| `consumo_kw`, `geracao_kw` | Potências médias em kW |
| `consumo_kwh`, `geracao_kwh` | Energias integradas no intervalo |
| `energia_inicial_kwh`, `energia_final_kwh` | Estados da bateria |
| `soc_inicial_pct`, `soc_final_pct` | Estados de carga em % |
| `carga_recebida_kwh`, `descarga_fornecida_kwh` | Fluxos da bateria no intervalo |
| `deficit_nao_atendido_kwh` | Demanda que geração e bateria não supriram |
| `excedente_nao_armazenado_kwh` | Geração restante que não coube na bateria |

O `resumo` contém:

| Campos | Definição |
|---|---|
| `quantidade_ciclos` | Número de registros processados |
| `consumo_total_kwh`, `geracao_total_kwh` | Somas das energias dos ciclos |
| `pico_consumo_kw`, `pico_geracao_kw` | Maiores potências médias registradas, não picos instantâneos |
| `energia_inicial_kwh`, `energia_final_kwh` | Estado antes e depois da série |
| `soc_minimo_pct`, `soc_final_pct` | Mínimo incluindo o estado inicial, e estado final |
| `carga_recebida_total_kwh`, `descarga_fornecida_total_kwh` | Somas dos fluxos da bateria |
| `deficit_total_kwh`, `excedente_total_kwh` | Somas da demanda não atendida e da geração descartada |
| `atendimento_percentual` | `100 × (1 - déficit_total / consumo_total)` |

**Consumo total zero:** atendimento de 100% por convenção, pois não há demanda a
suprir. **Série vazia:** `historico=[]`, quantidade, picos e totais zerados, carga
final igual à inicial, SoC mínimo/final iguais ao inicial e atendimento de 100%.

### Exemplo manual

```python
from simulacao_computacional import simular_balanco_energetico

resultado = simular_balanco_energetico(
    [{"ciclo": 1, "consumo_kw": 6, "geracao_kw": 4}],
    capacidade_kwh=20, carga_inicial_kwh=12, horas_por_ciclo=1,
)
print(resultado["historico"][0]["energia_final_kwh"])  # 10.0
print(resultado["resumo"]["soc_final_pct"])           # 50.0
```

Consumo de 6 kWh, geração de 4 kWh, descarga de 2 kWh, energia final de 10 kWh,
SoC de 50% e nenhum déficit não atendido. Com duração de 0,25 h, seriam 1,5 kWh
consumidos, 1 kWh gerado e energia final de 11,5 kWh.

### Hipóteses físicas

Bateria ideal, sem perdas de carga/descarga, degradação, autodescarga, reserva
mínima ou limite de potência. A capacidade é finita, mas não há dados de corrente,
tensão, temperatura ou tecnologia da bateria. O balanço por médias não detecta
picos nem interrupções dentro do intervalo. Portanto, o resultado é didático e
não constitui dimensionamento de um sistema físico real.

## 4. Regressão linear com avaliação cronológica

```python
avaliar_e_prever_consumo(
    serie_energia,
    horizonte_ciclos=HORIZONTE_PREVISAO_CICLOS,
)
```

O horizonte padrão de `config.py` é **3 ciclos**. Deve ser inteiro positivo e não
booleano. A função exige **pelo menos 10 observações**; vazio e séries menores
geram `ValueError`. A geração também é validada por integrar o formato da série,
mas não é utilizada como variável explicativa.

Pergunta: **qual tendência linear relaciona o ciclo ao consumo médio?**

```text
X = ciclo
y = consumo_kw
ŷ = a + bX
b = Σ((X - média_X)(y - média_y)) / Σ((X - média_X)²)
a = média_y - b × média_X
```

As médias das fórmulas são calculadas **somente no treino**. O cálculo desloca e
centraliza os ciclos para reduzir cancelamento numérico. A equação retornada
continua usando o ciclo original.

1. Validar e ordenar a cópia da série.
2. Obter quantidade, mínimo, máximo e média do consumo para descrição exploratória.
3. Separar os primeiros `floor(0.8 × n)` registros para treino e os demais para teste.
4. Ajustar a reta e a referência constante exclusivamente no treino.
5. Calcular as métricas exclusivamente no teste posterior.
6. Prever de `ultimo_ciclo + 1` até `ultimo_ciclo + horizonte_ciclos`, mantendo a
   mesma reta avaliada, sem novo ajuste em todos os registros.

Com o mínimo de 10 registros, a divisão é 8/2; com 24, é 19/5. Sempre há ao menos
dois registros em cada parte. Não há embaralhamento, imputação ou padronização.
Os indicadores exploratórios da série completa não são usados no ajuste.

### Métricas e interpretação

```text
resíduo = consumo real - consumo previsto
MAE = média(|resíduo|)
RMSE = raiz(média(resíduo²))
R² = 1 - Σ(resíduo²) / Σ((real_teste - média_real_teste)²)
referência = média do consumo de treino, repetida para cada ciclo de teste
MAE_referência = média(|real_teste - referência|)
```

- **MAE e RMSE:** kW; menores indicam menor erro. RMSE dá mais peso a erros grandes.
- **R²:** adimensional, não é porcentagem de acertos. Pode ser negativo: nesse
  caso, o erro quadrático supera o da constante igual à média do próprio teste.
  Essa interpretação não se confunde com a baseline operacional, que usa o treino.
- **Teste constante:** R² retorna `None`, com explicação em `limitacoes`. A mesma
  política vale se a variância do teste não for representável numericamente.
- **Intercepto `a`:** estimativa matemática no ciclo zero, sem significado físico
  garantido fora do intervalo observado.
- **Inclinação `b`:** variação estimada em kW por ciclo; associação, não causalidade.
- **Previsões negativas:** preservadas, com aviso em `limitacoes`, inclusive se
  ocorrerem no período de teste. Não são consumos fisicamente válidos. A quantidade
  de negativas no teste é exposta para que os agentes não endossem essa reta.

### Retorno

| Chave principal | Conteúdo |
|---|---|
| `coeficientes` | `intercepto_kw`, `inclinacao_kw_por_ciclo` |
| `metricas` | `quantidade_total`, `quantidade_treino`, `quantidade_teste`, `consumo_minimo_kw`, `consumo_maximo_kw`, `consumo_medio_kw`, `consumo_medio_treino_kw`, `mae_kw`, `rmse_kw`, `r2`, `mae_referencia_kw`, `quantidade_previsoes_negativas_teste` |
| `previsoes` | Lista de `{ciclo, consumo_previsto_kw, extrapolacao: True}` |
| `limitacoes` | Lista de textos com ressalvas de interpretação |

As limitações incluem a origem simulada quando aplicável, avaliação temporal
única, extrapolação, intercepto, ausência de causalidade e de variáveis como clima,
ocupação e manutenção. Menos de 30 observações dispara uma observação didática
de amostra pequena; esse limiar não é uma garantia estatística para bases maiores.
A função não consegue inferir a procedência da série. A demonstração identifica
expressamente seus dados sintéticos.

### Uso dos resultados nas recomendações

`consumo_medio_treino_kw` é a referência calculada só no treino, não a média global
`consumo_medio_kw`. Os agentes recomendam o pico/tendência da reta apenas se o MAE
for estritamente menor que o da referência e não houver negativas no teste/futuro.
Quando a reta empata/perde ou é fisicamente inválida, a sugestão usa a média do
treino como estimativa constante de referência, sem chamá-la de pico. Avaliação
incompleta, previsões ausentes ou referência necessária mas não informada levam
à abstenção, sem reconstruir a média usando dados de teste.

Isso não substitui `previsoes`, coeficientes ou métricas da regressão: preserva a
avaliação acadêmica mesmo em bases sem tendência útil. A seleção usa o mesmo teste
temporal e não tem avaliação independente; menor erro nesse recorte não é garantia
futura. Consulte [Análise integrada](DOC_ANALISE_INTEGRADA.md) para o resultado
do CSV do projeto, em que a referência supera a regressão.

## 5. Demonstração reproduzível e resultados

`criar_serie_demonstracao()` gera 24 ciclos, sem sorteio:

```text
consumo(ciclo) = 4,5 + 0,12 × ciclo + variação
variações repetidas = [-0,25; 0,10; 0,20; -0,10; 0,05; -0,15; 0,30; -0,05]
```

Os valores são arredondados a duas casas na construção da base. A geração segue
um perfil fixo definido na função, com valores entre 2,5 e 8,2 kW. São dados
criados para testar carga, saturação, descarga e esgotamento, sem pretensão de
representar o ciclo solar marciano. A série integral está no JSON gerado.

O cenário de estresse reduz **apenas a geração em 30%**. Os parâmetros da bateria,
a duração e o consumo permanecem iguais para permitir a comparação.

Resultados verificados em 07/11/2026, com os padrões atuais de `config.py`:

| Indicador | Base | Estresse |
|---|---:|---:|
| Consumo total (kWh) | 144,30 | 144,30 |
| Geração total (kWh) | 143,40 | 100,38 |
| Pico de consumo médio (kW) | 7,56 | 7,56 |
| Pico de geração média (kW) | 8,20 | 5,74 |
| Energia inicial (kWh) | 12,00 | 12,00 |
| Energia final (kWh) | 2,55 | 0,00 |
| SoC mínimo (%) | 0,00 | 0,00 |
| SoC final (%) | 12,75 | 0,00 |
| Carga recebida total (kWh) | 10,55 | 2,28 |
| Descarga fornecida total (kWh) | 20,00 | 14,28 |
| Déficit não atendido (kWh) | 5,50 | 31,92 |
| Excedente não armazenado (kWh) | 14,05 | 0,00 |
| Atendimento (%) | 96,19 | 77,88 |

Mesmo no cenário-base, a proximidade entre geração e consumo **totais** não garante
atendimento: há excedente descartado no início e déficit em ciclos posteriores.
A bateria chega a zero ao final do ciclo 18 na base e do ciclo 14 no estresse.
Isso justifica estudar armazenamento e distribuição temporal da demanda antes
de propor mudanças operacionais. O modelo não executa essas mudanças.

### Resultados da regressão

Análise exploratória: **24 observações**, consumo mínimo **4,37 kW**, máximo
**7,56 kW** e média **6,0125 kW**. O gráfico mostra tendência crescente com
variação; não se trata de uma reta perfeita.

```text
Treino: ciclos 1–19       Teste: ciclos 20–24
consumo_previsto_kw = 4,477193 + 0,123596 × ciclo
MAE do teste = 0,142351 kW
RMSE do teste = 0,164522 kW
R² do teste = 0,618767
MAE da referência = 1,436842 kW
```

A tendência ajustada equivale a um aumento estimado de aproximadamente
**0,124 kW por ciclo**. Nesta divisão, a reta tem MAE inferior à referência
constante. O resultado depende da tendência inserida na base sintética e não
comprova desempenho em dados reais. R² de 0,619 não significa 61,9% de acertos.

| Ciclo futuro | Consumo previsto (kW) |
|---|---:|
| 25 | 7,567105 |
| 26 | 7,690702 |
| 27 | 7,814298 |

Todos são extrapolações. Os resíduos dos ciclos 20–24 são, respectivamente,
aproximadamente **−0,149123; −0,002719; −0,206316; +0,240088; −0,113509 kW**.
Resíduo positivo significa subestimação; negativo, superestimação. Cinco pontos
de teste não permitem concluir estabilidade, independência ou normalidade dos erros.

### Evidências geradas

- [Potências por ciclo](../graficos_ou_imagens/potencias_por_ciclo.png): barras de consumo e geração, em kW.
- [Energia e SoC](../graficos_ou_imagens/bateria_e_soc.png): comparação dos estados da bateria nos dois cenários.
- [Regressão](../graficos_ou_imagens/regressao_consumo.png): observações, treino/teste, reta e previsões.
- [Resíduos do teste](../graficos_ou_imagens/residuos_teste.png): diferenças entre consumo real e previsto.
- [Dados e resultados completos](../graficos_ou_imagens/demonstracao_energia.json): séries de entrada, históricos, resumos e regressão.

As evidências versionadas registram a demonstração de 07/11/2026. Novas execuções
incluem também os dois campos de avaliação adicionados na Etapa 2; os resultados
numéricos originais da reta e da simulação não foram alterados por esse complemento.

No gráfico da bateria, zero marca o estado inicial, não um registro de entrada.
As linhas ligam estados conhecidos ao final dos ciclos para facilitar leitura;
não são medições intermediárias nem refinamento da simulação.

## 6. Verificação

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_simulacao_computacional.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_modelo_linear.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
```

Validação inicial de 07/11/2026: **102 testes aprovados**, sendo 58 existentes, 22 da simulação,
19 da regressão e 3 da demonstração. Os testes novos foram criados antes das
implementações numéricas e inicialmente confirmaram os respectivos stubs.

Na revisão da Etapa 2, a suíte completa passou a **272 testes aprovados**, incluindo
a escolha da referência, abstenção, métricas preservadas, negativas no teste/futuro
e comprovação de que a média do treino não utiliza as observações de teste.

Cobertura funcional:

- Exemplo manual, equilíbrio, carga/descarga, saturação, déficit, integração com
  duração fracionária e conservação por ciclo em uma série determinística de 100 ciclos.
- Limites, encadeamento de estados, resumo, atendimento, série vazia, ausência
  de mutação, lacunas e geradores.
- Campos obrigatórios, duplicatas, tipos, booleanos, valores negativos,
  não finitos e transbordamento de energia.
- Coeficientes em séries perfeitas e com variação, métricas verificadas à mão,
  separação 8/2 e 19/5, R² negativo e indefinido e previsão negativa.
- Alterar somente o teste não altera coeficientes nem previsões: evidência
  contra vazamento temporal e contra reajuste posterior em toda a série.
- Importação em processo separado sem saída, arquivos ou biblioteca gráfica;
  quatro PNGs válidos, JSON coerente e figuras fechadas.

Sem Matplotlib, somente o teste de geração de imagens é pulado com mensagem de
instalação. A validação completa acima foi executada no ambiente virtual com a
dependência instalada, **sem testes pulados**. Os quatro gráficos também foram
inspecionados visualmente.

## 7. Integração e pendências da equipe

1. **Alexandre:** alinhar os campos internos deste documento antes de consumir
   os resultados em agentes e análise integrada.
2. **Renato Nascimento:** fornecer a série agregada em `obter_serie_energia()`;
   definir com a equipe se representa um módulo ou toda a colônia e como agrega
   sensores de consumo e geração, mantendo as unidades e a duração.
3. **Equipe:** conectar menu/banco/análise e consolidar este material no relatório
   técnico e vídeo. O README já contém dependências, comandos, estrutura e estado
   desta revisão; mantê-lo atualizado conforme a integração avançar.
4. A demonstração local é executável, mas não atesta o fluxo completo do sistema;
   a integração depende das implementações dos demais módulos.

Possíveis extensões após alinhamento: perdas, limites de potência, reserva mínima,
degradação, dados adicionais e avaliação temporal em mais janelas. Qualquer
extensão deve manter explícita a contabilidade energética e a separação entre
avaliação e ajuste.
