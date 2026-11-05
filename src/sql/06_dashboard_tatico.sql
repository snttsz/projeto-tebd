-- Item 8: cinco consultas táticas no DW; ano de 2025.
-- Percentuais e produtividade são razões de somas, sem média de percentuais.

-- @consulta T1 | Produtividade por rota | A coordenação de rotas identifica menor peso por quilômetro; compare também o tipo de coleta, pois convencional e seletiva têm perfis diferentes. | rota | kg_por_km
SELECT r.nome AS rota, r.bairro, r.tipo_coleta, r.turno,
       COUNT(*) AS viagens_planejadas, SUM(v.qtd_cancelada) AS canceladas,
       SUM(v.peso_total_kg) AS peso_kg, SUM(v.km_percorridos) AS km,
       ROUND(SUM(v.peso_total_kg) / NULLIF(SUM(v.km_percorridos), 0), 2) AS kg_por_km,
       RANK() OVER (PARTITION BY r.tipo_coleta ORDER BY
         SUM(v.peso_total_kg) / NULLIF(SUM(v.km_percorridos), 0) ASC NULLS LAST) AS posicao_menor_produtividade
FROM dw.fato_viagem v
JOIN dw.dim_rota r ON r.sk_rota = v.sk_rota
JOIN dw.dim_tempo t ON t.sk_tempo = v.sk_tempo
WHERE t.ano = 2025
GROUP BY r.sk_rota, r.nome, r.bairro, r.tipo_coleta, r.turno
ORDER BY kg_por_km ASC NULLS LAST, r.nome;

-- @consulta T2 | Cancelamentos por turno e dia da semana | A coordenação compara a proporção de viagens canceladas sobre todas as viagens de cada turno e dia; volume e percentual devem ser lidos juntos. | turno_dia | cancelamento_pct
SELECT r.turno || ' / ' || t.nome_dia AS turno_dia, r.turno,
       t.dia_semana, t.nome_dia, COUNT(*) AS viagens_planejadas,
       SUM(v.qtd_cancelada) AS canceladas,
       ROUND(100.0 * SUM(v.qtd_cancelada) / COUNT(*), 2) AS cancelamento_pct
FROM dw.fato_viagem v
JOIN dw.dim_rota r ON r.sk_rota = v.sk_rota
JOIN dw.dim_tempo t ON t.sk_tempo = v.sk_tempo
WHERE t.ano = 2025
GROUP BY r.turno, t.dia_semana, t.nome_dia
ORDER BY cancelamento_pct DESC, r.turno, t.dia_semana;

-- @consulta T3 | Tempo de resolução por tipo e região | O atendimento compara a média apenas das resolvidas, incluindo fechamentos posteriores a 2025, e o total sem resolução no estado final da base; NULL significa ausência de resolução observada. | tipo_regiao | horas_medias
SELECT o.tipo_ocorrencia || ' / ' || l.regiao AS tipo_regiao,
       o.tipo_ocorrencia, l.regiao, COUNT(*) AS ocorrencias,
       COUNT(f.tempo_resolucao_horas) AS resolvidas,
       COUNT(*) - COUNT(f.tempo_resolucao_horas) AS sem_resolucao,
       ROUND(AVG(f.tempo_resolucao_horas), 2) AS horas_medias,
       MAX(f.tempo_resolucao_horas) AS horas_maximas
FROM dw.fato_ocorrencia f
JOIN dw.dim_ocorrencia o ON o.sk_ocorrencia = f.sk_ocorrencia
JOIN dw.dim_local l ON l.sk_local = f.sk_local
JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo_abertura
WHERE t.ano = 2025
GROUP BY o.tipo_ocorrencia, l.regiao
ORDER BY horas_medias DESC NULLS LAST, o.tipo_ocorrencia, l.regiao;

-- @consulta T4 | Cancelamentos e idade dos veículos | A frota compara veículos e idade no ano analisado; associação entre idade e cancelamentos não comprova defeito mecânico ou causalidade. | placa | cancelamento_pct
SELECT v.placa, v.tipo, v.ano_fabricacao, 2025 - v.ano_fabricacao AS idade_anos,
       COUNT(*) AS viagens_planejadas, SUM(f.qtd_cancelada) AS canceladas,
       ROUND(100.0 * SUM(f.qtd_cancelada) / COUNT(*), 2) AS cancelamento_pct
FROM dw.fato_viagem f
JOIN dw.dim_veiculo v ON v.sk_veiculo = f.sk_veiculo
JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
WHERE t.ano = 2025
GROUP BY v.sk_veiculo, v.placa, v.tipo, v.ano_fabricacao
ORDER BY cancelamento_pct DESC, v.placa;

-- @consulta T5 | Produtividade e cancelamentos por motorista | A coordenação compara resultados por motorista e tipo de coleta; diferenças de rota, turno e veículo precisam ser investigadas antes de avaliar desempenho individual. | motorista_tipo | kg_por_km
SELECT m.nome || ' / ' || r.tipo_coleta AS motorista_tipo,
       m.matricula, m.nome AS motorista, r.tipo_coleta,
       COUNT(*) AS viagens_planejadas, SUM(f.qtd_cancelada) AS canceladas,
       ROUND(100.0 * SUM(f.qtd_cancelada) / COUNT(*), 2) AS cancelamento_pct,
       ROUND(SUM(f.peso_total_kg) / NULLIF(SUM(f.km_percorridos), 0), 2) AS kg_por_km,
       ROUND(AVG(f.duracao_min), 2) AS duracao_media_min
FROM dw.fato_viagem f
JOIN dw.dim_funcionario m ON m.sk_funcionario = f.sk_motorista
JOIN dw.dim_rota r ON r.sk_rota = f.sk_rota
JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
WHERE t.ano = 2025
GROUP BY m.sk_funcionario, m.matricula, m.nome, r.tipo_coleta
ORDER BY r.tipo_coleta, kg_por_km ASC NULLS LAST, m.nome;
