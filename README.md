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

A solução integrará banco de dados, estruturas de dados, regras booleanas, simulação computacional, modelagem linear e agentes simulados para apoiar decisões operacionais.

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

A implementação feita por Renato Nascimento possui uma suíte com
100 testes automatizados previstos e revisados.

A execução pode ser realizada com:

`python3 -B -m unittest discover -s tests -v`

### **Integração com a equipe**

O projeto também prevê:

- Monitoramento e regras booleanas.
- Estruturas de dados operacionais.
- Simulação computacional energética.
- Regressão linear.
- Agentes especializados simulados.
- Análise integrada de sustentabilidade.

Essas funcionalidades pertencem às demais frentes de desenvolvimento e devem ser validadas durante a integração das branches.

A conclusão da base de dados não significa que todas as
funcionalidades especializadas já estejam integradas ao sistema.

Este README descreve os arquivos desta revisão. A implementação da simulação e
da regressão foi desenvolvida na `dev-danilo`; sua presença nesta branch não
significa que já tenha sido incorporada à `main`.

| Componente | Situação atual |
|---|---|
| Menu textual | Navegação, validação de opções e saída disponíveis; opções funcionais ainda exibem "Funcionalidade em Desenvolvimento" |
| Banco SQLite | Conexão, cinco tabelas e regras de integridade disponíveis |
| Monitoramento | Regras R1 (consumo elevado AND módulo crítico) e R2 (sensor inválido OR módulo em manutenção), com tabelas verdade e testes |
| Estruturas de dados | Índice hash, fila, pilha e grafo implementados e testados |
| Simulação energética | Bateria ideal, integração numérica, histórico, SoC, déficit e excedente implementados e testados |
| Regressão linear | Mínimos quadrados, avaliação cronológica, métricas, referência e previsões implementados e testados |
| Demonstração energética | Script independente com 24 ciclos sintéticos, comparação de cenários, quatro gráficos e resultados JSON |
| CRUD e importação | Implementação pendente |
| Agentes e análise integrada | Implementação pendente |
| Integração dos módulos ao menu e banco | Pendente |

A última validação local desta revisão teve **102 testes aprovados**, sem testes
pulados. Isso valida as funcionalidades cobertas, mas não representa um fluxo
completo do sistema já integrado.

## **Tecnologias**
- Python: ambiente verificado com **3.12.10** no Windows.
- SQLite, por meio de `sqlite3`, e demais bibliotecas padrão do Python.
- **Matplotlib 3.11.2** para gerar os gráficos, conforme `requirements.txt`.

Os cálculos da simulação e da regressão utilizam somente a biblioteca padrão.
O NumPy é uma dependência transitiva do Matplotlib; Pandas e scikit-learn não são
necessários para a implementação atual.

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

### **Menu principal**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B codigo_fonte.py
```

O sistema inicializa o banco SQLite e apresenta o menu. As opções de 1 a 8 ainda
não chamam os módulos especializados. Use `0` para sair.

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

## **Menu de Gerenciamento de Dados**

A opção 1 do Menu Principal abre o submenu de gerenciamento.

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

O projeto utiliza o módulo `unittest` da biblioteca padrão Python.

Para executar a suíte completa:

O projeto utiliza o módulo `unittest` da biblioteca padrão Python.

Para executar a suíte completa:

**Suíte completa:**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
```

Na conclusão da implementação da Pessoa 1, a suíte possui
100 testes automatizados previstos.

Os testes verificam, entre outros aspectos:

- Validação de dados.
- Operações CRUD.
- Restrições de chaves estrangeiras.
- Cadastro de sensores e leituras.
- Consultas SQL e agregações energéticas.
- Geração reproduzível do CSV.
- Importações idempotentes.
- Rollback em operações inválidas.
- Cadastro e consulta de solicitações.
- Deduplicação de alertas.
- Navegação e interações do Menu Principal.

Os testes de persistência utilizam bancos SQLite em memória,
evitando alterações no banco operacional local.

Testes de geração e importação utilizam arquivos temporários.

A quantidade total poderá aumentar com a integração
das implementações dos outros integrantes.


### **Requisitos**

- Python 3.
- Terminal ou ambiente de desenvolvimento compatível.
- SQLite, utilizado por meio da biblioteca padrão `sqlite3`.

A base do SIFSM utiliza bibliotecas padrão do Python.
Os módulos especializados poderão utilizar outras bibliotecas
conforme os requisitos e decisões técnicas da equipe.

### **Acessar a pasta do projeto**

```bash
cd phase-07-FIAP-SIFSM
```

### **Gerar os dados simulados**

```bash
python3 -B gerar_dados_iniciais.py
```

O comando gera o arquivo `dados_aurora_siger.csv`.

O conjunto inicial contém:

- 5 módulos operacionais.
- 10 sensores.
- 32 ciclos simulados.
- 320 leituras.

Cada ciclo representa uma hora na escala da simulação.

