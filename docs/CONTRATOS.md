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

A conexão será gerenciada por banco_dados.py.

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

### agentes.py

- `rotear_solicitacao(texto)` -> str.
- `gerar_recomendacoes(indicadores, alertas, simulacao, previsao)` -> dict.

As recomendações não poderão executar ações operacionais automáticamente.

### analise_integrada.py
- `executar_analise_integrada(conexao)` -> dict.

O retorno conterá `indicadores`, `alertas`, `simulacao`, `previsao`, `recomendacoes` e `limitacoes`.

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


## **Observações da Implementação por Renato Nascimento**

A camada de persistência foi implementada na branch `dev-renaton`,
mantendo os contratos compartilhados da versão 1.0.

### **Importação do CSV**

`carregar_csv_inicial(conexao, caminho_csv)` retorna a quantidade
de novas leituras inseridas.

Uma segunda importação do mesmo arquivo retorna zero quando
todas as leituras já estão armazenadas.

A importação utiliza validação e controle transacional.
Registros inválidos ou conflitantes provocam a reversão
das alterações realizadas pela tentativa de importação.

### **Solicitações**

`listar_solicitacoes(conexao)` retorna as solicitações pendentes.

`listar_solicitacoes(conexao, status=None)` retorna todas
as solicitações, ordenadas por ID crescente.

A ordenação por ID permite utilizar a lista como entrada
para a fila FIFO de solicitações.

### **Alertas**

`registrar_alertas(conexao, alertas)` recebe uma lista de
dicionários contendo:

- `sensor_id`
- `ciclo`
- `regra_codigo`
- `nivel`
- `mensagem`

A função retorna a quantidade de novos alertas inseridos.

A combinação `sensor_id`, `ciclo` e `regra_codigo` é única.

Alertas idênticos não são duplicados. Alertas conflitantes
produzem erro.

### **Séries Energéticas**

`obter_serie_energia(conexao)` retorna uma lista de dicionários
contendo:

- `ciclo`
- `consumo_kw`
- `geracao_kw`

Os valores são agregados por ciclo e representam potência em kW.

A conversão para energia em kWh pertence à simulação computacional.

### **Responsabilidades**

A camada de banco de dados não executa monitoramento, regressão,
simulação energética ou decisões dos agentes.

Os módulos especializados recebem os dados por meio dos contratos
compartilhados e devem validar suas próprias regras de negócio.


## **Regras de Integração**

1. Não modificar assinaturas compartilhadas sem aprovação.
2. Não criar conexões SQL dentro dos módulos de simulação, monitoramento ou agentes.
3. Não importar `codigo_fonte.py` nos módulos especializados.
4. Centralizar configurações em `config.py`.
5. Manter os formatos de retorno acordados.
6. Adicionar testes às funcionalidades implementadas.

**Versão dos Contratos: 1.1**