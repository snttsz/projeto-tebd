# Ciclo Urbano — Laboratório de Dados para Cidades Sustentáveis

**Gestão de resíduos sólidos urbanos e coleta seletiva · ODS 11**

| | |
|---|---|
| **Disciplina** | Tópicos Especiais em Banco de Dados — Prof. Antônio Cordeiro |
| **Entrega** | Parcial (feedback) · 19/10/2026 · itens 1 a 5 do barema |
| **Entrega final** | 06/11/2026 · itens 6 a 10 + apresentação |
| **SGBD** | PostgreSQL 17 (scripts compatíveis com 15+) |
| **Equipe** | _[preencher os nomes dos integrantes]_ |

<!--PROF-->
<!-- KICKER: TÓPICOS ESPECIAIS EM BANCO DE DADOS · ENTREGA PARCIAL -->
<!-- ROTULO: Entrega parcial · 19/10/2026 -->
<!--/PROF-->
<!--GUIA-->
<!-- KICKER: GUIA COMPLETO DE IMPLEMENTAÇÃO · USO INTERNO DA EQUIPE -->
<!-- ROTULO: Guia completo · uso interno -->
<!--/GUIA-->

<!-- INICIO -->

## Resumo executivo

**O problema.** A limpeza urbana é um dos serviços mais visíveis de uma prefeitura, mas os dados que a sustentam — rotas, pesagens, destinos, reclamações — costumam viver em planilhas e papéis que não conversam entre si. O resultado é uma gestão que não sabe responder, com números, perguntas simples: *quanto foi coletado? O que foi para reciclagem? Qual rota rende menos? Quanto tempo leva para resolver uma reclamação?*

**A proposta.** Um ecossistema de dados open-source com **dois ambientes no mesmo PostgreSQL**: um banco **OLTP** (12 tabelas, 3FN) que registra a operação do dia a dia e um **Data Warehouse OLAP** (4 tabelas fato e 8 dimensões, esquema estrela) que consolida o histórico para análise. Um ETL em SQL liga os dois.

**O que já está pronto (itens 1 a 5):**

| Item | Entrega | Onde |
|---|---|---|
| 1 | Contextualização, requisitos e justificativa da ODS | Capítulos 1 e 2 |
| 2 | Modelagem OLTP — **12 entidades** (mínimo: 6) | Capítulo 3 |
| 3 | Modelagem OLAP — 4 fatos, 8 dimensões | Capítulo 4 |
| 4 | Dicionário de dados (gerado do próprio banco) | Capítulo 5 |
| 5 | Script SQL de construção + carga + ETL, **testado** | Capítulo 6 e pasta `src/sql/` |

**Em números (dados sintéticos de 2025):** 12 bairros · 343,5 mil habitantes · 240 pontos de coleta · 24 rotas · 1.252 coletas (77 canceladas) · 47.234 pesagens · **920 toneladas** coletadas · 600 ocorrências de cidadãos. O script cria, popula e confere tudo sozinho.

**O que falta (06/11):** análise exploratória com mineração de dados, 15 consultas de dashboard (5 operacionais, 5 táticas, 5 estratégicas) e o plano de ação 5W2H.

---

## 1 · O problema

*Neste capítulo: o caso da prefeitura, as dores que justificam o projeto, a base legal, o alinhamento com a ODS 11 e a pergunta que o banco de dados precisa responder.*

### 1.1 O caso: a Prefeitura de Cidade-Modelo

Para tornar o problema concreto, o projeto trabalha com uma prefeitura **fictícia**, a de **Cidade-Modelo**: 12 bairros, cerca de 343 mil habitantes e uma Secretaria de Serviços Urbanos que mantém dois serviços de coleta — a **convencional** (orgânico e rejeito) e a **seletiva** (papel, plástico, vidro e metal), esta última com pontos de entrega voluntária (**PEV**) e uma cooperativa de catadores como destino.

Hoje, cada informação vive num lugar: a escala de caminhões numa planilha, o peso na balança do aterro, as reclamações no atendimento telefônico e as rotas na cabeça do encarregado. Quando a secretária pergunta "estamos reciclando mais do que no ano passado?", ninguém consegue responder sem dias de trabalho manual — e a resposta chega tarde para decidir qualquer coisa.

### 1.2 As dores (e o que a literatura mostra)

| Dor da prefeitura | Evidência encontrada na pesquisa |
|---|---|
| **Os números oficiais divergem entre si.** Não há padronização do que é "coleta seletiva". | Estimativas do percentual de municípios com coleta seletiva variam de 14% a 60%, conforme a fonte (CEMPRE, SNIS, IBGE, Abrelpe) [3]. |
| **O dado nacional não reflete o campo.** | Estudo no semiárido baiano encontrou disparidade entre os dados do SNIS e os observados em campo [2]. |
| **Pouco se recicla.** | A coleta seletiva existia em 38,7% dos municípios (SNIS 2019), com 13,5 kg/hab/ano de recicláveis coletados [4]; a Abrelpe estima que o Brasil recicle entre 4,5% e 8,7% do que produz [5]. |
<!--GUIA-->
| **Rotas mal dimensionadas custam caro.** | Em estudo de coleta domiciliar, o percurso excedente chegou a 30,84%, acima do limite de referência de 20% [6]. A gestão de rotas em Sorocaba (SP) rendeu +2,75 t/mês de recicláveis [6]. |
| **O rejeito consome o que a cooperativa recebe.** | Cooperativas reportam de 21% (Sudeste) a 35% (Centro-Oeste) de rejeito no material recebido (levantamento de empresa privada, 42 organizações) [5]. |
| **Otimizar uma métrica pode piorar outra.** | Em Paraíba do Sul (RJ), a rota "mais rápida" aumentou a distância em 92,6% [7]. |
<!--/GUIA-->

<!--GUIA-->
> [!WARNING]
> **Limitação.** Esses números são **contexto**, não metas do projeto: vêm de estudos e levantamentos de fontes diversas, algumas privadas. Não existe benchmark nacional padronizado de kg/km; no projeto, kg/km será um indicador **interno** para comparar rotas entre si.
<!--/GUIA-->

**A lição para o projeto:** o problema não é só *coletar* dados, é ter **dados locais integrados, com definições únicas** (o que é peso coletado, o que é ocorrência resolvida) e um histórico que permita comparar rotas, bairros e períodos.

### 1.3 Base legal e ODS 11

<!--GUIA-->
A **Política Nacional de Resíduos Sólidos** (Lei 12.305/2010) estabelece uma ordem de prioridade para a gestão: **não geração → redução → reutilização → reciclagem → tratamento → disposição final ambientalmente adequada dos rejeitos** [1]. Um ecossistema de dados municipal precisa ser capaz de *medir cada degrau* dessa escada. A tabela mostra como o modelo faz isso:

| Degrau da PNRS | O que o banco mede | Onde |
|---|---|---|
| Não geração / redução | Toneladas por bairro e por mês ao longo do tempo | `fato_coleta` × `dim_tempo`, `dim_local` |
| Reutilização | *(fora do escopo — exigiria cadastro de ecopontos de reuso)* | — |
| **Reciclagem** | Peso de recicláveis coletado e entregue à cooperativa | `fato_coleta` (`reciclavel`), `fato_destinacao` |
| **Tratamento** | Orgânico enviado à usina de compostagem | `fato_destinacao` × `dim_destino` |
| **Disposição final** | Rejeito enviado ao aterro | `fato_destinacao` × `dim_destino` |

