-- =====================================================================
-- Projeto: Laboratório de Dados para Cidades Sustentáveis (ODS 11)
-- Tema   : Gestão de Resíduos Sólidos Urbanos e Coleta Seletiva
-- Disciplina: Tópicos Especiais em Banco de Dados
-- SGBD   : PostgreSQL 15+ (open-source)
-- Conteúdo: (1) Ambiente OLTP  (2) Ambiente OLAP (Data Warehouse)
--           (3) Carga de dados de exemplo  (4) ETL OLTP -> OLAP
-- Execução: psql -U postgres -d <banco> -f 01_construcao_oltp_olap.sql
-- =====================================================================

DROP SCHEMA IF EXISTS dw   CASCADE;
DROP SCHEMA IF EXISTS oltp CASCADE;
CREATE SCHEMA oltp;
CREATE SCHEMA dw;

-- =====================================================================
-- PARTE 1 - AMBIENTE OLTP (3FN)  -  schema oltp
-- =====================================================================

CREATE TABLE oltp.bairro (
    id_bairro   SERIAL        PRIMARY KEY,
    nome        VARCHAR(80)   NOT NULL UNIQUE,
    regiao      VARCHAR(10)   NOT NULL
                CHECK (regiao IN ('CENTRO','NORTE','SUL','LESTE','OESTE')),
    populacao   INTEGER       NOT NULL CHECK (populacao > 0),
    area_km2    NUMERIC(8,2)  NOT NULL CHECK (area_km2 > 0)
);

CREATE TABLE oltp.ponto_coleta (
    id_ponto    SERIAL        PRIMARY KEY,
    id_bairro   INTEGER       NOT NULL REFERENCES oltp.bairro (id_bairro),
    tipo_ponto  VARCHAR(15)   NOT NULL
                CHECK (tipo_ponto IN ('RESIDENCIAL','COMERCIAL','CONDOMINIO','ORGAO_PUBLICO','PEV')),
    logradouro  VARCHAR(120)  NOT NULL,
    numero      VARCHAR(10),
    latitude    NUMERIC(9,6)  CHECK (latitude  BETWEEN -90  AND 90),
    longitude   NUMERIC(9,6)  CHECK (longitude BETWEEN -180 AND 180),
    ativo       BOOLEAN       NOT NULL DEFAULT TRUE
);

CREATE TABLE oltp.tipo_residuo (
    id_tipo_residuo   SERIAL       PRIMARY KEY,
    nome              VARCHAR(60)  NOT NULL UNIQUE,
    categoria         VARCHAR(12)  NOT NULL
                      CHECK (categoria IN ('ORGANICO','REJEITO','RECICLAVEL','PERIGOSO','VOLUMOSO')),
    reciclavel        BOOLEAN      NOT NULL,
    destinacao_padrao VARCHAR(20)  NOT NULL
                      CHECK (destinacao_padrao IN ('ATERRO_SANITARIO','COOPERATIVA','USINA_COMPOSTAGEM','CENTRAL_PERIGOSOS'))
);

