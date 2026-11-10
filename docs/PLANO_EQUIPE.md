# **SIFSM - Plano de Desenvolvimento da Equipe**

- **Projeto:** Sistema Integrado de Futuro Sustentável em Marte
- **Versão:** Scaffold v1.0
- **Equipe:** 
| Nome | GitHub | Matrícula 
|------|--------| --------|
| Renato Valle | [@renatolvalle](https://github.com/renatolvalle) | RM 572352
| Renato Nascimento | [@renascience](https://github.com/renascience) | RM 570266
| Alexandre Niewelt | [@QTAlox](https://github.com/QTAlox) | RM 570614
| Danilo Fernandes | [@dandgsf](https://github.com/dandgsf) | RM 570057

## **Divisão de Responsabilidades**

### **Renato Nascimento** - Base do Sistema

**Arquivos principais:**
- codigo_fonte.py
- config.py
- banco_dados.py
- banco_aurora_siger.sql
- dados_aurora_siger.csv

**Responsabilidades:**
- Manter o Menu Principal.
- Implementar conexão e operações CRUD.
- Importar dados simulados.
- Implementar consultas ao banco.
- Validar entradas e tratar erros.
- Desenvolver testes das operações de presistência.

### **Renato Valle** - Monitramento e Estruturas

**Arquivos principais:**
- monitoramento.py
- estruturas_dados.py
- circuito_logico.pdf

**Responsabilidades:**
- Implementar regras booleanas.
- Avaliar leituras e gerar alertas.
- Construir tabela verdade.
- Representar o circuito lógico.
- Implementar fila de solicitações.
- Implementar índices hash para sensores.
- Desenvolver testes das funcionalidades.

### **Danilo Fernandes**

**Arquivos principais:**
- simulacao_computacional.py
- modelo_linear.py

**Responsabilidades:**
- Desenvolver a simulação energética.
- Calcular consumo e geração de energia.
- Simular o estado de carga de baterias.
- Aplicar integração numérica.
- Desenvolver regressão linear.
- Interpretar coeficientes e métricas.
- Produzir gráficos e testes.

### **Alexandre Niewelt**

**Arquivos principais:**
- agents.py (nome efetivo do módulo de agentes)
- analise_integrada.py

**Responsabilidades:**
- Implementar agentes simulados.
- Criar roteamento de solicitações.
- Implementar guardrails.
- Integrar os resultados dos demais módulos.
- Desenvolver a análise de sustentabilidade.
- Documentar arquitetura computacional e impactos socioambientais.
- Consolidar a documentação recebida da equipe.

## **Dependências**

Renato Valle poderá desenvolver suas regras com leituras simuladas antes da conclusão do banco.

Danilo Fernandes poderá desenvolver a simulação e regressão utilizando listas de dicionários de teste.

Alexandre Niewelt poderá desenvolver os agentes com resultados simulados.

A integração final dependerá das funções especializadas estarem implementadas e respeitarem os contratos compartilhados.

## **Fluxo de Trabalho**

1. Consultar o README e os CONTRATOS.
2. Desenvolver na branch específica para cada um:

| Nome | Branch |
|---|---|
| Renato Valle | dev-renatov |
| Renato Nascimento | dev-renaton |
| Danilo Fernandes | dev-danilo |
| Alexandre Niewelt | dev-alex |

3. Criar ou atualiar os testes.
4. Executar a suíte de testes.
5. Revisar as alterações.
6. Abrir Pull Request para integração.
7. Integrar somente após a revisão.

### **Finalização por etapas — atualização de 10/11/2026**

Após a integração das contribuições iniciais, os ajustes finais seguem branches
sequenciais por conjunto de mudanças, preservando as responsabilidades acima:

1. `fix/agentes-contratos`: contratos, recomendações e guardrails; integrada à
   `main` pelo PR #7.
2. `feat/analise-integrada`: orquestração do banco, regras, hash/fila, simulação,
   regressão e recomendações. Implementada nesta branch para teste e revisão,
   com análise somente de leitura e demonstração CSV em memória. Os detalhes de
   campos/políticas estão em `CONTRATOS.md` e `DOC_ANALISE_INTEGRADA.md`.
3. `fix/integracao-menus`: conectar as opções e unificar a navegação, após integrar
   a análise. Os adaptadores da opção 2 atual permanecem como demonstração sintética.
4. `docs/finalizacao-entrega`: revisão completa do relatório, README final,
   evidências aplicáveis, vídeo e validação do ZIP.

A Etapa 2 conecta os módulos existentes sem mudar suas assinaturas compartilhadas,
o esquema do banco ou os algoritmos de ajuste e simulação. Na revisão autorizada
dessa etapa, o retorno de `metricas` da regressão recebeu dois campos aditivos:
média do treino e contagem de previsões negativas no teste. Os agentes deixam
de recomendar pico/tendência de uma reta que não supera a referência ou produz
negativas, usando a média do treino como referência explícita quando disponível;
avaliação incompleta implica abstenção. Os resultados brutos da regressão são
preservados. Esse complemento está comunicado em `CONTRATOS.md` para revisão no PR.
Persistir alertas continua sendo uma operação explícita da aplicação. O plano de branches finais
complementa as branches individuais da implementação inicial; cada etapa segue
teste, revisão e PR antes de integrar a `main` e iniciar a seguinte.

## **Regras de Colaboração**
- Não modificar arquivos de outro integrante sem combinar previamente.
- Evitar mudança nos contratos compartilhados.
- Não editar diretamente a branch principal para novas funcionalidades.
- Documentar alterações relevantes.
- Compartilhar problemas de integração assim que identificados.
- Manter mensagens de erro compreensíveis.
- Preservar o funcionamento do Menu Principal
- Manter as variáveis em Português.

## **Documentação**

Cada integrante deverá documentar as próprias funcionalidades, entradas, saídas, escolhas técnicas, resultados e limitações.

O Alexandre Niewelt consolidará o material no relatório técnico, com revisão de toda a equipe.

## **Validação e Entrega**

Todos serão responsáveis por executar os testes integrados.

A equipe deverá produzir:
- Sistema Python funcional.
- Banco de dados e arquivos exigidos.
- Relatório técnico completo.
- README atualizado.
- Vídeo de apresentação de até cinco minutos.
- Arquivo .ZIP final.

O vídeo deverá desmontrar o funcionamento do protótipo e explicar as principais decisões técnicas.