<!--/GUIA-->
O projeto se alinha à **ODS 11 — Cidades e Comunidades Sustentáveis**, em especial à **meta 11.6** (reduzir o impacto ambiental negativo per capita das cidades, com atenção à gestão de resíduos municipais). O indicador da ONU para essa meta, o **11.6.1**, mede a *proporção de resíduos sólidos urbanos regularmente coletados e com destinação final adequada, em relação ao total gerado, por cidade* [8]. O DW do projeto fornece o **numerador** (o que foi coletado e para onde foi); o denominador (resíduo gerado) exigiria dados de geração que a prefeitura ainda não tem.

| ODS | Conexão com o projeto |
|---|---|
| **11** (principal) | Cidades limpas e inclusivas; gestão de resíduos municipais (meta 11.6); inclusão de catadores via cooperativa. |
| **12** — Consumo e produção responsáveis | Reciclagem e redução: taxa de recuperação e fluxo para a cooperativa. |
| **13** — Ação contra a mudança do clima | Desviar orgânicos do aterro (compostagem) e reduzir quilômetros rodados. |
| **3** — Saúde e bem-estar | Descarte irregular é foco de vetores; ocorrências por bairro ajudam a priorizar. |

### 1.4 Cliente e partes interessadas

<!--PROF-->
Seguindo o método PBL (seção 1.6), a equipe atua como **consultoria de dados** e a **Prefeitura de Cidade-Modelo é o cliente**. Como não há uma prefeitura real à disposição, as necessidades abaixo foram deduzidas do conhecimento do domínio [9] e estão sujeitas à validação com o professor, que faz o papel de cliente.

| Parte interessada | O que precisa decidir ou saber | Nível de dashboard |
|---|---|---|
| Secretaria de Serviços Urbanos | Metas, orçamento e onde ampliar a coleta seletiva | Estratégico |
| Coordenação de rotas e frota | Produtividade das rotas, turnos e cancelamentos | Tático |
| Supervisão de operação | Coletas do dia e ocorrências abertas | Operacional |
| Cooperativa de catadores | Volume e qualidade dos recicláveis recebidos | Tático / estratégico |
| Moradores | Coleta regular e reclamação resolvida | Atendimento (ocorrências) |
<!--/PROF-->
<!--GUIA-->
Como não há uma prefeitura real à disposição para entrevistas, o projeto usa **proto-personas** — personas construídas a partir do conhecimento do domínio, técnica adequada quando os usuários reais não estão acessíveis [9]. Os nomes são fictícios.

| Persona | Papel | O que precisa decidir | Nível do dashboard |
|---|---|---|---|
| **Marina**, secretária de Serviços Urbanos | Decide orçamento, metas e expansão | Onde ampliar a coleta seletiva? Estamos cumprindo a meta de recuperação? | Estratégico |
| **Paulo**, coordenador de rotas | Planeja rotas, frota e turnos | Quais rotas rendem menos kg por km? Por que há mais cancelamentos de manhã? | Tático |
| **Carla**, supervisora de operação | Acompanha o dia | Quais coletas de hoje não saíram? Quais reclamações estão abertas há mais de 72 h? | Operacional |
| **Dona Lúcia**, presidente da cooperativa | Recebe e tria os recicláveis | Quanto material chegará esta semana? Vem muito rejeito misturado? | Tático / estratégico |
| **Seu João**, morador | Gera resíduo e reclama | A coleta passa no meu dia? Minha reclamação foi resolvida? | Atendimento (ocorrências) |
<!--/GUIA-->

### 1.5 Questão-foco, hipóteses e lacunas (método PBL)

No PBL, o problema vem antes do conteúdo: a equipe analisa o cenário, levanta hipóteses e identifica o que ainda precisa aprender [10].

> **Questão-foco:** *como integrar os dados da coleta de resíduos de uma prefeitura em um ecossistema OLTP + OLAP que sustente decisões operacionais, táticas e estratégicas e meça o avanço da reciclagem?*

| Hipótese | Como o projeto vai testá-la (06/11) |
|---|---|
| H1 — Há rotas com produtividade (kg/km) bem abaixo da média. | Dashboard tático sobre `fato_viagem`. |
| H2 — Cancelamentos se concentram em certos turnos. | Dashboard tático (cancelamento por turno). |
| H3 — O tempo de resolução de ocorrências varia por tipo e região. | Dashboard operacional/tático sobre `fato_ocorrencia`. |
| H4 — A taxa de recicláveis difere entre regiões e indica onde expandir a seletiva. | Dashboard estratégico + análise exploratória. |

<!--GUIA-->
**Lacunas de conhecimento da equipe** (a estudar até 06/11): técnicas de mineração de dados adequadas (agrupamento vs. regressão), funções de janela do PostgreSQL para as consultas táticas e estratégicas, e boas práticas de *views* para dashboards.
<!--/GUIA-->

### 1.6 Método de trabalho em grupo (PBL)

O enunciado indica, como método de trabalho em grupo, o artigo de Linge e Parsons (2006) [13], que descreve o uso de **aprendizagem baseada em problemas (PBL)**: equipes pequenas assumem o papel de **consultores** de um **cliente** fictício, recebem um problema descrito em **linguagem de negócio**, com **informações propositalmente incompletas**, e precisam levantar perguntas, propor uma solução e **apresentá-la à turma para crítica**. A tabela mostra como cada elemento do método foi aplicado.

| Elemento do método [13] | Como foi aplicado neste projeto |
|---|---|
| **Grupo pequeno e fixo** (4 a 5 pessoas que permanecem juntas) | Uma única equipe nas duas etapas do cronograma; composição e papéis na tabela abaixo. |
| **Papel profissional** (consultores de um cliente) | A equipe atua como consultoria de dados; a Prefeitura de Cidade-Modelo é o cliente fictício. O próprio artigo usa um cliente fictício realista. |
| **Cenário orientado ao negócio** | O problema (seções 1.1 e 1.2) é descrito em linguagem de gestão de resíduos; o vocabulário técnico só aparece a partir do capítulo 3. |
| **Briefing incompleto e perguntas ao cliente** | Há lacunas deliberadas (por exemplo, não há dados reais de geração de resíduos). As dúvidas viram a lista de perguntas ao cliente, abaixo. |
| **Sessões encadeadas**, cada uma sobre a anterior | Etapa 1 (19/10): requisitos, modelagem, dicionário e script (itens 1 a 5). Etapa 2 (06/11): análise, dashboards e plano de ação (itens 6 a 10), construída sobre a etapa 1. |
| **Apresentação e crítica** | Cada etapa termina com apresentação e debate; a equipe ensaia antes com perguntas cruzadas. |
| **Produto: lista priorizada** | O plano de ação 5W2H (item 10) prioriza as ações que decorrem dos dashboards. |

#### Composição da equipe e papéis (a preencher pela equipe)

| Integrante | Papel na etapa 1 (itens 1 a 5) | Papel na etapa 2 (itens 6 a 10) |
|---|---|---|
| _[nome]_ | _[ex.: requisitos e contextualização]_ | _[ex.: análise exploratória]_ |
| _[nome]_ | _[ex.: modelagem OLTP e script]_ | _[ex.: dashboard operacional]_ |
| _[nome]_ | _[ex.: modelagem OLAP e ETL]_ | _[ex.: dashboards tático e estratégico]_ |
| _[nome]_ | _[ex.: dicionário e documentação]_ | _[ex.: plano 5W2H e apresentação]_ |

#### Perguntas ao cliente (professor), a esclarecer

