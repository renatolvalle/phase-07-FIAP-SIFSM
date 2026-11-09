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

**Estado da implementação — concluída na branch `dev-renaton`.**

Entregas realizadas:

- Estrutura inicial do projeto.
- Menu Principal e submenu de gerenciamento.
- Conexão e inicialização SQLite.
- CRUD completo de módulos.
- Cadastro e consulta de sensores.
- Registro e consulta de leituras.
- Agregação de dados energéticos.
- Registro e consulta de solicitações.
- Persistência de alertas.
- Gerador de dados simulados em CSV.
- Importação com deduplicação e rollback.
- Testes automatizados de banco, dados e interface.
- Auditoria técnica da implementação.

A suíte possui 100 testes automatizados previstos após a
conclusão da integração da interface feita por Renato Nascimento.

**Próxima atividade:** revisão da documentação, commit e
Pull Request para integração com a equipe.

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
- agentes.py
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