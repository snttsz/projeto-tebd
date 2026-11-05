export const months = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
export const colors = {Orgânico:'#bb9877','Rejeito comum':'#9da8bc','Papel e papelão':'#6375df',Plástico:'#dd8278',Vidro:'#40a894',Metal:'#e1b85b'};
// Materiais recicláveis do catálogo do projeto; E1 também contém tipos sem coleta.
const recyclableMaterials=new Set(['Metal','Papel e papelão','Plástico','Vidro']);
export const fmt = (n,d=1) => Number(n).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
export const num = n => Number(n)||0;
export const sum = (rows,key) => rows.reduce((a,r)=>a+num(r[key]),0);
export const queryRows = (data,id) => data.resultados.find(q=>q.id===id)?.rows||[];
export function monthly(rows) {
  return Array.from({length:12},(_,i)=>({label:months[i],month:i+1,total:sum(rows.filter(r=>num(r.mes)===i+1),'toneladas'),
    reciclavel:sum(rows.filter(r=>num(r.mes)===i+1&&recyclableMaterials.has(r.tipo_residuo)),'toneladas')}));
}
export function composition(rows) {
  return [...new Set(rows.map(r=>r.tipo_residuo))].map(label=>({label,value:sum(rows.filter(r=>r.tipo_residuo===label),'toneladas'),color:colors[label]||'#8994aa'})).filter(r=>r.value>0).sort((a,b)=>b.value-a.value);
}
export function filtered(rows,term='',field='',value='') {
  const search=term.toLocaleLowerCase('pt-BR').trim();
  return rows.filter(r=>(!value||String(r[field])===value)&&(!search||Object.values(r).some(v=>String(v??'').toLocaleLowerCase('pt-BR').includes(search))));
}
export function sorted(rows,key,descending=false) {
  return [...rows].sort((a,b)=>{
    if(a[key]==null)return b[key]==null?0:1;if(b[key]==null)return -1;
    const numeric=v=>typeof v==='number'||(typeof v==='string'&&/^-?\d+(\.\d+)?$/.test(v));
    const comparison=numeric(a[key])&&numeric(b[key])?Number(a[key])-Number(b[key]):String(a[key]).localeCompare(String(b[key]),'pt-BR');
    return comparison*(descending?-1:1);
  });
}
export function csvDownload(rows) {
  if(!rows.length)return '';
  const cell=v=>{
    let text=v==null?'':String(v);
    if(typeof v==='string'&&/^[\s]*[=+@-]/.test(text)&&!/^\s*-?\d+(\.\d+)?\s*$/.test(text))text="'"+text;
    return '"'+text.replaceAll('"','""')+'"';
  };
  const keys=Object.keys(rows[0]);
  return '\uFEFF'+[keys.map(cell).join(','),...rows.map(r=>keys.map(k=>cell(r[k])).join(','))].join('\r\n');
}
export function display(v,key='') {
  if(v==null)return '—';
  if(typeof v==='number'||(typeof v==='string'&&/^-?\d+(\.\d+)?$/.test(v))) {
    if(/^id_|matricula|placa/.test(key))return String(v);
    const n=Number(v);return n.toLocaleString('pt-BR',{maximumFractionDigits:Number.isInteger(n)?0:2});
  }
  return String(v);
}
export const labels = {id_coleta:'Coleta',id_ocorrencia:'Ocorrência',data_coleta:'Data',bairro:'Bairro',regiao:'Região',rota:'Rota',turno:'Turno',placa:'Placa',motorista:'Motorista',status:'Status',canal:'Canal',tipo_ocorrencia:'Tipo de ocorrência',situacao_na_referencia:'Situação na referência',status_final_base:'Status final da base',data_abertura:'Abertura',data_fechamento:'Fechamento',horas_abertas:'Horas em aberto',coletas_concluidas:'Coletas concluídas',capacidade_kg:'Capacidade (kg)',peso_kg:'Peso (kg)',ocupacao_pct:'Ocupação (%)',coletor:'Coletor',matricula:'Matrícula',viagens_planejadas:'Viagens programadas',canceladas:'Canceladas',kg_por_km:'Produtividade (kg/km)',cancelamento_pct:'Cancelamentos (%)',tipo_coleta:'Tipo de coleta',tipo_veiculo:'Tipo de veículo',tipo:'Tipo',km:'Distância (km)',duracao_media_min:'Duração média (min)',tipo_regiao:'Tipo / região',ocorrencias:'Ocorrências',resolvidas:'Resolvidas',sem_resolucao:'Sem resolução',horas_medias:'Média (h)',horas_maximas:'Máximo (h)',ano_fabricacao:'Ano de fabricação',idade_anos:'Idade em 2025',motorista_tipo:'Motorista / tipo',mes:'Mês',mes_tipo:'Mês / material',tipo_residuo:'Material',toneladas:'Toneladas',variacao_mensal_pct:'Variação mensal (%)',local:'Local',nivel:'Nível',reciclaveis_t:'Recicláveis (t)',reciclaveis_pct:'Recicláveis (%)',material:'Material',total_destinado_t:'Destinado (t)',cooperativa_t:'Cooperativa (t)',rejeito_t:'Rejeito (t)',rejeito_pct:'Rejeito (%)',destino:'Destino',mes_destino:'Mês / destino',capacidade_ton_mes:'Capacidade (t/mês)',participacao_pct:'Participação (%)',capacidade_utilizada_pct:'Uso da capacidade (%)',trimestre:'Trimestre',trimestre_regiao:'Trimestre / região',variacao_trimestral_pct:'Variação trimestral (%)',turno_dia:'Turno / dia',dia_semana:'Dia (ISO)',nome_dia:'Dia da semana',posicao_menor_produtividade:'Posição por tipo',grupo:'Grupo',kg_coletados_hab:'Coleta (kg/hab.)',pct_reciclaveis:'Recicláveis (%)',pct_canceladas:'Cancelamentos (%)',ocorrencias_1000_hab:'Ocorrências / mil hab.',silhueta_individual:'Silhueta'};
