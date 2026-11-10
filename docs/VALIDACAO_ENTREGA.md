# Validação da Etapa 4

Registro técnico das verificações locais de 10/11/2026; não representa CI nem
aprovação independente de outro integrante. O vídeo não foi gravado/publicado.

## Resultado verificado

| Verificação | Resultado |
|---|---|
| Suíte completa em ambiente novo | **374 testes aprovados em 6,318 s**, sem skips; 348 anteriores + 26 da Etapa 4 |
| Instalação limpa | Python 3.12.10 / Windows; nova `.venv`, instalação dos dois arquivos de requisitos, `pip check` aprovado |
| Conteúdo do ZIP | **60 arquivos**, sendo 59 selecionados e um manifesto; CRC, SHA-256 e lista explícita aprovados |
| Execução extraída | `codigo_fonte.py` e `main.py`, importação, análise, modelos, guardrail e encerramento aprovados; suíte repetida na cópia extraída |
| Reconstrução editorial | Dois PDFs, três PNGs e JSON reconstruídos sem diferenças de bytes |
| Remontagem do ZIP | Pacote reconstruído idêntico ao original; sem copiar ambiente/banco criado no ensaio |
| Fechamento `--final` | Reprovado deliberadamente com saída 1: falta `link_video.txt` |
| Relatório / circuito | **23 / 2 páginas**, A4; sumário com links, marcadores e paginação conferidos |
| Geometria e inspeção visual | Nenhuma saída das margens detectada; contato de todas as páginas e leitura ampliada de capa, sumário, arquitetura, gráficos e portas |
| Integridade do código | Sintaxe de **32 arquivos Python** aprovada; módulos operacionais, configuração, SQL e CSV originais não alterados |

O ensaio foi feito em diretório temporário fora do repositório, sem acesso ao
SQLite local. Primeiro criou-se uma `.venv` sem acesso aos pacotes do ambiente de
trabalho; em seguida foram seguidos os comandos do README. A checagem extraída
repetiu a suíte e confirmou os resultados de 92,29 kWh de déficit e referência
de 5,344 kW. O pacote recomposto passou no validador técnico e falhou somente no
fechamento que exige o link humano. Edições posteriores apenas deste registro
exigem remontar o ZIP para atualizar seu manifesto, não alteram os modelos testados.

Na revisão foram corrigidos a paginação da primeira folha textual, a continuidade
dos fios das portas lógicas e a normalização CRLF/LF dos hashes e textos do pacote.
O JSON gerado usa LF explicitamente. Testes de regressão cobrem esses casos,
divergência de tabela documental, alterações de fontes e proteção do banco local
contra uso acidental como destino do empacotamento.

## Escopo conferido

- Esquema real de cinco tabelas, CRUD e políticas de persistência explícita.
- R1 AND com filtro de elegibilidade e limite estrito; R2 OR como diagnóstico.
- Hash/FIFO integrados; pilha/grafo em memória, sem undo SQL ou controle físico.
- Integração em kWh, conservação e bateria ideal; CSV e demonstração separados.
- Regressão simples, avaliação temporal, referência do treino e resultados brutos.
- Agentes determinísticos, guardrails e ausência de RAG/hardware/automação física.
- Arquitetura CPU/memória e seis pontos socioambientais ligados ao protótipo.
- Texto completo, duas representações vetoriais de portas, fontes e metadados.
- Pacote por lista explícita, hashes, ausência de banco local/ambiente/planejamento.

## Comandos de verificação

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 -B scripts/empacotar.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/validar_entrega.py --executar
```

## Ensaio limpo do conteúdo efetivo

Extrair o ZIP em pasta temporária nova e executar somente as instruções do README:
criar `.venv`, instalar `requirements.txt` e `requirements-docs.txt`, conferir
dependências, executar ambas as entradas e a suíte; reconstruir os documentos;
remontar e validar o ZIP. Essa instalação limpa é distinta do modo `--executar`,
que isola arquivos e banco, mas reaproveita o interpretador do chamador.

## Revisão editorial e de atribuições

Preservados os nomes dos quatro integrantes e as referências técnicas a IA,
agentes, handoffs e guardrails. A revisão de arquivos de entrega, metadados de PDFs,
PNGs e JSONs não introduz créditos automáticos de ferramentas de autoria. Não foram
encontradas atribuições dessa natureza a remover nos arquivos originais selecionados.
Histórico Git não foi reescrito; seus títulos sobre IA descrevem funcionalidades.
Mensagens novas de commit/PR devem seguir a mesma política, sem assinaturas automáticas.
Os timestamps dos PDFs são fixados pelo modo de construção determinística; não
devem ser interpretados como datas reais de redação. O ano acadêmico é 2026.

## Limite da aprovação técnica

A conclusão desta etapa não equivale à submissão acadêmica completa: permanecem
somente gravação e publicação/link do vídeo. O pacote sem link passa na conferência
técnica e falha deliberadamente em `--final`. A visibilidade Não listado e duração
são verificações humanas, não conclusões de um validador de URL.
