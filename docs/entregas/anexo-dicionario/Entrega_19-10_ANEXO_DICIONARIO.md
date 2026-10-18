# Ciclo Urbano — Laboratório de Dados para Cidades Sustentáveis

**Gestão de resíduos sólidos urbanos e coleta seletiva · ODS 11**

| | |
|---|---|
| **Disciplina** | Tópicos Especiais em Banco de Dados — Prof. Antônio Cordeiro |
| **Entrega** | Parcial (feedback) · 19/10/2026 · itens 1 a 5 do barema |
| **Entrega final** | 06/11/2026 · itens 6 a 10 + apresentação |
| **SGBD** | PostgreSQL 17 (scripts compatíveis com 15+) |
| **Equipe** | _[preencher os nomes dos integrantes]_ |

<!-- KICKER: ANEXO · DICIONÁRIO DE DADOS (ITEM 4 DO BAREMA) -->
<!-- ROTULO: Anexo · Dicionário de dados -->

<!-- INICIO -->

## 1 · Dicionário de dados

*Gerado automaticamente do catálogo do PostgreSQL: tipos, nulidade, chaves e restrições são os reais; as descrições vêm de `COMMENT ON` (arquivo `02_dicionario_comentarios.sql`).*
**Legenda:** **PK** chave primária · **FK** chave estrangeira (`→ tabela.coluna`) · **serial** autoincrementado · **DD** dimensão degenerada · `sk_*` chave substituta.

### 1.1 O que significa NULL

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

### 1.2 Tabelas e colunas


#### <span class='tag tag-oltp'>oltp</span> `bairro`

Bairros do município; base territorial para rotas, pontos e indicadores per capita.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_bairro` | integer | Não | serial<br>PK | Identificador do bairro (PK, sequencial). |
| `nome` | varchar(80) | Não | UNIQUE | Nome oficial do bairro (único). |
| `regiao` | varchar(10) | Não | CHECK regiao IN (CENTRO, NORTE, SUL, LESTE, OESTE) | Região administrativa: CENTRO, NORTE, SUL, LESTE ou OESTE. |
| `populacao` | integer | Não | CHECK populacao > 0 | População residente estimada (habitantes). |
| `area_km2` | numeric(8,2) | Não | CHECK area_km2 > 0 | Área territorial em km². |

#### <span class='tag tag-oltp'>oltp</span> `ponto_coleta`

Local físico onde resíduos são coletados (domicílio, comércio, PEV etc.).

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_ponto` | integer | Não | serial<br>PK | Identificador do ponto de coleta (PK). |
| `id_bairro` | integer | Não | FK → bairro.id_bairro | Bairro onde o ponto está localizado (FK bairro). |
| `tipo_ponto` | varchar(15) | Não | CHECK tipo_ponto IN (RESIDENCIAL, COMERCIAL, CONDOMINIO, ORGAO_PUBLICO, PEV) | Natureza do ponto: RESIDENCIAL, COMERCIAL, CONDOMINIO, ORGAO_PUBLICO ou PEV (Ponto de Entrega Voluntária). |
| `logradouro` | varchar(120) | Não | — | Nome da rua/avenida. |
| `numero` | varchar(10) | Sim | — | Número do imóvel (texto, aceita "s/n"). |
| `latitude` | numeric(9,6) | Sim | CHECK latitude >= -90 AND latitude <= 90 | Latitude em graus decimais (-90 a 90). |
| `longitude` | numeric(9,6) | Sim | CHECK longitude >= -180 AND longitude <= 180 | Longitude em graus decimais (-180 a 180). |
| `ativo` | boolean | Não | DEFAULT true | Indica se o ponto ainda é atendido. |

#### <span class='tag tag-oltp'>oltp</span> `tipo_residuo`

