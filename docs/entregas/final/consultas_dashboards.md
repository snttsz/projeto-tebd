# Ciclo Urbano — 15 consultas de gestão

Dados sintéticos de 2025. Operacional: últimos sete dias completos antes de 01/01/2026; O2: situação na referência.

Reprodução isolada dos scripts 01–03 em PostgreSQL embarcado (PGlite 0.5.15), reconciliada com a base do K-means de 31/10. Não é conexão ao banco original.

## O1 — Coletas canceladas

A supervisão identifica rota, veículo e motorista das coletas canceladas nos últimos sete dias completos.

```sql
SELECT c.id_coleta, c.data_coleta, b.nome AS bairro, r.nome AS rota,
       r.turno, v.placa, f.nome AS motorista, c.status
FROM oltp.coleta c
JOIN oltp.rota r ON r.id_rota = c.id_rota
JOIN oltp.bairro b ON b.id_bairro = r.id_bairro
JOIN oltp.veiculo v ON v.id_veiculo = c.id_veiculo
JOIN oltp.funcionario f ON f.id_funcionario = c.id_motorista
WHERE c.status = 'CANCELADA'
  AND c.data_coleta >= bi.data_referencia()::date - 7
  AND c.data_coleta < bi.data_referencia()::date
ORDER BY c.data_coleta DESC, c.id_coleta;
```

Colunas: id_coleta, data_coleta, bairro, rota, turno, placa, motorista, status.

Execução: 3 registros. Resultados completos no painel e em resultados_dashboards.json.

## O2 — Ocorrências abertas há mais de 72 horas

A supervisão prioriza registros sem resolução na referência, mesmo que tenham sido fechados depois; são 54 nessa data, contra 53 ainda abertos no estado final da base.

```sql
SELECT o.id_ocorrencia, b.nome AS bairro, b.regiao, o.tipo_ocorrencia,
       o.canal, 'SEM_RESOLUCAO' AS situacao_na_referencia,
       o.status AS status_final_base, o.data_abertura, o.data_fechamento,
       ROUND(EXTRACT(epoch FROM (bi.data_referencia() - o.data_abertura)) / 3600, 1) AS horas_abertas
FROM oltp.ocorrencia o
JOIN oltp.bairro b ON b.id_bairro = o.id_bairro
WHERE o.data_abertura < bi.data_referencia() - INTERVAL '72 hours'
  AND (o.data_fechamento IS NULL OR o.data_fechamento > bi.data_referencia())
ORDER BY horas_abertas DESC, o.id_ocorrencia;
```

Colunas: id_ocorrencia, bairro, regiao, tipo_ocorrencia, canal, situacao_na_referencia, status_final_base, data_abertura, data_fechamento, horas_abertas.

Execução: 54 registros. Resultados completos no painel e em resultados_dashboards.json.

## O3 — Quilômetros por veículo na semana

A coordenação de frota compara a distância registrada por veículo nos últimos sete dias completos; veículos sem viagens concluídas aparecem com zero.

```sql
SELECT v.placa, v.tipo, COUNT(c.id_coleta) AS coletas_concluidas,
       COALESCE(SUM(c.km_percorridos), 0) AS km
FROM oltp.veiculo v
LEFT JOIN oltp.coleta c ON c.id_veiculo = v.id_veiculo
  AND c.status = 'CONCLUIDA'
  AND c.data_coleta >= bi.data_referencia()::date - 7
  AND c.data_coleta < bi.data_referencia()::date
GROUP BY v.id_veiculo, v.placa, v.tipo
ORDER BY km DESC, v.placa;
```

Colunas: placa, tipo, coletas_concluidas, km.

Execução: 8 registros. Resultados completos no painel e em resultados_dashboards.json.

## O4 — Ocupação dos veículos por coleta

A coordenação de frota compara o peso de cada coleta concluída com a capacidade nominal; acima de 100% exige verificar a pesagem e a possibilidade de múltiplas descargas.

```sql
WITH pesos AS (
  SELECT id_coleta, SUM(peso_kg) AS peso_kg
  FROM oltp.coleta_item GROUP BY id_coleta
)
SELECT c.id_coleta, c.data_coleta, r.nome AS rota, v.placa, v.capacidade_kg,
       COALESCE(p.peso_kg, 0) AS peso_kg,
       ROUND(100.0 * COALESCE(p.peso_kg, 0) / NULLIF(v.capacidade_kg, 0), 2) AS ocupacao_pct
FROM oltp.coleta c
JOIN oltp.rota r ON r.id_rota = c.id_rota
JOIN oltp.veiculo v ON v.id_veiculo = c.id_veiculo
LEFT JOIN pesos p ON p.id_coleta = c.id_coleta
WHERE c.status = 'CONCLUIDA'
  AND c.data_coleta >= bi.data_referencia()::date - 7
  AND c.data_coleta < bi.data_referencia()::date
ORDER BY ocupacao_pct DESC, c.id_coleta;
```

Colunas: id_coleta, data_coleta, rota, placa, capacidade_kg, peso_kg, ocupacao_pct.

Execução: 21 registros. Resultados completos no painel e em resultados_dashboards.json.

## O5 — Coletas concluídas por coletor na semana

A supervisão consulta a participação de cada coletor nas viagens concluídas nos últimos sete dias completos; a soma entre coletores não representa viagens distintas.