CREATE TABLE oltp.veiculo (
    id_veiculo      SERIAL       PRIMARY KEY,
    placa           CHAR(7)      NOT NULL UNIQUE,
    tipo            VARCHAR(15)  NOT NULL
                    CHECK (tipo IN ('COMPACTADOR','BAU_SELETIVA','CACAMBA','CAMINHAO_BAU')),
    capacidade_kg   INTEGER      NOT NULL CHECK (capacidade_kg > 0),
    ano_fabricacao  SMALLINT     NOT NULL CHECK (ano_fabricacao BETWEEN 1990 AND 2100),
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE oltp.funcionario (
    id_funcionario  SERIAL       PRIMARY KEY,
    matricula       VARCHAR(10)  NOT NULL UNIQUE,
    nome            VARCHAR(100) NOT NULL,
    cargo           VARCHAR(10)  NOT NULL CHECK (cargo IN ('MOTORISTA','COLETOR','FISCAL')),
    data_admissao   DATE         NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE oltp.destino_final (
    id_destino         SERIAL        PRIMARY KEY,
    nome               VARCHAR(100)  NOT NULL,
    tipo               VARCHAR(20)   NOT NULL
                       CHECK (tipo IN ('ATERRO_SANITARIO','COOPERATIVA','USINA_COMPOSTAGEM','CENTRAL_PERIGOSOS')),
    cnpj               CHAR(14)      UNIQUE,
    capacidade_ton_mes NUMERIC(10,2) NOT NULL CHECK (capacidade_ton_mes > 0)
);

CREATE TABLE oltp.rota (
    id_rota       SERIAL       PRIMARY KEY,
    id_bairro     INTEGER      NOT NULL REFERENCES oltp.bairro (id_bairro),
    nome          VARCHAR(80)  NOT NULL,
    tipo_coleta   VARCHAR(12)  NOT NULL CHECK (tipo_coleta IN ('CONVENCIONAL','SELETIVA')),
    dia_semana    SMALLINT     NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),   -- ISO: 1=segunda ... 7=domingo
    turno         VARCHAR(5)   NOT NULL CHECK (turno IN ('MANHA','TARDE','NOITE')),
    extensao_km   NUMERIC(6,2) NOT NULL CHECK (extensao_km > 0),
    UNIQUE (id_bairro, tipo_coleta)
);

CREATE TABLE oltp.coleta (
    id_coleta       SERIAL        PRIMARY KEY,
    id_rota         INTEGER       NOT NULL REFERENCES oltp.rota (id_rota),
    id_veiculo      INTEGER       NOT NULL REFERENCES oltp.veiculo (id_veiculo),
    id_motorista    INTEGER       NOT NULL REFERENCES oltp.funcionario (id_funcionario),
    data_coleta     DATE          NOT NULL,
    hora_inicio     TIME          NOT NULL,
    hora_fim        TIME,
    km_percorridos  NUMERIC(7,2)  CHECK (km_percorridos >= 0),
    status          VARCHAR(12)   NOT NULL DEFAULT 'PLANEJADA'
                    CHECK (status IN ('PLANEJADA','EM_ANDAMENTO','CONCLUIDA','CANCELADA')),
    CONSTRAINT ck_coleta_horas CHECK (hora_fim IS NULL OR hora_fim > hora_inicio),
    CONSTRAINT uq_coleta_rota_data UNIQUE (id_rota, data_coleta)
);

CREATE TABLE oltp.coleta_equipe (
    id_coleta       INTEGER NOT NULL REFERENCES oltp.coleta (id_coleta) ON DELETE CASCADE,
    id_funcionario  INTEGER NOT NULL REFERENCES oltp.funcionario (id_funcionario),
    PRIMARY KEY (id_coleta, id_funcionario)
);

CREATE TABLE oltp.coleta_item (
    id_coleta_item  SERIAL        PRIMARY KEY,
    id_coleta       INTEGER       NOT NULL REFERENCES oltp.coleta (id_coleta) ON DELETE CASCADE,
    id_ponto        INTEGER       NOT NULL REFERENCES oltp.ponto_coleta (id_ponto),
    id_tipo_residuo INTEGER       NOT NULL REFERENCES oltp.tipo_residuo (id_tipo_residuo),
    peso_kg         NUMERIC(10,2) NOT NULL CHECK (peso_kg >= 0),
    UNIQUE (id_coleta, id_ponto, id_tipo_residuo)
);

CREATE TABLE oltp.descarga (
    id_descarga     SERIAL        PRIMARY KEY,
    id_coleta       INTEGER       NOT NULL REFERENCES oltp.coleta (id_coleta),
    id_destino      INTEGER       NOT NULL REFERENCES oltp.destino_final (id_destino),
    id_tipo_residuo INTEGER       NOT NULL REFERENCES oltp.tipo_residuo (id_tipo_residuo),
    peso_kg         NUMERIC(12,2) NOT NULL CHECK (peso_kg > 0),
    data_hora       TIMESTAMP     NOT NULL,
    UNIQUE (id_coleta, id_destino, id_tipo_residuo)
);

CREATE TABLE oltp.ocorrencia (
    id_ocorrencia   SERIAL       PRIMARY KEY,
    id_bairro       INTEGER      NOT NULL REFERENCES oltp.bairro (id_bairro),
    id_ponto        INTEGER      REFERENCES oltp.ponto_coleta (id_ponto),
    tipo_ocorrencia VARCHAR(25)  NOT NULL
                    CHECK (tipo_ocorrencia IN ('DESCARTE_IRREGULAR','COLETA_NAO_REALIZADA',
                                               'CONTAINER_DANIFICADO','SOLICITACAO_VOLUMOSO','OUTROS')),
    canal           VARCHAR(10)  NOT NULL CHECK (canal IN ('APP','TELEFONE','PRESENCIAL')),
    data_abertura   TIMESTAMP    NOT NULL,
    data_fechamento TIMESTAMP,
    status          VARCHAR(15)  NOT NULL DEFAULT 'ABERTA'
                    CHECK (status IN ('ABERTA','EM_ATENDIMENTO','RESOLVIDA')),
    CONSTRAINT ck_ocorrencia_datas CHECK (data_fechamento IS NULL OR data_fechamento >= data_abertura),
    CONSTRAINT ck_ocorrencia_status CHECK ((status = 'RESOLVIDA') = (data_fechamento IS NOT NULL))
);

-- Índices de apoio às chaves estrangeiras e às consultas operacionais
CREATE INDEX ix_ponto_bairro        ON oltp.ponto_coleta (id_bairro);
CREATE INDEX ix_rota_bairro         ON oltp.rota (id_bairro);
CREATE INDEX ix_coleta_data         ON oltp.coleta (data_coleta);
CREATE INDEX ix_coleta_veiculo      ON oltp.coleta (id_veiculo);
CREATE INDEX ix_coleta_motorista    ON oltp.coleta (id_motorista);
CREATE INDEX ix_item_coleta         ON oltp.coleta_item (id_coleta);
CREATE INDEX ix_item_ponto          ON oltp.coleta_item (id_ponto);
CREATE INDEX ix_descarga_coleta     ON oltp.descarga (id_coleta);
CREATE INDEX ix_ocorrencia_bairro   ON oltp.ocorrencia (id_bairro);
CREATE INDEX ix_ocorrencia_abertura ON oltp.ocorrencia (data_abertura);

-- =====================================================================
-- PARTE 2 - AMBIENTE OLAP (Data Warehouse, esquema estrela) - schema dw
-- Quatro fatos (coleta, viagem, destinação, ocorrência) com dimensões conformes.
-- =====================================================================

CREATE TABLE dw.dim_tempo (
    sk_tempo        INTEGER      PRIMARY KEY,          -- formato AAAAMMDD
    data            DATE         NOT NULL UNIQUE,
    dia             SMALLINT     NOT NULL,
    mes             SMALLINT     NOT NULL,
    nome_mes        VARCHAR(10)  NOT NULL,
    trimestre       SMALLINT     NOT NULL,
    semestre        SMALLINT     NOT NULL,
    ano             SMALLINT     NOT NULL,
    dia_semana      SMALLINT     NOT NULL,             -- ISO 1..7
    nome_dia        VARCHAR(15)  NOT NULL,
    fim_de_semana   BOOLEAN      NOT NULL
);

CREATE TABLE dw.dim_local (
    sk_local          SERIAL       PRIMARY KEY,
    id_ponto_origem   INTEGER,                          -- NULL = "bairro inteiro" (ocorrência sem ponto)
    id_bairro_origem  INTEGER      NOT NULL,
    tipo_ponto        VARCHAR(15)  NOT NULL,
    logradouro        VARCHAR(120),
    bairro            VARCHAR(80)  NOT NULL,
    regiao            VARCHAR(10)  NOT NULL,
    populacao_bairro  INTEGER      NOT NULL,
    area_km2_bairro   NUMERIC(8,2) NOT NULL
);

CREATE TABLE dw.dim_tipo_residuo (
    sk_tipo_residuo   SERIAL       PRIMARY KEY,
    id_origem         INTEGER      NOT NULL UNIQUE,
    nome              VARCHAR(60)  NOT NULL,
    categoria         VARCHAR(12)  NOT NULL,
    reciclavel        BOOLEAN      NOT NULL,
    destinacao_padrao VARCHAR(20)  NOT NULL
);

CREATE TABLE dw.dim_veiculo (
    sk_veiculo      SERIAL       PRIMARY KEY,
    id_origem       INTEGER      NOT NULL UNIQUE,
    placa           CHAR(7)      NOT NULL,
    tipo            VARCHAR(15)  NOT NULL,
    capacidade_kg   INTEGER      NOT NULL,
    ano_fabricacao  SMALLINT     NOT NULL
);

CREATE TABLE dw.dim_rota (
    sk_rota       SERIAL       PRIMARY KEY,
    id_origem     INTEGER      NOT NULL UNIQUE,
    nome          VARCHAR(80)  NOT NULL,
    tipo_coleta   VARCHAR(12)  NOT NULL,
    dia_semana    SMALLINT     NOT NULL,
    turno         VARCHAR(5)   NOT NULL,
    extensao_km   NUMERIC(6,2) NOT NULL,
    bairro        VARCHAR(80)  NOT NULL,
    regiao        VARCHAR(10)  NOT NULL
);

CREATE TABLE dw.dim_funcionario (
    sk_funcionario  SERIAL       PRIMARY KEY,
    id_origem       INTEGER      NOT NULL UNIQUE,
    matricula       VARCHAR(10)  NOT NULL,
    nome            VARCHAR(100) NOT NULL,
    cargo           VARCHAR(10)  NOT NULL
);

CREATE TABLE dw.dim_destino (
    sk_destino          SERIAL        PRIMARY KEY,
    id_origem           INTEGER       NOT NULL UNIQUE,
    nome                VARCHAR(100)  NOT NULL,
    tipo                VARCHAR(20)   NOT NULL,
    capacidade_ton_mes  NUMERIC(10,2) NOT NULL
);

-- Dimensão degenerada/lixo (junk): combina atributos descritivos de baixa cardinalidade
CREATE TABLE dw.dim_ocorrencia (
    sk_ocorrencia    SERIAL       PRIMARY KEY,
    tipo_ocorrencia  VARCHAR(25)  NOT NULL,
    canal            VARCHAR(10)  NOT NULL,
    status           VARCHAR(15)  NOT NULL,
    UNIQUE (tipo_ocorrencia, canal, status)
);

-- Fato 1: grão = um tipo de resíduo coletado em um ponto durante uma coleta
CREATE TABLE dw.fato_coleta (
    sk_tempo         INTEGER       NOT NULL REFERENCES dw.dim_tempo (sk_tempo),
    sk_local         INTEGER       NOT NULL REFERENCES dw.dim_local (sk_local),
    sk_tipo_residuo  INTEGER       NOT NULL REFERENCES dw.dim_tipo_residuo (sk_tipo_residuo),
    sk_rota          INTEGER       NOT NULL REFERENCES dw.dim_rota (sk_rota),
    sk_veiculo       INTEGER       NOT NULL REFERENCES dw.dim_veiculo (sk_veiculo),
    sk_motorista     INTEGER       NOT NULL REFERENCES dw.dim_funcionario (sk_funcionario),
    id_coleta        INTEGER       NOT NULL,            -- dimensão degenerada
    peso_kg          NUMERIC(10,2) NOT NULL CHECK (peso_kg >= 0),
    qtd_registros    SMALLINT      NOT NULL DEFAULT 1,
    PRIMARY KEY (id_coleta, sk_local, sk_tipo_residuo)
);

-- Fato 2: grão = peso de um tipo de resíduo descarregado em um destino por coleta
CREATE TABLE dw.fato_destinacao (
    sk_tempo         INTEGER       NOT NULL REFERENCES dw.dim_tempo (sk_tempo),
    sk_destino       INTEGER       NOT NULL REFERENCES dw.dim_destino (sk_destino),
    sk_tipo_residuo  INTEGER       NOT NULL REFERENCES dw.dim_tipo_residuo (sk_tipo_residuo),
    sk_rota          INTEGER       NOT NULL REFERENCES dw.dim_rota (sk_rota),
    sk_veiculo       INTEGER       NOT NULL REFERENCES dw.dim_veiculo (sk_veiculo),
    id_coleta        INTEGER       NOT NULL,
    peso_kg          NUMERIC(12,2) NOT NULL CHECK (peso_kg > 0),
    PRIMARY KEY (id_coleta, sk_destino, sk_tipo_residuo)
);

-- Fato 3: grão = uma ocorrência (reclamação/solicitação) registrada pelo cidadão
CREATE TABLE dw.fato_ocorrencia (
    id_ocorrencia          INTEGER       PRIMARY KEY,   -- dimensão degenerada
    sk_tempo_abertura      INTEGER       NOT NULL REFERENCES dw.dim_tempo (sk_tempo),
    sk_tempo_fechamento    INTEGER       REFERENCES dw.dim_tempo (sk_tempo),
    sk_local               INTEGER       NOT NULL REFERENCES dw.dim_local (sk_local),
    sk_ocorrencia          INTEGER       NOT NULL REFERENCES dw.dim_ocorrencia (sk_ocorrencia),
    qtd_ocorrencias        SMALLINT      NOT NULL DEFAULT 1,
    tempo_resolucao_horas  NUMERIC(8,2)  CHECK (tempo_resolucao_horas >= 0)
);

-- Fato 4: grão = uma coleta (viagem do veículo em uma rota, em uma data), inclusive as canceladas
CREATE TABLE dw.fato_viagem (
    id_coleta             INTEGER       PRIMARY KEY,   -- dimensão degenerada
    sk_tempo              INTEGER       NOT NULL REFERENCES dw.dim_tempo (sk_tempo),
    sk_rota               INTEGER       NOT NULL REFERENCES dw.dim_rota (sk_rota),
    sk_veiculo            INTEGER       NOT NULL REFERENCES dw.dim_veiculo (sk_veiculo),
    sk_motorista          INTEGER       NOT NULL REFERENCES dw.dim_funcionario (sk_funcionario),
    km_percorridos        NUMERIC(7,2)  CHECK (km_percorridos >= 0),   -- NULL = coleta cancelada
    duracao_min           INTEGER       CHECK (duracao_min > 0),       -- NULL = coleta cancelada
    peso_total_kg         NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (peso_total_kg >= 0),
    qtd_pontos_atendidos  INTEGER       NOT NULL DEFAULT 0 CHECK (qtd_pontos_atendidos >= 0),
    qtd_cancelada         SMALLINT      NOT NULL DEFAULT 0 CHECK (qtd_cancelada IN (0,1))
);

CREATE INDEX ix_fc_tempo   ON dw.fato_coleta (sk_tempo);
CREATE INDEX ix_fc_local   ON dw.fato_coleta (sk_local);
CREATE INDEX ix_fc_tipo    ON dw.fato_coleta (sk_tipo_residuo);
CREATE INDEX ix_fc_rota    ON dw.fato_coleta (sk_rota);
CREATE INDEX ix_fc_veiculo ON dw.fato_coleta (sk_veiculo);
CREATE INDEX ix_fd_tempo   ON dw.fato_destinacao (sk_tempo);
CREATE INDEX ix_fd_destino ON dw.fato_destinacao (sk_destino);
CREATE INDEX ix_fo_tempo   ON dw.fato_ocorrencia (sk_tempo_abertura);
CREATE INDEX ix_fo_local   ON dw.fato_ocorrencia (sk_local);
CREATE INDEX ix_fv_tempo   ON dw.fato_viagem (sk_tempo);
CREATE INDEX ix_fv_rota    ON dw.fato_viagem (sk_rota);
CREATE INDEX ix_fv_veiculo ON dw.fato_viagem (sk_veiculo);

-- =====================================================================
-- PARTE 3 - DADOS DE EXEMPLO (OLTP)  -  determinísticos e reproduzíveis
-- Período simulado: 01/01/2025 a 31/12/2025, com padrões deliberados (ver bloco P1 a P6 abaixo)
-- =====================================================================

INSERT INTO oltp.bairro (nome, regiao, populacao, area_km2) VALUES
 ('Centro',          'CENTRO', 18500,  4.20),
 ('Jardim Aurora',   'NORTE',  32400, 11.80),
 ('Vila Esperança',  'NORTE',  27100,  9.50),
 ('Parque das Águas','SUL',    41200, 15.30),
 ('Santa Luzia',     'SUL',    23800,  8.10),
 ('Bela Vista',      'LESTE',  36700, 12.60),
 ('Novo Horizonte',  'LESTE',  29900, 10.40),
 ('São José',        'OESTE',  34500, 13.20),
 ('Alvorada',        'OESTE',  21300,  7.90),
 ('Industrial',      'SUL',    12800, 18.70),
 ('Morada do Sol',   'NORTE',  38900, 14.10),
 ('Cidade Nova',     'LESTE',  26400,  9.20);

INSERT INTO oltp.tipo_residuo (nome, categoria, reciclavel, destinacao_padrao) VALUES
 ('Orgânico',                 'ORGANICO',   FALSE, 'USINA_COMPOSTAGEM'),
 ('Rejeito comum',            'REJEITO',    FALSE, 'ATERRO_SANITARIO'),
 ('Papel e papelão',          'RECICLAVEL', TRUE,  'COOPERATIVA'),
 ('Plástico',                 'RECICLAVEL', TRUE,  'COOPERATIVA'),
 ('Vidro',                    'RECICLAVEL', TRUE,  'COOPERATIVA'),
 ('Metal',                    'RECICLAVEL', TRUE,  'COOPERATIVA'),
 ('Eletroeletrônico e pilhas','PERIGOSO',   FALSE, 'CENTRAL_PERIGOSOS'),
 ('Volumoso e entulho',       'VOLUMOSO',   FALSE, 'ATERRO_SANITARIO');

INSERT INTO oltp.destino_final (nome, tipo, cnpj, capacidade_ton_mes) VALUES
 ('Aterro Sanitário Municipal',        'ATERRO_SANITARIO',  '11222333000181', 6000.00),
 ('Cooperativa Recicla Mais',          'COOPERATIVA',       '22333444000172', 1200.00),
 ('Usina de Compostagem Terra Viva',   'USINA_COMPOSTAGEM', '33444555000163',  900.00),
 ('Central de Resíduos Especiais',     'CENTRAL_PERIGOSOS', '44555666000154',   80.00);

INSERT INTO oltp.veiculo (placa, tipo, capacidade_kg, ano_fabricacao) VALUES
 ('ABC1D23','COMPACTADOR', 12000, 2019),
 ('ABC2E34','COMPACTADOR', 12000, 2020),
 ('ABC3F45','COMPACTADOR', 15000, 2021),
 ('ABC4G56','COMPACTADOR', 15000, 2016),
 ('SEL1A11','BAU_SELETIVA', 6000, 2022),
 ('SEL2B22','BAU_SELETIVA', 6000, 2023),
 ('CAC1C33','CACAMBA',      8000, 2018),
 ('BAU1D44','CAMINHAO_BAU', 4000, 2017);

INSERT INTO oltp.funcionario (matricula, nome, cargo, data_admissao, ativo)
SELECT 'M' || lpad(i::text, 4, '0'),
       (ARRAY['Carlos Silva','Marcos Souza','Paulo Lima','Rogério Alves','Antônio Reis','Jorge Pinto'])[i],
       'MOTORISTA', DATE '2015-03-01' + i * 190, TRUE
FROM generate_series(1, 6) AS i;

INSERT INTO oltp.funcionario (matricula, nome, cargo, data_admissao, ativo)
SELECT 'C' || lpad(i::text, 4, '0'),
       'Coletor ' || lpad(i::text, 2, '0'),
       'COLETOR', DATE '2017-01-10' + i * 120, TRUE
FROM generate_series(1, 18) AS i;

INSERT INTO oltp.funcionario (matricula, nome, cargo, data_admissao, ativo) VALUES
 ('F0001','Helena Prado','FISCAL','2014-06-02',TRUE),
 ('F0002','Ricardo Matos','FISCAL','2018-09-17',TRUE);

-- 240 pontos de coleta (20 por bairro)
INSERT INTO oltp.ponto_coleta (id_bairro, tipo_ponto, logradouro, numero, latitude, longitude)
SELECT 1 + (i % 12),
       (ARRAY['RESIDENCIAL','RESIDENCIAL','COMERCIAL','CONDOMINIO','PEV'])[1 + (i % 5)],
       'Rua ' || (ARRAY['das Flores','dos Ipês','Sete de Setembro','da Paz','do Comércio',
                        'Bahia','das Palmeiras','Santos Dumont','XV de Novembro','Brasil'])[1 + (i % 10)],
       (10 + (i * 7) % 990)::text,
       -3.700000 + ((i % 12) * 0.004) + ((i % 20) * 0.0007),
       -38.550000 + ((i % 12) * 0.005) + ((i % 20) * 0.0009)
FROM generate_series(1, 240) AS i;

-- ---------------------------------------------------------------------
-- PADRÕES DELIBERADOS NOS DADOS SINTÉTICOS (para que os dashboards tenham o que mostrar)
--   P1 perfil por bairro   : geração, adesão à seletiva e fração orgânica diferentes
--                            (Centro e Industrial geram mais; Novo Horizonte, Industrial e Vila Esperança
--                             aderem pouco; Morada do Sol e Parque das Águas aderem muito)
--   P2 sazonalidade        : dezembro com mais resíduo (+30%), fevereiro com menos (-15%); segundas +15%
--   P3 cancelamentos       : mais frequentes no turno da MANHÃ, no 1º trimestre (chuvas) e com o
--                            veículo mais antigo (id 4, ano 2016)
--   P4 rotas problemáticas : Industrial (convencional) e Novo Horizonte (seletiva): rota longa e pouco peso
--   P5 ocorrências         : mais "coleta não realizada" nos bairros de turno da manhã; mais descarte
--                            irregular em Industrial e Novo Horizonte; tempo de resolução varia por
--                            tipo e região, com casos extremos; algumas ainda abertas
--   P6 rejeito da triagem  : parte dos recicláveis entregues à cooperativa vira rejeito e segue ao aterro
--                            (plástico 35%, papel 12%, vidro 8%, metal 5%)
-- ---------------------------------------------------------------------
CREATE TEMP TABLE sint_perfil_bairro (id_bairro INT, geracao NUMERIC, adesao NUMERIC, organico NUMERIC);
INSERT INTO sint_perfil_bairro VALUES
 (1, 1.6, 1.0, 0.7), (2, 1.0, 1.3, 1.2), (3, 0.9, 0.5, 1.3), (4, 1.1, 1.4, 1.0),
 (5, 0.8, 0.7, 1.2), (6, 1.2, 1.0, 1.0), (7, 1.0, 0.4, 1.1), (8, 1.1, 0.9, 1.0),
 (9, 0.8, 0.6, 1.3), (10, 1.5, 0.3, 0.6), (11, 1.0, 1.5, 1.2), (12, 0.9, 0.8, 1.2);

CREATE TEMP TABLE sint_fator_mes (mes INT, fator NUMERIC);
INSERT INTO sint_fator_mes VALUES
 (1, 1.05), (2, 0.85), (3, 1.00), (4, 0.98), (5, 0.97), (6, 0.95),
 (7, 1.00), (8, 1.00), (9, 1.02), (10, 1.05), (11, 1.10), (12, 1.30);

-- pesos (somam 100) para sortear bairro e mês das ocorrências, com faixa acumulada [lo, hi)
CREATE TEMP TABLE sint_peso_bairro AS
SELECT id_bairro, SUM(peso) OVER (ORDER BY id_bairro) - peso AS lo, SUM(peso) OVER (ORDER BY id_bairro) AS hi
FROM (VALUES (1,5),(2,8),(3,11),(4,9),(5,6),(6,11),(7,8),(8,8),(9,9),(10,5),(11,9),(12,11)) v(id_bairro, peso);
CREATE TEMP TABLE sint_peso_mes AS
SELECT mes, SUM(peso) OVER (ORDER BY mes) - peso AS lo, SUM(peso) OVER (ORDER BY mes) AS hi
FROM (VALUES (1,11),(2,8),(3,10),(4,8),(5,7),(6,6),(7,6),(8,7),(9,8),(10,9),(11,9),(12,11)) v(mes, peso);

-- 24 rotas: uma convencional e uma seletiva por bairro
INSERT INTO oltp.rota (id_bairro, nome, tipo_coleta, dia_semana, turno, extensao_km)
SELECT b.id_bairro,
       'Rota ' || t.tipo_coleta || ' - ' || b.nome,
       t.tipo_coleta,
       CASE t.tipo_coleta WHEN 'CONVENCIONAL' THEN 1 + (b.id_bairro % 3) * 2    -- seg, qua ou sex
                          ELSE 2 + (b.id_bairro % 2) * 2 END,                   -- ter ou qui
       (ARRAY['MANHA','TARDE','NOITE'])[1 + (b.id_bairro % 3)],
       round((12 + (b.id_bairro * 3.7)::numeric % 18), 2)
FROM oltp.bairro b
CROSS JOIN (VALUES ('CONVENCIONAL'), ('SELETIVA')) AS t(tipo_coleta);

-- P4: duas rotas longas (o peso coletado nelas é reduzido mais abaixo)
UPDATE oltp.rota SET extensao_km = 36.00 WHERE id_bairro = 10 AND tipo_coleta = 'CONVENCIONAL';
UPDATE oltp.rota SET extensao_km = 33.00 WHERE id_bairro = 7  AND tipo_coleta = 'SELETIVA';

-- Coletas: cada rota roda uma vez por semana em 2025; cancelamentos seguem o padrão P3
INSERT INTO oltp.coleta (id_rota, id_veiculo, id_motorista, data_coleta, hora_inicio, hora_fim, km_percorridos, status)
SELECT x.id_rota, x.id_veiculo, x.id_motorista, x.data_coleta, x.hora_inicio,
       CASE WHEN x.cancelada THEN NULL
            ELSE x.hora_inicio + interval '3 hours' + (x.h % 90) * interval '1 minute' END,
       CASE WHEN x.cancelada THEN NULL ELSE round(x.extensao_km * (1.1 + (x.h % 30) / 100.0), 2) END,
       CASE WHEN x.cancelada THEN 'CANCELADA' ELSE 'CONCLUIDA' END
FROM (
    SELECT y.*,
           (abs(hashtext('c' || y.id_rota || y.data_coleta)::bigint) % 100) <
           ( CASE y.turno WHEN 'MANHA' THEN 9 WHEN 'TARDE' THEN 2 ELSE 3 END
           + CASE WHEN EXTRACT(month FROM y.data_coleta) IN (1, 2, 3) THEN 6 ELSE 0 END
           + CASE WHEN y.id_veiculo = 4 THEN 5 ELSE 0 END ) AS cancelada
    FROM (
        SELECT r.id_rota,
               r.extensao_km,
               r.turno,
               CASE r.tipo_coleta
                    WHEN 'CONVENCIONAL' THEN 1 + ((r.id_rota + EXTRACT(week FROM d)::int) % 4)
                    ELSE 5 + ((r.id_rota + EXTRACT(week FROM d)::int) % 2) END AS id_veiculo,
               1 + ((r.id_rota * 3 + EXTRACT(week FROM d)::int) % 6)           AS id_motorista,
               d::date                                                          AS data_coleta,
               CASE r.turno WHEN 'MANHA' THEN TIME '06:00'
                            WHEN 'TARDE' THEN TIME '14:00' ELSE TIME '18:00' END AS hora_inicio,
               abs(hashtext(r.id_rota || '#' || d::date)::bigint)               AS h
        FROM oltp.rota r
        JOIN generate_series(DATE '2025-01-01', DATE '2025-12-31', INTERVAL '1 day') AS d
          ON EXTRACT(isodow FROM d)::int = r.dia_semana
    ) y
) x;

-- Equipe: dois coletores por coleta concluída
INSERT INTO oltp.coleta_equipe (id_coleta, id_funcionario)
SELECT id_coleta, 7 + (id_coleta % 18) FROM oltp.coleta WHERE status = 'CONCLUIDA'
UNION ALL
SELECT id_coleta, 7 + ((id_coleta + 5) % 18) FROM oltp.coleta WHERE status = 'CONCLUIDA';

-- Itens coletados: convencional -> orgânico e rejeito; seletiva -> recicláveis (padrões P1, P2 e P4)
INSERT INTO oltp.coleta_item (id_coleta, id_ponto, id_tipo_residuo, peso_kg)
SELECT c.id_coleta, p.id_ponto, t.id_tipo_residuo,
       round(( 2 + (abs(hashtext(c.id_coleta || '-' || p.id_ponto || '-' || t.id_tipo_residuo)::bigint) % 3000) / 100.0
             ) * CASE p.tipo_ponto WHEN 'PEV' THEN 4.0 WHEN 'CONDOMINIO' THEN 3.0
                                   WHEN 'COMERCIAL' THEN 2.5 ELSE 1.0 END
               * CASE t.categoria WHEN 'RECICLAVEL' THEN 0.2 * pb.adesao
                                  WHEN 'ORGANICO'   THEN pb.organico ELSE 1.0 END
               * pb.geracao * fm.fator
               * CASE WHEN EXTRACT(isodow FROM c.data_coleta) = 1 THEN 1.15 ELSE 1.0 END
               * CASE WHEN (r.id_bairro, r.tipo_coleta) IN ((10, 'CONVENCIONAL'), (7, 'SELETIVA'))
                      THEN 0.5 ELSE 1.0 END, 2)
FROM oltp.coleta c
JOIN oltp.rota r           ON r.id_rota = c.id_rota
JOIN oltp.ponto_coleta p   ON p.id_bairro = r.id_bairro
JOIN oltp.tipo_residuo t   ON (r.tipo_coleta = 'CONVENCIONAL' AND t.categoria IN ('ORGANICO','REJEITO'))
                           OR (r.tipo_coleta = 'SELETIVA'     AND t.categoria = 'RECICLAVEL')
JOIN sint_perfil_bairro pb ON pb.id_bairro = r.id_bairro
JOIN sint_fator_mes fm     ON fm.mes = EXTRACT(month FROM c.data_coleta)::int
WHERE c.status = 'CONCLUIDA'
  AND abs(hashtext(c.id_coleta || '~' || p.id_ponto || '~' || t.id_tipo_residuo)::bigint) % 3 <> 0;

-- Descargas: soma por coleta e tipo. A parte aproveitada vai ao destino padrão do tipo; o REJEITO da
-- triagem dos recicláveis (padrão P6) segue ao aterro dois dias depois.
INSERT INTO oltp.descarga (id_coleta, id_destino, id_tipo_residuo, peso_kg, data_hora)
WITH base AS (
    SELECT c.id_coleta, i.id_tipo_residuo, t.destinacao_padrao, SUM(i.peso_kg) AS kg,
           (c.data_coleta + c.hora_fim) + INTERVAL '30 minutes' AS dh,
           CASE t.nome WHEN 'Plástico' THEN 0.35 WHEN 'Papel e papelão' THEN 0.12
                       WHEN 'Vidro' THEN 0.08 WHEN 'Metal' THEN 0.05 ELSE 0 END AS rej
    FROM oltp.coleta_item i
    JOIN oltp.coleta c       ON c.id_coleta = i.id_coleta
    JOIN oltp.tipo_residuo t ON t.id_tipo_residuo = i.id_tipo_residuo
    GROUP BY c.id_coleta, i.id_tipo_residuo, t.destinacao_padrao, t.nome, c.data_coleta, c.hora_fim
)
SELECT b.id_coleta, d.id_destino, b.id_tipo_residuo, round(b.kg * (1 - b.rej), 2), b.dh
FROM base b JOIN oltp.destino_final d ON d.tipo = b.destinacao_padrao
WHERE round(b.kg * (1 - b.rej), 2) > 0
UNION ALL
SELECT b.id_coleta, a.id_destino, b.id_tipo_residuo, round(b.kg * b.rej, 2), b.dh + INTERVAL '2 days'
FROM base b JOIN oltp.destino_final a ON a.tipo = 'ATERRO_SANITARIO'
WHERE b.rej > 0 AND round(b.kg * b.rej, 2) > 0;

-- Ocorrências: 600 registros de cidadãos ao longo de 2025 (padrão P5)
INSERT INTO oltp.ocorrencia (id_bairro, id_ponto, tipo_ocorrencia, canal, data_abertura, data_fechamento, status)
WITH g AS (
    SELECT i,
           abs(hashtext('ob' || i)::bigint) AS h_b, abs(hashtext('om' || i)::bigint) AS h_m,
           abs(hashtext('od' || i)::bigint) AS h_d, abs(hashtext('op' || i)::bigint) AS h_p,
           abs(hashtext('oc' || i)::bigint) AS h_c, abs(hashtext('ot' || i)::bigint) AS h_t,
           abs(hashtext('on' || i)::bigint) AS h_n, abs(hashtext('oo' || i)::bigint) AS h_o,
           abs(hashtext('os' || i)::bigint) AS h_s
    FROM generate_series(1, 600) AS i
), k AS (
    SELECT g.*, pb.id_bairro, bb.regiao,
           MAKE_TIMESTAMP(2025, pm.mes, 1 + (g.h_d % 28)::int, ((g.h_d / 28) % 24)::int,
                          ((g.h_d / 700) % 60)::int, 0) AS ts
    FROM g
    JOIN sint_peso_bairro pb ON g.h_b % 100 >= pb.lo AND g.h_b % 100 < pb.hi
    JOIN oltp.bairro bb      ON bb.id_bairro = pb.id_bairro
    JOIN sint_peso_mes pm    ON g.h_m % 100 >= pm.lo AND g.h_m % 100 < pm.hi
), t AS (
    SELECT k.*,
           CASE WHEN id_bairro IN (3, 6, 9, 12) THEN        -- bairros de turno da manhã (mais cancelamentos)
                    CASE WHEN h_t % 100 < 40 THEN 'COLETA_NAO_REALIZADA' WHEN h_t % 100 < 55 THEN 'DESCARTE_IRREGULAR'
                         WHEN h_t % 100 < 72 THEN 'CONTAINER_DANIFICADO' WHEN h_t % 100 < 88 THEN 'SOLICITACAO_VOLUMOSO'
                         ELSE 'OUTROS' END
                WHEN id_bairro IN (7, 10) THEN              -- mais descarte irregular
                    CASE WHEN h_t % 100 < 10 THEN 'COLETA_NAO_REALIZADA' WHEN h_t % 100 < 55 THEN 'DESCARTE_IRREGULAR'
                         WHEN h_t % 100 < 70 THEN 'CONTAINER_DANIFICADO' WHEN h_t % 100 < 85 THEN 'SOLICITACAO_VOLUMOSO'
                         ELSE 'OUTROS' END
                ELSE
                    CASE WHEN h_t % 100 < 12 THEN 'COLETA_NAO_REALIZADA' WHEN h_t % 100 < 35 THEN 'DESCARTE_IRREGULAR'
                         WHEN h_t % 100 < 60 THEN 'CONTAINER_DANIFICADO' WHEN h_t % 100 < 80 THEN 'SOLICITACAO_VOLUMOSO'
                         ELSE 'OUTROS' END
           END AS tipo
    FROM k
), q AS (
    SELECT t.*,
           ( CASE tipo WHEN 'COLETA_NAO_REALIZADA' THEN 24 WHEN 'DESCARTE_IRREGULAR' THEN 60
                       WHEN 'CONTAINER_DANIFICADO' THEN 96 WHEN 'SOLICITACAO_VOLUMOSO' THEN 120 ELSE 48 END
           * CASE regiao WHEN 'CENTRO' THEN 0.7 WHEN 'NORTE' THEN 1.0 WHEN 'SUL' THEN 1.3
                         WHEN 'LESTE' THEN 1.1 ELSE 1.5 END
           * (0.6 + (h_n % 100) / 125.0)
           * CASE WHEN h_o % 33 = 0 THEN 4 ELSE 1 END ) AS horas,
           ((ts >= TIMESTAMP '2025-12-05' AND h_s % 100 < 55) OR h_s % 100 < 2) AS aberta
    FROM t
)
SELECT q.id_bairro,
       CASE WHEN q.h_p % 100 < 25 THEN NULL
            ELSE (SELECT pc.id_ponto FROM oltp.ponto_coleta pc
                  WHERE pc.id_bairro = q.id_bairro ORDER BY pc.id_ponto OFFSET (q.h_p % 20)::int LIMIT 1) END,
       q.tipo,
       CASE WHEN q.h_c % 100 < 55 THEN 'APP' WHEN q.h_c % 100 < 85 THEN 'TELEFONE' ELSE 'PRESENCIAL' END,
       q.ts,
       CASE WHEN q.aberta THEN NULL ELSE q.ts + GREATEST(2, round(q.horas)::int) * INTERVAL '1 hour' END,
       CASE WHEN NOT q.aberta THEN 'RESOLVIDA'
            WHEN q.h_s % 2 = 0   THEN 'ABERTA' ELSE 'EM_ATENDIMENTO' END
FROM q;

DROP TABLE sint_perfil_bairro, sint_fator_mes, sint_peso_bairro, sint_peso_mes;

-- =====================================================================
-- PARTE 4 - ETL: OLTP -> OLAP (carga completa; reexecutável após TRUNCATE)
-- =====================================================================

-- 4.1 Dimensões
INSERT INTO dw.dim_tempo
SELECT to_char(d, 'YYYYMMDD')::int,
       d::date,
       EXTRACT(day FROM d)::smallint,
       EXTRACT(month FROM d)::smallint,
       (ARRAY['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto',
              'Setembro','Outubro','Novembro','Dezembro'])[EXTRACT(month FROM d)::int],
       EXTRACT(quarter FROM d)::smallint,
       CASE WHEN EXTRACT(month FROM d) <= 6 THEN 1 ELSE 2 END,
       EXTRACT(year FROM d)::smallint,
       EXTRACT(isodow FROM d)::smallint,
       (ARRAY['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'])[EXTRACT(isodow FROM d)::int],
       EXTRACT(isodow FROM d) >= 6
FROM generate_series(DATE '2025-01-01', DATE '2026-12-31', INTERVAL '1 day') AS d;

INSERT INTO dw.dim_local (id_ponto_origem, id_bairro_origem, tipo_ponto, logradouro, bairro, regiao,
                          populacao_bairro, area_km2_bairro)
SELECT p.id_ponto, b.id_bairro, p.tipo_ponto, p.logradouro || ', ' || COALESCE(p.numero, 's/n'),
       b.nome, b.regiao, b.populacao, b.area_km2
FROM oltp.ponto_coleta p JOIN oltp.bairro b ON b.id_bairro = p.id_bairro;

-- Membro "bairro inteiro" para ocorrências sem ponto específico
INSERT INTO dw.dim_local (id_ponto_origem, id_bairro_origem, tipo_ponto, logradouro, bairro, regiao,
                          populacao_bairro, area_km2_bairro)
SELECT NULL, b.id_bairro, 'NAO_INFORMADO', NULL, b.nome, b.regiao, b.populacao, b.area_km2
FROM oltp.bairro b;

INSERT INTO dw.dim_tipo_residuo (id_origem, nome, categoria, reciclavel, destinacao_padrao)
SELECT id_tipo_residuo, nome, categoria, reciclavel, destinacao_padrao FROM oltp.tipo_residuo;

INSERT INTO dw.dim_veiculo (id_origem, placa, tipo, capacidade_kg, ano_fabricacao)
SELECT id_veiculo, placa, tipo, capacidade_kg, ano_fabricacao FROM oltp.veiculo;

INSERT INTO dw.dim_rota (id_origem, nome, tipo_coleta, dia_semana, turno, extensao_km, bairro, regiao)
SELECT r.id_rota, r.nome, r.tipo_coleta, r.dia_semana, r.turno, r.extensao_km, b.nome, b.regiao
FROM oltp.rota r JOIN oltp.bairro b ON b.id_bairro = r.id_bairro;

INSERT INTO dw.dim_funcionario (id_origem, matricula, nome, cargo)
SELECT id_funcionario, matricula, nome, cargo FROM oltp.funcionario;

INSERT INTO dw.dim_destino (id_origem, nome, tipo, capacidade_ton_mes)
SELECT id_destino, nome, tipo, capacidade_ton_mes FROM oltp.destino_final;

INSERT INTO dw.dim_ocorrencia (tipo_ocorrencia, canal, status)
SELECT DISTINCT tipo_ocorrencia, canal, status FROM oltp.ocorrencia;

-- 4.2 Fatos
INSERT INTO dw.fato_coleta (sk_tempo, sk_local, sk_tipo_residuo, sk_rota, sk_veiculo, sk_motorista,
                            id_coleta, peso_kg)
SELECT to_char(c.data_coleta, 'YYYYMMDD')::int, l.sk_local, tr.sk_tipo_residuo, r.sk_rota,
       v.sk_veiculo, f.sk_funcionario, c.id_coleta, i.peso_kg
FROM oltp.coleta_item i
JOIN oltp.coleta c            ON c.id_coleta = i.id_coleta
JOIN dw.dim_local l           ON l.id_ponto_origem = i.id_ponto
JOIN dw.dim_tipo_residuo tr   ON tr.id_origem = i.id_tipo_residuo
JOIN dw.dim_rota r            ON r.id_origem = c.id_rota
JOIN dw.dim_veiculo v         ON v.id_origem = c.id_veiculo
JOIN dw.dim_funcionario f     ON f.id_origem = c.id_motorista;

INSERT INTO dw.fato_destinacao (sk_tempo, sk_destino, sk_tipo_residuo, sk_rota, sk_veiculo, id_coleta, peso_kg)
SELECT to_char(ds.data_hora, 'YYYYMMDD')::int, d.sk_destino, tr.sk_tipo_residuo, r.sk_rota,
       v.sk_veiculo, ds.id_coleta, ds.peso_kg
FROM oltp.descarga ds
JOIN oltp.coleta c            ON c.id_coleta = ds.id_coleta
JOIN dw.dim_destino d         ON d.id_origem = ds.id_destino
JOIN dw.dim_tipo_residuo tr   ON tr.id_origem = ds.id_tipo_residuo
JOIN dw.dim_rota r            ON r.id_origem = c.id_rota
JOIN dw.dim_veiculo v         ON v.id_origem = c.id_veiculo;

INSERT INTO dw.fato_ocorrencia (id_ocorrencia, sk_tempo_abertura, sk_tempo_fechamento, sk_local,
                                sk_ocorrencia, tempo_resolucao_horas)
SELECT o.id_ocorrencia,
       to_char(o.data_abertura, 'YYYYMMDD')::int,
       to_char(o.data_fechamento, 'YYYYMMDD')::int,
       l.sk_local,
       d.sk_ocorrencia,
       round((EXTRACT(epoch FROM (o.data_fechamento - o.data_abertura)) / 3600)::numeric, 2)
FROM oltp.ocorrencia o
JOIN dw.dim_local l       ON l.id_bairro_origem = o.id_bairro
                         AND l.id_ponto_origem IS NOT DISTINCT FROM o.id_ponto
JOIN dw.dim_ocorrencia d  ON d.tipo_ocorrencia = o.tipo_ocorrencia
                         AND d.canal = o.canal AND d.status = o.status;

INSERT INTO dw.fato_viagem (id_coleta, sk_tempo, sk_rota, sk_veiculo, sk_motorista, km_percorridos,
                            duracao_min, peso_total_kg, qtd_pontos_atendidos, qtd_cancelada)
SELECT c.id_coleta,
       to_char(c.data_coleta, 'YYYYMMDD')::int,
       r.sk_rota, v.sk_veiculo, f.sk_funcionario,
       c.km_percorridos,
       (EXTRACT(epoch FROM (c.hora_fim - c.hora_inicio)) / 60)::int,
       COALESCE(i.peso, 0), COALESCE(i.pontos, 0),
       CASE WHEN c.status = 'CANCELADA' THEN 1 ELSE 0 END
FROM oltp.coleta c
JOIN dw.dim_rota r        ON r.id_origem = c.id_rota
JOIN dw.dim_veiculo v     ON v.id_origem = c.id_veiculo
JOIN dw.dim_funcionario f ON f.id_origem = c.id_motorista
LEFT JOIN (SELECT id_coleta, SUM(peso_kg) AS peso, COUNT(DISTINCT id_ponto) AS pontos
           FROM oltp.coleta_item GROUP BY id_coleta) i ON i.id_coleta = c.id_coleta;

ANALYZE;

-- =====================================================================
-- PARTE 5 - VERIFICAÇÃO RÁPIDA (volumes carregados)
-- =====================================================================
SELECT 'oltp.coleta' AS tabela, COUNT(*) AS linhas FROM oltp.coleta
UNION ALL SELECT 'oltp.coleta_item',     COUNT(*) FROM oltp.coleta_item
UNION ALL SELECT 'oltp.descarga',        COUNT(*) FROM oltp.descarga
UNION ALL SELECT 'oltp.ocorrencia',      COUNT(*) FROM oltp.ocorrencia
UNION ALL SELECT 'dw.fato_coleta',       COUNT(*) FROM dw.fato_coleta
UNION ALL SELECT 'dw.fato_viagem',       COUNT(*) FROM dw.fato_viagem
UNION ALL SELECT 'dw.fato_destinacao',   COUNT(*) FROM dw.fato_destinacao
UNION ALL SELECT 'dw.fato_ocorrencia',   COUNT(*) FROM dw.fato_ocorrencia;
