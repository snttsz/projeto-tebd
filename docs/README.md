# Documentos do projeto: como ler

Esta pasta guarda **tudo que não é código**. Cada subpasta tem um tipo de documento. Os PDFs e os `.md` de `entregas/` são **gerados** a partir de um único modelo (`../src/documentos/modelo_entrega.md`): para mudar o texto, edite o modelo e rode `python src/documentos/montar_entregas.py`.

## Mapa das pastas

| Pasta | O que tem | Para quem | Quando ler |
|---|---|---|---|
| [`enunciado/`](enunciado/) | O enunciado do professor e o artigo do método PBL (`2020.1.pdf`) | Todos | **Primeiro**, e sempre que houver dúvida do que é exigido. O enunciado vale mais que qualquer outro documento |
| [`entregas/professor/`](entregas/professor/) | Roteiro visual de ≈ 20 páginas | Equipe, para **mostrar** ao professor | No checkpoint |
| [`entregas/anexo-dicionario/`](entregas/anexo-dicionario/) | Só o dicionário de dados (item 4 do barema) | Professor, se pedir | Para consultar uma tabela ou coluna |
| [`entregas/guia-completo/`](entregas/guia-completo/) | Documento completo, com o **capítulo 8** de continuidade | Equipe e IAs assistentes | Para continuar o projeto |
| [`diagramas/`](diagramas/) | Diagramas em `.png` e `.svg`; `graficos/` tem os gráficos do DW | Todos | Para explicar o modelo |
| [`roteiros/`](roteiros/) | Roteiro de demonstração do checkpoint e as consultas ao vivo | Equipe | Antes de apresentar |
| [`analises/`](analises/) | Análise de complexidade, auditoria enunciado × entregue e o que foi resolvido | Equipe | Para entender **por que** o projeto é como é |
| [`pesquisas/`](pesquisas/) | Pesquisas na web (diagramas; abordagem e layout), com fontes | Equipe | Para conferir uma decisão ou uma fonte |

## Por onde começar (conforme o que você quer)

| Eu quero... | Leia |
|---|---|
| **Mostrar o andamento ao professor** | `roteiros/roteiro_demonstracao_checkpoint.md`, com `entregas/professor/` aberto |
| **Entender o projeto inteiro** | `entregas/guia-completo/`, capítulos 1 a 4, e os diagramas |
| **Continuar o trabalho (itens 6 a 10)** | `entregas/guia-completo/`, capítulo 8, e `analises/` (parte III) |
| **Passar o projeto para outra IA ou chat** | Anexar o PDF do guia completo e o enunciado, e colar o prompt P1 (seção 8.10 do guia) |
| **Saber o que o enunciado exige** | `enunciado/` e, na análise, a Parte II (auditoria) |
| **Consultar uma tabela ou coluna** | `entregas/anexo-dicionario/` (ou o pgAdmin, onde cada coluna tem comentário) |
| **Saber de onde veio uma decisão de layout ou de diagrama** | `pesquisas/` |

## O que cada versão da entrega contém

| Conteúdo | Professor | Anexo | Guia completo |
|---|:---:|:---:|:---:|
| Resumo, problema, ODS 11, questão-foco | ✔ (enxuto) | | ✔ |
| 15 perguntas de negócio do cliente | ✔ | | ✔ |
| Requisitos, regras de negócio | ✔ | | ✔ |
| Diagramas OLTP (conceitual + 3 subáreas) | ✔ | | ✔ |
| Diagramas OLAP (4 estrelas), matriz de barramento | ✔ | | ✔ |
| Dicionário de dados | | ✔ | ✔ (com exemplos) |
| Personas, histórias de usuário, glossário, rastreabilidade | | | ✔ |
| Método de trabalho PBL e perguntas ao professor | | | ✔ |
| Gráficos do DW, ETL, script e validação | | | ✔ |
| Situação do barema, tarefas, roteiro e perguntas de apresentação | | | ✔ |
| Capítulo 8: continuidade (ambiente, pendências, prompts) | | | ✔ |

Cada documento lista em **Referências** apenas o que ele mesmo cita, numerado pela ordem de citação.

## Os diagramas (`diagramas/`)

| Arquivo | Conteúdo |
|---|---|
| `00_arquitetura_ecossistema` | OLTP → ETL → DW → dashboards |
| `01_er_conceitual_visao_geral` | As 12 entidades, só com relacionamentos |
| `02` a `04_er_logico_*` | Subáreas A (planejamento e execução), B (pesagem e destinação) e C (território e cidadão), com colunas e chaves |
| `05` a `08_estrela_*` | Estrelas de coleta, destinação, ocorrências e viagem |
| `09_fluxo_do_residuo` | Etapas do processo, do ponto de coleta ao destino |

**Como ler:** notação *pé-de-galinha* (a bolinha é "opcional", o pé é "muitos", a barra é "um"); tabela tracejada é um *atalho* de outra subárea; cabeçalho escuro é uma **fato**, verde é uma **dimensão**. Os `.svg` são vetoriais (abra no navegador e amplie sem perder qualidade); os `.png` servem para colar em slides. Os desenhos são **gerados do banco** (`src/diagramas/`), então não divergem do esquema.

## Convenções

- **Fonte da verdade:** o enunciado. Em caso de conflito, ele vale mais que os documentos.
- **Dados sintéticos:** os números dos documentos vêm de dados fictícios, gerados por script com padrões deliberados. Isso deve ser dito sempre.
- **Números:** devem vir de uma consulta ao banco. Se os dados mudarem, atualize o texto (a seção 8.7 do guia lista o que depende dos dados).
- **PDFs e `.md` de `entregas/`:** não edite à mão; edite o modelo e regenere.
