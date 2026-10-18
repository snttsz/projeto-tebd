## 8 · Guia de continuidade (para outra IA ou chat)

*Neste capítulo: tudo que uma pessoa ou uma IA precisa saber para continuar o projeto sem refazer decisões: contexto, ambiente, estado atual, pendências com critérios de aceite, armadilhas e prompts prontos.*

### 8.1 Como usar este guia

1. Anexe ao chat: **este PDF (ou o `.md`)**, o **enunciado** do professor (`docs/enunciado/Projeto_TEBD_…PBL.pdf`) e, se quiser, o artigo do método PBL (`docs/enunciado/2020.1.pdf`).
2. Cole o **prompt P1** (seção 8.10). Ele faz a IA ler tudo e resumir o que entendeu antes de agir.
3. Trabalhe **uma pendência por vez** (seção 8.8), pedindo a saída no formato indicado.
4. **A IA não enxerga o seu banco.** Peça o SQL, execute no PostgreSQL e cole de volta o resultado para ela interpretar.
5. Sempre confira os resultados antes de colocar em um documento. Não aceite número que a IA não tenha visto na saída do banco.

> [!WARNING]
> **Limitação.** Este guia descreve o estado em **18/10/2026**. Se o modelo ou os dados mudarem, atualize o capítulo 5 (dicionário) e os números citados (seção 8.7).

### 8.2 Contexto em doze linhas (fatos que não mudam)

1. **Disciplina:** Tópicos Especiais em Banco de Dados (Prof. Antônio Cordeiro), Sistemas de Informação, 9º semestre.
2. **Tema:** gestão de resíduos sólidos urbanos e coleta seletiva, alinhado à **ODS 11** (meta 11.6).
3. **Cliente fictício:** *Prefeitura de Cidade-Modelo* (12 bairros, ~343,5 mil habitantes). A equipe atua como consultoria de dados (método PBL, artigo de Linge e Parsons, 2006).
4. **SGBD:** PostgreSQL 17 (compatível com 15+). Dois *schemas*: `oltp` (12 tabelas, 3FN) e `dw` (8 dimensões, 4 fatos, esquema estrela).
5. **Dados:** **sintéticos**, gerados por script determinístico para 2025, **com padrões deliberados** (seção 8.7). Não representam cidade real; isso deve ser dito sempre.
6. **Entregas:** parcial em **19/10/2026** (itens 1–5 do barema) e final em **06/11/2026** (itens 6–10 + apresentação).
7. **Itens 6–10 pendentes:** análise exploratória com mineração, 3 dashboards (≥ 5 consultas cada, **enunciado + código**) e plano 5W2H.
8. **Apresentação (40% da nota):** domínio do conteúdo **individual**, clareza, concatenação de ideias, resposta a argumentações, originalidade (extra).
9. **Estrutura do banco: congelada.** Mudanças só no plano B (seção 8.7).
10. **Identificadores** sem acento, em português, no singular; chaves substitutas `sk_*`; chave de origem `id_origem`.
11. **Dicionário de dados** vive no banco (`COMMENT ON`); o PDF o gera de lá.
12. **Tudo que for número no texto deve vir de uma consulta ao banco.**

### 8.3 Mapa de arquivos

| Caminho | O que é |
|---|---|
| `README.md` e `docs/README.md` | Visão geral do projeto e **como ler cada documento** |
| `docs/entregas/professor/` | **Roteiro visual** (≈ 20 páginas) para mostrar o andamento ao professor: resumo, contexto, perguntas do cliente, diagramas em sequência |
| `docs/entregas/anexo-dicionario/` | Só o dicionário de dados (item 4), fora do roteiro visual |
| `docs/entregas/guia-completo/` | Este guia |
| `docs/enunciado/` | **Enunciado** do professor (fonte da verdade) e o artigo do método PBL (`2020.1.pdf`, seção 7 do enunciado) |
| `docs/analises/` | Análise de adequação, auditoria do enunciado e plano até 06/11 |
| `docs/pesquisas/` | Pesquisas (diagramas; abordagem e layout) com fontes |
| `docs/roteiros/` | Roteiro de demonstração para o checkpoint |
| `docs/diagramas/` | Diagramas `.png` e `.svg`; `graficos/` guarda os gráficos gerados do DW |
| `src/sql/01_construcao_oltp_olap.sql` | Cria `oltp` e `dw`, dados de exemplo e ETL |
| `src/sql/02_dicionario_comentarios.sql` | `COMMENT ON` de todas as tabelas e colunas |
| `src/sql/03_views_apoio.sql` | Views `bi.*` que simplificam os dashboards (seção 8.5) |
| `src/scripts/popular_banco.py` | Cria e popula o banco executando 01, 02 e 03 em ordem, e confere o resultado |
| `src/config.py`, `.env.example` | Configuração central (conexão e caminhos). Copie `.env.example` para `.env` |
| `src/diagramas/` | Geradores dos diagramas e gráficos (código-fonte `.dot` em `dot/`) |
| `src/documentos/` | Geradores dos PDFs e do dicionário; **o texto de todos os documentos mora em `modelo_entrega.md`** (edite lá; blocos `<!--PROF-->` e `<!--GUIA-->` separam o que é de cada versão) |

