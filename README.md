# **SIFSM - Sistema Integrado de Futuro Sustentável em Marte**

## **FIAP - Ciência da Computação | Fase 07**

- **Colônia:** Aurora Siger
- **Versão:** Scaffold v1.0
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

O projeto encontra-se na versão Scaffold v1.0

**Funcionalidades disponíveis:**
- Menu Principal com oito opções.
- Limpeza de tela e validação de opções.
- Conexão SQLite.
- Inicialização das cinco tabelas do banco.
- Contratos de integração dos módulos.
- Oito testes automatizados

**Funcionalidades ainda NÃO implementadas:**
- Operações CRUD e importação de dados.
- Monitoramento e regras booleanas.
- Estruturas de dados operacionais.
- Simulação energética.
- Regressão linear.
- Agentes simulados.
- Análise integrada de sustentabilidade.

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

## **Como Executar os Testes**

```bash
python3 -B -m unittest discover -s tests -v
```

Nesta versão, são esperados oito testes automatizados.

## **Estrutura do Projeto**

| Arquivo         | Responsabilidade |
|-----------------|------------------|
| codigo_fonte.py | Menu Principal   |
| config.py      | Configurações compartilhadas |
| banco_dados.py  | Conexão SQLite e contratos de persistência |
| monitoramento.py | Monitoramento e regras booleanas |
| estruturas_dados.py | Estruturas de dados |
| simulacao_computacional.py | Simulação energética |
| modelo_linear.py | Regressão linear |
| agentes.py | Agentes especializados simulados |
| analise_integrada.py | Integração das análises |
| banco_aurora_siger.sql | Estrutura das tabelas |
| tests/ | Testes automatizados |
| docs/ | Documentação da equipe |

O arquivo aurora_siger.db é gerado automaticamente.

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

O Scaffold v1.0 representa a estrutura inicial do sistema. As funcionalidades operacionais e analíticas aidna serão desenvolvidas e validadas pelos integrantes.

OS dados utilizados posteriormente serão simulados e não representarão medições reais de Marte.