| # | Pergunta | Por que importa |
|---|---|---|
| 1 | Os dashboards devem ser apenas consultas SQL com enunciado e código, ou também visuais? | Define o esforço dos itens 7 a 9. |
| 2 | Podem ser usados dados fictícios (sintéticos) para a prefeitura? | O enunciado fala em problemas reais de prefeituras. |
| 3 | Há SGBD obrigatório ou o PostgreSQL atende? | O script de construção é específico de SGBD. |
| 4 | O método de mineração pode ser executado em Python, ou deve ser em SQL ou outra ferramenta? | Define o item 6. |
| 5 | Qual o formato da entrega de 06/11 (PDF, pasta compactada, repositório)? | Evita retrabalho. |
| 6 | Há algum ajuste a fazer na etapa 1, com base no feedback de 19/10? | Segue a lógica de sessões encadeadas do método. |

### 1.7 Escopo: o que está dentro e o que está fora

| Dentro do escopo | Fora do escopo (decisão consciente) |
|---|---|
| Registro de coletas, pesagens, descargas e ocorrências | Roteirização automática / otimização de rotas |
| DW histórico com 4 processos de negócio | Rastreamento GPS em tempo real |
| Dashboards em SQL (consultas) e análise exploratória | Aplicativo ou interface web para o cidadão |
| Dados **sintéticos** que simulam 2025, com padrões deliberados | Integração com sistemas reais (SNIS/SINIR) |

---

## 2 · Requisitos

<!--PROF-->
*Neste capítulo: o que o cliente precisa saber (perguntas de negócio), o que o sistema deve fazer e quais regras de negócio o banco de dados precisa garantir.*
<!--/PROF-->
<!--GUIA-->
*Neste capítulo: o que o cliente precisa saber (perguntas de negócio), o que o sistema deve fazer (histórias de usuário), as regras que ele precisa garantir, o vocabulário do domínio e a rastreabilidade entre requisito, tabela e consulta.*
<!--/GUIA-->

### 2.0 Necessidades do cliente: perguntas de negócio

Seguindo o método PBL [13], a necessidade do cliente é descrita em **linguagem de gestão**, não de tecnologia. As 15 perguntas abaixo são o "briefing" da prefeitura: cada uma indica quem a faz, onde está a resposta no banco e qual *view* a apoia. Elas orientam o modelo (capítulos 3 e 4) e serão o **enunciado** das consultas dos itens 7, 8 e 9 do barema.

<!--PROF-->
| ID | Pergunta do cliente | Quem pergunta | Responde com |
|---|---|---|---|
| **Operacional** | *o que está acontecendo agora* (consulta o OLTP) | | |
| O1 | Quais coletas foram canceladas e de qual rota, veículo e motorista? | Supervisão de operação | `coleta`, `rota`, `veiculo`, `funcionario` |
| O2 | Quais ocorrências estão abertas há mais de 72 horas? | Supervisão de operação | `ocorrencia`, `bairro` |
| O3 | Quais veículos mais rodaram na semana? | Coordenação de frota | `coleta`, `veiculo` |
| O4 | Qual a taxa de ocupação dos veículos (peso coletado ÷ capacidade)? | Coordenação de frota | `coleta`, `coleta_item`, `veiculo` |
| O5 | Quantas coletas cada coletor fez na semana? | Supervisão de operação | `coleta_equipe`, `funcionario`, `coleta` |
| **Tático** | *como estamos indo* (consulta o DW) | | |
| T1 | Quais rotas rendem menos quilos por quilômetro? | Coordenação de rotas | `fato_viagem`, `dim_rota` |
| T2 | Em que turno e dia da semana mais se cancelam coletas? | Coordenação de rotas | `fato_viagem`, `dim_rota`, `dim_tempo` |
| T3 | Quanto tempo leva, em média, resolver cada tipo de ocorrência em cada região? | Atendimento | `fato_ocorrencia`, `dim_ocorrencia`, `dim_local` |
| T4 | Os veículos mais antigos cancelam mais coletas? | Coordenação de frota | `fato_viagem`, `dim_veiculo` |
| T5 | Há motoristas com produtividade ou cancelamentos muito diferentes dos demais? | Coordenação de rotas | `fato_viagem`, `dim_funcionario` |
| **Estratégico** | *para onde vamos* (consulta o DW) | | |
| E1 | Como evolui a quantidade coletada, por mês e por tipo de resíduo? | Secretaria | `fato_coleta`, `dim_tempo`, `dim_tipo_residuo` |
| E2 | Qual a taxa de recicláveis por região e bairro? Onde expandir a coleta seletiva? | Secretaria | `fato_coleta`, `dim_local`, `dim_tipo_residuo` |
| E3 | Quanto do material enviado à cooperativa vira rejeito, por tipo de material? | Secretaria e cooperativa | `fato_destinacao`, `dim_destino`, `dim_tipo_residuo` |
| E4 | Qual a participação de cada destino e quanto da capacidade mensal ele usa? | Secretaria | `fato_destinacao`, `dim_destino` |
| E5 | Como evoluem as ocorrências por trimestre e região? | Secretaria | `fato_ocorrencia`, `dim_tempo`, `dim_local` |
<!--/PROF-->
<!--GUIA-->
| ID | Pergunta do cliente | Quem pergunta | Responde com | View de apoio |
|---|---|---|---|---|
| **Operacional** | *o que está acontecendo agora* (consulta o OLTP) | | | |
| O1 | Quais coletas foram canceladas e de qual rota, veículo e motorista? | Supervisão de operação | `coleta`, `rota`, `veiculo`, `funcionario` | `bi.v_coleta_detalhe` |
| O2 | Quais ocorrências estão abertas há mais de 72 horas? | Supervisão de operação | `ocorrencia`, `bairro` | `bi.v_ocorrencia_aberta` |
| O3 | Quais veículos mais rodaram na semana? | Coordenação de frota | `coleta`, `veiculo` | `bi.v_coleta_detalhe` |
| O4 | Qual a taxa de ocupação dos veículos (peso coletado ÷ capacidade)? | Coordenação de frota | `coleta`, `coleta_item`, `veiculo` | `bi.v_coleta_detalhe` |
| O5 | Quantas coletas cada coletor fez na semana? | Supervisão de operação | `coleta_equipe`, `funcionario`, `coleta` | consulta direta |
| **Tático** | *como estamos indo* (consulta o DW) | | | |
| T1 | Quais rotas rendem menos quilos por quilômetro? | Coordenação de rotas | `fato_viagem`, `dim_rota` | `bi.v_produtividade_rota` |
| T2 | Em que turno e dia da semana mais se cancelam coletas? | Coordenação de rotas | `fato_viagem`, `dim_rota`, `dim_tempo` | `bi.v_produtividade_rota` |
| T3 | Quanto tempo leva, em média, resolver cada tipo de ocorrência em cada região? | Atendimento | `fato_ocorrencia`, `dim_ocorrencia`, `dim_local` | `bi.v_resolucao_ocorrencia` |
| T4 | Os veículos mais antigos cancelam mais coletas? | Coordenação de frota | `fato_viagem`, `dim_veiculo` | consulta direta |
| T5 | Há motoristas com produtividade ou cancelamentos muito diferentes dos demais? | Coordenação de rotas | `fato_viagem`, `dim_funcionario` | consulta direta |
| **Estratégico** | *para onde vamos* (consulta o DW) | | | |
| E1 | Como evolui a quantidade coletada, por mês e por tipo de resíduo? | Secretaria | `fato_coleta`, `dim_tempo`, `dim_tipo_residuo` | `bi.v_toneladas_mes` |
| E2 | Qual a taxa de recicláveis por região e bairro? Onde expandir a coleta seletiva? | Secretaria | `fato_coleta`, `dim_local`, `dim_tipo_residuo` | `bi.v_toneladas_mes` |
| E3 | Quanto do material enviado à cooperativa vira rejeito, por tipo de material? | Secretaria e cooperativa | `fato_destinacao`, `dim_destino`, `dim_tipo_residuo` | `bi.v_destinacao` |
| E4 | Qual a participação de cada destino e quanto da capacidade mensal ele usa? | Secretaria | `fato_destinacao`, `dim_destino` | `bi.v_destinacao` |
| E5 | Como evoluem as ocorrências por trimestre e região? | Secretaria | `fato_ocorrencia`, `dim_tempo`, `dim_local` | consulta direta |
<!--/GUIA-->

