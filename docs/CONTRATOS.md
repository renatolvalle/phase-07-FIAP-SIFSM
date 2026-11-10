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

### agents.py

- `rotear_solicitacao(texto)` -> str.
- `gerar_recomendacoes(indicadores, alertas, simulacao, previsao)` -> dict.

`agents.py` é o nome efetivo do módulo (referido como `agentes.py` no plano
original). As recomendações não executam ações operacionais automaticamente,
não abrem conexão SQL, não registram ordens e não inserem solicitações em fila.
Eventual cadastro cabe à camada de integração/persistência, após validação humana.

**Roteamento e guardrails:**

- `texto` deve ser uma string não vazia; entrada inválida gera `ValueError`.
- O triador normaliza caixa, acentos, espaços e pontuação e compara palavras
  inteiras. Energia/bateria/consumo têm precedência sobre falha/manutenção/reparo.
- Antes de qualquer encaminhamento, menções a `suporte vital`, `módulo(s)
  crítico(s)` ou `sistema(s) crítico(s)` são bloqueadas e encaminhadas à supervisão
  humana/autorização manual. Os especialistas também aplicam esse bloqueio em
  chamadas diretas. Não existe parâmetro para autorizar execução automática.
- A política é conservadora: consultas e negações sobre esses sistemas também
  exigem revisão humana. Palavras desconhecidas recebem orientação de intervenção
  humana. Trata-se de simulação por palavras-chave, não de um classificador geral
  de riscos ou de uma barreira suficiente para controlar equipamentos reais.
- Importar o módulo não executa demonstração, menu, acesso ao banco ou impressão.
  `demonstrar_agentes()` exibe e retorna `list[dict]` com `solicitacao` e `resposta`;
  pode ser repetida ou executada com `python -X utf8 -B agents.py`.

**Entradas de `gerar_recomendacoes`:**

| Argumento | Tipo | Campos utilizados |
|---|---|---|
| `indicadores` | `dict` | `quantidade_leituras` (inteiro >= 0), `consumo_medio_kw` (>= 0) |
| `alertas` | `list[dict]` | Quantidade de alertas recebidos para revisão de manutenção |
| `simulacao` | `dict` | `resumo`: `quantidade_ciclos` (inteiro >= 0), `deficit_total_kwh`, `excedente_total_kwh` (>= 0), `soc_final_pct` (0 a 100) |
| `previsao` | `dict` | `coeficientes.inclinacao_kw_por_ciclo` (pode ser negativa), `metricas.mae_kw` e `metricas.mae_referencia_kw` (ambos >= 0), `metricas.r2` (número ou `None`), `previsoes` (`list[dict]` com `consumo_previsto_kw`), `limitacoes` (`list[str]`) |

Os quatro argumentos são obrigatórios. Campos conhecidos são opcionais, sem
substituir ausência por zero; `{}`/`[]` representam resultados indisponíveis.
Campos adicionais dos módulos analíticos são aceitos. Valores fornecidos devem
respeitar os tipos e intervalos acima; números devem ser finitos e não booleanos.
Estruturas/valores inválidos geram `ValueError`. Entradas não são alteradas.

O retorno é `dict` com:

- `energia`: `list[str]` baseada no consumo informado, déficit/excedente e estado
  final simulados, tendência e pico previstos, quando disponíveis;
- `manutencao`: `list[str]` para revisão dos alertas recebidos, sem confirmar cadastro;
- `supervisao_humana`: sempre `True`;
- `limitacoes`: `list[str]` com ausência de dados, restrições operacionais e ressalvas
  da previsão recebida, incluindo valores negativos, R² indefinido e modelo que
  não supera a referência pelo MAE, quando aplicável.

Sem ciclos não se interpreta o estado inicial da bateria como resultado de
operação. Previsões negativas são preservadas na entrada e sinalizadas como
inválidas, sem recomendação de pico. Sugestões não atestam segurança operacional.

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

## **Regras de Integração**

1. Não modificar assinaturas compartilhadas sem aprovação.
2. Não criar conexões SQL dentro dos módulos de simulação, monitoramento ou agentes.
3. Não importar `codigo_fonte.py` nos módulos especializados.
4. Centralizar configurações em `config.py`.
5. Manter os formatos de retorno acordados.
6. Adicionar testes às funcionalidades implementadas.

**Versão dos Contratos: 1.0**
