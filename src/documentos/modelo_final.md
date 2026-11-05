# Ciclo Urbano — entrega final

**Disciplina:** Tópicos Especiais em Banco de Dados  
**Professor:** Antônio Cordeiro  
**Equipe:** Carlos Erick · Carlos José · Glenda Santana · Kalvin Albuquerque  
**Entrega:** 06/11/2026  
**Tema:** gestão de resíduos sólidos urbanos e coleta seletiva · ODS 11

## 1. Problema e objetivo

A Secretaria de Serviços Urbanos da prefeitura fictícia de Cidade-Modelo precisa integrar rotas, equipes, pesagens, destinos dos resíduos e ocorrências do cidadão. Informações fragmentadas dificultam acompanhar a regularidade do serviço, a produtividade das rotas e a participação da coleta seletiva.

A questão-foco é: como integrar esses registros em um ecossistema OLTP + OLAP para apoiar decisões operacionais, táticas e estratégicas? O trabalho segue a metodologia PBL: problema de gestão → perguntas do cliente → requisitos → modelagem → carga e análise → propostas de ação.

O projeto está alinhado à meta 11.6 da ODS 11, ligada à redução do impacto ambiental das cidades e à gestão de resíduos. A base não contém geração total de resíduos e, portanto, não permite calcular integralmente o indicador 11.6.1. As conexões secundárias são com reciclagem e consumo responsável (ODS 12), impactos ambientais (ODS 13) e saúde urbana (ODS 3).

Todos os dados são **sintéticos de 2025**, gerados de forma determinística com padrões deliberados. Resultados demonstram o método; não constituem descobertas sobre uma cidade real.

## 2. Modelagem, construção e dicionário (itens 1 a 5)

O PostgreSQL organiza três schemas: `oltp`, `dw` e `bi`. O OLTP possui 12 tabelas normalizadas em 3FN, com chaves, restrições e índices. O DW contém oito dimensões e quatro fatos de grãos distintos:

| Fato | O que uma linha representa | Medidas principais |
|---|---|---|
| Coleta | Um tipo de resíduo pesado em um ponto durante uma coleta | Peso em kg |
| Viagem | Uma coleta programada, inclusive cancelada | Peso total, km, duração, pontos atendidos, indicador de cancelamento |
| Destinação | Um tipo de resíduo descarregado em um destino por coleta | Peso em kg |
| Ocorrência | Um registro do cidadão | Quantidade e horas até resolução |

Separar viagem de pesagem impede repetir a distância da viagem a cada item pesado. O ETL em SQL extrai o OLTP, gera as dimensões e alimenta os fatos. Taxas são calculadas por razões de somas; horas de resolução são analisadas por média das resolvidas.

Os documentos da entrega parcial continuam como anexos de detalhamento dos itens 1 a 5; suas listas de pendências retratam 19/10, não a situação final descrita aqui.

- [Guia completo: contextualização, requisitos, regras e modelos](../guia-completo/Entrega_19-10_GUIA_COMPLETO.md).
- [Dicionário de dados: atributos, tipos e restrições](../anexo-dicionario/Entrega_19-10_ANEXO_DICIONARIO.md).
- [Construção, dados sintéticos e ETL](../../../src/sql/01_construcao_oltp_olap.sql).
- [Dicionário no catálogo PostgreSQL](../../../src/sql/02_dicionario_comentarios.sql).
- [Views de apoio](../../../src/sql/03_views_apoio.sql).
- [Enunciado e barema](../../enunciado/enunciado.md).

## 3. Base utilizada e verificação

{{ORIGEM}}

As sete medidas de cada um dos 12 bairros foram comparadas com `base_bairros.csv` da mineração: população, quantidade de pesagens, viagens, cancelamentos, ocorrências, peso total e peso reciclável. As **84 comparações conferiram**. Os testes também confrontaram contagens e peso entre o OLTP e o DW.

{{TOTAIS}}

Essa reconciliação confirma a correspondência das medidas comparadas; não é uma auditoria de todos os registros do banco original. A origem, a versão do motor, o horário da extração e os hashes dos artefatos estão em [manifesto_dashboards.json](manifesto_dashboards.json).

## 4. Mineração exploratória (item 6)

**Problema:** quais bairros apresentam perfis semelhantes de coleta, participação de recicláveis, cancelamentos e ocorrências?

O K-means agrupa os 12 bairros com base em quatro variáveis anuais: kg coletados por habitante, percentual de recicláveis, percentual de viagens canceladas e ocorrências por mil habitantes. Os fatos são agregados separadamente antes da junção por bairro, evitando multiplicação de linhas. As variáveis são padronizadas pelo StandardScaler para que unidades diferentes não dominem as distâncias.

O algoritmo alterna a atribuição ao centro mais próximo e o recálculo dos centros. A execução usa k-means++, 50 inicializações, semente 42 e até 500 iterações. Foram comparadas soluções de dois a cinco grupos; soluções com grupos unitários não foram elegíveis. A maior silhueta elegível foi obtida com **três grupos e média 0,3637**. O cotovelo foi usado como diagnóstico visual complementar.

