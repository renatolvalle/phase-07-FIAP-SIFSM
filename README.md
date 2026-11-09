# **SIFSM - Sistema Integrado de Futuro Sustentável em Marte**

## **FIAP - Ciência da Computação | Fase 07**

- **Colônia:** Aurora Siger
- **Versão:** Scaffold v1.1
- **Linguagem:** Python
- **Banco de Dados:** SQLite

## **Integrantes**

| Nome | GitHub | Matrícula 
|------|--------| --------|
| Renato Valle | [@renatolvalle](https://github.com/renatolvalle) | RM 572352
| Renato Nascimento | [@renascience](https://github.com/renascience) | RM 570266
| Alexandre Niewelt | [@QTAlox](https://github.com/QTAlox) | RM 570614
| Danilo Fernandes | [@dandgsf](https://github.com/dandgsf) | RM 570057

## **Pasta Principal**
`phase-07-FIAP-SIFSM/`

## **Link do Repositório**
[Clique para Acessar:](https://github.com/renatolvalle/phase-07-FIAP-SIFSM.git) - `https://github.com/renatolvalle/phase-07-FIAP-SIFSM.git`

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


## **Tecnologias**
- Python 3.
- SQLite (sqlite3).
- Bibliotecas padrão do Python.

NumPy, Pandas, Matplotlib e scikit-learn poderão ser utilizados nas etapas futuras, conforme as necessidades do projeto e baseado nos conteúdos estudados na Fase 07.

## **Como Executar**

Abra o terminal na pasta principal do projeto.

Execute:

```bash
python3 codigo_fonte.py
```

O sistema inicializará o banco SQLite e apresentará o Menu Principal.

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

```bash
python3 -B -m unittest discover -s tests -v
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

## **Estrutura do Projeto**

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
| `agentes.py` | Agentes especializados simulados |
| `analise_integrada.py` | Integração dos resultados |
| `tests/` | Testes automatizados |
| `docs/` | Contratos e documentação da equipe |

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

O projeto será desenvolvido por quatro integrantes. Cada integrante será responsável por módulos específicos, seguindo os contratos de integração.

Consultar:
- docs/CONTRATOS.md
- docs/PLANO_EQUIPE.md

## **Regras de Desenvolvimento**

- Manter os contratos de integração.
- Utilizar nomes em snake_case.
- Evitar código duplicado.
- Documentar funções importantes.
- Não executar operações SQL fora de banco_dados.py.
- Executar os testes antes de integrar alterações.
- Não modificar interfaces compartilhadas sem comunicar à equipe.

## **Entrega Final**

Ao término do projeto, serão preparados os arquivos exigidos pela Fase 07, incluindo relatório técnico, dados simulados, representação lógica, apresentação em vídeo e pasta ZIP.

O vídeo terá duração máxima de cinco minuto e será publicado no YouTube como "Não listado".


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