<!--GUIA-->
**Adequação ao propósito.** O artigo do método [13] insiste que a solução deve se ajustar ao propósito do cliente, e não ser a mais sofisticada. Por isso cada elemento do modelo foi conferido contra as 15 perguntas:

| Camada | Elementos e as perguntas que os usam |
|---|---|
| **Fatos** | `fato_coleta`: E1, E2 · `fato_viagem`: T1, T2, T4, T5 · `fato_destinacao`: E3, E4 · `fato_ocorrencia`: T3, E5 |
| **Dimensões** | `dim_tempo`: T2, E1, E5 · `dim_local`: E2, T3, E5 · `dim_tipo_residuo`: E1, E2, E3 · `dim_rota`: T1, T2 · `dim_veiculo`: T4 · `dim_funcionario`: T5 · `dim_destino`: E3, E4 · `dim_ocorrencia`: T3, E5 |
| **Tabelas do OLTP** | `coleta`: O1, O3, O4 · `rota`: O1 · `veiculo`: O1, O3, O4 · `funcionario`: O1, O5 · `coleta_item`: O4 · `coleta_equipe`: O5 · `ocorrencia`: O2 · `bairro`: O2 · `descarga`, `destino_final`, `tipo_residuo`, `ponto_coleta`: alimentam o DW (E1 a E5) |

<!--/GUIA-->
> [!NOTE]
> **Decisão de projeto — o modelo não é maior que as perguntas.** Os 12 elementos do OLTP, os 4 fatos e as 8 dimensões respondem a pelo menos uma pergunta. Um elemento sem pergunta que o justifique seria cortado.

### 2.1 Histórias de usuário (com prioridade MoSCoW)

Prioridade: **M**ust (obrigatório) · **S**hould (importante) · **C**ould (desejável).

| ID | História | Critério de aceite | Prior. |
|---|---|---|---|
| US01 | Como **supervisora**, quero registrar cada execução de rota (veículo, motorista, equipe, horários, km) para saber o que foi feito no dia. | Uma rota só tem uma coleta por data; hora de término > hora de início; status válido. | M |
| US02 | Como **coletor**, quero registrar o peso retirado em cada ponto por tipo de resíduo para medir a coleta. | Peso ≥ 0; um registro por coleta + ponto + tipo. | M |
| US03 | Como **operador da balança**, quero registrar a descarga em cada destino para rastrear o que foi para onde. | Cada descarga referencia a coleta, o destino e o tipo; peso > 0. | M |
| US04 | Como **atendente**, quero registrar e encerrar ocorrências de moradores para medir o tempo de resposta. | Ocorrência só fica "resolvida" com data de fechamento ≥ abertura. | M |
| US05 | Como **secretária**, quero ver a evolução mensal de toneladas por tipo e região para acompanhar metas. | Consulta sobre o DW devolve toneladas por mês × região × tipo. | M |
| US06 | Como **presidente da cooperativa**, quero saber quanto material reciclável chega e em que proporção do total para planejar a triagem. | Recicláveis ÷ total coletado; toneladas por destino. | M |
| US07 | Como **coordenador**, quero comparar rotas por kg/km e por turno para redistribuir a frota. | kg/km por rota calculável a partir do DW. | S |
| US08 | Como **supervisora**, quero listar ocorrências abertas há mais de 72 h para priorizar o atendimento. | Consulta operacional sobre o OLTP. | S |
| US09 | Como **coordenador**, quero ver cancelamentos de coleta por turno e dia da semana para investigar causas. | `qtd_cancelada` somável por turno/dia. | S |
| US10 | Como **secretária**, quero identificar bairros com baixa taxa de recicláveis para decidir onde ampliar a seletiva. | Taxa por bairro/região no DW. | C |

### 2.2 Requisitos funcionais

<!--PROF-->
| ID | Requisito |
|---|---|
| RF01 | Cadastrar bairros, pontos (incl. PEV), rotas, veículos, funcionários, tipos de resíduo e destinos finais. |
| RF02 | Registrar coletas (rota, data, veículo, motorista, equipe, horários, km, status). |
| RF03 | Registrar o peso coletado por ponto e por tipo de resíduo. |
| RF04 | Registrar descargas por destino e tipo de resíduo. |
| RF05 | Registrar ocorrências do cidadão e o ciclo até a resolução. |
| RF06 | Consolidar o histórico em um DW com dimensões conformes. |
| RF07 | Permitir consultas operacionais, táticas e estratégicas sobre OLTP/DW. |
<!--/PROF-->
<!--GUIA-->
| ID | Requisito | Histórias |
|---|---|---|
| RF01 | Cadastrar bairros, pontos (incl. PEV), rotas, veículos, funcionários, tipos de resíduo e destinos finais. | US01–US04 |
| RF02 | Registrar coletas (rota, data, veículo, motorista, equipe, horários, km, status). | US01, US09 |
| RF03 | Registrar o peso coletado por ponto e por tipo de resíduo. | US02 |
| RF04 | Registrar descargas por destino e tipo de resíduo. | US03, US06 |
| RF05 | Registrar ocorrências do cidadão e o ciclo até a resolução. | US04, US08 |
| RF06 | Consolidar o histórico em um DW com dimensões conformes. | US05–US10 |
| RF07 | Permitir consultas operacionais, táticas e estratégicas sobre OLTP/DW. | US05–US10 |
<!--/GUIA-->

### 2.3 Requisitos não funcionais (mensuráveis)

| ID | Requisito | Como verificar |
|---|---|---|
| RNF01 | SGBD relacional open-source. | PostgreSQL 17 (compatível com 15+). |
| RNF02 | OLTP normalizado até a 3FN, com integridade referencial. | 15 chaves estrangeiras · 28 `CHECK` · 9 `UNIQUE` · 64 colunas `NOT NULL`. |
| RNF03 | OLAP em esquema estrela, com chaves substitutas. | 8 dimensões com `sk_*`; fatos só referenciam `sk_*`. |
| RNF04 | Carga completa reexecutável por um único script. | `DROP SCHEMA … CASCADE` no início; execução sem erro. |
| RNF05 | Contagens do OLTP e do DW devem coincidir. | Consulta de verificação no fim do script (capítulo 6). |
| RNF06 | Dicionário de dados mantido no catálogo do banco. | `COMMENT ON` em 100% das tabelas e colunas (0 colunas sem comentário). |
| RNF07 | Tempo de carga completa (dados + ETL) abaixo de 1 minuto em máquina comum. | Medido na execução: **≈ 4 s** no ambiente de desenvolvimento. |

### 2.4 Regras de negócio e onde o banco as garante

> [!IMPORTANT]
> **Regras de negócio** não ficam só no texto: cada uma é uma restrição do banco, para que dado inválido nem entre.

