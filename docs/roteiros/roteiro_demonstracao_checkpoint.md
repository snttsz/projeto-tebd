# Roteiro de demonstração do checkpoint (≈ 13 minutos)

> **Para que serve:** mostrar ao professor, ao vivo, o que está **feito de fato** (itens 1 a 5 do barema) e o **planejamento** até 06/11. O PDF do professor não é para ele ler: é o roteiro visual que vocês conduzem. Quem fala em cada etapa está em branco para a equipe preencher.

## A mensagem central (decorar)

1. **O problema é de gestão**, não de tecnologia: a prefeitura não consegue responder, com números, quanto recicla, qual rota rende menos e quanto leva para resolver uma reclamação.
2. **O modelo já existe e funciona**: um banco OLTP (12 tabelas) e um Data Warehouse (4 estrelas) criados por um único script, que o professor pode rodar.
3. **O que falta está planejado**: análise exploratória, 15 consultas de dashboard e plano 5W2H, todos até 06/11.

## 1. Antes de começar (10 minutos antes)

| # | Conferir | Como |
|---|---|---|
| 1 | O banco está no ar e consistente | `python src/scripts/popular_banco.py --verificar`: todas as linhas devem sair `[ok]` |
| 2 | pgAdmin conectado | Registrar o servidor (seção 3) e abrir `cidades_sustentaveis` |
| 3 | Consultas prontas | No pgAdmin, Query Tool > abrir `docs/roteiros/consultas_demonstracao.sql` |
| 4 | PDF aberto | `docs/entregas/professor/Entrega_19-10_PROFESSOR.pdf`, na página 1 |
| 5 | Plano B à mão | Pasta `docs/diagramas/` (PNG) aberta, caso o banco falhe |
| 6 | Zoom e tela | Fonte do pgAdmin e do PDF grande o bastante para a sala |

## 2. Linha do tempo

| Min | Etapa | O que mostrar | Frase-chave | Quem |
|---|---|---|---|---|
| 0–1 | **Abertura** | PDF p. 1 (capa) e p. 3 (resumo executivo) | "Nosso projeto é o Ciclo Urbano: dados da limpeza urbana para decidir melhor. Hoje mostramos o que está pronto e o que falta." | |
| 1–3 | **O problema e o cliente** | PDF p. 4 (caso, dores, ODS 11.6) e p. 5 (questão-foco, hipóteses, escopo) | "A Prefeitura de Cidade-Modelo é fictícia. Os números oficiais divergem entre si e o dado nacional não reflete o campo." | |
| 3–4 | **O briefing do cliente** | PDF p. 6: as **15 perguntas** (O1 a E5) | "Estas 15 perguntas são o que o cliente quer saber. Elas orientaram o modelo e serão o enunciado das consultas dos dashboards." | |
| 4–5 | **Requisitos e regras** | PDF p. 7 e 8 | "Cada regra de negócio é uma restrição no banco, não só um texto." | |
| 5–7 | **OLTP: o banco que registra a operação** | PDF p. 9 a 13 (conceitual e as 3 subáreas); **pgAdmin**: tabelas e ERD (seção 3) | "12 tabelas em 3FN. Cada coleta tem rota, veículo, motorista e equipe; cada pesagem registra ponto, tipo e peso." | |
| 7–9 | **OLAP: o Data Warehouse** | PDF p. 14 (barramento) e p. 15 a 18 (as 4 estrelas) | "4 processos, 4 estrelas, 8 dimensões compartilhadas. Declaramos o grão antes de escolher dimensões e medidas." | |
| 9–11 | **Ao vivo no banco** | pgAdmin: consultas C1 a C7 (seção 4) | "Estes números saem do banco agora, não de um slide." | |
| 11–12 | **O que falta e o cronograma** | Falar a partir da seção 5 deste roteiro | "Itens 6 a 10 até 06/11, divididos assim..." | |
| 12–13 | **Perguntas ao professor** | As 6 perguntas da seção 6 | "Antes de seguir, precisamos alinhar alguns pontos com o senhor." | |

## 3. pgAdmin: preparação e o que mostrar

**Registrar o servidor (uma vez):** botão direito em *Servers* > *Register* ou *Import/Export Servers*, importando `src/scripts/pgadmin_servidor.json`. A senha **não** está no arquivo: use a do seu `.env`.

**O que mostrar no pgAdmin**

| Para provar | Onde clicar |
|---|---|
| As tabelas existem | *Databases > cidades_sustentaveis > Schemas*: três schemas, `oltp`, `dw` e `bi`, com suas tabelas e views |
| O dicionário está no banco | Em uma tabela (por exemplo `bairro`), *Columns*: a aba *Properties* de cada coluna mostra o **comentário** |
| O diagrama vem do banco | Botão direito no banco > opção de **ERD** (ou *Tools > ERD Tool*); marque as tabelas de `oltp`. *Se o nome do menu for diferente na sua versão, procure "ERD".* |
| O script cria tudo | Mostrar `src/sql/01_construcao_oltp_olap.sql` e dizer que `popular_banco.py` o executa |

> [!NOTE]
> O ERD automático do pgAdmin **não evita cruzamento de linhas**. Use-o como **prova de que o banco existe**; para **explicar**, use os diagramas do PDF (ou os PNG de `docs/diagramas/`).

## 4. Consultas ao vivo (arquivo `consultas_demonstracao.sql`)

