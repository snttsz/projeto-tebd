// Plano proposto para a prefeitura fictícia. Custos e metas são hipóteses de planejamento.
export function acoes(resultados, km) {
  const linhas = id => resultados.find(q => q.id === id).rows;
  const rota = linhas('T1')[0], turno = linhas('T2')[0], rejeito = linhas('E3')[0];
  const fmt = n => Number(n).toLocaleString('pt-BR', {maximumFractionDigits:2});
  const grupo = km.centroides.find(c => Number(c.grupo) === 1);
  const bairros = km.bairros.filter(b => Number(b.grupo) === 1).map(b => b.bairro).join(', ');
  return [
    {id:'A1', prioridade:1, oque:'Revisar a programação das viagens com mais cancelamentos',
      porque:`T2: ${turno.turno_dia} registra ${fmt(turno.cancelamento_pct)}% de cancelamentos (${turno.canceladas}/${turno.viagens_planejadas} viagens).`,
      onde:`Rotas de ${turno.turno_dia}; conferir também os veículos de T4.`, quando:'Diagnóstico em D+7; piloto até D+30.',
      quem:'Coordenação de rotas e de frota', como:'Classificar motivos de cancelamento, conferir escalas e manutenção e testar remanejamento sem retirar cobertura de outros turnos.',
      custo:1500, meta:'Meta proposta: reduzir o percentual em 20% relativo no piloto, comparando períodos equivalentes.'},
    {id:'A2', prioridade:1, oque:'Organizar uma força-tarefa para ocorrências atrasadas',
      porque:`O2: ${linhas('O2').length} registros sem resolução há mais de 72 horas na referência de 01/01/2026. T3 distingue tipos e regiões.`,
      onde:'Bairros e tipos listados em O2 e T3', quando:'Triagem em D+2; retorno aos cidadãos até D+15.',
      quem:'Supervisão de atendimento e equipes de campo', como:'Validar cada registro, priorizar risco sanitário, agendar atendimento e registrar fechamento apenas após confirmação.',
      custo:1200, meta:'Meta proposta: dar encaminhamento e prazo a todos os registros; acompanhar pendências semanalmente.'},
    {id:'A3', prioridade:2, oque:'Testar comunicação e acesso à coleta seletiva no grupo 1',
      porque:`K-means: grupo 1 com média entre bairros de ${fmt(grupo.pct_reciclaveis)}% de recicláveis e ${fmt(grupo.pct_canceladas)}% de cancelamentos; confrontar E2 antes de expandir.`,
      onde:bairros, quando:'Diagnóstico em D+15; piloto de 30 dias até D+45.',
      quem:'Secretaria, educação ambiental e representantes dos bairros', como:'Conferir cobertura e calendário, ouvir moradores e testar comunicação e pontos de entrega, em conjunto com regularização das viagens.',
      custo:2000, meta:'Meta proposta: aumentar a participação de recicláveis em 2 pontos percentuais no piloto, sem elevar cancelamentos.'},
    {id:'A4', prioridade:2, oque:'Investigar e reduzir rejeito na separação de recicláveis',
      porque:`E3: ${rejeito.material} tem ${fmt(rejeito.rejeito_pct)}% de rejeito destinado ao aterro na coorte de coletas de 2025.`,
      onde:'Cooperativa e bairros fornecedores do material', quando:'Amostragem em D+10; intervenção até D+30.',
      quem:'Cooperativa e equipe de educação ambiental', como:'Identificar contaminantes, revisar orientações de separação e pesar entrada, recuperação e rejeito em amostras comparáveis.',
      custo:1000, meta:'Meta proposta: reduzir o rejeito do material em 5 pontos percentuais, mediante medição no piloto.'},
    {id:'A5', prioridade:2, oque:'Reavaliar uma rota de baixa produtividade',
      porque:`T1: ${rota.rota} registra ${fmt(rota.kg_por_km)} kg/km. Comparar apenas com rotas do mesmo tipo antes de intervir.`,
      onde:rota.rota, quando:'Levantamento em D+15; piloto até D+45.', quem:'Coordenação de rotas e equipe da rota',
      como:'Conferir extensão, pontos atendidos e demanda; testar ajustes de sequência e frequência preservando cobertura e ouvindo moradores.',
      custo:800, meta:'Meta proposta: aumentar kg/km em 10% relativo sem piorar cobertura, cancelamentos ou ocorrências.'},
    {id:'A6', prioridade:3, oque:'Revisar Industrial antes de usar o agrupamento na priorização',
      porque:'K-means: Industrial tem silhueta individual negativa (-0,1038); a atribuição ao grupo 2 é ambígua.',
      onde:'Bairro Industrial e análise da Secretaria', quando:'Antes de aprovar investimentos por grupo; até D+7.',
      quem:'Analista de dados e gestor da Secretaria', como:'Conferir variáveis e registros, comparar com o centro do outro grupo e revisar diagnósticos de sensibilidade; registrar a decisão.',
      custo:0, meta:'Registrar parecer e usar indicadores diretos enquanto a classificação permanecer ambígua.'}
  ];
}

export function markdownAcoes(lista) {
  return '# Ciclo Urbano — plano de ação 5W2H\n\n' +
    'Proposta para a prefeitura fictícia, baseada em dados sintéticos. D é a data de aprovação do plano. Custos incrementais e metas são hipóteses didáticas, sem cotação ou comprovação de viabilidade; não representam previsão do K-means. A equipe municipal deve validar recursos, cobertura e orçamento.\n\n' +
    '| Prioridade / ação | O quê (What) | Por quê (Why) | Onde (Where) | Quando (When) | Quem (Who) | Como (How) | Quanto (How much) | Acompanhamento |\n|---|---|---|---|---|---|---|---|---|\n' +
    lista.map(a => `| ${a.prioridade} / ${a.id} | ${a.oque} | ${a.porque} | ${a.onde} | ${a.quando} | ${a.quem} | ${a.como} | R$ ${a.custo.toLocaleString('pt-BR', {minimumFractionDigits:2})} (estimativa) | ${a.meta} |`).join('\n') +
    `\n\nOrçamento incremental hipotético total: **R$ ${lista.reduce((s,a) => s+a.custo,0).toLocaleString('pt-BR',{minimumFractionDigits:2})}**. A ação A6 utiliza a equipe existente, sem desembolso incremental previsto; há custo de trabalho não quantificado. Não se estimam benefícios financeiros.\n`;
}
