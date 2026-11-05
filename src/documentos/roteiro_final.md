# Ciclo Urbano — roteiro de apresentação final

Proposta de fala de aproximadamente cinco a sete minutos; a duração não foi fixada pelo enunciado fornecido. Dividir as falas com a equipe e ensaiar. Os dados são sintéticos.

## Preparação

Abrir `painel.html` no navegador e `relatorio_final.md` para consulta. Deixar os diagramas OLTP/DW da entrega parcial acessíveis. O painel funciona sem internet e sem banco conectado. Ampliar a fonte conforme a sala. Antes da apresentação, testar navegação, filtros e legibilidade no computador utilizado.

## Sequência sugerida

| Tempo | Tela / material | Fala central |
|---|---|---|
| 0:00–0:40 | Relatório final, problema | A prefeitura precisa reunir dados de coleta e atendimento para decidir com evidências. Cidade-Modelo e os dados são fictícios. A conexão principal é com a ODS 11. |
| 0:40–1:20 | Diagramas OLTP e DW | Doze tabelas registram a operação. O ETL alimenta quatro fatos e oito dimensões. Viagem e pesagem ficam separadas porque têm grãos diferentes. |
| 1:20–2:00 | Painel operacional, O2 e O4 | Há cinco perguntas operacionais. O2 mostra 54 ocorrências pendentes há mais de 72 horas em 01/01/2026; 53 continuam sem fechamento no estado final da base. O4 compara peso da coleta com capacidade nominal. |
| 2:00–2:40 | Painel tático, T1 e T2 | Há cinco perguntas táticas. A seletiva de Novo Horizonte apresenta 2,23 kg/km. Na combinação manhã/segunda, 25 das 208 viagens foram canceladas: 12,02%. Isso orienta investigação, sem provar a causa. |
| 2:40–3:20 | Painel estratégico, E2 e E3 | Há cinco perguntas estratégicas. Comparamos recicláveis por bairro e região e o rejeito por material. Plástico tem 35% de rejeito no cenário simulado. Coletar recicláveis não garante reciclá-los integralmente. |
| 3:20–4:20 | Mineração, centroides e silhuetas | Quatro variáveis foram padronizadas. K-means agrupou bairros por proximidade de perfil; três grupos tiveram a maior silhueta elegível, 0,3637. O grupo 1 reúne menor participação média de recicláveis e maior cancelamento. Industrial tem silhueta negativa e exige revisão. |
| 4:20–5:20 | Plano de ação 5W2H | As evidências motivam seis ações com responsáveis, locais, prazos e acompanhamento. O orçamento de R$ 6.500 é hipotético. Metas são propostas de pilotos, não ganhos previstos pelo algoritmo. |
| 5:20–6:00 | Relatório final, limites | As 15 consultas executaram e 84 medidas por bairro conferiram com a mineração. Não generalizamos para cidades reais, não inferimos causalidade e não calculamos integralmente o indicador 11.6.1 por falta da geração total. |

## Perguntas para ensaiar com todos os integrantes

1. **Por que OLTP e OLAP?** O primeiro preserva registros e integridade da operação; o segundo organiza medidas e dimensões para comparação e agregação.
2. **O que é grão?** O significado de uma linha do fato. Uma viagem tem muitas pesagens; misturar os grãos repete quilômetros.
3. **Como o ETL é verificado?** Comparando contagens e somas OLTP/DW e reconciliando sete medidas em cada um dos 12 bairros com a base da mineração.
4. **Por que padronizar?** Quilos por habitante, percentuais e ocorrências têm escalas diferentes; sem padronização, uma unidade pode dominar a distância.
5. **Por que três grupos?** Foi a maior silhueta entre soluções elegíveis sem grupo unitário. O cotovelo é diagnóstico complementar.
6. **Silhueta de 0,3637 é acurácia de 36%?** Não. É uma medida de separação/coerência dos agrupamentos; não há rótulos verdadeiros para calcular acurácia.
7. **Por que não mudar Industrial de grupo?** Seu valor negativo é uma limitação a investigar. Não se muda o resultado para ocultar ambiguidade; verificam-se dados, contexto e sensibilidade.
8. **Por que o painel diz 54 e o documento antigo 53?** Um conta pendências na referência de 01/01/2026; o outro, registros ainda sem fechamento no estado final da base. Uma ocorrência fechou depois da referência.
9. **O veículo antigo causa cancelamento?** Os dados mostram associação simulada; turno, rota e outros fatores podem explicar a diferença.
10. **O orçamento foi calculado pelo K-means?** Não. É uma hipótese de planejamento; o método apenas agrupa perfis e não calcula custos ou benefícios.
11. **Onde estão os cinco códigos por nível?** Nos arquivos SQL 05, 06 e 07 e no documento `consultas_dashboards.md`. O painel apresenta os resultados em linguagem de gestão; os códigos ficam nos documentos técnicos.
12. **O painel está ao vivo?** Não. Ele preserva um snapshot, com origem e horário registrados. Reexecutar o gerador atualiza os dados.

## Ensaio final

Cada integrante explica em voz alta o fluxo completo e responde a três perguntas escolhidas pelos colegas. Conferir a transição entre falas, a precisão dos números e o tempo. Não afirmar que os padrões sintéticos foram descobertos em uma prefeitura real.
