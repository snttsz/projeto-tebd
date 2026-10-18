-- =====================================================================
-- Dicionário de dados embutido no catálogo do PostgreSQL (COMMENT ON)
-- Executar APÓS 01_construcao_oltp_olap.sql
-- Consulta: SELECT * FROM information_schema.columns + col_description()
-- =====================================================================

DO $$
DECLARE r RECORD;
BEGIN
  -- Comentários de tabela: (schema.tabela, descrição)
  FOR r IN SELECT * FROM (VALUES
    ('oltp.bairro','Bairros do município; base territorial para rotas, pontos e indicadores per capita.'),
    ('oltp.ponto_coleta','Local físico onde resíduos são coletados (domicílio, comércio, PEV etc.).'),
    ('oltp.tipo_residuo','Catálogo de tipos de resíduo com categoria e destinação padrão.'),
    ('oltp.veiculo','Frota de veículos de coleta.'),
    ('oltp.funcionario','Motoristas, coletores e fiscais do serviço de limpeza urbana.'),
    ('oltp.destino_final','Locais de destinação: aterro, cooperativas, usina de compostagem, central de perigosos.'),
    ('oltp.rota','Rota de coleta recorrente (semanal) de um bairro, convencional ou seletiva.'),
    ('oltp.coleta','Execução de uma rota em uma data (viagem do caminhão).'),
    ('oltp.coleta_equipe','Associativa N:N entre coleta e funcionários que compuseram a equipe.'),
    ('oltp.coleta_item','Peso de um tipo de resíduo coletado em um ponto durante uma coleta.'),
    ('oltp.descarga','Descarga dos resíduos de uma coleta em um destino final, por tipo de resíduo; inclui o rejeito da triagem dos recicláveis, enviado ao aterro.'),
    ('oltp.ocorrencia','Reclamações e solicitações do cidadão relacionadas à limpeza urbana.'),
    ('dw.dim_tempo','Dimensão calendário (chave inteira AAAAMMDD).'),
    ('dw.dim_local','Dimensão local: ponto de coleta com hierarquia ponto > bairro > região.'),
    ('dw.dim_tipo_residuo','Dimensão tipo de resíduo (categoria, reciclabilidade, destinação).'),
    ('dw.dim_veiculo','Dimensão veículo.'),
    ('dw.dim_rota','Dimensão rota, com bairro e região desnormalizados.'),
    ('dw.dim_funcionario','Dimensão funcionário (usada como papel "motorista" na fato de coleta).'),
    ('dw.dim_destino','Dimensão destino final.'),
    ('dw.dim_ocorrencia','Dimensão lixo (junk) com tipo, canal e status da ocorrência.'),
    ('dw.fato_coleta','Fato: peso coletado por coleta x ponto x tipo de resíduo.'),
    ('dw.fato_viagem','Fato: uma linha por coleta (viagem), com km, duração, peso total e indicador de cancelamento.'),
    ('dw.fato_destinacao','Fato: peso destinado por coleta x destino x tipo de resíduo.'),
    ('dw.fato_ocorrencia','Fato: uma linha por ocorrência, com tempo de resolução.')
  ) AS t(obj, descr) LOOP
    EXECUTE format('COMMENT ON TABLE %s IS %L', r.obj, r.descr);
  END LOOP;

  -- Comentários de coluna: (schema.tabela.coluna, descrição)
  FOR r IN SELECT * FROM (VALUES
    ('oltp.bairro.id_bairro','Identificador do bairro (PK, sequencial).'),
    ('oltp.bairro.nome','Nome oficial do bairro (único).'),
    ('oltp.bairro.regiao','Região administrativa: CENTRO, NORTE, SUL, LESTE ou OESTE.'),
    ('oltp.bairro.populacao','População residente estimada (habitantes).'),
    ('oltp.bairro.area_km2','Área territorial em km².'),

    ('oltp.ponto_coleta.id_ponto','Identificador do ponto de coleta (PK).'),
    ('oltp.ponto_coleta.id_bairro','Bairro onde o ponto está localizado (FK bairro).'),
    ('oltp.ponto_coleta.tipo_ponto','Natureza do ponto: RESIDENCIAL, COMERCIAL, CONDOMINIO, ORGAO_PUBLICO ou PEV (Ponto de Entrega Voluntária).'),
    ('oltp.ponto_coleta.logradouro','Nome da rua/avenida.'),
    ('oltp.ponto_coleta.numero','Número do imóvel (texto, aceita "s/n").'),
    ('oltp.ponto_coleta.latitude','Latitude em graus decimais (-90 a 90).'),
    ('oltp.ponto_coleta.longitude','Longitude em graus decimais (-180 a 180).'),
    ('oltp.ponto_coleta.ativo','Indica se o ponto ainda é atendido.'),

    ('oltp.tipo_residuo.id_tipo_residuo','Identificador do tipo de resíduo (PK).'),
    ('oltp.tipo_residuo.nome','Nome do tipo de resíduo (único).'),
    ('oltp.tipo_residuo.categoria','Categoria: ORGANICO, REJEITO, RECICLAVEL, PERIGOSO ou VOLUMOSO.'),
    ('oltp.tipo_residuo.reciclavel','Indica se o material é reciclável.'),
    ('oltp.tipo_residuo.destinacao_padrao','Tipo de destino final esperado para o resíduo.'),

    ('oltp.veiculo.id_veiculo','Identificador do veículo (PK).'),
    ('oltp.veiculo.placa','Placa Mercosul (7 caracteres, única).'),
    ('oltp.veiculo.tipo','COMPACTADOR, BAU_SELETIVA, CACAMBA ou CAMINHAO_BAU.'),
    ('oltp.veiculo.capacidade_kg','Capacidade de carga em kg (> 0).'),
    ('oltp.veiculo.ano_fabricacao','Ano de fabricação.'),
    ('oltp.veiculo.ativo','Indica se o veículo está em operação.'),

    ('oltp.funcionario.id_funcionario','Identificador do funcionário (PK).'),
    ('oltp.funcionario.matricula','Matrícula funcional (única).'),
    ('oltp.funcionario.nome','Nome completo.'),
    ('oltp.funcionario.cargo','MOTORISTA, COLETOR ou FISCAL.'),
    ('oltp.funcionario.data_admissao','Data de admissão.'),
    ('oltp.funcionario.ativo','Indica se o vínculo está ativo.'),

    ('oltp.destino_final.id_destino','Identificador do destino (PK).'),
    ('oltp.destino_final.nome','Nome da instalação.'),
    ('oltp.destino_final.tipo','ATERRO_SANITARIO, COOPERATIVA, USINA_COMPOSTAGEM ou CENTRAL_PERIGOSOS.'),
    ('oltp.destino_final.cnpj','CNPJ sem máscara (14 dígitos, único).'),
    ('oltp.destino_final.capacidade_ton_mes','Capacidade mensal de recebimento em toneladas (> 0).'),

    ('oltp.rota.id_rota','Identificador da rota (PK).'),
    ('oltp.rota.id_bairro','Bairro atendido pela rota (FK bairro).'),
    ('oltp.rota.nome','Nome descritivo da rota.'),
    ('oltp.rota.tipo_coleta','CONVENCIONAL (orgânico/rejeito) ou SELETIVA (recicláveis). Única por bairro e tipo.'),
    ('oltp.rota.dia_semana','Dia de operação, padrão ISO: 1=segunda ... 7=domingo.'),
    ('oltp.rota.turno','MANHA, TARDE ou NOITE.'),
    ('oltp.rota.extensao_km','Extensão planejada da rota em km (> 0).'),

    ('oltp.coleta.id_coleta','Identificador da coleta (PK).'),
    ('oltp.coleta.id_rota','Rota executada (FK rota).'),
    ('oltp.coleta.id_veiculo','Veículo utilizado (FK veiculo).'),
    ('oltp.coleta.id_motorista','Motorista responsável (FK funcionario).'),
    ('oltp.coleta.data_coleta','Data de execução. Única por rota (UNIQUE id_rota + data).'),
    ('oltp.coleta.hora_inicio','Hora de saída.'),
    ('oltp.coleta.hora_fim','Hora de término; NULL se não concluída; deve ser maior que hora_inicio.'),
    ('oltp.coleta.km_percorridos','Quilometragem real percorrida (>= 0).'),
    ('oltp.coleta.status','PLANEJADA, EM_ANDAMENTO, CONCLUIDA ou CANCELADA.'),

    ('oltp.coleta_equipe.id_coleta','Coleta (parte da PK composta, FK coleta).'),
    ('oltp.coleta_equipe.id_funcionario','Funcionário da equipe (parte da PK composta, FK funcionario).'),

    ('oltp.coleta_item.id_coleta_item','Identificador do item (PK).'),
    ('oltp.coleta_item.id_coleta','Coleta a que o item pertence (FK coleta).'),
    ('oltp.coleta_item.id_ponto','Ponto de onde o resíduo foi retirado (FK ponto_coleta).'),
    ('oltp.coleta_item.id_tipo_residuo','Tipo do resíduo coletado (FK tipo_residuo).'),
    ('oltp.coleta_item.peso_kg','Peso coletado em kg (>= 0).'),

    ('oltp.descarga.id_descarga','Identificador da descarga (PK).'),
    ('oltp.descarga.id_coleta','Coleta de origem (FK coleta).'),
    ('oltp.descarga.id_destino','Destino que recebeu o material (FK destino_final).'),
    ('oltp.descarga.id_tipo_residuo','Tipo de resíduo descarregado (FK tipo_residuo).'),
    ('oltp.descarga.peso_kg','Peso descarregado em kg (> 0).'),
    ('oltp.descarga.data_hora','Data e hora do recebimento no destino.'),

    ('oltp.ocorrencia.id_ocorrencia','Identificador da ocorrência (PK).'),
    ('oltp.ocorrencia.id_bairro','Bairro da ocorrência (FK bairro).'),
    ('oltp.ocorrencia.id_ponto','Ponto específico, quando informado (FK ponto_coleta, opcional).'),
    ('oltp.ocorrencia.tipo_ocorrencia','DESCARTE_IRREGULAR, COLETA_NAO_REALIZADA, CONTAINER_DANIFICADO, SOLICITACAO_VOLUMOSO ou OUTROS.'),
    ('oltp.ocorrencia.canal','Canal de abertura: APP, TELEFONE ou PRESENCIAL.'),
    ('oltp.ocorrencia.data_abertura','Data e hora de registro.'),
    ('oltp.ocorrencia.data_fechamento','Data e hora da resolução; NULL enquanto não resolvida.'),
    ('oltp.ocorrencia.status','ABERTA, EM_ATENDIMENTO ou RESOLVIDA (RESOLVIDA se e somente se há data_fechamento).'),

    ('dw.dim_tempo.sk_tempo','Chave substituta no formato AAAAMMDD (PK).'),
    ('dw.dim_tempo.data','Data de calendário (única).'),
    ('dw.dim_tempo.dia','Dia do mês.'),
    ('dw.dim_tempo.mes','Número do mês (1-12).'),
    ('dw.dim_tempo.nome_mes','Nome do mês em português.'),
    ('dw.dim_tempo.trimestre','Trimestre (1-4).'),
    ('dw.dim_tempo.semestre','Semestre (1-2).'),
    ('dw.dim_tempo.ano','Ano.'),
    ('dw.dim_tempo.dia_semana','Dia da semana ISO (1=segunda ... 7=domingo).'),
    ('dw.dim_tempo.nome_dia','Nome do dia da semana.'),
    ('dw.dim_tempo.fim_de_semana','TRUE para sábado e domingo.'),

    ('dw.dim_local.sk_local','Chave substituta do local (PK).'),
    ('dw.dim_local.id_ponto_origem','ID do ponto no OLTP; NULL para o membro "bairro inteiro".'),
    ('dw.dim_local.id_bairro_origem','ID do bairro no OLTP.'),
    ('dw.dim_local.tipo_ponto','Tipo do ponto ou NAO_INFORMADO.'),
    ('dw.dim_local.logradouro','Endereço do ponto (logradouro, número).'),
    ('dw.dim_local.bairro','Nome do bairro (nível da hierarquia).'),
    ('dw.dim_local.regiao','Região (nível superior da hierarquia).'),
    ('dw.dim_local.populacao_bairro','População do bairro, para métricas per capita.'),
    ('dw.dim_local.area_km2_bairro','Área do bairro em km².'),

    ('dw.dim_tipo_residuo.sk_tipo_residuo','Chave substituta (PK).'),
    ('dw.dim_tipo_residuo.id_origem','ID no OLTP (único).'),
    ('dw.dim_tipo_residuo.nome','Nome do tipo de resíduo.'),
    ('dw.dim_tipo_residuo.categoria','Categoria do resíduo.'),
    ('dw.dim_tipo_residuo.reciclavel','Indicador de reciclável.'),
    ('dw.dim_tipo_residuo.destinacao_padrao','Destinação padrão.'),

    ('dw.dim_veiculo.sk_veiculo','Chave substituta (PK).'),
    ('dw.dim_veiculo.id_origem','ID no OLTP (único).'),
    ('dw.dim_veiculo.placa','Placa.'),
    ('dw.dim_veiculo.tipo','Tipo do veículo.'),
    ('dw.dim_veiculo.capacidade_kg','Capacidade em kg.'),
    ('dw.dim_veiculo.ano_fabricacao','Ano de fabricação (permite análise por idade da frota).'),

    ('dw.dim_rota.sk_rota','Chave substituta (PK).'),
    ('dw.dim_rota.id_origem','ID no OLTP (único).'),
    ('dw.dim_rota.nome','Nome da rota.'),
    ('dw.dim_rota.tipo_coleta','CONVENCIONAL ou SELETIVA.'),
    ('dw.dim_rota.dia_semana','Dia ISO de operação.'),
    ('dw.dim_rota.turno','Turno de operação.'),
    ('dw.dim_rota.extensao_km','Extensão planejada em km.'),
    ('dw.dim_rota.bairro','Bairro atendido (desnormalizado).'),
    ('dw.dim_rota.regiao','Região do bairro (desnormalizado).'),

    ('dw.dim_funcionario.sk_funcionario','Chave substituta (PK).'),
    ('dw.dim_funcionario.id_origem','ID no OLTP (único).'),
    ('dw.dim_funcionario.matricula','Matrícula.'),
    ('dw.dim_funcionario.nome','Nome.'),
    ('dw.dim_funcionario.cargo','Cargo.'),

    ('dw.dim_destino.sk_destino','Chave substituta (PK).'),
    ('dw.dim_destino.id_origem','ID no OLTP (único).'),
    ('dw.dim_destino.nome','Nome do destino.'),
    ('dw.dim_destino.tipo','Tipo do destino.'),
    ('dw.dim_destino.capacidade_ton_mes','Capacidade mensal em toneladas.'),

    ('dw.dim_ocorrencia.sk_ocorrencia','Chave substituta (PK).'),
    ('dw.dim_ocorrencia.tipo_ocorrencia','Tipo da ocorrência.'),
    ('dw.dim_ocorrencia.canal','Canal de abertura.'),
    ('dw.dim_ocorrencia.status','Status atual.'),

    ('dw.fato_coleta.sk_tempo','FK dim_tempo (data da coleta).'),
    ('dw.fato_coleta.sk_local','FK dim_local (ponto de coleta).'),
    ('dw.fato_coleta.sk_tipo_residuo','FK dim_tipo_residuo.'),
    ('dw.fato_coleta.sk_rota','FK dim_rota.'),
    ('dw.fato_coleta.sk_veiculo','FK dim_veiculo.'),
    ('dw.fato_coleta.sk_motorista','FK dim_funcionario (papel motorista).'),
    ('dw.fato_coleta.id_coleta','Dimensão degenerada: ID da coleta no OLTP.'),
    ('dw.fato_coleta.peso_kg','Medida aditiva: peso coletado em kg.'),
    ('dw.fato_coleta.qtd_registros','Medida aditiva: contador (sempre 1) para contagem de atendimentos.'),

    ('dw.fato_viagem.id_coleta','Dimensão degenerada e PK: ID da coleta no OLTP.'),
    ('dw.fato_viagem.sk_tempo','FK dim_tempo (data da coleta).'),
    ('dw.fato_viagem.sk_rota','FK dim_rota.'),
    ('dw.fato_viagem.sk_veiculo','FK dim_veiculo.'),
    ('dw.fato_viagem.sk_motorista','FK dim_funcionario (papel motorista).'),
    ('dw.fato_viagem.km_percorridos','Medida aditiva: km rodados; NULL quando a coleta foi cancelada.'),
    ('dw.fato_viagem.duracao_min','Medida aditiva: minutos entre hora_inicio e hora_fim; NULL quando cancelada.'),
    ('dw.fato_viagem.peso_total_kg','Medida aditiva: soma do peso coletado na viagem (0 se cancelada).'),
    ('dw.fato_viagem.qtd_pontos_atendidos','Medida aditiva: pontos distintos atendidos na viagem (0 se cancelada).'),
    ('dw.fato_viagem.qtd_cancelada','Medida aditiva: 1 se a coleta foi cancelada, 0 caso contrário (SUM = nº de cancelamentos).'),

    ('dw.fato_destinacao.sk_tempo','FK dim_tempo (data do recebimento).'),
    ('dw.fato_destinacao.sk_destino','FK dim_destino.'),
    ('dw.fato_destinacao.sk_tipo_residuo','FK dim_tipo_residuo.'),
    ('dw.fato_destinacao.sk_rota','FK dim_rota.'),
    ('dw.fato_destinacao.sk_veiculo','FK dim_veiculo.'),
    ('dw.fato_destinacao.id_coleta','Dimensão degenerada: ID da coleta.'),
    ('dw.fato_destinacao.peso_kg','Medida aditiva: peso destinado em kg.'),

    ('dw.fato_ocorrencia.id_ocorrencia','Dimensão degenerada e PK: ID da ocorrência no OLTP.'),
    ('dw.fato_ocorrencia.sk_tempo_abertura','FK dim_tempo (papel data de abertura).'),
    ('dw.fato_ocorrencia.sk_tempo_fechamento','FK dim_tempo (papel data de fechamento); NULL se em aberto.'),
    ('dw.fato_ocorrencia.sk_local','FK dim_local.'),
    ('dw.fato_ocorrencia.sk_ocorrencia','FK dim_ocorrencia.'),
    ('dw.fato_ocorrencia.qtd_ocorrencias','Medida aditiva: contador (sempre 1).'),
    ('dw.fato_ocorrencia.tempo_resolucao_horas','Medida semiaditiva: horas entre abertura e fechamento; NULL se em aberto.')
  ) AS t(obj, descr) LOOP
    EXECUTE format('COMMENT ON COLUMN %s IS %L', r.obj, r.descr);
  END LOOP;
END $$;