| ID | Regra | Garantia no banco |
|---|---|---|
| RN01 | Cada bairro tem no máximo uma rota convencional e uma seletiva. | `UNIQUE (id_bairro, tipo_coleta)` em `rota` |
| RN02 | Uma rota só executa uma vez por data. | `UNIQUE (id_rota, data_coleta)` em `coleta` |
| RN03 | O término de uma coleta é posterior ao início. | `CHECK ck_coleta_horas` |
| RN04 | Convencional coleta orgânico e rejeito; seletiva coleta recicláveis. | Regra aplicada na carga/aplicação (documentada) |
| RN05 | Cada tipo de resíduo tem uma destinação padrão; o rejeito da triagem dos recicláveis segue ao aterro. | `destinacao_padrao` + `CHECK` de domínio; rejeito registrado em `descarga` |
| RN06 | Ocorrência é "resolvida" se, e somente se, tem data de fechamento ≥ abertura. | `CHECK ck_ocorrencia_status` e `ck_ocorrencia_datas` |
| RN07 | Um mesmo tipo de resíduo não se repete no mesmo ponto da mesma coleta. | `UNIQUE (id_coleta, id_ponto, id_tipo_residuo)` |
| RN08 | Peso nunca é negativo. | `CHECK (peso_kg >= 0)` |

### 2.5 Glossário do domínio

| Termo | Significado no projeto |
|---|---|
| **RDO** | Resíduo sólido domiciliar (o "lixo de casa"). |
| **Coleta convencional** | Coleta de orgânico e rejeito, em dias fixos por bairro. |
| **Coleta seletiva** | Coleta de recicláveis secos (papel, plástico, vidro, metal). |
| **PEV** | Ponto de Entrega Voluntária: contêiner onde o morador leva recicláveis. |
| **Rejeito** | O que não tem aproveitamento e vai ao aterro (destino final). |
| **Compostagem** | Transformação do orgânico em adubo na usina. |
| **Destino final** | Instalação que recebe o resíduo: aterro, cooperativa, usina, central de perigosos. |
| **Grão** | O que representa uma linha de uma tabela fato. |
| **Chave substituta (`sk`)** | Identificador artificial de uma dimensão, independente do sistema de origem. |
| **ETL** | Extrair, transformar e carregar dados do OLTP para o DW. |

### 2.6 Matriz de rastreabilidade

Liga cada requisito ao modelo e às consultas previstas para a entrega final. Cada linha tem de apontar para ao menos uma tabela e uma consulta.

| Requisito | Tabelas OLTP | Fato / dimensões (DW) | Dashboard previsto (06/11) |
|---|---|---|---|
| RF02 · US01 | `coleta`, `coleta_equipe` | `fato_viagem`, `dim_rota`, `dim_veiculo` | Operacional: coletas do dia e canceladas |
| RF03 · US02 | `coleta_item`, `ponto_coleta` | `fato_coleta`, `dim_local` | Tático: kg por ponto e por rota |
| RF04 · US03/06 | `descarga`, `destino_final` | `fato_destinacao`, `dim_destino` | Estratégico: destino por tipo de resíduo |
| RF05 · US04/08 | `ocorrencia` | `fato_ocorrencia`, `dim_ocorrencia` | Operacional: ocorrências abertas > 72 h |
| RF06 · US05 | todas | `fato_coleta` × `dim_tempo` | Estratégico: evolução mensal por região |
| RF07 · US07/09 | `coleta`, `rota` | `fato_viagem` | Tático: kg/km e cancelamentos por turno |
| RF07 · US10 | `bairro`, `coleta_item` | `fato_coleta`, `dim_local` | Estratégico: taxa de recicláveis por bairro |

---

## 3 · Modelagem OLTP

*Neste capítulo: como o modelo foi construído em três níveis — conceitual, lógico e físico — e as decisões por trás de cada tabela.*

### 3.1 O ecossistema em uma imagem

![Figura 1 · Arquitetura do ecossistema de dados](diagramas/00_arquitetura_ecossistema.png)

A operação grava no **OLTP**; um **ETL** em SQL alimenta o **DW**; os dashboards e a mineração consomem o DW (e, no nível operacional, o próprio OLTP). Tudo roda no mesmo PostgreSQL, separado por *schemas*.

<!--GUIA-->
![Figura 2 · Fluxo do resíduo: cada etapa do processo vira um registro no banco](diagramas/09_fluxo_do_residuo.png)

<!--/GUIA-->
<!--PROF-->
### 3.2 Modelo conceitual e lógico: 12 entidades em 3 subáreas

O modelo foi dividido em **três subáreas** para poder ser lido sem se perder: uma visão geral só com entidades e relacionamentos (Figura 3) e um diagrama detalhado por subárea (Figuras 4 a 6). Notação **pé-de-galinha**; as tabelas tracejadas são *atalhos* de entidades de outra subárea. O modelo está em **3FN**, com 15 chaves estrangeiras e restrições `CHECK` e `UNIQUE` que garantem as regras de negócio da seção 2.4.

| Subárea | Entidades | Pergunta que responde |
|---|---|---|
| **A · Planejamento e execução** | `rota`, `coleta`, `coleta_equipe`, `veiculo`, `funcionario` | Quem coletou, com qual veículo, em qual rota, em qual dia? |
| **B · Pesagem e destinação** | `coleta_item`, `descarga`, `tipo_residuo`, `destino_final` | O que foi pesado, de que tipo e para onde foi? |
| **C · Território e cidadão** | `bairro`, `ponto_coleta`, `ocorrencia` | Onde? E o que os moradores reportaram? |

![Figura 3 · Modelo conceitual (visão geral): entidades e relacionamentos, sem atributos](diagramas/01_er_conceitual_visao_geral.png)

![Figura 4 · Subárea A — Planejamento e execução da coleta](diagramas/02_er_logico_A_planejamento_execucao.png)

![Figura 5 · Subárea B — Pesagem e destinação](diagramas/03_er_logico_B_pesagem_destinacao.png)

![Figura 6 · Subárea C — Território e atendimento ao cidadão](diagramas/04_er_logico_C_territorio_cidadao.png)

<!--/PROF-->
<!--GUIA-->
### 3.2 Nível conceitual: 12 entidades em 3 subáreas

O modelo foi dividido em **três subáreas** para poder ser lido sem se perder: uma visão geral só com entidades e relacionamentos, e depois um diagrama detalhado por subárea.

![Figura 3 · Modelo conceitual (visão geral): entidades e relacionamentos, sem atributos](diagramas/01_er_conceitual_visao_geral.png)

| Subárea | Entidades | Pergunta que responde |
|---|---|---|
| **A · Planejamento e execução** | `rota`, `coleta`, `coleta_equipe`, `veiculo`, `funcionario` | Quem coletou, com qual veículo, em qual rota, em qual dia? |
| **B · Pesagem e destinação** | `coleta_item`, `descarga`, `tipo_residuo`, `destino_final` | O que foi pesado, de que tipo e para onde foi? |
| **C · Território e cidadão** | `bairro`, `ponto_coleta`, `ocorrencia` | Onde? E o que os moradores reportaram? |

### 3.3 Nível lógico/físico: um diagrama por subárea

Notação **pé-de-galinha**. Tabelas tracejadas são *atalhos* de entidades que pertencem a outra subárea (aparecem só para completar o relacionamento). Os tipos são os do PostgreSQL.

![Figura 4 · Subárea A — Planejamento e execução da coleta](diagramas/02_er_logico_A_planejamento_execucao.png)