{{GRUPOS}}

As médias dos grupos atribuem o mesmo peso a cada bairro, independentemente da população; não devem ser confundidas com taxas municipais ponderadas. Os números dos grupos são identificadores, não um ranking.

**Revisão de Industrial:** sua silhueta individual é -0,1038, sinal de atribuição ambígua. As dez sementes adicionais produziram a mesma partição (ARI = 1), mas retirar um bairro por vez resultou em ARI mínimo de 0,7970. Esses diagnósticos indicam sensibilidade e não validam uma política pública. A ação A6 propõe usar indicadores diretos e revisar o caso antes de investir com base no grupo. Não foi alterada a classificação para esconder essa limitação.

{{REVISAO_INDUSTRIAL}}

Os **16 arquivos** da execução preservada foram conferidos com os hashes SHA-256 do manifesto, incluindo os cinco gráficos, CSVs, consulta e relatório. A mineração não precisou ser refeita.

[Relatório completo, gráficos e evidências da mineração](../../analises/kmeans/kmeans_2025_20261031T122945_177876Z/relatorio.md).

## 5. Dashboards de gestão (itens 7, 8 e 9)

Abra [painel.html](painel.html) em um navegador. A aplicação React compilada funciona offline, com fonte, ícones, dados e imagens incorporados. Reúne visão geral, os três níveis, perfis dos bairros e 5W2H, com linguagem destinada à gestão municipal. Há busca, filtros, ordenação, paginação e exportação CSV. Os códigos SQL e diagnósticos técnicos permanecem nos documentos de apoio. Barras exibem até 12 registros na ordem da tabela; gráficos mensais e trimestrais agregam o recorte selecionado. As tabelas preservam todos os registros do filtro, paginados em oito linhas. E2 abre no nível bairro e E4 em dezembro, ambos alteráveis nos filtros.

O painel é um snapshot reproduzível, não uma conexão em tempo real. Operacional: últimos sete dias completos antes de 01/01/2026, com exceção de O2, que reconstrói pendências na data de referência. Tático e estratégico: ano de 2025. T3 inclui o acompanhamento posterior das ocorrências abertas em 2025; E3 inclui descargas posteriores das coletas de 2025 e E4 usa a data de descarga no ano.

{{CONSULTAS}}

Cada nível possui **cinco consultas executadas**, totalizando 15. Seus enunciados, códigos e colunas estão em [consultas_dashboards.md](consultas_dashboards.md); os valores completos também estão em [resultados_dashboards.json](resultados_dashboards.json).

### Diferença entre 54 e 53 ocorrências

O2 retorna **54 registros sem resolução há mais de 72 horas na referência de 01/01/2026**. Uma ocorrência foi fechada depois dessa data. O número **53** dos documentos antigos é a quantidade sem resolução no estado final da base. São recortes temporais diferentes. O painel mostra a situação reconstruída e o status final em colunas separadas.

## 6. Decisões e plano de ação (item 10)

{{ACHADOS}}

O [plano 5W2H](plano_5w2h.md) reúne seis ações priorizadas, com responsáveis por função, locais, prazos, execução, custos e acompanhamento. Cada ação aponta o resultado que a motivou. D é a data de aprovação do plano pela gestão.

O orçamento incremental total proposto é **R$ 6.500,00**, uma hipótese didática sem cotação. Metas são propostas para pilotos, não previsões de resultado. A ação de análise utiliza a equipe existente, sem desembolso incremental previsto; seu custo de trabalho não foi quantificado. O K-means não estima retorno financeiro nem demonstra causalidade.

## 7. Limites e próximos passos no cenário real

- A prefeitura e os dados são fictícios; os padrões foram plantados para demonstrar a análise.
- São apenas 12 bairros, com agregação anual que oculta sazonalidade.
- Coleta por habitante não mede geração total; recicláveis coletados não equivalem a material efetivamente reciclado após a triagem.
- Menos ocorrências registradas podem refletir dificuldade de acesso ao atendimento.
- Associação entre idade do veículo e cancelamentos não comprova falha mecânica; comparar motoristas exige considerar rotas, veículos e turnos.
- A implantação real exigiria integração com fontes municipais, histórico de alterações, motivos de cancelamento, validação de pesagens e acompanhamento dos pilotos.

## 8. Reprodução e apresentação

Consulte [as instruções de execução e testes](../../../src/dashboards/README.md). O modo padrão apenas lê um snapshot do PostgreSQL configurado; o modo `--reproduzir` carrega os scripts em banco embarcado efêmero e dispensa PostgreSQL instalado. Ele não altera o banco original.

O [roteiro de apresentação](roteiro_apresentacao.md) orienta a demonstração do problema até o plano de ação. O domínio do conteúdo é individual: todos devem saber explicar grão, ETL, taxas, escolha de k e limites dos resultados.

**Critério de fechamento técnico:** itens 1 a 10 possuem materiais no pacote; as quinze consultas foram executadas, a base foi reconciliada com a mineração e os testes passaram. Ainda cabe à equipe conferir a apresentação no navegador usado em sala e ensaiar a defesa oral. Nenhuma nota é presumida.