**Arquivos novos que a continuação deve criar** (um por pendência, em `src/sql/`): `04_dashboard_operacional.sql`, `05_dashboard_tatico.sql`, `06_dashboard_estrategico.sql`; e a pasta `src/mineracao/` para o item 6.

### 8.4 Ambiente e comandos

| Item | Valor |
|---|---|
| Configuração | `src/config.py`, lendo variáveis de ambiente ou o arquivo `.env` (copie `.env.example`). **Nenhuma porta, senha ou caminho fica escrito nos scripts.** |
| PostgreSQL | 17.x (compatível com 15+). Na máquina onde foi desenvolvido: porta 5433, usuário `postgres`, banco `cidades_sustentaveis`. A senha fica só no `.env` local (**não compartilhar**). |
| `psql`, Graphviz, navegador | Detectados automaticamente (PATH ou pastas padrão do Windows), ou definidos no `.env` |
| Python | `markdown`, `pymupdf`, `matplotlib` |
| Codificação | `PGCLIENTENCODING=UTF8` já é definido pelo `config.py` |

```bash
# recriar o banco do zero, popular (scripts 01, 02 e 03 em ordem) e conferir o resultado
python src/scripts/popular_banco.py --recriar

# só conferir se o banco atual está consistente
python src/scripts/popular_banco.py --verificar

# regenerar diagramas, gráficos e os três PDFs (professor, guia e anexo)
python src/diagramas/gerar_diagramas.py
python src/diagramas/gerar_graficos.py
python src/documentos/montar_entregas.py
```

> [!IMPORTANT]
> **Ordem importa.** O script 01 começa com `DROP SCHEMA … CASCADE`: ele **apaga** qualquer *view* ou objeto criado sobre `oltp`/`dw`. Depois de rodá-lo, execute de novo os scripts `02`, `03`, `04`… na ordem.

### 8.5 O banco em uma tela

Notação: `PK` chave primária · `→` chave estrangeira · `?` aceita NULL.

```text
{{ESQUEMA_RESUMO}}
```

**Padrões de junção no DW** (use sempre as chaves `sk_*`, nunca `id_origem`):

```sql
-- peso por região, tipo de coleta e mês
SELECT l.regiao, r.tipo_coleta, t.mes, SUM(f.peso_kg) AS kg
FROM dw.fato_coleta f
JOIN dw.dim_local l ON l.sk_local = f.sk_local
JOIN dw.dim_rota  r ON r.sk_rota  = f.sk_rota
JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
GROUP BY 1, 2, 3;

-- produtividade: kg por km, por rota (soma antes de dividir!)
SELECT r.nome, SUM(v.peso_total_kg) / NULLIF(SUM(v.km_percorridos), 0) AS kg_por_km
FROM dw.fato_viagem v JOIN dw.dim_rota r ON r.sk_rota = v.sk_rota
GROUP BY r.nome ORDER BY kg_por_km;
```

**Views prontas (schema `bi`, arquivo `src/sql/03_views_apoio.sql`)** — usam as perguntas da seção 2.1 como roteiro:

| View | O que entrega | Perguntas |
|---|---|---|
| `bi.v_coleta_detalhe` | Uma linha por coleta, com rota, veículo, motorista, peso e pontos | O1, O3, O4 |
| `bi.v_ocorrencia_aberta` | Ocorrências não resolvidas e horas em aberto (relativas a `bi.data_referencia()` = 01/01/2026) | O2 |
| `bi.v_produtividade_rota` | Viagens, cancelamentos, km, kg, kg/km e duração por rota | T1, T2 |
| `bi.v_resolucao_ocorrencia` | Tempo de resolução por tipo e região | T3 |
| `bi.v_toneladas_mes` | Toneladas por mês, região, bairro, tipo e tipo de coleta | E1, E2 |
| `bi.v_destinacao` | Toneladas por destino, tipo de resíduo e mês, com a capacidade do destino | E3, E4 |

