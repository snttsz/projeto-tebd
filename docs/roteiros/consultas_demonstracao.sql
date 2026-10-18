-- =====================================================================
-- Consultas da demonstração ao vivo (checkpoint). Abrir no pgAdmin: Query Tool > abrir arquivo.
-- Banco: cidades_sustentaveis. Execute UMA consulta por vez (selecione o trecho e F5).
-- Antes: confira que o banco está consistente com
--        python src/scripts/popular_banco.py --verificar
-- Lembrete: os dados são SINTÉTICOS, com padrões deliberados.
-- =====================================================================

-- C1 · O ETL funcionou? OLTP e DW têm as mesmas contagens.
-- Esperado: coleta_item = fato_coleta (47.234) e coleta = fato_viagem (1.252)
SELECT 'oltp.coleta_item' AS tabela, COUNT(*) AS linhas FROM oltp.coleta_item
UNION ALL SELECT 'dw.fato_coleta',  COUNT(*) FROM dw.fato_coleta
UNION ALL SELECT 'oltp.coleta',     COUNT(*) FROM oltp.coleta
UNION ALL SELECT 'dw.fato_viagem',  COUNT(*) FROM dw.fato_viagem;

-- C2 · (Tático T1) Quais rotas rendem menos quilos por quilômetro?
-- Esperado: a seletiva de Novo Horizonte em último, com 2,2 kg/km
SELECT rota, kg_por_km, pct_canceladas
FROM bi.v_produtividade_rota
ORDER BY kg_por_km
LIMIT 5;

-- C3 · (Tático T2) Em que turno mais se cancelam coletas?
-- Esperado: MANHA 11,1% contra ~3,7% nos outros turnos
SELECT turno,
       SUM(viagens)    AS viagens,
       SUM(canceladas) AS canceladas,
       ROUND(100.0 * SUM(canceladas) / SUM(viagens), 1) AS pct
FROM bi.v_produtividade_rota
GROUP BY turno
ORDER BY pct DESC;

-- C4 · (Estratégico E2) Qual a taxa de recicláveis por bairro? Onde expandir a seletiva?
-- Esperado: de 36,3% (Parque das Águas) a 7,0% (Novo Horizonte)
SELECT bairro,
       ROUND(100.0 * SUM(toneladas) FILTER (WHERE reciclavel) / SUM(toneladas), 1) AS pct_reciclavel
FROM bi.v_toneladas_mes
GROUP BY bairro
ORDER BY pct_reciclavel DESC;

-- C5 · (Estratégico E3) Quanto do material enviado à cooperativa vira rejeito, por tipo?
-- Esperado: Plástico 35%, Papel 12%, Vidro 8%, Metal 5%
SELECT tipo_residuo,
       ROUND(100.0 * SUM(toneladas) FILTER (WHERE tipo_destino = 'ATERRO_SANITARIO') / SUM(toneladas), 1) AS pct_rejeito
FROM bi.v_destinacao
WHERE tipo_residuo IN ('Plástico', 'Papel e papelão', 'Vidro', 'Metal')
GROUP BY tipo_residuo
ORDER BY pct_rejeito DESC;

-- C6 · (Operacional O2) Quantas ocorrências estão abertas há mais de 72 horas?
-- Esperado: 53
SELECT COUNT(*) AS abertas_mais_de_72h
FROM bi.v_ocorrencia_aberta
WHERE horas_abertas > 72;

-- C7 · (Estratégico E1) Como evolui a quantidade coletada por mês?
-- Esperado: fevereiro ~53 t (mínimo) e dezembro ~107 t (máximo)
SELECT mes, ROUND(SUM(toneladas), 1) AS toneladas
FROM bi.v_toneladas_mes
GROUP BY mes
ORDER BY mes;
