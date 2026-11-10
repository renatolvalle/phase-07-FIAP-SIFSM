# Navegação integrada — Etapa 3

## Entrada e preparação

O arquivo principal padronizado é **`codigo_fonte.py`**. `main.py` apenas importa
essa função principal e a chama quando executado, sem outro fluxo de navegação.
Importar qualquer entrada é silencioso, sem banco ou demonstrações automáticas.

Na raiz do projeto, com as dependências do README instaladas:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B codigo_fonte.py
```

Alternativa equivalente: substituir `codigo_fonte.py` por `main.py`. Ambos criam
o SQLite local se necessário e inicializam o esquema. **Não importam o CSV
automaticamente.** Para ensaio sem alterar um banco existente, copie o projeto
sem `aurora_siger.db` e execute na cópia; mudar somente o diretório corrente não
isola o banco, pois `config.py` define caminhos a partir da própria pasta.

Na primeira execução: principal **1 → 9 → `IMPORTAR` → Enter → 0**. A base
fornecida contém dados simulados: 5 módulos, 10 sensores e 320 leituras em 32
ciclos. Reimportar dados idênticos não os duplica; conflitos são informados.

## Opções do menu principal

| Opção | Fluxo e interpretação |
|---|---|
| 1 | Submenu de dados preservado: CRUD de módulos, listagem de sensores, leituras, série agregada e importação CSV |
| 2 | Ciclo opcional (Enter = todos), R1/R2, tabelas verdade; oferece `REGISTRAR` se houver R1 |
| 3 | Hash por código, cadastro administrativo de solicitação, fila FIFO, pilha LIFO e grafo BFS hipotético |
| 4 | Simulação do SQLite com cobertura validada e comparação com geração agregada reduzida em 30% |
| 5 | Exploração, coeficientes, avaliação cronológica, referência e previsões brutas; recomendações separadas |
| 6 | `demonstrar_agentes()` em cada visita e consulta textual opcional via triador; não consulta/persiste banco |
| 7 | Análise integrada: contagens, regras, hash/fila, simulação, regressão, recomendações, impactos e limitações |
| 8 | Configuração, unidades, implementação/limites, CPU/memória e aceleração apenas conceitual |
| 0 | Sair e fechar a conexão |

Submenu 3: **1** busca hash; **2** cadastro de solicitação; **3** FIFO; **4** pilha;
**5** grafo; **0** volta. Pilha: registrar/listar/desfazer só em memória, com
`DESFAZER` para confirmar a retirada do topo. Grafo: o usuário escolhe um módulo
cadastrado; dependências do cenário são explicitamente hipotéticas, não vínculos
descobertos no banco. Módulos ausentes não são inventados.

## Escritas, segurança e estados ausentes

- CRUD/importação continuam na camada de persistência. Excluir requer `EXCLUIR`.
- Monitoramento calcula alertas das leituras consultadas. Só `REGISTRAR` grava
  R1, de modo idempotente por sensor/ciclo/regra. Não é uma consulta aos alertas
  históricos persistidos nem oferece sua resolução/alteração de status.
- R2 no monitoramento conta sensores observados bloqueados, uma vez por sensor;
  na análise integrada conta ocorrências por leitura. Ambos usam **status atuais**,
  não reconstituem estados históricos e não executam bloqueios físicos.
- Cadastro de solicitação é entrada administrativa explícita; não significa
  autorização de seu conteúdo. Prioridade fica registrada, mas não reordena FIFO.
  `SIMULAR` retira somente da deque temporária; o registro continua pendente.
- Pilha/grafo não executam nem desfazem CRUD, atendimento ou falhas físicas.
- Opções 4, 5 e 7 usam `executar_analise_integrada(conexao)`, somente de leitura.
  A simulação do cenário −30% usa o histórico validado e o mesmo modelo numérico.
  Não há implementação analítica paralela nem dados sintéticos substitutos.
- Banco vazio: resultados indisponíveis e orientação de importação, sem consumo
  zero, normalidade, previsões ou atendimento de 100% inventados. De 1 a 9 ciclos
  válidos: simulação disponível e regressão indisponível. Cobertura parcial,
  unidades incorretas ou medidas inválidas geram erro compreensível nas análises.
- Guardrail exige revisão humana para suporte vital/sistemas críticos antes do
  handoff. É conservador por palavras-chave, não barreira suficiente para hardware.
- Opções podem ser repetidas. Entradas inválidas voltam ao menu; 0 nos submenus
  volta ao principal. EOF/Ctrl+C encerram a sessão e fecham a conexão em `finally`.
  Inicialização falha retorna saída 1; erros inesperados propagam após fechamento.

## Resultados verificáveis na base fornecida

| Medida exibida | Resultado |
|---|---:|
| Alertas R1 calculados | 19 |
| Consumo / geração acumulados | 171,05 / 66,76 kWh |
| Déficit não atendido / bateria final | 92,29 / 0 kWh |
| Atendimento simulado | 46,05% (arredondado) |
| Treino / teste posterior | 25 / 7 ciclos |
| MAE da regressão / referência | 0,2766813 / 0,2722857 kW |
| R² | −0,0193275 |
| Média só do treino, referência recomendada | 5,344 kW por ciclo |

As previsões da reta dos ciclos 33–35 continuam visíveis como **brutas e
extrapoladas**, não como recomendações. O modelo não supera a referência pelo
MAE: a sugestão usa a média do treino, sem pico/tendência ou garantia. Negativas
também impedem endossar a reta; R² indefinido permanece indefinido. Seleção na
mesma janela de teste não tem avaliação independente. Fórmulas e políticas em
[análise integrada](DOC_ANALISE_INTEGRADA.md) e [modelos](DOC_SIMULACAO_REGRESSAO.md).

## Roteiro de conferência

1. Importe o CSV no menu 1 e consulte dados. Para CRUD, use módulo temporário sem
   vínculos: cadastre, busque/liste, altere e exclua com confirmação. Teste também
   entrada inválida/código duplicado e cancelamento de exclusão.
2. Abra 2, Enter para todos os ciclos, confira 19 R1/tabelas. Salve com `REGISTRAR`.
   Repita: devem ser **0 novos**; sair sem essa palavra não grava.
3. Abra 3 → 1 e busque `SEN-HAB-CONS-01`. Cadastre solicitação em 3 → 2, depois
   simule a FIFO em 3 → 3; reabra e confira que continua pendente. Confira pilha
   e grafo como demonstrações em memória, sem alegar desfazer SQL.
4. Confira os cenários da opção 4 e a diferença entre kW, kWh, horas e SoC.
5. Abra 5 e confronte treino/teste e métricas com a tabela acima. Leia a referência
   recomendada e as limitações, não apenas os números brutos da reta.
6. Visite 6 duas vezes: a demonstração deve aparecer em ambas. Consulte
   `Desligar suporte vital por falha`: guardrail, sem ordem/cadastro automático.
7. Abra 7 para conferir o fluxo integrado; 8 para arquitetura/limites. Saia com 0.

## Testes e limites da conclusão

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p "test_navegacao.py" -v
```

Validação da etapa: **348 testes aprovados**, incluindo 45 testes de interface da
contribuição de Renato Nascimento e 31 de navegação/ciclo de vida/CLI. O teste
antigo da entrada sintética foi adaptado à mudança intencional: auxiliares seguem
testados separadamente e o menu agora é testado com SQLite real.

CLI de ambas as entradas é executada em cópias temporárias com SQL/CSV, verificando
persistência, repetição, resultados e ausência de gráficos/caches. Os demais testes
usam SQLite em memória/diretórios temporários, sem acessar o banco local. Cobrem
erros SQLite/numéricos, cobertura incompleta, ausência de dados, negativas/R²
indefinido, guardrails, retorno de submenus e fechamento em saída/erro/EOF/Ctrl+C.

Esta etapa conclui a **navegação**, não a entrega acadêmica: a revisão completa
do relatório, representação lógica em arquivo, revisão de atribuições, vídeo/link,
ZIP e ensaio da entrega final continuam na **Etapa 4**.