### 8.6 Armadilhas (leia antes de escrever consultas)

| # | Armadilha | Como evitar |
|---|---|---|
| 1 | `fato_viagem.km_percorridos` e `duracao_min` são **NULL** nas coletas canceladas. | Use `SUM` (ignora NULL) e `NULLIF` em divisões; **não** faça média de razões, divida somas. |
| 2 | `tempo_resolucao_horas` é **semiaditiva** e **NULL** em ocorrências abertas. | Use `AVG`, nunca `SUM`; filtre `IS NOT NULL` quando preciso. |
| 3 | `dim_local` tem 12 membros "bairro inteiro" (`tipo_ponto = 'NAO_INFORMADO'`, `id_ponto_origem` NULL). | Exclua-os ao contar pontos; eles existem para ocorrências sem ponto. |
| 4 | `dim_tempo` é usada em **dois papéis** em `fato_ocorrencia` (`sk_tempo_abertura`, `sk_tempo_fechamento`). | Junte a dimensão **duas vezes**, com aliases distintos. |
| 5 | `fato_coleta` tem **uma linha por ponto e tipo**; contar linhas **não** conta coletas. | Para nº de coletas use `fato_viagem` ou `COUNT(DISTINCT id_coleta)`. |
| 6 | `dim_funcionario` serve como **motorista** (`sk_motorista`); a equipe de coletores não está no DW. | Se precisar da equipe, consulte `oltp.coleta_equipe`. |
| 7 | Dia da semana segue o padrão **ISO** (1 = segunda … 7 = domingo). Só há coletas de segunda a sexta. | Não espere sábado/domingo. |
| 8 | Os dados têm **padrões plantados** (seção 8.7): o que as consultas "descobrem" foi colocado de propósito. | Diga isso na apresentação; não trate como achado de uma cidade real. |
| 9 | `fato_destinacao` inclui o **rejeito da triagem**: o plástico, por exemplo, aparece na cooperativa e também no aterro. | Para a taxa de rejeito, compare as linhas do mesmo tipo em destinos diferentes. A soma de `fato_destinacao` por tipo bate com `fato_coleta`. |
| 10 | Os identificadores são **sem acento** (`tipo_residuo`), mas os **valores** têm (`Orgânico`). | Cuidado em filtros por texto. |

### 8.7 Estado atual e dívidas

| Item | Situação | Ação recomendada |
|---|---|---|
| **R1 — Dados uniformes** | **Resolvido em 18/10/2026.** Antes: taxa de recicláveis entre 26% e 31% em todos os bairros; ocorrências por tipo: 120 de cada. Agora há padrões (tabela abaixo). | Conferir os padrões antes de usá-los (prompt P3). |
| Nomes da equipe | Placeholder na capa e na seção 1.6. | Preencher. |
| Números de contexto (cap. 1) | Vêm de estudos achados por busca; alguns sem a fonte original localizada. | Conferir os originais antes de citar formalmente. |
| Indicador 11.6.1 (Brasil) | Valor oficial **não** confirmado. | Não citar número; ver `odsbrasil.gov.br`. |
| Dependência de ferramentas | PDFs usam Graphviz e Edge. | Não são exigidos pela disciplina. |
| Plano B de simplificação | S3 (retirar `fato_destinacao`) e S4 (retirar `fato_ocorrencia`), só se faltar tempo (até 28/10). | Ver `docs/analises/analise_complexidade_e_simplificacao.md`, seção 5. |
| SGBD / formato | Confirmar com o professor. | Ver "Perguntas ao cliente" (seção 1.6). |

**Padrões plantados nos dados (bloco P1 a P6 do script 01) e como confirmá-los:**

