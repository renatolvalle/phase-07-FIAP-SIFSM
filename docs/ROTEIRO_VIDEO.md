# Roteiro humano — até 5 minutos

**Meta: 4min50s**, com dez segundos de margem. Ensaiar antes de gravar.
Usar o ZIP extraído em pasta separada, sem banco existente, instalar conforme README
e abrir `codigo_fonte.py`. Não gravar o diretório de trabalho com dados locais.
Deixar os PDFs e as seções do menu previamente localizados. Não apresentar
trechos acelerados como prova de duração de execução.

| Intervalo | Mostrar e explicar |
|---|---|
| 0:00–0:20 | Objetivo do SIFSM, equipe e dados simulados; sem sensores físicos ou controle de equipamentos |
| 0:20–1:20 | Menu 1: importar em 9 com IMPORTAR, listar; cadastrar módulo temporário sem vínculos, buscar, alterar e excluir com EXCLUIR. Mostrar código duplicado ou entrada inválida e o tratamento do erro |
| 1:20–1:50 | Menu 2: todos os ciclos, 19 R1, limite estrito de 2,5 kW, AND; exibir circuito_logico.pdf e R2 OR. REGISTRAR e repetir: 0 novos; nenhum corte automático |
| 1:50–2:20 | Menu 3: hash SEN-HAB-CONS-01, solicitação administrativa e fila FIFO; SIMULAR não altera SQLite. Pilha/grafo são em memória/hipotéticos; não alegar desfazer SQL |
| 2:20–3:00 | Menu 4: dt=1 h, E=Pdt, bateria de 20 kWh/inicial 12; base 171,05/66,76 kWh, déficit 92,29; geração −30% dá déficit 112,32 kWh; limites ideais |
| 3:00–3:35 | Menu 5: treino 25/teste 7, coeficientes, MAE 0,2766813 contra 0,2722857; reta perde. Referência recomendada 5,344 kW é só do treino; extrapolações não garantem o futuro |
| 3:35–4:00 | Menu 6: triagem de energia/manutenção e Desligar suporte vital por falha. Bloqueio para humanos, sem cadastro ou execução; palavras-chave, não LLM/RAG |
| 4:00–4:35 | Menu 7/8 e relatório: CPU local, RAM/cache/armazenamento, latência finita, aceleradores só conceituais; simular evita experimentos físicos, transparência de métricas, privacidade de solicitações e custo ambiental do processamento |
| 4:35–4:50 | Limitações, responsabilidade humana, PDFs e testes/pacote; encerrar em 0 |

## Preparação das telas

- O menu de dados mantém os IDs gerados; anotar o ID do módulo temporário antes de
  atualizar/excluir. Um módulo com sensores vinculados não pode ser excluído.
- Pressionar Enter nas pausas. O submenu 3 volta ao principal por 0.
- Não recadastrar dados ou solicitações durante a gravação sem reiniciar o ensaio;
  a solicitação fica pendente após a simulação FIFO.
- Deixar a expressão booleana e o diagrama legíveis, não apenas citar o arquivo.
- Mostrar a demonstração real dos comandos; a narrativa não substitui CRUD e erro.
- Não mostrar tokens, contas pessoais, ambiente de desenvolvimento ou dados reais.

## Publicação

No YouTube, selecionar **Não listado**; conferir reprodução, áudio, legibilidade,
conteúdo e duração máxima de cinco minutos. Abrir o link sem a conta publicadora,
criar `link_video.txt` na raiz e reconstruir/conferir com `--final`, conforme
[ENTREGA.md](ENTREGA.md). Não reutilizar o vídeo de outra fase.
