# Entrega técnica — Etapa 4

## Situação

Documentação e pacote técnico preparados. **Somente duas tarefas humanas permanecem pendentes:**

- [ ] Gravar a demonstração completa de até cinco minutos.
- [ ] Publicar no YouTube como **Não listado** e fornecer `link_video.txt` com a URL válida.

O pacote `entrega/sifsm-entrega.zip` não deve ser submetido como entrega acadêmica
completa enquanto não incluir esse link. Não existe arquivo de link fictício.
O ZIP técnico não contém a si próprio, seu checksum externo ou o banco local.
O manifesto interno registra a ausência do vídeo, além dos SHA-256 dos arquivos.

## Reconstrução

Na raiz, com o Python 3.12 e o ambiente do README:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-docs.txt
.\.venv\Scripts\python.exe -X utf8 -B scripts/gerar_documentos.py
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 -B scripts/empacotar.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/validar_entrega.py --executar
```

`gerar_documentos.py` consulta somente SQLite em memória. Reconstrói os dois PDFs,
três PNGs (`arquitetura`, `csv_energia`, `csv_regressao`) e o JSON integrado.
Substitui exclusivamente esses arquivos de mesmo nome. A fonte textual canônica
do relatório é [relatorio_tecnico.md](relatorio_tecnico.md); capa, folha de rosto,
resumo, abstract e sumário com links internos são compostos pelo gerador.
As tabelas do relatório são conferidas contra o JSON pelos testes. Os cinco
artefatos da demonstração independente de 24 ciclos são preservados; para
recriá-los, executar `demonstracao_energia.py` como descrito no README.

Dependências editoriais: ReportLab produz diagramas vetoriais, estilos e sumário;
pypdf permite verificar a estrutura e metadados nos testes. São ferramentas de
produção documental, não bibliotecas usadas pela solução operacional. Matplotlib
gera os gráficos dos modelos do curso. Nenhuma instalação global é necessária.

O empacotador usa lista explícita, datas fixas das entradas e SHA-256. Textos são
normalizados para finais de linha LF dentro do ZIP e nos hashes das fontes,
preservando os arquivos originais: CRLF/LF de Windows/Linux não mudam o pacote.
Para entradas equivalentes após essa normalização, gera o mesmo ZIP.
Rejeita arquivos ausentes e links simbólicos externos;
não inclui automaticamente arquivos novos. `validar_entrega.py` rejeita extras,
duplicatas, caminhos inesperados, CRC inválido, hashes divergentes, sintaxe Python
inválida, evidências desatualizadas e links locais ausentes. Seu modo `--executar`
roda o código **do pacote** em pasta temporária e executa a suíte ali; usá-lo apenas
para o pacote confiável produzido pela equipe. Ele reutiliza o interpretador ativo;
o ensaio com instalação limpa é documentado em [VALIDACAO_ENTREGA.md](VALIDACAO_ENTREGA.md).

## Fechamento depois da publicação humana

1. Seguir o [roteiro de vídeo](ROTEIRO_VIDEO.md).
2. Publicar como Não listado, verificar duração máxima e abrir o link sem a conta
   do publicador para conferir acesso. Usar somente dados simulados na gravação.
3. Na raiz, criar `link_video.txt` contendo apenas a URL HTTPS real, por exemplo
   no formato `https://www.youtube.com/watch?v=` seguido do ID do vídeo publicado.
4. Atualizar a situação nas seções de entrega do README e deste documento,
   sem alterar os resultados técnicos do relatório.
5. Executar:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/empacotar.py --final
.\.venv\Scripts\python.exe -X utf8 -B scripts/validar_entrega.py --final --executar
```

O modo `--final` falha se o link estiver ausente ou malformado. Validar formato
não prova existência, duração, conteúdo ou visibilidade do vídeo; essa conferência
é parte da publicação humana. O ZIP e checksum são substituídos pelo novo pacote.

## Apresentação ABNT

O relatório usa A4, margens esquerda/superior de 3 cm e direita/inferior de 2 cm,
Times 12, texto preto justificado, recuo inicial de 1,25 cm e entrelinhas 1,5.
Legendas e fontes têm tamanho 10 e espaçamento simples; referências são alinhadas
à esquerda com espaçamento simples. A capa não é contada; a folha de rosto inicia
a contagem. A numeração arábica aparece no alto à direita a partir da introdução.
Seções primárias começam em nova página. Figuras têm identificação acima e fonte
abaixo; cores são reservadas às ilustrações. Quadros e tabelas usam regras sóbrias
sem grade vertical. O circuito é um documento técnico autônomo de duas páginas.

Referenciais de apresentação: NBR 10719:2015 (relatório técnico), NBR 14724:2024,
NBR 6024:2012, NBR 6027:2012, NBR 6028:2021, NBR 10520:2023 e NBR 6023:2025.
Foram consultados o manual da PUC-SP de 2025 e as páginas institucionais da UFABC
e do COTUCA/UNICAMP em 10/11/2026. Não se trata de certificado de normalização nem
de tese/dissertação: não há banca, orientador ou ficha catalográfica inventados.
Links e referências completos estão no relatório. A qualidade visual toma como
referência SIGIC/NCAS, preservando as regras acadêmicas em vez de copiar seus layouts.