Catálogo de tipos de resíduo com categoria e destinação padrão.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_tipo_residuo` | integer | Não | serial<br>PK | Identificador do tipo de resíduo (PK). |
| `nome` | varchar(60) | Não | UNIQUE | Nome do tipo de resíduo (único). |
| `categoria` | varchar(12) | Não | CHECK categoria IN (ORGANICO, REJEITO, RECICLAVEL, PERIGOSO, VOLUMOSO) | Categoria: ORGANICO, REJEITO, RECICLAVEL, PERIGOSO ou VOLUMOSO. |
| `reciclavel` | boolean | Não | — | Indica se o material é reciclável. |
| `destinacao_padrao` | varchar(20) | Não | CHECK destinacao_padrao IN (ATERRO_SANITARIO, COOPERATIVA, USINA_COMPOSTAGEM, CENTRAL_PERIGOSOS) | Tipo de destino final esperado para o resíduo. |

#### <span class='tag tag-oltp'>oltp</span> `veiculo`

Frota de veículos de coleta.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_veiculo` | integer | Não | serial<br>PK | Identificador do veículo (PK). |
| `placa` | char(7) | Não | UNIQUE | Placa Mercosul (7 caracteres, única). |
| `tipo` | varchar(15) | Não | CHECK tipo IN (COMPACTADOR, BAU_SELETIVA, CACAMBA, CAMINHAO_BAU) | COMPACTADOR, BAU_SELETIVA, CACAMBA ou CAMINHAO_BAU. |
| `capacidade_kg` | integer | Não | CHECK capacidade_kg > 0 | Capacidade de carga em kg (> 0). |
| `ano_fabricacao` | smallint | Não | CHECK ano_fabricacao >= 1990 AND ano_fabricacao <= 2100 | Ano de fabricação. |
| `ativo` | boolean | Não | DEFAULT true | Indica se o veículo está em operação. |

#### <span class='tag tag-oltp'>oltp</span> `funcionario`

Motoristas, coletores e fiscais do serviço de limpeza urbana.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_funcionario` | integer | Não | serial<br>PK | Identificador do funcionário (PK). |
| `matricula` | varchar(10) | Não | UNIQUE | Matrícula funcional (única). |
| `nome` | varchar(100) | Não | — | Nome completo. |
| `cargo` | varchar(10) | Não | CHECK cargo IN (MOTORISTA, COLETOR, FISCAL) | MOTORISTA, COLETOR ou FISCAL. |
| `data_admissao` | date | Não | — | Data de admissão. |
| `ativo` | boolean | Não | DEFAULT true | Indica se o vínculo está ativo. |

#### <span class='tag tag-oltp'>oltp</span> `destino_final`

Locais de destinação: aterro, cooperativas, usina de compostagem, central de perigosos.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_destino` | integer | Não | serial<br>PK | Identificador do destino (PK). |
| `nome` | varchar(100) | Não | — | Nome da instalação. |
| `tipo` | varchar(20) | Não | CHECK tipo IN (ATERRO_SANITARIO, COOPERATIVA, USINA_COMPOSTAGEM, CENTRAL_PERIGOSOS) | ATERRO_SANITARIO, COOPERATIVA, USINA_COMPOSTAGEM ou CENTRAL_PERIGOSOS. |
| `cnpj` | char(14) | Sim | UNIQUE | CNPJ sem máscara (14 dígitos, único). |
| `capacidade_ton_mes` | numeric(10,2) | Não | CHECK capacidade_ton_mes > 0 | Capacidade mensal de recebimento em toneladas (> 0). |

#### <span class='tag tag-oltp'>oltp</span> `rota`