| # | Padrão | Valor medido em 18/10/2026 | Onde ver |
|---|---|---|---|
| P1 | Perfil por bairro: geração, adesão à seletiva e fração orgânica diferentes | Taxa de recicláveis de **7,0%** (Novo Horizonte) a **36,3%** (Parque das Águas) | `bi.v_toneladas_mes` (E2) |
| P2 | Sazonalidade: dezembro alto, fevereiro baixo; segundas mais pesadas | ≈ **107 t** em dezembro contra ≈ **53 t** em fevereiro | `bi.v_toneladas_mes` (E1) |
| P3 | Cancelamentos: mais na manhã, no 1º trimestre e com o veículo mais antigo | Manhã **11,1%** × tarde 3,6% e noite 3,8%; 1º trimestre **7,5%** × 3º trimestre 4,7%; veículo de 2016 **10,3%** | `bi.v_produtividade_rota` (T2), `dim_veiculo` (T4) |
| P4 | Duas rotas longas e de baixo rendimento (Industrial convencional; Novo Horizonte seletiva) | Menor kg/km: **2,2** (seletiva de Novo Horizonte); maior: **78,2** (convencional de Bela Vista) | `bi.v_produtividade_rota` (T1) |
| P5 | Ocorrências: mais "coleta não realizada" nos bairros de turno da manhã; tempo de resolução por tipo e região; algumas ainda abertas | Média de **29 h** (coleta não realizada) a **139 h** (volumoso); Centro **57 h** × Sul **97 h**; **53** abertas, todas há mais de 72 h; 97 de 237 ocorrências dos bairros da manhã são "coleta não realizada" contra 36 de 363 nos demais | `bi.v_resolucao_ocorrencia` (T3), `bi.v_ocorrencia_aberta` (O2) |
| P6 | Rejeito da triagem dos recicláveis, enviado ao aterro | **34,9 t** (**14,9%** dos recicláveis); plástico 35%, papel 12%, vidro 8%, metal 5% | `bi.v_destinacao` (E3) |

> [!NOTE]
> **Decisão de projeto — números que dependem da semente.** Mudar os dados altera: nº de coletas canceladas (77), pesagens (47.234), descargas (5.878), toneladas (920,3 t; 686,7 convencional; 233,6 seletiva; 25,4%), tonelagem por tipo e por destino, os 3 gráficos, a rosca da capa (constante `DONUT` em `src/documentos/gerar_pdf.py`), os números da seção 6.3 e os da tabela acima. **Reescreva-os a partir de novas consultas.**

### 8.8 Pendências com especificação

**Item 6 — Análise exploratória / mineração (1,0 ponto)**

| | |
|---|---|
| **Pede o enunciado** | "Definição de um problema e adoção de um método de mineração de dados para a resolução e explicação do método." |
| **Entrada** | Dados do DW (os padrões P1 a P6 já existem). |
| **Saída** | Um documento curto + código (`mineracao/`) com: problema, método, preparação dos dados, resultado, interpretação, ligação com a decisão. |
| **Sugestão** | **K-means** para agrupar bairros por perfil (kg por habitante, % recicláveis, cancelamentos, ocorrências). Alternativas: regressão (previsão por região) ou árvore de decisão (fatores de cancelamento). |
| **Critério de aceite** | Método **nomeado e explicado** em linguagem simples (por que esse método, como escolher *k* ou parâmetros, como interpretar); resultado reprodutível; conclusão que alimente o plano 5W2H. |
| **Cuidado** | Normalizar variáveis antes do K-means; dizer que os dados são sintéticos. |

**Itens 7, 8 e 9 — Dashboards (1,0 ponto cada; ≥ 5 consultas por nível)**

| | |
|---|---|
| **Pede o enunciado** | "Mínimo de 5 consultas (**enunciado + código**) voltadas ao nível operacional / tático / estratégico." |
| **Roteiro** | As **15 perguntas da seção 2.1** (O1–O5, T1–T5, E1–E5) já são os enunciados; falta escrever e testar o SQL (use as views `bi.*`). |
| **Formato de cada consulta** | (1) **Enunciado**: a pergunta de negócio e quem a faz; (2) **SQL**; (3) colunas da saída; (4) **como ler** em uma frase. |
| **Operacional** (consulta o **OLTP**, olha o "agora") | Coletas do dia e canceladas · ocorrências abertas há mais de 72 h · veículos mais usados na semana · pesagens acima da capacidade do veículo · coletas sem descarga registrada. |
| **Tático** (DW, rotas/turnos/meses) | kg/km por rota e por turno · cancelamentos por turno e dia da semana · tempo médio de resolução por tipo e região · ranking de rotas por produtividade · duração média da coleta por tipo de veículo. |
| **Estratégico** (DW, tendências e metas) | Evolução mensal por tipo · taxa de recuperação por região · participação de cada destino e uso da capacidade · bairros com menor taxa de recicláveis · tendência trimestral de ocorrências. |
| **Critério de aceite** | Cada consulta **roda sem erro**, devolve linhas coerentes e tem enunciado que alguém de negócio entenderia. Use funções de janela (`RANK`, `LAG`) e `ROLLUP` onde fizer sentido. |
| **Dica** | Crie *views* em `04_views_dashboards.sql` para simplificar. |

**Item 10 — Plano de ação 5W2H (1,0 ponto)**

