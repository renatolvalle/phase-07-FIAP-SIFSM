# **SIFSM - Sistema Integrado de Futuro Sustentável em Marte**

## **FIAP - Ciência da Computação | Fase 07**

- **Colônia:** Aurora Siger
- **Estado:** Protótipo integrado pelo terminal; documentação final e pacote de entrega pendentes
- **Versão-alvo:** v0.2.0, após revisão e integração na `main`
- **Linguagem:** Python
- **Banco de Dados:** SQLite

## **Integrantes**

| Nome | GitHub | Matrícula |
|------|--------| --------|
| Renato Valle | [@renatolvalle](https://github.com/renatolvalle) | RM 572352
| Renato Nascimento | [@renascience](https://github.com/renascience) | RM 570266
| Alexandre Niewelt | [@QTAlox](https://github.com/QTAlox) | RM 570614
| Danilo Fernandes | [@dandgsf](https://github.com/dandgsf) | RM 570057

## **Link do Repositório**
[renatolvalle/phase-07-FIAP-SIFSM](https://github.com/renatolvalle/phase-07-FIAP-SIFSM)

## **Sobre o Projeto**

O Sistema Integrado de Futuro Sustentável em Marte (SIFSM) é um protótipo acadêmico desenvolvido para organizar informações operacionais da colônia Aurora Siger e auxiliar na utilização sustentável de seus recursos.

O protótipo reúne implementações de banco de dados, estruturas de dados, regras
booleanas, simulação computacional, modelagem linear e agentes simulados. Esses
módulos estão conectados pela análise integrada e pelo menu único de `codigo_fonte.py`.
`main.py` é uma entrada alternativa para a mesma aplicação.

Não será necessário utilizar sensores físicos, APIs externas ou modelos avançados de inteligência artificial.

## **Situação do Desenvolvimento**

O SIFSM foi iniciado com o Scaffold v1.0, que estabeleceu a
estrutura do projeto, os contratos compartilhados, o Menu Principal
e o esquema inicial do banco de dados.

### **Implementação Renato Nascimento**

A implementação de base, persistência e interface foi concluída na branch `dev-renaton`.

Funcionalidades implementadas:

- Inicialização do banco SQLite.
- CRUD completo de módulos.
- Cadastro e listagem de sensores.
- Registro e consulta de leituras.
- Consultas de leituras com filtros por ciclo.
- Agregação de consumo e geração de potência por ciclo.
- Cadastro e listagem de solicitações operacionais.
- Registro de alertas com prevenção de duplicações.
- Geração de dados simulados em CSV.
- Importação de dados com validação e rollback.
- Menu de gerenciamento de dados com nove operações funcionais.
- Tratamento de entradas inválidas e exceções do SQLite.
- Testes automatizados das operações e da interface.

### **Testes**

A suíte automatizada usa `unittest`; veja [Como Executar os Testes](#como-executar-os-testes).

| Componente | Situação atual |
|---|---|
| Banco de dados e CRUD | Persistência SQLite, gerenciamento de módulos, sensores, leituras e importação CSV disponíveis em `codigo_fonte.py` |
| Monitoramento | Regras booleanas e avaliação documentadas em `monitoramento.py` |
| Estruturas de dados | Índice hash, fila, pilha e grafo em `estruturas_dados.py` |
| Simulação e regressão | Implementações em `simulacao_computacional.py` e `modelo_linear.py`; demonstração reproduzível em `demonstracao_energia.py` |
| Agentes | `agents.py` oferece roteamento com guardrail antes do handoff, recomendações baseadas nos resultados e demonstração explícita, sem execução operacional ou persistência |
| Análise integrada | `executar_analise_integrada(conexao)` consulta o banco, aplica R1/R2, organiza hash/fila, simula energia, avalia a regressão e gera recomendações; somente leitura |
| Entrada `main.py` | Encaminha explicitamente para a mesma função principal de `codigo_fonte.py`, sem menu paralelo |
| Menu `codigo_fonte.py` | Entrada principal padronizada: dados, monitoramento, estruturas, simulação, regressão, agentes, sustentabilidade e informações técnicas; opções repetíveis |
| Integração | Fluxo completo disponível no terminal, por função e por demonstração CSV em memória; nenhuma atuação física automática |

## **Tecnologias**
- Python: ambiente verificado com **3.12.10** no Windows.
- SQLite, por meio de `sqlite3`, e demais bibliotecas padrão do Python.
- NumPy, Pandas e **Matplotlib 3.11.2** permanecem declarados em `requirements.txt`.
  A análise integrada e os modelos numéricos usam a biblioteca padrão; Matplotlib
  é carregado apenas na demonstração gráfica. A antiga análise paralela com
  NumPy/Pandas foi substituída pelos modelos compartilhados.

### **Instalação em ambiente virtual**

Execute os comandos na raiz `phase-07-FIAP-SIFSM/`.

**Windows / PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

**Linux / macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

Os comandos usam diretamente o Python do ambiente virtual, sem exigir ativação
ou mudanças na política de execução do PowerShell.

## **Como Executar**

Os exemplos abaixo são executados a partir da raiz do repositório.

### **Executar a aplicação — entrada principal `codigo_fonte.py`**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B codigo_fonte.py
```

Na primeira execução, escolha **1 → 9 → digite `IMPORTAR`** para carregar o CSV
simulado fornecido. Pressione Enter para continuar e `0` para voltar ao principal.
Não há importação automática nem substituição de dados ausentes por exemplos sintéticos.

| Opção principal | Funcionalidade |
|---|---|
| 1 | Gerenciar dados: CRUD de módulos, consultas e importação CSV |
| 2 | Monitorar leituras por ciclo/todos, R1/R2 e tabelas verdade; `REGISTRAR` salva R1 explicitamente |
| 3 | Hash de sensores, cadastro de solicitações, fila FIFO, pilha LIFO e grafo hipotético |
| 4 | Bateria ideal com dados do SQLite e comparação hipotética com geração −30% |
| 5 | Exploração, regressão, métricas no teste, previsões brutas e recomendações com ressalvas |
| 6 | Demonstração explícita de agentes e consulta textual opcional, sem cadastro ou operação |
| 7 | Análise integrada de sustentabilidade com dados do SQLite, resultados e limitações |
| 8 | Configuração, arquitetura computacional, políticas e limitações do protótipo |
| 0 | Encerrar e fechar a conexão |

### **Entrada alternativa**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B main.py
```

Ambos os comandos inicializam o mesmo esquema e abrem o mesmo menu. A navegação
aceita repetição, trata opções inválidas e encerra também com EOF/Ctrl+C, fechando
a conexão. Falha de inicialização informa o erro e retorna código de saída 1.

O arquivo `aurora_siger.db` é criado automaticamente quando necessário e está
ignorado pelo Git.
Para ensaiar sem modificar um banco já existente, use uma cópia da pasta sem esse
arquivo. O roteiro e as políticas de escrita estão em [Navegação](docs/DOC_NAVEGACAO.md).

### **Demonstração dos agentes e guardrails**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B agents.py
```

A demonstração mostra encaminhamento para energia e manutenção, bloqueio de
solicitação sobre suporte vital e encaminhamento humano para assunto fora do
escopo. Pode ser repetida por `agents.demonstrar_agentes()`, sem depender do cache
de importação. Não abre o banco, não cadastra ordens e não controla equipamentos.

`gerar_recomendacoes(indicadores, alertas, simulacao, previsao)` retorna um
dicionário de sugestões e limitações baseado nos resultados recebidos. A validação
humana é obrigatória. Veja os formatos e os limites da triagem por palavras-chave
em [Contratos de integração](docs/CONTRATOS.md#agentspy).

### **Demonstração da simulação e regressão**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B demonstracao_energia.py
```

A demonstração executa diretamente os módulos analíticos, independentemente do
menu e do banco. Ela:

1. Cria 24 ciclos sintéticos de consumo e geração.
2. Simula uma bateria ideal com os parâmetros de `config.py`.
3. Compara o cenário-base com uma redução de 30% na geração.
4. Ajusta a regressão nos primeiros 19 ciclos e avalia nos 5 posteriores.
5. Prevê os próximos 3 ciclos, identificados como extrapolação.
6. Exibe os resultados e salva quatro gráficos PNG e um JSON em `graficos_ou_imagens/`.

Para escolher outro destino:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B demonstracao_energia.py --saida graficos_ou_imagens/ensaio
```

Reexecutar substitui os cinco arquivos de mesmo nome no destino. A geração usa
backend não interativo; não abre janelas. Importar os módulos não executa a demonstração.

Nos comandos de execução e testes, em Linux/macOS, substitua
`.\.venv\Scripts\python.exe` por `.venv/bin/python`.
`-X utf8` uniformiza a codificação da saída e `-B` evita arquivos de bytecode.

As fórmulas, os contratos de retorno e os resultados estão detalhados em
[Simulação e regressão](docs/DOC_SIMULACAO_REGRESSAO.md).

### **Análise integrada com o CSV do projeto**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B analise_integrada.py
```

Esse comando importa `dados_aurora_siger.csv` em um SQLite **em memória**, executa
o fluxo completo e imprime o resultado em JSON. Não abre o banco local nem gera
arquivos. Na base fornecida: 5 módulos, 10 sensores, 320 leituras, 32 ciclos e
19 alertas calculados. A regressão usa 25 ciclos de treino e 7 de teste, prevendo
os ciclos 33–35. Importar o módulo não executa a demonstração.

Para analisar o banco já inicializado pela aplicação:

```python
from contextlib import closing
from banco_dados import abrir_conexao
from analise_integrada import executar_analise_integrada

with closing(abrir_conexao()) as conexao:
    resultado = executar_analise_integrada(conexao)
    print(resultado["indicadores"])
    print(resultado["recomendacoes"])
    print(resultado["limitacoes"])
```

O exemplo pressupõe o esquema existente; `abrir_conexao()` cria o arquivo se
ausente, mas a análise não cria tabelas nem importa dados automaticamente.
Ela não grava alertas, não cria/atende solicitações e não confirma transações.
Sem energia, retorna simulação/previsão vazias; com menos de 10 ciclos, apenas
a previsão fica indisponível. Leituras energéticas incompletas ou inválidas
geram erro, em vez de serem substituídas por zero.

**Qualidade da previsão:** na base CSV atual a regressão não supera a média do
treino pelo MAE. As previsões e métricas da reta são preservadas para inspeção,
mas não fundamentam recomendações de pico/tendência. A sugestão usa a média dos
25 ciclos de treino, **5,344 kW**, como referência constante por ciclo, não como
pico nem garantia de atendimento. A mesma proteção vale para empate e previsões
negativas no teste/futuro. Sem avaliação completa ou referência necessária, o
sistema se abstém de recomendar estimativas preditivas; nunca substitui a média
do treino pela média global. A comparação nessa janela não garante desempenho
futuro e toda sugestão exige validação humana.

Veja [Análise integrada](docs/DOC_ANALISE_INTEGRADA.md) para políticas de cobertura,
unidades, persistência explícita, resultados e limitações. As opções 4, 5 e 7
usam essa análise validada; não utilizam os 24 ciclos da demonstração independente.

### **Gerar os dados iniciais**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B gerar_dados_iniciais.py
```

O comando gera `dados_aurora_siger.csv`, com dados simulados para módulos,
sensores e leituras. Executá-lo novamente sobrescreve esse CSV.

## **Menu de Gerenciamento de Dados**

O menu de gerenciamento é aberto pela **opção 1** do menu principal.

| Opção | Funcionalidade |
|---|---|
| 1 | Listar módulos |
| 2 | Cadastrar módulo |
| 3 | Buscar módulo pelo código |
| 4 | Atualizar módulo |
| 5 | Excluir módulo |
| 6 | Listar sensores |
| 7 | Consultar leituras |
| 8 | Consultar série energética |
| 9 | Importar dados iniciais |
| 0 | Voltar ao Menu Principal |

O CRUD de módulos permite inserir, consultar, atualizar e excluir
registros por meio do terminal.

A exclusão exige confirmação explícita e respeita as
restrições de integridade referencial do banco de dados.

As consultas de sensores, leituras e dados energéticos utilizam
as funções compartilhadas de `banco_dados.py`.

No submenu de estruturas (principal → 3), as opções 1–5 oferecem busca hash,
cadastro de solicitação, fila FIFO, pilha e grafo. A fila temporária não conclui
solicitações no SQLite; a pilha não desfaz CRUD; as dependências do grafo são
hipotéticas e só incluem módulos cadastrados. Alertas são calculados e podem ser
registrados no monitoramento (principal → 2), sem duplicar registros idênticos.


## **Como Executar os Testes**

Na raiz do repositório, execute o comando solicitado:

```powershell
py -m unittest discover -s tests
```

Esse comando precisa usar um Python com as dependências de `requirements.txt`
instaladas. Se elas foram instaladas no ambiente virtual do projeto, rode os
testes com o interpretador desse ambiente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Para instalar as dependências no Python selecionado pelo launcher `py`, use
`py -m pip install -r requirements.txt` antes de executar o comando inicial.

Para executar com detalhes de cada teste:

```powershell
py -m unittest discover -s tests -v
```

Em Linux/macOS, o comando equivalente é `python3 -m unittest discover -s tests`.

Os testes de persistência usam bancos SQLite em memória, e os testes de
arquivos usam diretórios temporários. Os testes da demonstração gráfica
precisam das dependências instaladas por `requirements.txt`.
Os testes de CLI copiam os módulos, SQL e CSV para uma pasta temporária, pois o
caminho do banco é relativo a `config.py`, não ao diretório de execução. Não
acessam o banco local. Validação da Etapa 3: **348 testes aprovados**.

Para executar apenas os testes de simulação, regressão ou demonstração:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_simulacao_computacional.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_modelo_linear.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_demonstracao_energia.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_analise_integrada.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_navegacao.py" -v
```

## **Estrutura do Projeto**

```text
phase-07-FIAP-SIFSM/
├── .gitignore
├── agents.py
├── analise_integrada.py
├── banco_aurora_siger.sql
├── banco_dados.py
├── codigo_fonte.py
├── config.py
├── dados_aurora_siger.csv
├── demonstracao_energia.py
├── estruturas_dados.py
├── gerar_dados_iniciais.py
├── main.py
├── modelo_linear.py
├── monitoramento.py
├── README.md
├── requirements.txt
├── simulacao_computacional.py
├── docs/
│   ├── CONTRATOS.md
│   ├── DOC_ANALISE_INTEGRADA.md
│   ├── DOC_MONITORAMENTO_ESTRUTURAS.md
│   ├── DOC_NAVEGACAO.md
│   ├── DOC_SIMULACAO_REGRESSAO.md
│   ├── PLANO_EQUIPE.md
│   └── relatorio_tecnico.md
├── tests/
│   ├── test_agents.py
│   ├── test_analise_integrada.py
│   ├── test_banco_dados.py
│   ├── test_contratos.py
│   ├── test_demonstracao_energia.py
│   ├── test_estruturas_dados.py
│   ├── test_gerador_dados.py
│   ├── test_interface.py
│   ├── test_interface_estruturas.py
│   ├── test_interface_monitoramento.py
│   ├── test_interface_pilha_grafo.py
│   ├── test_interface_simulacao.py
│   ├── test_modelo_linear.py
│   ├── test_monitoramento.py
│   ├── test_navegacao.py
│   └── test_simulacao_computacional.py
└── graficos_ou_imagens/
    ├── bateria_e_soc.png
    ├── demonstracao_energia.json
    ├── potencias_por_ciclo.png
    ├── regressao_consumo.png
    └── residuos_teste.png
```

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Entrada alternativa, sem fluxo ou menu próprio |
| `codigo_fonte.py` | Arquivo principal: navegação integrada, apresentações, CRUD e ciclo de vida da conexão |
| `agents.py` | Simulação de agentes e regras de guardrail |
| `analise_integrada.py` | Orquestração somente de leitura com conexão recebida; demonstração CSV em memória e auxiliares sintéticos independentes dos menus |
| `config.py` | Configurações compartilhadas |
| `banco_dados.py` | Persistência e operações SQLite |
| `banco_aurora_siger.sql` | Esquema relacional do banco |
| `gerar_dados_iniciais.py` | Geração dos dados simulados |
| `dados_aurora_siger.csv` | Dados iniciais simulados usados pela importação |
| `monitoramento.py` | Regras booleanas e monitoramento |
| `estruturas_dados.py` | Estruturas de dados operacionais |
| `simulacao_computacional.py` | Simulação energética |
| `modelo_linear.py` | Modelagem e regressão linear |
| `demonstracao_energia.py` | Demonstração reproduzível, comparação de cenários, gráficos e JSON |
| `requirements.txt` | Dependências externas para os módulos analíticos e gráficos |
| `tests/` | Dezesseis arquivos de testes automatizados |
| `docs/` | Contratos, documentação técnica, plano da equipe e relatório |
| `graficos_ou_imagens/` | Gráficos e resultados JSON da demonstração |

### **Banco de dados**

O SQLite utiliza cinco tabelas:

- `modulos`
- `sensores`
- `leituras`
- `alertas`
- `solicitacoes`

O arquivo `aurora_siger.db` é gerado localmente e não deve ser
versionado no Git.

O esquema compartilhado está em `banco_aurora_siger.sql`.


## **Organização da Equipe**

Cada integrante desenvolve seus módulos seguindo os contratos compartilhados:

| Integrante | Responsabilidade | Branch |
|---|---|---|
| Renato Nascimento | Menu, configuração, banco e dados | `dev-renaton` |
| Renato Valle | Monitoramento e estruturas de dados | `dev-renatov` |
| Danilo Fernandes | Simulação, integração matemática e regressão | `dev-danilo` |
| Alexandre Niewelt | Agentes, análise integrada e consolidação da documentação | `dev-alex` |

Documentação:
- [Contratos de integração](docs/CONTRATOS.md).
- [Plano da equipe](docs/PLANO_EQUIPE.md).
- [Monitoramento e estruturas](docs/DOC_MONITORAMENTO_ESTRUTURAS.md).
- [Simulação e regressão](docs/DOC_SIMULACAO_REGRESSAO.md).
- [Análise integrada](docs/DOC_ANALISE_INTEGRADA.md).
- [Navegação e demonstração pelo terminal](docs/DOC_NAVEGACAO.md).
- [Relatório técnico](docs/relatorio_tecnico.md).

## **Regras de Desenvolvimento**

- Manter os contratos de integração.
- Utilizar nomes em snake_case.
- Evitar código duplicado.
- Documentar funções importantes.
- Não executar operações SQL fora de banco_dados.py.
- Executar os testes antes de integrar alterações.
- Não modificar interfaces compartilhadas sem comunicar à equipe.

### **Versionamento**

O próximo marco planejado é **v0.2.0**, reunindo as funcionalidades atuais após
revisão e integração. Esse é um alvo de desenvolvimento, não uma release já publicada.

O fluxo previsto é: branch de trabalho → commits por funcionalidade → testes →
Pull Request e revisão → integração na `main`. Tags identificam marcos integrados
e validados do projeto, não cada branch ou integrante. A versão `v1.0.0` fica
reservada à entrega completa validada pela equipe.

## **Entrega Final**

Ao término do projeto, serão preparados os arquivos exigidos pela Fase 07, incluindo relatório técnico, dados simulados, representação lógica, apresentação em vídeo e pasta ZIP.

O vídeo terá duração máxima de cinco minutos e será publicado no YouTube como "Não listado".


## **Limitações Atuais**

O SIFSM é um protótipo acadêmico desenvolvido para demonstrar
conceitos de Ciência da Computação aplicados a uma colônia
marciana simulada.

### **Dados Simulados**

- Os sensores não correspondem a dispositivos físicos reais.
- As medições são geradas por expressões matemáticas determinísticas.
- Os valores não representam medições reais de Marte.
- A duração padrão do ciclo é uma hora simulada.
- A curva solar utiliza uma aproximação ilustrativa de 24 horas
  terrestres, não o ciclo solar exato de Marte.

### **Consultas e Modelagem**

- Os campos `consumo_kw` e `geracao_kw` representam potência.
- A energia em kWh depende da duração do ciclo.
- O banco não registra o histórico completo das mudanças de
  status operacional de módulos e sensores.
- A série energética preserva leituras anteriores, mesmo que
  os dispositivos tenham sido posteriormente desativados.

### **Arquitetura**

- O protótipo utiliza SQLite local.
- Não depende de sensores físicos ou serviços externos.
- Não implementa controle físico de equipamentos marcianos.
- Os dois pontos de entrada compartilham a mesma aplicação, sem autenticação
  ou controle de acesso multiusuário; o arquivo SQLite deve ser protegido localmente.

Essas limitações deverão ser consideradas na interpretação
dos resultados e no relatório técnico final.

### **Escopo integrado e finalização pendente**

- As oito opções do menu estão conectadas, sem placeholders. Consultar agentes
  executa a demonstração explicitamente em cada visita, sem depender do cache de importação.
- A análise já usa `obter_serie_energia()`: soma por ciclo dos sensores energéticos
  com leituras, de todos os módulos. Cobertura parcial e status atuais têm as
  limitações descritas no contrato; não se presume medição de toda a colônia real.
- R1/R2 podem ser consultadas sem série energética completa. Simulação, regressão
  e análise integrada rejeitam cobertura parcial, medidas/unidades inválidas.
- O relatório técnico ainda é um rascunho com divergências conhecidas (esquema,
  RAG/automação e descrição dos modelos); sua revisão completa pertence à Etapa 4.
- Representação lógica em arquivo, vídeo/link e ZIP reproduzível ainda precisam
  ser preparados/conferidos. A navegação concluída não equivale à entrega final concluída.

### **Modelos e resultados**

- A bateria é ideal: não representa perdas, degradação, reserva mínima ou limites de potência.
- A regressão usa uma única separação cronológica; previsões futuras são extrapolações,
  e associação entre ciclo e consumo não implica causalidade.
- Os dados da demonstração são simulados e não representam medições reais de Marte.
- Os resultados apoiam avaliação humana; não executam ações operacionais automaticamente.