Rota de coleta recorrente (semanal) de um bairro, convencional ou seletiva.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_rota` | integer | Não | serial<br>PK | Identificador da rota (PK). |
| `id_bairro` | integer | Não | UNIQUE (composta)<br>FK → bairro.id_bairro | Bairro atendido pela rota (FK bairro). |
| `nome` | varchar(80) | Não | — | Nome descritivo da rota. |
| `tipo_coleta` | varchar(12) | Não | UNIQUE (composta)<br>CHECK tipo_coleta IN (CONVENCIONAL, SELETIVA) | CONVENCIONAL (orgânico/rejeito) ou SELETIVA (recicláveis). Única por bairro e tipo. |
| `dia_semana` | smallint | Não | CHECK dia_semana >= 1 AND dia_semana <= 7 | Dia de operação, padrão ISO: 1=segunda ... 7=domingo. |
| `turno` | varchar(5) | Não | CHECK turno IN (MANHA, TARDE, NOITE) | MANHA, TARDE ou NOITE. |
| `extensao_km` | numeric(6,2) | Não | CHECK extensao_km > 0 | Extensão planejada da rota em km (> 0). |

#### <span class='tag tag-oltp'>oltp</span> `coleta`

Execução de uma rota em uma data (viagem do caminhão).

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_coleta` | integer | Não | serial<br>PK | Identificador da coleta (PK). |
| `id_rota` | integer | Não | UNIQUE (composta)<br>FK → rota.id_rota | Rota executada (FK rota). |
| `id_veiculo` | integer | Não | FK → veiculo.id_veiculo | Veículo utilizado (FK veiculo). |
| `id_motorista` | integer | Não | FK → funcionario.id_funcionario | Motorista responsável (FK funcionario). |
| `data_coleta` | date | Não | UNIQUE (composta) | Data de execução. Única por rota (UNIQUE id_rota + data). |
| `hora_inicio` | time | Não | — | Hora de saída. |
| `hora_fim` | time | Sim | — | Hora de término; NULL se não concluída; deve ser maior que hora_inicio. |
| `km_percorridos` | numeric(7,2) | Sim | CHECK km_percorridos >= 0 | Quilometragem real percorrida (>= 0). |
| `status` | varchar(12) | Não | CHECK status IN (PLANEJADA, EM_ANDAMENTO, CONCLUIDA, CANCELADA)<br>DEFAULT 'PLANEJADA' | PLANEJADA, EM_ANDAMENTO, CONCLUIDA ou CANCELADA. |

#### <span class='tag tag-oltp'>oltp</span> `coleta_equipe`

Associativa N:N entre coleta e funcionários que compuseram a equipe.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_coleta` | integer | Não | PK (composta)<br>FK → coleta.id_coleta | Coleta (parte da PK composta, FK coleta). |
| `id_funcionario` | integer | Não | PK (composta)<br>FK → funcionario.id_funcionario | Funcionário da equipe (parte da PK composta, FK funcionario). |

#### <span class='tag tag-oltp'>oltp</span> `coleta_item`

Peso de um tipo de resíduo coletado em um ponto durante uma coleta.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_coleta_item` | integer | Não | serial<br>PK | Identificador do item (PK). |
| `id_coleta` | integer | Não | UNIQUE (composta)<br>FK → coleta.id_coleta | Coleta a que o item pertence (FK coleta). |
| `id_ponto` | integer | Não | UNIQUE (composta)<br>FK → ponto_coleta.id_ponto | Ponto de onde o resíduo foi retirado (FK ponto_coleta). |
| `id_tipo_residuo` | integer | Não | UNIQUE (composta)<br>FK → tipo_residuo.id_tipo_residuo | Tipo do resíduo coletado (FK tipo_residuo). |
| `peso_kg` | numeric(10,2) | Não | CHECK peso_kg >= 0 | Peso coletado em kg (>= 0). |

#### <span class='tag tag-oltp'>oltp</span> `descarga`

