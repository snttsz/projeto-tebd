-- Somente leitura. Execute um bloco selecionado por vez no Query Tool.
-- Banco: cidades_sustentaveis.

-- V1: inventário dos ambientes implementados.
SELECT table_schema AS ambiente, COUNT(*) AS quantidade_tabelas
FROM information_schema.tables
WHERE table_schema IN ('oltp', 'dw') AND table_type = 'BASE TABLE'
GROUP BY table_schema
ORDER BY table_schema;

-- V2: exemplo de dicionário consultado no catálogo do PostgreSQL.
SELECT a.attname AS atributo,
       format_type(a.atttypid, a.atttypmod) AS tipo,
       CASE WHEN a.attnotnull THEN 'Não' ELSE 'Sim' END AS aceita_nulo,
       col_description(c.oid, a.attnum) AS descricao
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid
WHERE n.nspname = 'oltp' AND c.relname = 'coleta_item'
  AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum;

-- V3: amostra legível de dados operacionais sintéticos.
SELECT c.data_coleta, b.nome AS bairro, tr.nome AS residuo, i.peso_kg
FROM oltp.coleta_item i
JOIN oltp.coleta c ON c.id_coleta = i.id_coleta
JOIN oltp.ponto_coleta p ON p.id_ponto = i.id_ponto
JOIN oltp.bairro b ON b.id_bairro = p.id_bairro
JOIN oltp.tipo_residuo tr ON tr.id_tipo_residuo = i.id_tipo_residuo
ORDER BY c.data_coleta, i.id_coleta, i.id_ponto, i.id_tipo_residuo
LIMIT 5;

-- V4: conferência de contagens entre origem e DW.
SELECT 'Pesagens' AS processo,
       (SELECT COUNT(*) FROM oltp.coleta_item) AS linhas_origem,
       (SELECT COUNT(*) FROM dw.fato_coleta) AS linhas_dw
UNION ALL
SELECT 'Viagens',
       (SELECT COUNT(*) FROM oltp.coleta),
       (SELECT COUNT(*) FROM dw.fato_viagem);
