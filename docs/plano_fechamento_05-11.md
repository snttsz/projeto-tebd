# Plano para fechar o Ciclo Urbano em 05/11/2026

## Objetivo

Concluir os itens 6 a 10 do barema, consolidar a entrega final e preparar a apresentação de 06/11. Preservar a estrutura atual do banco e trabalhar com os dados sintéticos existentes.

## Verificação do K-means

Após o pull realizado pelo usuário em 05/11, os resultados estão presentes em `docs/analises/kmeans/kmeans_2025_20261031T122945_177876Z/`. Os 16 arquivos conferiram com os hashes SHA-256 do manifesto, cujo status é `concluido`. Não é necessário refazer a mineração.

Execução em 31/10: 12 bairros, k=3, silhueta média 0,3637 e silhueta negativa para Industrial. A regra que ignorava `docs/analises/` foi removida pelo pull. A base dos dashboards foi reproduzida isoladamente e reconciliada em 84 medidas (sete medidas por bairro) com os dados da mineração.

## Sequência de execução

Tempos são estimativas de esforço, contados a partir do início. Dependem da disponibilidade do PostgreSQL e do Python.

| Ordem | Trabalho | Estimativa | Entrega e critério de conclusão |
|---|---|---|---|
| 1 | Conferir o ambiente e o banco atual | 20–30 min | Conexão funcionando; conferência de tabelas, carga e totais OLTP/DW. Não recriar o banco automaticamente. |
| 2 | Fechar a evidência do K-means (item 6) | 30–60 min | Recuperar os resultados da máquina de origem ou executar o código existente. Conferir `manifesto.json` com status `concluido`, relatório, cinco gráficos, CSVs e interpretação. Arquivar os resultados para acompanhar a entrega. |
| 3 | Dashboard operacional (item 7) | 45–60 min | Cinco consultas O1–O5 com enunciado, SQL, resultado e interpretação: cancelamentos; ocorrências acima de 72 h; km por veículo na semana; ocupação dos veículos; coletas por coletor. |
| 4 | Dashboard tático (item 8) | 45–60 min | Cinco consultas T1–T5: produtividade por rota; cancelamentos por turno/dia; resolução por tipo/região; cancelamentos por idade do veículo; produtividade/cancelamentos por motorista. |
| 5 | Dashboard estratégico (item 9) | 45–60 min | Cinco consultas E1–E5: evolução mensal; percentual de recicláveis por bairro/região; rejeito por material; participação/capacidade dos destinos; ocorrências por trimestre/região. |
| 6 | Consolidar os três painéis visuais | 45–75 min | Um painel por nível, com indicadores, tabelas ou gráficos derivados das consultas validadas. Mostrar unidades, período e identificação de dados sintéticos. Reutilizar ferramentas existentes; não depender de construir uma aplicação web. |
| 7 | Plano 5W2H (item 10) | 30–45 min | Ações ligadas a resultados conferidos; preencher o quê, por quê, onde, quando, quem, como e quanto. Custos explicitamente estimados. Meta interna: cinco ações priorizadas. |
| 8 | Consolidar documentos e pacote final | 45–60 min | Atualizar os modelos de texto, regenerar documentos, incluir SQL dos três níveis, mineração e 5W2H; conferir links e arquivos. Garantir que os resultados não dependam de pastas ignoradas ausentes. |
| 9 | Preparar e ensaiar a apresentação | 30–45 min | Material cobrindo problema → OLTP → ETL → DW → dashboards → mineração → ações. Cada integrante explica o fluxo e responde às decisões de modelagem e limitações. |

Estimativa total sequencial: aproximadamente 6 a 8 horas.

## Regras de validação

- Cada nível deve ter pelo menos cinco consultas com enunciado e código: este é o mínimo explícito do enunciado. Os painéis visuais complementam essa entrega.
- Usar a data de referência da base sintética nas consultas operacionais; não usar o relógio atual inadvertidamente sobre dados de 2025.
- Agregar processos de grãos diferentes antes de combinar resultados; não multiplicar quilômetros ou pesos em junções.
- Distinguir percentual coletado de recicláveis de reciclagem efetiva após a triagem.
- Conferir totais e denominadores; evitar média simples de percentuais de grupos com tamanhos diferentes.
- Explicar limitações do K-means e revisar Industrial; não apresentar grupos como ranking ou prova de causalidade.
- Não afirmar cálculo completo do indicador ODS 11.6.1: falta a geração total de resíduos.
- Não editar documentos gerados de `docs/entregas/` manualmente; atualizar os modelos.

## Prioridade se o prazo apertar

Garantir primeiro as 15 consultas executadas e documentadas, a evidência da mineração e o 5W2H. Em seguida, consolidar os painéis visuais e a apresentação. Evitar mudanças estruturais, nova aplicação web e recursos visuais que atrasem a entrega dos requisitos.

## Checklist de saída

- [x] Banco conferido em reprodução isolada dos scripts; 84 medidas conciliadas com a mineração. Banco original não acessado.
- [x] Mineração com artefatos acessíveis, 16 hashes conferidos e silhuetas recalculadas independentemente; Industrial documentado.
- [x] Cinco consultas operacionais executadas e documentadas.
- [x] Cinco consultas táticas executadas e documentadas.
- [x] Cinco consultas estratégicas executadas e documentadas.
- [x] Três painéis consolidados em HTML offline, com busca, filtros, tabelas completas e SQL.
- [x] Plano 5W2H com seis ações sustentadas pelos resultados; metas e custos hipotéticos explícitos.
- [x] Relatório final, roteiro de apresentação e pacote de entrega gerados.
- [ ] Conferência visual no navegador do computador da apresentação (automação de navegador indisponível nesta sessão).
- [ ] Apresentação ensaiada pela equipe.

Resultado técnico: a interface foi migrada para React, com visão geral, gráficos mensais e de composição, exportação CSV, ordenação e paginação. Os 15 testes passaram, incluindo SQL em PostgreSQL embarcado e controles React em DOM de teste. Os materiais finais estão em `docs/entregas/final/`; o ZIP é gerado em `output/` pelo script `src/scripts/empacotar_entrega.ps1`. A entrega parcial de 19/10 permanece preservada como histórico.