Descarga dos resíduos de uma coleta em um destino final, por tipo de resíduo; inclui o rejeito da triagem dos recicláveis, enviado ao aterro.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_descarga` | integer | Não | serial<br>PK | Identificador da descarga (PK). |
| `id_coleta` | integer | Não | UNIQUE (composta)<br>FK → coleta.id_coleta | Coleta de origem (FK coleta). |
| `id_destino` | integer | Não | UNIQUE (composta)<br>FK → destino_final.id_destino | Destino que recebeu o material (FK destino_final). |
| `id_tipo_residuo` | integer | Não | UNIQUE (composta)<br>FK → tipo_residuo.id_tipo_residuo | Tipo de resíduo descarregado (FK tipo_residuo). |
| `peso_kg` | numeric(12,2) | Não | CHECK peso_kg > 0 | Peso descarregado em kg (> 0). |
| `data_hora` | timestamp | Não | — | Data e hora do recebimento no destino. |

#### <span class='tag tag-oltp'>oltp</span> `ocorrencia`

Reclamações e solicitações do cidadão relacionadas à limpeza urbana.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_ocorrencia` | integer | Não | serial<br>PK | Identificador da ocorrência (PK). |
| `id_bairro` | integer | Não | FK → bairro.id_bairro | Bairro da ocorrência (FK bairro). |
| `id_ponto` | integer | Sim | FK → ponto_coleta.id_ponto | Ponto específico, quando informado (FK ponto_coleta, opcional). |
| `tipo_ocorrencia` | varchar(25) | Não | CHECK tipo_ocorrencia IN (DESCARTE_IRREGULAR, COLETA_NAO_REALIZADA, CONTAINER_DANIFICADO, SOLICITACAO_VOLUMOSO, OUTROS) | DESCARTE_IRREGULAR, COLETA_NAO_REALIZADA, CONTAINER_DANIFICADO, SOLICITACAO_VOLUMOSO ou OUTROS. |
| `canal` | varchar(10) | Não | CHECK canal IN (APP, TELEFONE, PRESENCIAL) | Canal de abertura: APP, TELEFONE ou PRESENCIAL. |
| `data_abertura` | timestamp | Não | — | Data e hora de registro. |
| `data_fechamento` | timestamp | Sim | — | Data e hora da resolução; NULL enquanto não resolvida. |
| `status` | varchar(15) | Não | CHECK status IN (ABERTA, EM_ATENDIMENTO, RESOLVIDA)<br>DEFAULT 'ABERTA' | ABERTA, EM_ATENDIMENTO ou RESOLVIDA (RESOLVIDA se e somente se há data_fechamento). |

#### <span class='tag tag-dw'>dw</span> `dim_tempo`

Dimensão calendário (chave inteira AAAAMMDD).

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_tempo` | integer | Não | PK | Chave substituta no formato AAAAMMDD (PK). |
| `data` | date | Não | UNIQUE | Data de calendário (única). |
| `dia` | smallint | Não | — | Dia do mês. |
| `mes` | smallint | Não | — | Número do mês (1-12). |
| `nome_mes` | varchar(10) | Não | — | Nome do mês em português. |
| `trimestre` | smallint | Não | — | Trimestre (1-4). |
| `semestre` | smallint | Não | — | Semestre (1-2). |
| `ano` | smallint | Não | — | Ano. |
| `dia_semana` | smallint | Não | — | Dia da semana ISO (1=segunda ... 7=domingo). |
| `nome_dia` | varchar(15) | Não | — | Nome do dia da semana. |
| `fim_de_semana` | boolean | Não | — | TRUE para sábado e domingo. |

#### <span class='tag tag-dw'>dw</span> `dim_local`

Dimensão local: ponto de coleta com hierarquia ponto > bairro > região.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_local` | integer | Não | serial<br>PK | Chave substituta do local (PK). |
| `id_ponto_origem` | integer | Sim | — | ID do ponto no OLTP; NULL para o membro "bairro inteiro". |
| `id_bairro_origem` | integer | Não | — | ID do bairro no OLTP. |
| `tipo_ponto` | varchar(15) | Não | — | Tipo do ponto ou NAO_INFORMADO. |
| `logradouro` | varchar(120) | Sim | — | Endereço do ponto (logradouro, número). |
| `bairro` | varchar(80) | Não | — | Nome do bairro (nível da hierarquia). |
| `regiao` | varchar(10) | Não | — | Região (nível superior da hierarquia). |
| `populacao_bairro` | integer | Não | — | População do bairro, para métricas per capita. |
| `area_km2_bairro` | numeric(8,2) | Não | — | Área do bairro em km². |

#### <span class='tag tag-dw'>dw</span> `dim_tipo_residuo`

Dimensão tipo de resíduo (categoria, reciclabilidade, destinação).

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_tipo_residuo` | integer | Não | serial<br>PK | Chave substituta (PK). |
| `id_origem` | integer | Não | UNIQUE | ID no OLTP (único). |
| `nome` | varchar(60) | Não | — | Nome do tipo de resíduo. |
| `categoria` | varchar(12) | Não | — | Categoria do resíduo. |
| `reciclavel` | boolean | Não | — | Indicador de reciclável. |
| `destinacao_padrao` | varchar(20) | Não | — | Destinação padrão. |

#### <span class='tag tag-dw'>dw</span> `dim_veiculo`

Dimensão veículo.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_veiculo` | integer | Não | serial<br>PK | Chave substituta (PK). |
| `id_origem` | integer | Não | UNIQUE | ID no OLTP (único). |
| `placa` | char(7) | Não | — | Placa. |
| `tipo` | varchar(15) | Não | — | Tipo do veículo. |
| `capacidade_kg` | integer | Não | — | Capacidade em kg. |
| `ano_fabricacao` | smallint | Não | — | Ano de fabricação (permite análise por idade da frota). |

