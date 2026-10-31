-- Item 6: base anual do K-means. Somente SELECT; não altera o banco.
-- No pgAdmin, substitua __ANO__ por 2025 e exporte o resultado como CSV UTF-8,
-- com cabeçalho, separador vírgula e ponto decimal.
-- Não juntar fatos entre si: cada processo é agregado antes das junções.
WITH cadastro AS (
    SELECT id_bairro_origem AS id_bairro,
           MIN(bairro) AS bairro, MIN(regiao) AS regiao,
           MIN(populacao_bairro) AS populacao,
           COUNT(DISTINCT (bairro, regiao, populacao_bairro)) AS variantes_cadastro
    FROM dw.dim_local
    GROUP BY id_bairro_origem
), pesos AS (
    SELECT l.id_bairro_origem AS id_bairro,
           SUM(f.peso_kg) AS peso_total_kg,
           COALESCE(SUM(f.peso_kg) FILTER (WHERE tr.reciclavel), 0) AS peso_reciclavel_kg,
           COUNT(*) AS qtd_pesagens
    FROM dw.fato_coleta f
    JOIN dw.dim_local l ON l.sk_local = f.sk_local
    JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
    JOIN dw.dim_tipo_residuo tr ON tr.sk_tipo_residuo = f.sk_tipo_residuo
    WHERE t.ano = __ANO__
    GROUP BY l.id_bairro_origem
), viagens AS (
    -- dim_rota não possui id_bairro: resolve-se a identidade pelo cadastro,
    -- cujo nome/região devem identificar um único bairro (validado no Python).
    SELECT c.id_bairro, COUNT(*) AS viagens, SUM(v.qtd_cancelada) AS canceladas
    FROM dw.fato_viagem v
    JOIN dw.dim_tempo t ON t.sk_tempo = v.sk_tempo
    JOIN dw.dim_rota r ON r.sk_rota = v.sk_rota
    JOIN cadastro c ON c.bairro = r.bairro AND c.regiao = r.regiao
    WHERE t.ano = __ANO__
    GROUP BY c.id_bairro
), ocorrencias AS (
    SELECT l.id_bairro_origem AS id_bairro, COUNT(*) AS ocorrencias
    FROM dw.fato_ocorrencia f
    JOIN dw.dim_local l ON l.sk_local = f.sk_local
    JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo_abertura
    WHERE t.ano = __ANO__
    GROUP BY l.id_bairro_origem
), totais AS (
    -- Totais independentes: permitem detectar perda ou multiplicação nas junções.
    SELECT
      (SELECT SUM(f.peso_kg) FROM dw.fato_coleta f
       JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
       WHERE t.ano = __ANO__) AS total_peso_periodo,
      (SELECT COUNT(*) FROM dw.fato_viagem f
       JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
       WHERE t.ano = __ANO__) AS total_viagens_periodo,
      (SELECT COUNT(*) FROM dw.fato_ocorrencia f
       JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo_abertura
       WHERE t.ano = __ANO__) AS total_ocorrencias_periodo
)
SELECT __ANO__ AS ano, c.*,
       p.peso_total_kg, p.peso_reciclavel_kg, p.qtd_pesagens,
       v.viagens, v.canceladas, COALESCE(o.ocorrencias, 0) AS ocorrencias,
       t.total_peso_periodo, t.total_viagens_periodo, t.total_ocorrencias_periodo
FROM cadastro c
LEFT JOIN pesos p ON p.id_bairro = c.id_bairro
LEFT JOIN viagens v ON v.id_bairro = c.id_bairro
LEFT JOIN ocorrencias o ON o.id_bairro = c.id_bairro
CROSS JOIN totais t
ORDER BY c.id_bairro;