**Como ler:** uma `rota` pertence a um bairro e é executada várias vezes ao longo do ano (cada execução é uma `coleta`). Cada `coleta` usa um `veiculo`, tem um motorista (`funcionario`) e uma equipe de coletores — a equipe é uma relação N:N resolvida pela associativa `coleta_equipe`.

![Figura 5 · Subárea B — Pesagem e destinação](diagramas/03_er_logico_B_pesagem_destinacao.png)

**Como ler:** durante uma `coleta`, cada pesagem (`coleta_item`) registra *quanto de qual tipo de resíduo saiu de qual ponto*. No fim, o caminhão faz uma `descarga` por tipo em um `destino_final`; a `descarga` também registra o **rejeito da triagem**, a parte dos recicláveis que a cooperativa não aproveita e que segue ao aterro. `coleta_item` é a **tabela de maior volume** do banco (47.234 linhas no exemplo).

![Figura 6 · Subárea C — Território e atendimento ao cidadão](diagramas/04_er_logico_C_territorio_cidadao.png)

**Como ler:** o `bairro` contém pontos e origina ocorrências. A ocorrência pode apontar para um ponto específico (`id_ponto` é opcional — por isso o círculo no lado do ponto) ou só para o bairro, como no caso de descarte irregular em terreno baldio.

<!--/GUIA-->
### 3.4 Decisões de modelagem

> [!NOTE]
> **Decisão de projeto — `coleta` × `coleta_item`.** O cabeçalho da viagem (rota, veículo, horário) foi separado do detalhe da pesagem (ponto, tipo, peso). Misturar os dois repetiria rota e veículo em cada pesagem e violaria a 2FN.

> [!NOTE]
> **Decisão de projeto — `coleta_equipe`.** A equipe tem de 2 a vários coletores por coleta, e cada coletor trabalha em várias coletas: relação N:N, resolvida por uma tabela associativa de chave composta.

> [!NOTE]
> **Decisão de projeto — domínios por `CHECK`.** Status, tipos e categorias são listas fixas e curtas; `CHECK` em vez de tabelas de domínio mantém o modelo enxuto sem perder integridade.

> [!NOTE]
> **Decisão de projeto — `tipo_residuo.destinacao_padrao`.** Liga o tipo ao *tipo de destino* esperado e permite à carga calcular, sem consulta manual, para onde cada material deve ir.

**Normalização (3FN).** Nenhum atributo não-chave depende de outro não-chave: dados de bairro (região, população) não se repetem em ponto, rota ou ocorrência; tipo de resíduo e destino são catálogos; cada fato sobre coleta mora na tabela da coleta.

**Índices.** 10 índices cobrem as chaves estrangeiras mais consultadas e as datas (`coleta.data_coleta`, `ocorrencia.data_abertura`), base dos dashboards operacionais.

---

## 4 · Modelagem OLAP

<!--PROF-->
*Neste capítulo: como o Data Warehouse foi desenhado seguindo os quatro passos de Kimball [12], a matriz de barramento e as quatro estrelas.*
<!--/PROF-->
<!--GUIA-->
*Neste capítulo: como o Data Warehouse foi desenhado seguindo os quatro passos de Kimball [12], as quatro estrelas, e o ETL que o alimenta.*
<!--/GUIA-->

### 4.1 Os quatro passos de Kimball aplicados

| Passo | Decisão neste projeto |
|---|---|
| **1 · Processo de negócio** | Quatro: **coleta** (o que foi retirado), **viagem** (como a coleta andou), **destinação** (para onde foi) e **ocorrência** (o que o cidadão reportou). |
| **2 · Grão** | Declarado *antes* das dimensões, no nível mais atômico: pesagem por ponto e tipo (coleta); uma coleta (viagem); descarga por destino e tipo; uma ocorrência. |
| **3 · Dimensões** | Quem, o quê, onde, quando: tempo, local, tipo de resíduo, rota, veículo, funcionário (motorista), destino e ocorrência. |
| **4 · Fatos** | Só medidas numéricas no grão: peso, km, duração, pontos atendidos, cancelamentos, tempo de resolução. |

### 4.2 Matriz de barramento

Cada linha é um processo (fato); cada coluna, uma dimensão. As dimensões usadas por mais de um fato são **conformes**: têm as mesmas chaves e atributos em todas as estrelas, o que permite comparar processos diferentes (*drill-across*).

| Dimensão | `fato_coleta` | `fato_viagem` | `fato_destinacao` | `fato_ocorrencia` |
|---|:---:|:---:|:---:|:---:|
| `dim_tempo` | ✔ | ✔ | ✔ | ✔ (2 papéis) |
| `dim_local` | ✔ | | | ✔ |
| `dim_tipo_residuo` | ✔ | | ✔ | |
| `dim_rota` | ✔ | ✔ | ✔ | |
| `dim_veiculo` | ✔ | ✔ | ✔ | |
| `dim_funcionario` | ✔ (motorista) | ✔ (motorista) | | |
| `dim_destino` | | | ✔ | |
| `dim_ocorrencia` | | | | ✔ |

### 4.3 As quatro estrelas

Em cada diagrama, a tabela **fato** (cabeçalho escuro) fica no centro e as **dimensões** (verdes) ao redor. O **grão** vem escrito dentro da fato e a **aditividade** das medidas, na nota.

![Figura 7 · Estrela 1 — Coleta de resíduos](diagramas/05_estrela_1_coleta.png)

![Figura 8 · Estrela 2 — Destinação final](diagramas/06_estrela_2_destinacao.png)

![Figura 9 · Estrela 3 — Atendimento ao cidadão (ocorrências)](diagramas/07_estrela_3_ocorrencias.png)

![Figura 10 · Estrela 4 — Viagem de coleta (produtividade)](diagramas/08_estrela_4_viagem.png)

> [!NOTE]
> **Decisão de projeto — por que 4 fatos e não 1.** Os processos têm **grãos diferentes**. Misturá-los numa só tabela repetiria o km da viagem em cada pesagem, e somar km daria um total inflado. A `fato_viagem` guarda o km uma única vez por coleta; a `fato_coleta` guarda o peso por ponto e tipo.

### 4.4 Medidas, aditividade e hierarquias

| Fato | Medida | Aditividade | Observação |
|---|---|---|---|
| `fato_coleta` | `peso_kg` | **aditiva** | Pode ser somada por qualquer dimensão. |
| `fato_viagem` | `km_percorridos`, `duracao_min`, `peso_total_kg`, `qtd_pontos_atendidos`, `qtd_cancelada` | **aditivas** | `km` e `duracao` são NULL nas coletas canceladas (não rodaram). `SUM(qtd_cancelada)` = nº de cancelamentos. |
| `fato_destinacao` | `peso_kg` | **aditiva** | |
| `fato_ocorrencia` | `qtd_ocorrencias` | aditiva | |
| `fato_ocorrencia` | `tempo_resolucao_horas` | **semiaditiva** | Usar **média**, nunca soma; NULL = ainda em aberto. |

<!--GUIA-->
| Dimensão | Hierarquia (drill-down) |
|---|---|
| `dim_tempo` | Ano › Semestre › Trimestre › Mês › Dia |
| `dim_local` | Região › Bairro › Ponto de coleta |
| `dim_tipo_residuo` | Categoria › Tipo |
| `dim_rota` | Região › Bairro › Rota |
| `dim_destino` | Tipo de destino › Instalação |

> [!NOTE]
> **Decisão de projeto — SCD tipo 1.** Todas as dimensões sobrescrevem o valor antigo quando algo muda (ex.: um veículo trocar de tipo). Nesta versão não há necessidade de preservar histórico de atributos; se houvesse (ex.: bairro mudar de região), passaríamos a SCD tipo 2 com data de vigência.