#### <span class='tag tag-dw'>dw</span> `dim_rota`

Dimensão rota, com bairro e região desnormalizados.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_rota` | integer | Não | serial<br>PK | Chave substituta (PK). |
| `id_origem` | integer | Não | UNIQUE | ID no OLTP (único). |
| `nome` | varchar(80) | Não | — | Nome da rota. |
| `tipo_coleta` | varchar(12) | Não | — | CONVENCIONAL ou SELETIVA. |
| `dia_semana` | smallint | Não | — | Dia ISO de operação. |
| `turno` | varchar(5) | Não | — | Turno de operação. |
| `extensao_km` | numeric(6,2) | Não | — | Extensão planejada em km. |
| `bairro` | varchar(80) | Não | — | Bairro atendido (desnormalizado). |
| `regiao` | varchar(10) | Não | — | Região do bairro (desnormalizado). |

#### <span class='tag tag-dw'>dw</span> `dim_funcionario`

Dimensão funcionário (usada como papel "motorista" na fato de coleta).

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_funcionario` | integer | Não | serial<br>PK | Chave substituta (PK). |
| `id_origem` | integer | Não | UNIQUE | ID no OLTP (único). |
| `matricula` | varchar(10) | Não | — | Matrícula. |
| `nome` | varchar(100) | Não | — | Nome. |
| `cargo` | varchar(10) | Não | — | Cargo. |

#### <span class='tag tag-dw'>dw</span> `dim_destino`

Dimensão destino final.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_destino` | integer | Não | serial<br>PK | Chave substituta (PK). |
| `id_origem` | integer | Não | UNIQUE | ID no OLTP (único). |
| `nome` | varchar(100) | Não | — | Nome do destino. |
| `tipo` | varchar(20) | Não | — | Tipo do destino. |
| `capacidade_ton_mes` | numeric(10,2) | Não | — | Capacidade mensal em toneladas. |

#### <span class='tag tag-dw'>dw</span> `dim_ocorrencia`

Dimensão lixo (junk) com tipo, canal e status da ocorrência.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_ocorrencia` | integer | Não | serial<br>PK | Chave substituta (PK). |
| `tipo_ocorrencia` | varchar(25) | Não | UNIQUE (composta) | Tipo da ocorrência. |
| `canal` | varchar(10) | Não | UNIQUE (composta) | Canal de abertura. |
| `status` | varchar(15) | Não | UNIQUE (composta) | Status atual. |

#### <span class='tag tag-dw'>dw</span> `fato_coleta`