| | |
|---|---|
| **Pede o enunciado** | "Plano de ação para orientar tarefas a partir do processo de tomada de decisão." |
| **Formato** | Tabela com **What, Why, Where, When, Who, How, How much**, uma linha por ação. |
| **Entrada** | Os achados dos dashboards e da mineração. **Cada ação deve citar a consulta ou o resultado que a justifica.** |
| **Critério de aceite** | ≥ 5 ações priorizadas; responsáveis e prazos plausíveis; custos como estimativa explícita. |

**Apresentação (40% da nota)**

| | |
|---|---|
| **Saída** | ≈ 10 slides e roteiro de 5 minutos (modelo na seção 7.3). |
| **Cuidados** | Cada integrante deve saber explicar **todo** o fluxo; ensaiar **perguntas cruzadas** (seção 7.4); tratar os conceitos extras (dimensão lixo, papéis, semiaditiva) como "decisões de projeto" de **uma frase**. |

### 8.9 Convenções para quem continuar

- **Não invente fontes nem números.** Cite apenas o que viu; marque o que for estimativa.
- Diga sempre que os dados são **sintéticos**.
- Escreva SQL **PostgreSQL**, com `schema.tabela` explícito, sem acentos nos identificadores.
- Se alterar o modelo: atualize `src/sql/01`, `src/sql/02`, regenere diagramas, dicionário e PDFs, e revise os números do texto.
- Linguagem do documento: **português do Brasil**, tom direto; explicar siglas na primeira vez.
- Para qualquer pergunta sobre o que o enunciado exige, **o enunciado vale mais que este guia**.

### 8.10 Prompts prontos

**P1 — Contexto inicial (cole primeiro)**

```text
Você vai me ajudar a continuar um trabalho acadêmico de Tópicos Especiais em Banco de Dados
(Sistemas de Informação, 9º semestre). Anexei: (1) o enunciado do professor, (2) o artigo do
método PBL e (3) o "Guia completo" do projeto.
Antes de fazer qualquer coisa: leia tudo e responda em até 15 linhas:
a) o que o enunciado exige nos itens 6 a 10 e na apresentação;
b) o que já está pronto e o que NÃO deve ser alterado (estrutura do banco);
c) quais armadilhas da seção 8.6 mais importam para mim;
d) que dúvidas você tem.
Regras: não invente números nem fontes; os dados são sintéticos; PostgreSQL; tudo em português do Brasil.
```

**P2 — Dashboards (um nível por vez)**

```text
Crie 5 consultas SQL para o dashboard [OPERACIONAL | TÁTICO | ESTRATÉGICO] deste projeto,
uma para cada pergunta correspondente da seção 2.1 (O1-O5 | T1-T5 | E1-E5), usando as views bi.*.
Para cada uma entregue: (1) enunciado em linguagem de negócio, dizendo quem faz a pergunta;
(2) SQL PostgreSQL usando as tabelas do capítulo 5 e os padrões da seção 8.5;
(3) colunas da saída; (4) como ler o resultado em uma frase.
Respeite as armadilhas da seção 8.6. Não invente colunas: use só as do dicionário.
Depois, liste o que eu devo conferir ao rodar cada consulta.
```

**P3 — Confirmar os padrões antes de concluir**

```text
Escreva consultas SQL (PostgreSQL, schemas oltp, dw e bi) que CONFIRMEM cada padrão P1 a P6 da
seção 8.7 do guia e mostrem os números. Se algum padrão não aparecer, diga e sugira o ajuste no
bloco de dados do script 01 (sem mudar a estrutura). Lembre que os padrões foram plantados:
nas conclusões, escreva que são dados sintéticos.
```

**P4 — Mineração de dados**

```text
Proponha e implemente (Python + scikit-learn, lendo do PostgreSQL) um K-means que agrupe os
bairros por perfil. Entregue: query de preparação das variáveis, normalização, escolha de k
(cotovelo e silhueta), interpretação de cada grupo em linguagem de negócio e como isso apoia a
decisão de onde expandir a coleta seletiva. Explique o método como se fosse para a turma.
```

**P5 — Plano 5W2H**

```text
Com base nestes achados dos dashboards e da mineração: [cole os resultados], monte um plano de
ação 5W2H com pelo menos 5 ações priorizadas. Cada linha deve citar o achado que a justifica.
Custos são estimativas e devem ser marcados como tal.
```

**P6 — Apresentação**

```text
Monte um roteiro de apresentação de 5 minutos e ~10 slides a partir do guia. Inclua 8 perguntas
difíceis que o professor poderia fazer e respostas curtas. Aponte onde cada integrante pode ter
mais dificuldade em responder individualmente.
```