Rode uma de cada vez e diga **sempre** que os dados são sintéticos, com padrões deliberados.

| # | Consulta | Esperado | O que dizer |
|---|---|---|---|
| C1 | Contagens OLTP × DW | 47.234 × 47.234 e 1.252 × 1.252 | "O ETL não perdeu nenhuma linha." |
| C2 | Rotas com menor kg/km (T1) | Seletiva de Novo Horizonte, **2,2 kg/km** | "Aqui o dashboard tático apontaria a rota a rever." |
| C3 | Cancelamento por turno (T2) | **Manhã 11,1%** × tarde 3,6% e noite 3,8% | "Pergunta que o coordenador de rotas faria." |
| C4 | Taxa de recicláveis por bairro (E2) | De **36,3%** a **7,0%** | "Decisão estratégica: onde ampliar a coleta seletiva." |
| C5 | Rejeito por material (E3) | Plástico **35%**, papel 12%, vidro 8%, metal 5% | "Do que vai à cooperativa, parte vira rejeito e segue ao aterro." |
| C6 | Ocorrências abertas há mais de 72 h (O2) | **53** | "Consulta operacional do supervisor." |
| C7 | Toneladas por mês (E1) | Fevereiro ≈ **53 t**, dezembro ≈ **107 t** | "Sazonalidade que o secretário acompanharia." |

> [!WARNING]
> **Seja transparente.** Estes padrões foram **colocados de propósito** nos dados sintéticos para que as consultas tenham o que mostrar. Não os apresente como descobertas de uma cidade real.

## 5. O que falta e o cronograma (para a fala)

| Item do barema | Situação | Previsão |
|---|---|---|
| 1 a 5 | Entregues e testados | 19/10 (hoje) |
| 6 · Análise exploratória (mineração) | A fazer: sugestão de agrupar bairros por perfil (K-means) | até 06/11 |
| 7 · Dashboard operacional | A fazer: 5 consultas (perguntas O1 a O5) | até 06/11 |
| 8 · Dashboard tático | A fazer: 5 consultas (T1 a T5) | até 06/11 |
| 9 · Dashboard estratégico | A fazer: 5 consultas (E1 a E5) | até 06/11 |
| 10 · Plano 5W2H | A fazer, a partir dos achados | até 06/11 |

**Divisão de tarefas:** _[preencher: quem fica com cada item]_.
**O que já adiantamos:** as 15 perguntas (enunciados), as views `bi.*` que simplificam as consultas e os padrões nos dados.

## 6. Perguntas ao professor (levar anotadas)

1. Os dashboards devem ser **apenas consultas SQL** com enunciado e código, ou também visuais?
2. Podem ser usados **dados fictícios (sintéticos)** para a prefeitura? O enunciado fala em *problemas reais*.
3. Há **SGBD obrigatório**, ou o PostgreSQL atende?
4. O método de mineração pode ser em **Python**, ou deve ser em SQL ou outra ferramenta?
5. Qual o **formato da entrega** de 06/11 (PDF, pasta compactada, repositório)?
6. Há algum **ajuste a fazer** na etapa 1, com base no que o senhor viu hoje?

> **Anote as respostas** e o feedback: o método PBL do enunciado trata a conversa com o "cliente" como parte do trabalho.

## 7. Perguntas difíceis que podem surgir

| Pergunta | Resposta curta |
|---|---|
| Os dados são reais? | Não: são sintéticos, gerados por script determinístico, com padrões deliberados. Queremos confirmar com o senhor se isso é aceito (pergunta 2). |
| Por que 4 tabelas fato e não uma? | Os processos têm grãos diferentes. Misturá-los repetiria o km da viagem em cada pesagem e inflaria as somas. |
| Onde está o dicionário de dados? | No banco (`COMMENT ON`, visível no pgAdmin) e no anexo em PDF `docs/entregas/anexo-dicionario/`. |
| Como o professor roda o projeto? | `python src/scripts/popular_banco.py --recriar` cria o banco, executa os 3 scripts e confere o resultado. |
| Por que 3FN no OLTP e estrela no OLAP? | OLTP otimiza escrita e integridade; OLAP otimiza leitura e agregação, com poucas junções. |
| O que significa "grão"? | O que uma linha da tabela fato representa. É declarado antes de escolher dimensões e medidas. |
| O ETL perdeu dados? | Não: as contagens do OLTP e do DW coincidem (consulta C1). |

## 8. Plano B (se algo falhar)

| Falha | O que fazer |
|---|---|
| Banco não sobe ou pgAdmin não conecta | Seguir com o **PDF** e os **PNG** de `docs/diagramas/`; mostrar `src/sql/01_construcao_oltp_olap.sql` como prova. Dizer que roda com `popular_banco.py`. |
| Uma consulta dá erro | Passar para a próxima; os números esperados estão na tabela da seção 4. |
| Faltou tempo | Cortar C5 a C7. Prioridade: OLTP, OLAP, C1 e C3. |
| O professor pede algo fora do roteiro | Anotar e responder na próxima etapa; não improvisar números. |

## 9. Fechamento (30 segundos)

"Os itens 1 a 5 estão prontos e verificáveis: o banco é criado e conferido por um único comando. Até 06/11 entregamos a análise exploratória, as 15 consultas e o plano de ação. Obrigado; ficamos com suas respostas e seu feedback."