```sql
SELECT f.matricula, f.nome AS coletor, COUNT(c.id_coleta) AS coletas_concluidas
FROM oltp.funcionario f
LEFT JOIN oltp.coleta_equipe e ON e.id_funcionario = f.id_funcionario
LEFT JOIN oltp.coleta c ON c.id_coleta = e.id_coleta
  AND c.status = 'CONCLUIDA'
  AND c.data_coleta >= bi.data_referencia()::date - 7
  AND c.data_coleta < bi.data_referencia()::date
WHERE f.cargo = 'COLETOR'
GROUP BY f.id_funcionario, f.matricula, f.nome
ORDER BY coletas_concluidas DESC, f.nome;
```

Colunas: matricula, coletor, coletas_concluidas.

Execução: 18 registros. Resultados completos no painel e em resultados_dashboards.json.

## T1 — Produtividade por rota

A coordenação de rotas identifica menor peso por quilômetro; compare também o tipo de coleta, pois convencional e seletiva têm perfis diferentes.

```sql
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
```

Colunas: rota, bairro, tipo_coleta, turno, viagens_planejadas, canceladas, peso_kg, km, kg_por_km, posicao_menor_produtividade.

Execução: 24 registros. Resultados completos no painel e em resultados_dashboards.json.

## T2 — Cancelamentos por turno e dia da semana

A coordenação compara a proporção de viagens canceladas sobre todas as viagens de cada turno e dia; volume e percentual devem ser lidos juntos.

```sql
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
```

Colunas: turno_dia, turno, dia_semana, nome_dia, viagens_planejadas, canceladas, cancelamento_pct.

Execução: 9 registros. Resultados completos no painel e em resultados_dashboards.json.

## T3 — Tempo de resolução por tipo e região

O atendimento compara a média apenas das resolvidas, incluindo fechamentos posteriores a 2025, e o total sem resolução no estado final da base; NULL significa ausência de resolução observada.

```sql
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
```

Colunas: tipo_regiao, tipo_ocorrencia, regiao, ocorrencias, resolvidas, sem_resolucao, horas_medias, horas_maximas.

Execução: 25 registros. Resultados completos no painel e em resultados_dashboards.json.

## T4 — Cancelamentos e idade dos veículos

A frota compara veículos e idade no ano analisado; associação entre idade e cancelamentos não comprova defeito mecânico ou causalidade.

```sql
SELECT v.placa, v.tipo, v.ano_fabricacao, 2025 - v.ano_fabricacao AS idade_anos,
       COUNT(*) AS viagens_planejadas, SUM(f.qtd_cancelada) AS canceladas,
       ROUND(100.0 * SUM(f.qtd_cancelada) / COUNT(*), 2) AS cancelamento_pct
FROM dw.fato_viagem f
JOIN dw.dim_veiculo v ON v.sk_veiculo = f.sk_veiculo
JOIN dw.dim_tempo t ON t.sk_tempo = f.sk_tempo
WHERE t.ano = 2025
GROUP BY v.sk_veiculo, v.placa, v.tipo, v.ano_fabricacao
ORDER BY cancelamento_pct DESC, v.placa;
```

Colunas: placa, tipo, ano_fabricacao, idade_anos, viagens_planejadas, canceladas, cancelamento_pct.

Execução: 6 registros. Resultados completos no painel e em resultados_dashboards.json.

## T5 — Produtividade e cancelamentos por motorista

A coordenação compara resultados por motorista e tipo de coleta; diferenças de rota, turno e veículo precisam ser investigadas antes de avaliar desempenho individual.

```sql
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
```

Colunas: motorista_tipo, matricula, motorista, tipo_coleta, viagens_planejadas, canceladas, cancelamento_pct, kg_por_km, duracao_media_min.

Execução: 12 registros. Resultados completos no painel e em resultados_dashboards.json.

## E1 — Evolução mensal por tipo de resíduo

A secretaria acompanha toneladas e variação sobre o mês anterior; meses sem coleta ficam com zero e o primeiro mês fica sem comparação.

```sql
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
```

Colunas: mes, tipo_residuo, mes_tipo, toneladas, variacao_mensal_pct.

Execução: 96 registros. Resultados completos no painel e em resultados_dashboards.json.

## E2 — Participação de recicláveis por bairro e região

A secretaria identifica onde investigar expansão da seletiva; o percentual mede material reciclável coletado antes da triagem, não reciclagem efetiva.

```sql
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
```

Colunas: local, regiao, nivel, toneladas, reciclaveis_t, reciclaveis_pct.

Execução: 17 registros. Resultados completos no painel e em resultados_dashboards.json.

## E3 — Rejeito da triagem por material reciclável

A secretaria e a cooperativa comparam recicláveis destinados ao aterro com o total destinado do mesmo material nas coletas de 2025, incluindo descargas posteriores ao ano.

```sql
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
```

Colunas: material, total_destinado_t, cooperativa_t, rejeito_t, rejeito_pct.

Execução: 4 registros. Resultados completos no painel e em resultados_dashboards.json.

## E4 — Destinos e uso da capacidade mensal

A secretaria acompanha participação no peso destinado no mês e uso da capacidade; meses sem descarga ficam com zero e capacidades não são somadas por material.

```sql
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
```

Colunas: mes, destino, mes_destino, tipo, capacidade_ton_mes, toneladas, participacao_pct, capacidade_utilizada_pct.

Execução: 48 registros. Resultados completos no painel e em resultados_dashboards.json.

## E5 — Ocorrências por trimestre e região

A secretaria acompanha registros abertos por trimestre, incluindo zeros; queda de registros não comprova melhora sem avaliar os canais de atendimento.

```sql
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
```

Colunas: trimestre, regiao, trimestre_regiao, ocorrencias, variacao_trimestral_pct.

Execução: 20 registros. Resultados completos no painel e em resultados_dashboards.json.