> [!NOTE]
> **Decisão de projeto — "bairro inteiro" em `dim_local`.** Ocorrências sem ponto específico apontam para um membro do bairro (`tipo_ponto = 'NAO_INFORMADO'`). Assim a fato nunca tem chave nula.

<!--/GUIA-->
### 4.5 ETL: do OLTP ao DW

O ETL é feito inteiramente em SQL (`INSERT … SELECT`), na parte 4 do script, em uma ordem que respeita as dependências:

| Etapa | O que faz | Transformação |
|---|---|---|
| 1 | `dim_tempo` | Gera o calendário 2025–2026 com `generate_series`; calcula mês, trimestre, nome do dia, fim de semana. |
| 2 | Dimensões | Copia os cadastros e **desnormaliza** (bairro e região dentro de `dim_local` e `dim_rota`); cria `sk_*`. |
| 3 | `dim_ocorrencia` | Combinações distintas de tipo, canal e status. |
| 4 | `fato_coleta` | `coleta_item` → *lookup* das `sk_*` por `id_origem`. |
| 5 | `fato_viagem` | Agrega itens por coleta (peso e pontos distintos); calcula duração em minutos; marca cancelamentos. |
| 6 | `fato_destinacao` | `descarga` → *lookup* das `sk_*`. |
| 7 | `fato_ocorrencia` | Calcula `tempo_resolucao_horas`; liga ao membro "bairro inteiro" quando não há ponto. |

### 4.6 O DW em ação (dados reais do banco)

Os gráficos abaixo foram gerados **a partir das tabelas fato**, mostrando que o modelo responde a perguntas de negócio. Lembrete: os dados são sintéticos, mas foram gerados com **padrões deliberados** (perfil de cada bairro, sazonalidade, cancelamentos por turno), para que as consultas tenham o que mostrar. Não representam uma cidade real.

![Figura 11 · Toneladas coletadas por mês e por tipo de coleta (fato_coleta × dim_tempo × dim_rota)](diagramas/graficos/g1_toneladas_por_mes.png)

![Figura 12 · Toneladas por tipo de resíduo (fato_coleta × dim_tipo_residuo)](diagramas/graficos/g2_toneladas_por_tipo.png)

![Figura 13 · Destinação final (fato_destinacao × dim_destino)](diagramas/graficos/g3_destinacao_final.png)

**Leitura:** das **920,3 t** coletadas em 2025, **25,4%** (233,6 t) são recicláveis. Desses, 198,7 t chegaram à cooperativa como material aproveitável e 34,9 t (**14,9%**) viraram rejeito da triagem e seguiram ao aterro. Além disso, 354,6 t de orgânico foram à usina de compostagem e 332,2 t de rejeito comum ao aterro (367,1 t no total). Esses números são os que a PNRS pede para distinguir: reciclagem, tratamento e disposição final.

---

## 5 · Dicionário de dados

*Gerado automaticamente do catálogo do PostgreSQL: tipos, nulidade, chaves e restrições são os reais; as descrições vêm de `COMMENT ON` (arquivo `02_dicionario_comentarios.sql`).*<!--GUIA--> *Na versão completa, a coluna Exemplo traz valores reais do banco.*<!--/GUIA-->

**Legenda:** **PK** chave primária · **FK** chave estrangeira (`→ tabela.coluna`) · **serial** autoincrementado · **DD** dimensão degenerada · `sk_*` chave substituta.

### 5.1 O que significa NULL

| Coluna | Significado do NULL |
|---|---|
| `ponto_coleta.numero`, `latitude`, `longitude` | Ainda não informado/geocodificado. |
| `destino_final.cnpj` | Destino sem CNPJ cadastrado (ex.: ponto informal). |
| `coleta.hora_fim`, `km_percorridos` | Coleta ainda não terminada **ou** cancelada. |
| `ocorrencia.id_ponto` | Ocorrência do bairro, sem ponto específico. |
| `ocorrencia.data_fechamento` | Ocorrência ainda não resolvida. |
| `dim_local.id_ponto_origem`, `logradouro` | Membro "bairro inteiro" (sem ponto). |
| `fato_viagem.km_percorridos`, `duracao_min` | Coleta cancelada (não rodou). |
| `fato_ocorrencia.sk_tempo_fechamento`, `tempo_resolucao_horas` | Ocorrência em aberto. |

### 5.2 Tabelas e colunas

{{DICIONARIO}}

---

## 6 · Script de construção e validação

*Neste capítulo: o que cada arquivo faz, como executar e como conferir que tudo funcionou.*

### 6.1 Arquivos

| Arquivo | Conteúdo |
|---|---|
| `src/sql/01_construcao_oltp_olap.sql` | Cria os schemas `oltp` e `dw`, todas as tabelas, restrições e índices; carrega dados de exemplo; executa o ETL e exibe a conferência de volumes. |
| `src/sql/02_dicionario_comentarios.sql` | Grava o dicionário no catálogo (`COMMENT ON TABLE/COLUMN`). Executar depois do primeiro. |
| `src/sql/03_views_apoio.sql` | Views de apoio aos dashboards (schema `bi`), para a entrega de 06/11. Executar depois dos dois anteriores. |
| `docs/diagramas/` | Diagramas em **PNG** e **SVG**; o código-fonte e o gerador estão em `src/diagramas/`. |
| `docs/pesquisas/` | Pesquisas que embasaram os diagramas e o documento. |

| Parte do script | Descrição |
|---|---|
| 1 | DDL do OLTP: 12 tabelas, PK, FK, `UNIQUE`, `CHECK`, 10 índices. |
| 2 | DDL do OLAP: 8 dimensões, 4 fatos, 12 índices. |
| 3 | Dados de exemplo determinísticos (2025), com padrões deliberados — sempre os mesmos números a cada execução. |
| 4 | ETL OLTP → OLAP. |
| 5 | Consulta de verificação de volumes. |

### 6.2 Como executar

```bash
# 1) Criar o banco
createdb -U postgres cidades_sustentaveis

# 2) Estruturas, dados de exemplo e ETL
psql -U postgres -d cidades_sustentaveis -f src/sql/01_construcao_oltp_olap.sql

# 3) Dicionário de dados no catálogo
psql -U postgres -d cidades_sustentaveis -f src/sql/02_dicionario_comentarios.sql

# 4) Views de apoio aos dashboards (opcional nesta etapa)
psql -U postgres -d cidades_sustentaveis -f src/sql/03_views_apoio.sql
```

O script começa com `DROP SCHEMA … CASCADE`, então pode ser reexecutado quantas vezes for preciso. Para criar o banco e executar os três scripts em ordem, já conferindo o resultado: `python src/scripts/popular_banco.py --recriar`.

### 6.3 Resultado validado

Executado em PostgreSQL 17.11 **sem erros**. Todas as contagens do OLTP batem com as do DW:

| Origem (OLTP) | Linhas | Destino (DW) | Linhas |
|---|---:|---|---:|
| `coleta_item` | 47.234 | `fato_coleta` | 47.234 |
| `coleta` | 1.252 | `fato_viagem` | 1.252 |
| `descarga` | 5.878 | `fato_destinacao` | 5.878 |
| `ocorrencia` | 600 | `fato_ocorrencia` | 600 |

**Conferências cruzadas:** o total de **920,3 t** é o mesmo em `fato_coleta` e em `fato_viagem`; o total descarregado coincide com o coletado (diferença de 0,6 kg em 920 mil, por arredondamento); as **77 coletas canceladas** (6,2%) aparecem tanto no OLTP quanto em `SUM(qtd_cancelada)`; e **0 colunas** ficaram sem descrição no dicionário.