Fato: peso coletado por coleta x ponto x tipo de resíduo.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_tempo` | integer | Não | FK → dim_tempo.sk_tempo | FK dim_tempo (data da coleta). |
| `sk_local` | integer | Não | PK (composta)<br>FK → dim_local.sk_local | FK dim_local (ponto de coleta). |
| `sk_tipo_residuo` | integer | Não | PK (composta)<br>FK → dim_tipo_residuo.sk_tipo_residuo | FK dim_tipo_residuo. |
| `sk_rota` | integer | Não | FK → dim_rota.sk_rota | FK dim_rota. |
| `sk_veiculo` | integer | Não | FK → dim_veiculo.sk_veiculo | FK dim_veiculo. |
| `sk_motorista` | integer | Não | FK → dim_funcionario.sk_funcionario | FK dim_funcionario (papel motorista). |
| `id_coleta` | integer | Não | PK (composta) | Dimensão degenerada: ID da coleta no OLTP. |
| `peso_kg` | numeric(10,2) | Não | CHECK peso_kg >= 0 | Medida aditiva: peso coletado em kg. |
| `qtd_registros` | smallint | Não | DEFAULT 1 | Medida aditiva: contador (sempre 1) para contagem de atendimentos. |

#### <span class='tag tag-dw'>dw</span> `fato_destinacao`

Fato: peso destinado por coleta x destino x tipo de resíduo.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `sk_tempo` | integer | Não | FK → dim_tempo.sk_tempo | FK dim_tempo (data do recebimento). |
| `sk_destino` | integer | Não | PK (composta)<br>FK → dim_destino.sk_destino | FK dim_destino. |
| `sk_tipo_residuo` | integer | Não | PK (composta)<br>FK → dim_tipo_residuo.sk_tipo_residuo | FK dim_tipo_residuo. |
| `sk_rota` | integer | Não | FK → dim_rota.sk_rota | FK dim_rota. |
| `sk_veiculo` | integer | Não | FK → dim_veiculo.sk_veiculo | FK dim_veiculo. |
| `id_coleta` | integer | Não | PK (composta) | Dimensão degenerada: ID da coleta. |
| `peso_kg` | numeric(12,2) | Não | CHECK peso_kg > 0 | Medida aditiva: peso destinado em kg. |

#### <span class='tag tag-dw'>dw</span> `fato_ocorrencia`

Fato: uma linha por ocorrência, com tempo de resolução.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_ocorrencia` | integer | Não | PK | Dimensão degenerada e PK: ID da ocorrência no OLTP. |
| `sk_tempo_abertura` | integer | Não | FK → dim_tempo.sk_tempo | FK dim_tempo (papel data de abertura). |
| `sk_tempo_fechamento` | integer | Sim | FK → dim_tempo.sk_tempo | FK dim_tempo (papel data de fechamento); NULL se em aberto. |
| `sk_local` | integer | Não | FK → dim_local.sk_local | FK dim_local. |
| `sk_ocorrencia` | integer | Não | FK → dim_ocorrencia.sk_ocorrencia | FK dim_ocorrencia. |
| `qtd_ocorrencias` | smallint | Não | DEFAULT 1 | Medida aditiva: contador (sempre 1). |
| `tempo_resolucao_horas` | numeric(8,2) | Sim | CHECK tempo_resolucao_horas >= 0 | Medida semiaditiva: horas entre abertura e fechamento; NULL se em aberto. |

#### <span class='tag tag-dw'>dw</span> `fato_viagem`

Fato: uma linha por coleta (viagem), com km, duração, peso total e indicador de cancelamento.

| Atributo | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id_coleta` | integer | Não | PK | Dimensão degenerada e PK: ID da coleta no OLTP. |
| `sk_tempo` | integer | Não | FK → dim_tempo.sk_tempo | FK dim_tempo (data da coleta). |
| `sk_rota` | integer | Não | FK → dim_rota.sk_rota | FK dim_rota. |
| `sk_veiculo` | integer | Não | FK → dim_veiculo.sk_veiculo | FK dim_veiculo. |
| `sk_motorista` | integer | Não | FK → dim_funcionario.sk_funcionario | FK dim_funcionario (papel motorista). |
| `km_percorridos` | numeric(7,2) | Sim | CHECK km_percorridos >= 0 | Medida aditiva: km rodados; NULL quando a coleta foi cancelada. |
| `duracao_min` | integer | Sim | CHECK duracao_min > 0 | Medida aditiva: minutos entre hora_inicio e hora_fim; NULL quando cancelada. |
| `peso_total_kg` | numeric(12,2) | Não | CHECK peso_total_kg >= 0<br>DEFAULT 0 | Medida aditiva: soma do peso coletado na viagem (0 se cancelada). |
| `qtd_pontos_atendidos` | integer | Não | CHECK qtd_pontos_atendidos >= 0<br>DEFAULT 0 | Medida aditiva: pontos distintos atendidos na viagem (0 se cancelada). |
| `qtd_cancelada` | smallint | Não | CHECK qtd_cancelada = ANY ARRAY[0, 1]<br>DEFAULT 0 | Medida aditiva: 1 se a coleta foi cancelada, 0 caso contrário (SUM = nº de cancelamentos). |


---

