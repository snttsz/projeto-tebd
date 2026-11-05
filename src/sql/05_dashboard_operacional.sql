-- Item 7: cinco consultas operacionais, somente leitura no OLTP.
-- Referência: bi.data_referencia() = 01/01/2026. Semana = últimos sete dias completos.
-- Execute cada SELECT separadamente no pgAdmin ou use gerar_paineis.mjs.

-- @consulta O1 | Coletas canceladas | A supervisão identifica rota, veículo e motorista das coletas canceladas nos últimos sete dias completos. | data_coleta | id_coleta
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

-- @consulta O2 | Ocorrências abertas há mais de 72 horas | A supervisão prioriza registros sem resolução na referência, mesmo que tenham sido fechados depois; são 54 nessa data, contra 53 ainda abertos no estado final da base. | bairro | horas_abertas
SELECT o.id_ocorrencia, b.nome AS bairro, b.regiao, o.tipo_ocorrencia,
       o.canal, 'SEM_RESOLUCAO' AS situacao_na_referencia,
       o.status AS status_final_base, o.data_abertura, o.data_fechamento,
       ROUND(EXTRACT(epoch FROM (bi.data_referencia() - o.data_abertura)) / 3600, 1) AS horas_abertas
FROM oltp.ocorrencia o
JOIN oltp.bairro b ON b.id_bairro = o.id_bairro
WHERE o.data_abertura < bi.data_referencia() - INTERVAL '72 hours'
  AND (o.data_fechamento IS NULL OR o.data_fechamento > bi.data_referencia())
ORDER BY horas_abertas DESC, o.id_ocorrencia;

-- @consulta O3 | Quilômetros por veículo na semana | A coordenação de frota compara a distância registrada por veículo nos últimos sete dias completos; veículos sem viagens concluídas aparecem com zero. | placa | km
SELECT v.placa, v.tipo, COUNT(c.id_coleta) AS coletas_concluidas,
       COALESCE(SUM(c.km_percorridos), 0) AS km
FROM oltp.veiculo v
LEFT JOIN oltp.coleta c ON c.id_veiculo = v.id_veiculo
  AND c.status = 'CONCLUIDA'
  AND c.data_coleta >= bi.data_referencia()::date - 7
  AND c.data_coleta < bi.data_referencia()::date
GROUP BY v.id_veiculo, v.placa, v.tipo
ORDER BY km DESC, v.placa;

-- @consulta O4 | Ocupação dos veículos por coleta | A coordenação de frota compara o peso de cada coleta concluída com a capacidade nominal; acima de 100% exige verificar a pesagem e a possibilidade de múltiplas descargas. | id_coleta | ocupacao_pct
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

-- @consulta O5 | Coletas concluídas por coletor na semana | A supervisão consulta a participação de cada coletor nas viagens concluídas nos últimos sete dias completos; a soma entre coletores não representa viagens distintas. | coletor | coletas_concluidas
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
