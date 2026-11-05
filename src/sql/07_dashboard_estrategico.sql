-- Item 9: cinco consultas estratégicas no DW; ano de 2025.

-- @consulta E1 | Evolução mensal por tipo de resíduo | A secretaria acompanha toneladas e variação sobre o mês anterior; meses sem coleta ficam com zero e o primeiro mês fica sem comparação. | mes_tipo | toneladas
WITH mensal AS (
  SELECT t.mes, tr.sk_tipo_residuo, SUM(f.peso_kg) / 1000 AS toneladas
  FROM dw.fato_coleta f
  JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
  JOIN dw.dim_tipo_residuo tr ON tr.sk_tipo_residuo = f.sk_tipo_residuo
  WHERE t.ano = 2025 GROUP BY t.mes, tr.sk_tipo_residuo
), grade AS (
  SELECT m.mes, tr.sk_tipo_residuo, tr.nome AS tipo_residuo,
         COALESCE(p.toneladas, 0) AS toneladas
  FROM generate_series(1, 12) m(mes) CROSS JOIN dw.dim_tipo_residuo tr
  LEFT JOIN mensal p ON p.mes = m.mes AND p.sk_tipo_residuo = tr.sk_tipo_residuo
), evolucao AS (
  SELECT *, LAG(toneladas) OVER (PARTITION BY sk_tipo_residuo ORDER BY mes) AS anterior
  FROM grade
)
SELECT mes, tipo_residuo, LPAD(mes::text, 2, '0') || ' / ' || tipo_residuo AS mes_tipo,
       ROUND(toneladas, 3) AS toneladas,
       ROUND(100 * (toneladas - anterior) / NULLIF(anterior, 0), 2) AS variacao_mensal_pct
FROM evolucao ORDER BY mes, tipo_residuo;

-- @consulta E2 | Participação de recicláveis por bairro e região | A secretaria identifica onde investigar expansão da seletiva; o percentual mede material reciclável coletado antes da triagem, não reciclagem efetiva. | local | reciclaveis_pct
SELECT CASE WHEN GROUPING(l.bairro) = 1 THEN 'Região ' || l.regiao ELSE l.bairro END AS local,
       l.regiao, CASE WHEN GROUPING(l.bairro) = 1 THEN 'REGIAO' ELSE 'BAIRRO' END AS nivel,
       ROUND(SUM(f.peso_kg) / 1000, 3) AS toneladas,
       ROUND(SUM(CASE WHEN tr.reciclavel THEN f.peso_kg ELSE 0 END) / 1000, 3) AS reciclaveis_t,
       ROUND(100.0 * SUM(CASE WHEN tr.reciclavel THEN f.peso_kg ELSE 0 END)
         / NULLIF(SUM(f.peso_kg), 0), 2) AS reciclaveis_pct
FROM dw.fato_coleta f
JOIN dw.dim_local l ON l.sk_local = f.sk_local
JOIN dw.dim_tipo_residuo tr ON tr.sk_tipo_residuo = f.sk_tipo_residuo
JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
WHERE t.ano = 2025
GROUP BY GROUPING SETS ((l.regiao, l.bairro), (l.regiao))
ORDER BY nivel, reciclaveis_pct, local;

-- @consulta E3 | Rejeito da triagem por material reciclável | A secretaria e a cooperativa comparam recicláveis destinados ao aterro com o total destinado do mesmo material nas coletas de 2025, incluindo descargas posteriores ao ano. | material | rejeito_pct
SELECT tr.nome AS material,
       ROUND(SUM(f.peso_kg) / 1000, 3) AS total_destinado_t,
       ROUND(SUM(CASE WHEN d.tipo = 'COOPERATIVA' THEN f.peso_kg ELSE 0 END) / 1000, 3) AS cooperativa_t,
       ROUND(SUM(CASE WHEN d.tipo = 'ATERRO_SANITARIO' THEN f.peso_kg ELSE 0 END) / 1000, 3) AS rejeito_t,
       ROUND(100.0 * SUM(CASE WHEN d.tipo = 'ATERRO_SANITARIO' THEN f.peso_kg ELSE 0 END)
         / NULLIF(SUM(f.peso_kg), 0), 2) AS rejeito_pct
FROM dw.fato_destinacao f
JOIN dw.dim_tipo_residuo tr ON tr.sk_tipo_residuo = f.sk_tipo_residuo
JOIN dw.dim_destino d ON d.sk_destino = f.sk_destino
JOIN dw.fato_viagem v ON v.id_coleta = f.id_coleta
JOIN dw.dim_tempo t ON t.sk_tempo = v.sk_tempo
WHERE t.ano = 2025 AND tr.reciclavel
GROUP BY tr.sk_tipo_residuo, tr.nome
ORDER BY rejeito_pct DESC, material;

-- @consulta E4 | Destinos e uso da capacidade mensal | A secretaria acompanha participação no peso destinado no mês e uso da capacidade; meses sem descarga ficam com zero e capacidades não são somadas por material. | mes_destino | capacidade_utilizada_pct
WITH mensal AS (
  SELECT t.mes, f.sk_destino, SUM(f.peso_kg) / 1000 AS toneladas
  FROM dw.fato_destinacao f
  JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
  WHERE t.ano = 2025 GROUP BY t.mes, f.sk_destino
), grade AS (
  SELECT m.mes, d.nome AS destino, d.tipo, d.capacidade_ton_mes,
         COALESCE(p.toneladas, 0) AS toneladas
  FROM generate_series(1, 12) m(mes) CROSS JOIN dw.dim_destino d
  LEFT JOIN mensal p ON p.mes = m.mes AND p.sk_destino = d.sk_destino
)
SELECT mes, destino, LPAD(mes::text, 2, '0') || ' / ' || destino AS mes_destino,
       tipo, capacidade_ton_mes, ROUND(toneladas, 3) AS toneladas,
       ROUND(100.0 * toneladas / NULLIF(SUM(toneladas) OVER (PARTITION BY mes), 0), 2) AS participacao_pct,
       ROUND(100.0 * toneladas / NULLIF(capacidade_ton_mes, 0), 2) AS capacidade_utilizada_pct
FROM grade ORDER BY mes, destino;

-- @consulta E5 | Ocorrências por trimestre e região | A secretaria acompanha registros abertos por trimestre, incluindo zeros; queda de registros não comprova melhora sem avaliar os canais de atendimento. | trimestre_regiao | ocorrencias
WITH trimestral AS (
  SELECT t.trimestre, l.regiao, SUM(f.qtd_ocorrencias) AS ocorrencias
  FROM dw.fato_ocorrencia f
  JOIN dw.dim_local l ON l.sk_local = f.sk_local
  JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo_abertura
  WHERE t.ano = 2025 GROUP BY t.trimestre, l.regiao
), grade AS (
  SELECT q.trimestre, r.regiao, COALESCE(p.ocorrencias, 0) AS ocorrencias
  FROM generate_series(1, 4) q(trimestre)
  CROSS JOIN (SELECT DISTINCT regiao FROM dw.dim_local) r
  LEFT JOIN trimestral p ON p.trimestre = q.trimestre AND p.regiao = r.regiao
), evolucao AS (
  SELECT *, LAG(ocorrencias) OVER (PARTITION BY regiao ORDER BY trimestre) AS anterior
  FROM grade
)
SELECT trimestre, regiao, trimestre::text || 'º tri / ' || regiao AS trimestre_regiao,
       ocorrencias,
       ROUND(100.0 * (ocorrencias - anterior) / NULLIF(anterior, 0), 2) AS variacao_trimestral_pct
FROM evolucao ORDER BY trimestre, regiao;
