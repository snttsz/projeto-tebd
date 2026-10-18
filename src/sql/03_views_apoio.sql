-- =====================================================================
-- Views de apoio aos dashboards (entrega de 06/11) - schema bi
-- Executar APÓS 01 e 02. Se o script 01 for reexecutado, estas views são apagadas
-- junto com os schemas oltp/dw (DROP ... CASCADE): rode este arquivo de novo.
-- Objetivo: simplificar as consultas dos dashboards (cada view já faz as junções).
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS bi;

-- Data de referência do "agora": os dados sintéticos terminam em 31/12/2025.
CREATE OR REPLACE FUNCTION bi.data_referencia() RETURNS TIMESTAMP
LANGUAGE sql IMMUTABLE AS $$ SELECT TIMESTAMP '2026-01-01 00:00' $$;

-- ---------------------------------------------------------------------
-- OPERACIONAL (lê o OLTP: olha o dia a dia)
-- ---------------------------------------------------------------------
-- Uma linha por coleta, com rota, veículo, motorista, peso e pontos atendidos.
CREATE OR REPLACE VIEW bi.v_coleta_detalhe AS
SELECT c.id_coleta, c.data_coleta,
       EXTRACT(isodow FROM c.data_coleta)::int AS dia_semana,
       b.nome AS bairro, b.regiao, r.nome AS rota, r.tipo_coleta, r.turno,
       v.placa, v.tipo AS tipo_veiculo, v.capacidade_kg, v.ano_fabricacao,
       f.nome AS motorista, c.status, c.hora_inicio, c.hora_fim, c.km_percorridos,
       COALESCE(i.peso_kg, 0) AS peso_kg, COALESCE(i.pontos, 0) AS pontos_atendidos
FROM oltp.coleta c
JOIN oltp.rota r        ON r.id_rota = c.id_rota
JOIN oltp.bairro b      ON b.id_bairro = r.id_bairro
JOIN oltp.veiculo v     ON v.id_veiculo = c.id_veiculo
JOIN oltp.funcionario f ON f.id_funcionario = c.id_motorista
LEFT JOIN (SELECT id_coleta, SUM(peso_kg) AS peso_kg, COUNT(DISTINCT id_ponto) AS pontos
           FROM oltp.coleta_item GROUP BY id_coleta) i ON i.id_coleta = c.id_coleta;

-- Ocorrências ainda não resolvidas e há quantas horas estão abertas (em relação a bi.data_referencia()).
CREATE OR REPLACE VIEW bi.v_ocorrencia_aberta AS
SELECT o.id_ocorrencia, o.tipo_ocorrencia, o.canal, o.status, o.data_abertura,
       b.nome AS bairro, b.regiao,
       ROUND((EXTRACT(epoch FROM (bi.data_referencia() - o.data_abertura)) / 3600)::numeric, 0) AS horas_abertas
FROM oltp.ocorrencia o
JOIN oltp.bairro b ON b.id_bairro = o.id_bairro
WHERE o.status <> 'RESOLVIDA';

-- ---------------------------------------------------------------------
-- TÁTICO (lê o DW: rotas, turnos, meses)
-- ---------------------------------------------------------------------
-- Produtividade por rota: viagens, cancelamentos, km, kg, kg/km e duração média.
CREATE OR REPLACE VIEW bi.v_produtividade_rota AS
SELECT r.nome AS rota, r.bairro, r.regiao, r.tipo_coleta, r.turno,
       COUNT(*) AS viagens,
       SUM(v.qtd_cancelada) AS canceladas,
       ROUND(100.0 * SUM(v.qtd_cancelada) / COUNT(*), 1) AS pct_canceladas,
       ROUND(SUM(v.km_percorridos), 0) AS km,
       ROUND(SUM(v.peso_total_kg), 0) AS kg,
       ROUND((SUM(v.peso_total_kg) / NULLIF(SUM(v.km_percorridos), 0))::numeric, 1) AS kg_por_km,
       ROUND(AVG(v.duracao_min), 0) AS duracao_media_min
FROM dw.fato_viagem v
JOIN dw.dim_rota r ON r.sk_rota = v.sk_rota
GROUP BY r.nome, r.bairro, r.regiao, r.tipo_coleta, r.turno;

-- Tempo de resolução de ocorrências por tipo e região (média, nunca soma).
CREATE OR REPLACE VIEW bi.v_resolucao_ocorrencia AS
SELECT o.tipo_ocorrencia, l.regiao,
       COUNT(*) AS qtd,
       COUNT(f.tempo_resolucao_horas) AS resolvidas,
       ROUND(AVG(f.tempo_resolucao_horas), 0) AS horas_medias,
       ROUND(MAX(f.tempo_resolucao_horas), 0) AS horas_maximas
FROM dw.fato_ocorrencia f
JOIN dw.dim_ocorrencia o ON o.sk_ocorrencia = f.sk_ocorrencia
JOIN dw.dim_local l      ON l.sk_local = f.sk_local
GROUP BY o.tipo_ocorrencia, l.regiao;

-- ---------------------------------------------------------------------
-- ESTRATÉGICO (lê o DW: tendências e metas)
-- ---------------------------------------------------------------------
-- Toneladas por mês, região, bairro, tipo de resíduo e tipo de coleta.
CREATE OR REPLACE VIEW bi.v_toneladas_mes AS
SELECT t.ano, t.mes, t.trimestre, l.regiao, l.bairro,
       tr.categoria, tr.nome AS tipo_residuo, tr.reciclavel, r.tipo_coleta,
       ROUND(SUM(f.peso_kg) / 1000, 2) AS toneladas
FROM dw.fato_coleta f
JOIN dw.dim_tempo t         ON t.sk_tempo = f.sk_tempo
JOIN dw.dim_local l         ON l.sk_local = f.sk_local
JOIN dw.dim_tipo_residuo tr ON tr.sk_tipo_residuo = f.sk_tipo_residuo
JOIN dw.dim_rota r          ON r.sk_rota = f.sk_rota
GROUP BY t.ano, t.mes, t.trimestre, l.regiao, l.bairro, tr.categoria, tr.nome, tr.reciclavel, r.tipo_coleta;

-- Para onde foi o material: toneladas por destino, tipo de resíduo e mês (inclui o rejeito da triagem).
CREATE OR REPLACE VIEW bi.v_destinacao AS
SELECT t.ano, t.mes, d.nome AS destino, d.tipo AS tipo_destino, d.capacidade_ton_mes,
       tr.nome AS tipo_residuo,
       ROUND(SUM(f.peso_kg) / 1000, 2) AS toneladas
FROM dw.fato_destinacao f
JOIN dw.dim_tempo t         ON t.sk_tempo = f.sk_tempo
JOIN dw.dim_destino d       ON d.sk_destino = f.sk_destino
JOIN dw.dim_tipo_residuo tr ON tr.sk_tipo_residuo = f.sk_tipo_residuo
GROUP BY t.ano, t.mes, d.nome, d.tipo, d.capacidade_ton_mes, tr.nome;

COMMENT ON SCHEMA bi IS 'Views de apoio aos dashboards (operacional, tático e estratégico).';