**Atenção:** executar novamente o gerador sobrescreve o CSV no
caminho configurado. Preserve alterações manuais, se existirem.

### **Executar o sistema**

```bash
python3 codigo_fonte.py
```

O SIFSM inicializa o esquema SQLite e apresenta o Menu Principal.

O arquivo `aurora_siger.db` é criado automaticamente quando necessário.

### **Importar os dados iniciais**

No Menu Principal:

1. Selecione `1 - Gerenciar dados da colônia`.
2. Selecione `9 - Importar dados iniciais`.
3. Digite `IMPORTAR` para confirmar.

A importação verifica módulos, sensores e leituras já existentes.

Repetir a importação do mesmo CSV não duplica as leituras.
Registros conflitantes provocam erro e a tentativa de
importação é revertida.

### **Consultar os dados**

No submenu de gerenciamento, utilize:

- Opção 1: listar módulos.
- Opção 6: listar sensores.
- Opção 7: consultar leituras.
- Opção 8: consultar série energética.

As opções 2 a 5 permitem cadastrar, buscar, atualizar e
excluir módulos.
**Testes específicos da parte energética:**

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_simulacao_computacional.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_modelo_linear.py" -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_demonstracao_energia.py" -v
```

| Grupo | Quantidade |
|---|---:|
| Banco, contratos, monitoramento e estruturas | 58 |
| Simulação energética | 22 |
| Regressão linear | 19 |
| Demonstração e gráficos | 3 |
| **Total** | **102** |

Os testes usam banco em memória e dados de teste; não dependem de registros no
banco local. Sem Matplotlib, o teste de geração de imagens é pulado. Instale
`requirements.txt` para validar a suíte completa, incluindo os gráficos.

## **Estrutura do Projeto**

```text
phase-07-FIAP-SIFSM/
├── codigo_fonte.py
├── config.py
├── banco_dados.py
├── banco_aurora_siger.sql
├── monitoramento.py
├── estruturas_dados.py
├── simulacao_computacional.py
├── modelo_linear.py
├── agentes.py
├── analise_integrada.py
├── demonstracao_energia.py
├── requirements.txt
├── README.md
├── docs/
│   ├── CONTRATOS.md
│   ├── PLANO_EQUIPE.md
│   ├── DOC_MONITORAMENTO_ESTRUTURAS.md
│   └── DOC_SIMULACAO_REGRESSAO.md
├── tests/
│   ├── test_banco_dados.py
│   ├── test_contratos.py
│   ├── test_monitoramento.py
│   ├── test_estruturas_dados.py
│   ├── test_simulacao_computacional.py
│   ├── test_modelo_linear.py
│   └── test_demonstracao_energia.py
└── graficos_ou_imagens/
    ├── potencias_por_ciclo.png
    ├── bateria_e_soc.png
    ├── regressao_consumo.png
    ├── residuos_teste.png
    └── demonstracao_energia.json
```

| Arquivo | Responsabilidade |
|---|---|
| `codigo_fonte.py` | Menu Principal e interface do terminal |
| `config.py` | Configurações compartilhadas |
| `banco_dados.py` | Persistência e operações SQLite |
| `banco_aurora_siger.sql` | Esquema relacional do banco |
| `gerar_dados_iniciais.py` | Geração dos dados simulados |
| `dados_aurora_siger.csv` | Dados iniciais compartilhados |
| `monitoramento.py` | Regras booleanas e monitoramento |
| `estruturas_dados.py` | Estruturas de dados operacionais |
| `simulacao_computacional.py` | Simulação energética |
| `modelo_linear.py` | Modelagem e regressão linear |
| demonstracao_energia.py | Demonstração reproduzível, comparação de cenários e gráficos |
| `agentes.py` | Agentes especializados simulados |
| `analise_integrada.py` | Integração dos resultados |
| `tests/` | Testes automatizados |
| `docs/` | Contratos e documentação da equipe |
| graficos_ou_imagens/ | Evidências da demonstração energética |

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
- A integração final depende da validação dos módulos
  desenvolvidos pelos demais integrantes.

Essas limitações deverão ser consideradas na interpretação
dos resultados e no relatório técnico final.
- A integração entre banco, menu, agentes e análises ainda precisa ser concluída.
- Os campos internos dos resultados analíticos estão documentados e precisam de
  alinhamento com o responsável pela integração; as assinaturas e chaves principais
  dos contratos foram preservadas.
- É necessário definir a agregação dos sensores e se a série representa um módulo
  ou toda a colônia antes de conectar `obter_serie_energia()` aos módulos analíticos.
- A bateria é ideal: não representa perdas, degradação, reserva mínima ou limites de potência.
- A regressão usa uma única separação cronológica; previsões futuras são extrapolações,
  e associação entre ciclo e consumo não implica causalidade.
- Os dados da demonstração são simulados e não representam medições reais de Marte.
- Os resultados apoiam avaliação humana; não executam ações operacionais automaticamente.