### 6.4 Exemplo de consulta no DW

```sql
-- Toneladas por região e tipo de coleta
SELECT l.regiao, r.tipo_coleta, ROUND(SUM(f.peso_kg) / 1000, 1) AS toneladas
FROM dw.fato_coleta f
JOIN dw.dim_local l ON l.sk_local = f.sk_local
JOIN dw.dim_rota  r ON r.sk_rota  = f.sk_rota
GROUP BY l.regiao, r.tipo_coleta
ORDER BY l.regiao, r.tipo_coleta;
```

---

## 7 · Situação do barema e próximos passos

*Neste capítulo: o que já foi entregue, o que falta e como o cronograma se encaixa nas datas do enunciado.*

### 7.1 Situação do barema e cronograma

| Marco do enunciado | Data | Conteúdo |
|---|---|---|
| Parcial do projeto (feedback) | 19/10/2026 | Itens 1 a 5 |
| Entrega do projeto | 06/11/2026 | Itens 1 a 10 |
| Início das apresentações | 06/11/2026 | Apresentação do projeto |

| # | Item | Situação | O que falta |
|---|---|---|---|
| 1 | Contextualização | ✅ Entregue | Revisão final. |
| 2 | Modelagem OLTP | ✅ Entregue | — |
| 3 | Modelagem OLAP | ✅ Entregue | — |
| 4 | Dicionário de dados | ✅ Entregue | — |
| 5 | Script de construção | ✅ Entregue e testado | — |
| 6 | Análise exploratória | ⏳ 06/11 | Definir o problema e o método de mineração; explicar o método. |
| 7 | Dashboard operacional | ⏳ 06/11 | 5 consultas (enunciado + SQL). |
| 8 | Dashboard tático | ⏳ 06/11 | 5 consultas (enunciado + SQL). |
| 9 | Dashboard estratégico | ⏳ 06/11 | 5 consultas (enunciado + SQL). |
| 10 | Plano de ação 5W2H | ⏳ 06/11 | A partir dos achados dos dashboards. |

### 7.2 Divisão sugerida de tarefas

| Quem | Responsabilidade |
|---|---|
| Pessoa A | Itens 6 (análise exploratória) e 10 (5W2H) |
| Pessoa B | Item 7 (dashboard operacional) |
| Pessoa C | Itens 8 e 9 (táticos e estratégicos) |
| Todos | Revisão cruzada e ensaio da apresentação |

> [!TIP]
> **Dica de apresentação.** O **domínio do conteúdo é avaliado individualmente** (25% da nota de apresentação). Cada integrante deve saber explicar *todo* o modelo, não só a parte que fez.

### 7.3 Roteiro de 5 minutos

1. **Problema** — dados de limpeza urbana dispersos; números oficiais que divergem; ODS 11.6.
2. **OLTP** — 12 tabelas em 3FN: rota → coleta → pesagem → descarga; ocorrências do cidadão.
3. **OLAP** — 4 estrelas, 8 dimensões, grão declarado, matriz de barramento.
4. **ETL e validação** — um script cria tudo; contagens batem.
5. **Próximos passos** — dashboards em 3 níveis e plano 5W2H.

### 7.4 Perguntas prováveis e como responder

| Pergunta | Resposta curta |
|---|---|
| Por que o OLTP está em 3FN e o OLAP em estrela? | OLTP otimiza escrita e integridade (sem redundância); OLAP otimiza leitura e agregação (poucas junções, dimensões desnormalizadas). |
| O que é o grão e por que declará-lo primeiro? | É o que uma linha da fato representa; define quais dimensões e medidas fazem sentido e evita somas duplicadas. |
| Por que 4 fatos? | Porque os processos têm grãos diferentes; misturar inflaria somas (ex.: km repetido em cada pesagem). |
| Por que chaves substitutas? | Isolam o DW do sistema de origem, permitem histórico (SCD) e juntam mais rápido que chaves naturais. |
| Por que `CHECK` e não tabelas de domínio? | Listas curtas e estáveis; mantém o modelo enxuto sem perder integridade. |
| Por que SCD tipo 1? | Não há exigência de histórico de atributos; evita complexidade. Trocaríamos para tipo 2 se houvesse. |
| Os dados são reais? | Não: são sintéticos, gerados por script determinístico, para validar o modelo. |
| O que `tempo_resolucao_horas` ser semiaditiva significa? | Somar não faz sentido; deve-se usar média por tipo/região. |

{{CAP8}}

---

## Referências

1. BRASIL. **Lei nº 12.305, de 2 de agosto de 2010**: Política Nacional de Resíduos Sólidos. (Hierarquia de gestão, art. 9º — conferir no texto consolidado do Planalto.) Resumos consultados: SEMIL-SP, *Política Nacional de Resíduos Sólidos*, semil.sp.gov.br.
2. Estudo sobre consórcio de resíduos no semiárido baiano: disparidade entre dados do SNIS e do campo. Rev. Ciências Exatas e Ambientais, UCP. seer.ucp.br.
3. Levantamento comparativo de estimativas de coleta seletiva (CEMPRE, SNIS, IBGE, Abrelpe). Repositório da UFC, repositorio.ufc.br.
4. Artigo com base no SNIS 2019 sobre coleta seletiva (38,7% dos municípios; 13,5 kg/hab/ano). periodicos.ufpb.br (GAIA).
5. ECYCLE. *Até 35% dos resíduos recebidos por cooperativas acabam como rejeito, aponta estudo nacional*. ecycle.com.br. (Estimativa da Abrelpe de 4,5% a 8,7% de reciclagem no Brasil, citada em estudo de coleta seletiva.)
6. Estudos de coleta domiciliar e roteirização (percurso excedente de 30,84%; caso de Sorocaba-SP). Resultados obtidos por busca; **localizar o artigo original antes de citar formalmente**.
7. Estudos de roteirização de coleta (Paraíba do Sul-RJ; Monte Carmelo-MG). repositorio.ufpb.br; revistasufj.emnuvens.com.br.
8. UNEP / UN-Habitat. **SDG indicator 11.6.1** — proportion of municipal solid waste collected and managed in controlled facilities. sdgs.unep.org.
9. Técnicas de levantamento de requisitos e identificação de partes interessadas, incluindo proto-personas (DIO; UFSC; TRT9/RUP; BDTD-IBICT).
10. Aprendizagem Baseada em Problemas em disciplinas de banco de dados. SBC — Workshop sobre Educação em Computação. sol.sbc.org.br.
11. MINISTÉRIO DAS CIDADES. **Glossário de indicadores SINISA — Resíduos**. gov.br/cidades.
12. KIMBALL, R.; ROSS, M. **The Data Warehouse Toolkit**. 3. ed. Wiley, 2013. (Processo de quatro passos, grão, matriz de barramento — conforme sínteses consultadas.)
13. LINGE, N.; PARSONS, D. **Problem-based learning as an effective tool for teaching computer network design**. IEEE Transactions on Education, v. 49, n. 1, p. 5-10, fev. 2006. DOI 10.1109/TE.2005.852600. (Método de trabalho em grupo indicado no enunciado.)

<!--GUIA-->
> As referências 1–10 estão detalhadas, com links, em `docs/pesquisas/02_pesquisa_abordagem_e_layout_do_documento.md`. Valores de contexto são secundários e devem ser conferidos nas fontes originais antes de qualquer uso formal.
<!--/GUIA-->
