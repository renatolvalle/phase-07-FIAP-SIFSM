# **SIFSM - Sistema Integrado de Futuro Sustentável em Marte**

## **FIAP - Ciência da Computação | Fase 07**

- **Colônia:** Aurora Siger
- **Estado:** Em desenvolvimento, com módulos implementados e integração pendente
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
booleanas, simulação computacional, modelagem linear e agentes simulados. A
integração entre todos esses módulos ainda está em andamento.

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
| Menu `main.py` | Executa a simulação/regressão e a demonstração de agentes; a opção de banco ainda não inicia o menu de CRUD |
| Menu `codigo_fonte.py` | Inicializa o banco e abre o gerenciamento de dados; opções especializadas restantes ainda exibem “Funcionalidade em Desenvolvimento” |
| Integração | Os menus e alguns módulos especializados ainda não estão completamente integrados entre si |

O nome atual do módulo de agentes é `agents.py`. O teste
`tests/test_contratos.py` ainda importa `agentes`, então a descoberta completa
dos testes apresenta um erro de importação até que esse contrato seja alinhado.

## **Tecnologias**
- Python: ambiente verificado com **3.12.10** no Windows.
- SQLite, por meio de `sqlite3`, e demais bibliotecas padrão do Python.
- NumPy, Pandas e **Matplotlib 3.11.2**, declarados em `requirements.txt`.

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

### **Executar o menu principal**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B main.py
```

No menu de `main.py`, escolha `2` para executar a simulação energética e a
previsão linear, `3` para executar a demonstração de agentes, ou `4` para sair.
A opção `1` importa `codigo_fonte.py`, mas não inicia o menu de banco de dados.

### **Executar o menu de banco de dados e CRUD**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B codigo_fonte.py
```

Esse menu inicializa o banco SQLite e oferece gerenciamento de módulos,
sensores, leituras e importação dos dados iniciais. As outras opções do menu
principal estão disponíveis como pontos de integração, mas ainda não executam
seus módulos especializados.

O arquivo `aurora_siger.db` é criado automaticamente quando necessário e está
ignorado pelo Git.

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

### **Gerar os dados iniciais**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B gerar_dados_iniciais.py
```

O comando gera `dados_aurora_siger.csv`, com dados simulados para módulos,
sensores e leituras. Executá-lo novamente sobrescreve esse CSV.

## **Menu de Gerenciamento de Dados**

O menu de gerenciamento é aberto ao executar `codigo_fonte.py` diretamente.

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

O Menu Principal mantém as demais opções destinadas aos
módulos especializados do SIFSM.


## **Como Executar os Testes**

Na raiz do repositório, execute o comando solicitado:

```powershell
py -m unittest discover -s tests
```

Se estiver usando o ambiente virtual criado acima, também pode chamar o seu
interpretador diretamente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Para executar com detalhes de cada teste:

```powershell
py -m unittest discover -s tests -v
```

O comando de descoberta atual encontra testes que ainda importam o módulo
`agentes`, embora o arquivo disponível seja `agents.py`. Por esse motivo, a
execução completa atualmente termina com erro de importação em
`test_contratos.py`; os demais testes continuam sendo executados.
Em Linux/macOS, o comando equivalente é `python3 -m unittest discover -s tests`.

Os testes de persistência usam bancos SQLite em memória, e os testes de
arquivos usam diretórios temporários. Os testes da demonstração gráfica
precisam das dependências instaladas por `requirements.txt`.

Para executar apenas os testes de simulação, regressão ou demonstração:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_simulacao_computacional.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_modelo_linear.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_demonstracao_energia.py" -v
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
│   ├── DOC_MONITORAMENTO_ESTRUTURAS.md
│   ├── DOC_SIMULACAO_REGRESSAO.md
│   ├── PLANO_EQUIPE.md
│   └── relatorio_tecnico.md
├── tests/
│   ├── test_banco_dados.py
│   ├── test_contratos.py
│   ├── test_demonstracao_energia.py
│   ├── test_estruturas_dados.py
│   ├── test_gerador_dados.py
│   ├── test_interface.py
│   ├── test_modelo_linear.py
│   ├── test_monitoramento.py
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
| `main.py` | Menu de entrada para a simulação/regressão e a demonstração de agentes |
| `codigo_fonte.py` | Menu de gerenciamento de dados, CRUD e interface SQLite |
| `agents.py` | Simulação de agentes e regras de guardrail |
| `analise_integrada.py` | Demonstração antiga de consumo energético e regressão usada pelo `main.py` |
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
| `tests/` | Nove arquivos de testes automatizados |
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
- Os dois pontos de entrada, `main.py` e `codigo_fonte.py`, ainda não estão
  integrados entre si.

Essas limitações deverão ser consideradas na interpretação
dos resultados e no relatório técnico final.

### **Integração pendente**

- As opções especializadas do menu de `codigo_fonte.py` ainda são pontos de
  integração e não executam os módulos correspondentes.
- A opção de banco de dados do `main.py` importa `codigo_fonte.py`, mas não abre
  seu menu.
- É necessário definir a agregação dos sensores e se a série representa um
  módulo ou toda a colônia antes de conectar `obter_serie_energia()` às análises.
- `tests/test_contratos.py` ainda espera o módulo `agentes`; o arquivo atual é
  `agents.py`, o que causa erro na descoberta completa dos testes.

### **Modelos e resultados**

- A bateria é ideal: não representa perdas, degradação, reserva mínima ou limites de potência.
- A regressão usa uma única separação cronológica; previsões futuras são extrapolações,
  e associação entre ciclo e consumo não implica causalidade.
- Os dados da demonstração são simulados e não representam medições reais de Marte.
- Os resultados apoiam avaliação humana; não executam ações operacionais automaticamente.
