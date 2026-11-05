import {test, before, after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import vm from 'node:vm';
import {consultas, mineracao, reconciliar, revisarParticao, csv} from '../dados.mjs';
import {prepararInterface,renderizar} from '../renderizar.mjs';
import {acoes} from '../acoes.mjs';
import {monthly,composition,csvDownload,filtered,sorted} from '../ui/model.mjs';

const raiz=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const modulo=process.env.PGLITE_MODULE;
const {PGlite}=modulo?await import(pathToFileURL(path.resolve(modulo)).href):await import('@electric-sql/pglite');
const lista=consultas(raiz),km=mineracao(raiz);
let db, resultados;
const rows=async sql=>(await db.query(sql)).rows;
const query=id=>resultados.find(q=>q.id===id).rows;
before(async()=>{
  await prepararInterface();
  db=new PGlite();await db.waitReady;
  for(const n of ['01_construcao_oltp_olap.sql','02_dicionario_comentarios.sql','03_views_apoio.sql'])
    await db.exec(fs.readFileSync(path.join(raiz,'src/sql',n),'utf8'));
  resultados=[];for(const q of lista)resultados.push({...q,rows:await rows(q.sql)});
});
after(async()=>{await db?.close()});

test('cinco consultas de cada nível executam e retornam os campos de visualização',()=>{
  for(const nivel of ['O','T','E'])assert.equal(resultados.filter(q=>q.id[0]===nivel).length,5);
  for(const q of resultados){assert.ok(q.rows.length>0,q.id);assert.ok(q.eixo in q.rows[0],q.id);assert.ok(q.medida in q.rows[0],q.id)}
});
test('base de 12 bairros reconcilia 84 medidas com a execução preservada do K-means',async()=>{
  const base=await rows(fs.readFileSync(path.join(raiz,'src/mineracao/preparar_bairros.sql'),'utf8').replaceAll('__ANO__','2025'));
  assert.equal(reconciliar(base,km.base),84);
  base[0].peso_total_kg=Number(base[0].peso_total_kg)+1;
  assert.throws(()=>reconciliar(base,km.base),/Base diferente/);
});
test('OLTP e DW preservam contagens e peso sem duplicar as viagens',async()=>{
  for(const [a,b] of [['coleta','fato_viagem'],['coleta_item','fato_coleta'],['descarga','fato_destinacao'],['ocorrencia','fato_ocorrencia']]){
    const [r]=await rows(`SELECT (SELECT COUNT(*) FROM oltp.${a}) a,(SELECT COUNT(*) FROM dw.${b}) b`);
    assert.equal(r.a,r.b);
  }
  const [r]=await rows('SELECT (SELECT SUM(peso_kg) FROM oltp.coleta_item) a,(SELECT SUM(peso_total_kg) FROM dw.fato_viagem) b');
  assert.equal(Number(r.a),920320.77);assert.equal(r.a,r.b);
});
test('O2 reconstrói pendências na referência e distingue fechamento posterior',()=>{
  assert.equal(query('O2').length,54);
  const depois=query('O2').filter(r=>r.status_final_base==='RESOLVIDA');
  assert.equal(depois.length,1);assert.equal(depois[0].situacao_na_referencia,'SEM_RESOLUCAO');
  assert.ok(new Date(depois[0].data_fechamento)>new Date('2026-01-01T00:00:00Z'));
});
test('O3 e O4 conciliam km e pesos com as viagens da semana; O5 não conta canceladas',async()=>{
  const [r]=await rows("SELECT SUM(km_percorridos) km FROM oltp.coleta WHERE status='CONCLUIDA' AND data_coleta BETWEEN DATE '2025-12-25' AND DATE '2025-12-31'");
  assert.ok(Math.abs(query('O3').reduce((s,v)=>s+Number(v.km),0)-Number(r.km))<.001);
  for(const v of query('O4'))assert.ok(Math.abs(Number(v.ocupacao_pct)-100*Number(v.peso_kg)/Number(v.capacidade_kg))<=.0051);
  const [equipes]=await rows("SELECT COUNT(*) n FROM oltp.coleta_equipe e JOIN oltp.coleta c USING(id_coleta) WHERE c.status='CONCLUIDA' AND c.data_coleta BETWEEN DATE '2025-12-25' AND DATE '2025-12-31'");
  assert.equal(query('O5').reduce((s,v)=>s+Number(v.coletas_concluidas),0),Number(equipes.n));
});
test('T1, T2 e T4 conciliam 1.252 viagens e 77 cancelamentos',()=>{
  for(const id of ['T1','T2','T4']){
    assert.equal(query(id).reduce((s,r)=>s+Number(r.viagens_planejadas),0),1252,id);
    assert.equal(query(id).reduce((s,r)=>s+Number(r.canceladas),0),77,id);
  }
  assert.equal(query('T1')[0].bairro,'Novo Horizonte');
});
test('T3 contabiliza as 600 ocorrências e mantém denominador apenas das resolvidas',async()=>{
  assert.equal(query('T3').reduce((s,r)=>s+Number(r.ocorrencias),0),600);
  const [r]=await rows("SELECT COUNT(*) resolvidas FROM oltp.ocorrencia WHERE data_abertura >= DATE '2025-01-01' AND data_abertura < DATE '2026-01-01' AND data_fechamento IS NOT NULL");
  assert.equal(query('T3').reduce((s,r)=>s+Number(r.resolvidas),0),Number(r.resolvidas));
  assert.equal(query('T3').reduce((s,r)=>s+Number(r.sem_resolucao),0),53);
});
test('E1 e E2 conciliam toneladas; subtotais regionais não duplicam bairros',()=>{
  assert.ok(Math.abs(query('E1').reduce((s,r)=>s+Number(r.toneladas),0)-920.32077)<.02);
  assert.equal(query('E2').filter(r=>r.nivel==='BAIRRO').length,12);
  for(const nivel of ['BAIRRO','REGIAO'])assert.ok(Math.abs(query('E2').filter(r=>r.nivel===nivel).reduce((s,r)=>s+Number(r.toneladas),0)-920.32077)<.01);
  assert.ok(query('E1').filter(r=>r.mes===1).every(r=>r.variacao_mensal_pct===null));
});
test('E3 mede rejeitos de plástico a 35%; E4 não repete capacidade; E5 totaliza 600',()=>{
  assert.equal(Number(query('E3').find(r=>r.material==='Plástico').rejeito_pct),35);
  assert.equal(new Set(query('E4').map(r=>r.mes+'|'+r.destino)).size,48);
  for(let mes=1;mes<=12;mes++)assert.ok(Math.abs(query('E4').filter(r=>r.mes===mes).reduce((s,r)=>s+Number(r.participacao_pct),0)-100)<.03);
  assert.equal(query('E5').reduce((s,r)=>s+Number(r.ocorrencias),0),600);
});
test('CSV mantém aspas, vírgula e quebra de linha; entrada incompleta falha',()=>{
  assert.deepEqual(csv('\uFEFFa,b\r\n"bairro, centro","fala ""oi""\nlinha"\r\n'),[{a:'bairro, centro',b:'fala "oi"\nlinha'}]);
  assert.throws(()=>csv('a,b\n1'),/colunas/);
});
test('plano 5W2H tem seis ações rastreáveis, custo explícito e revisão de Industrial',()=>{
  const plano=acoes(resultados,km);assert.equal(plano.length,6);
  assert.equal(plano.reduce((s,a)=>s+a.custo,0),6500);
  assert.match(plano.find(a=>a.id==='A2').porque,/54/);
  assert.match(plano.find(a=>a.id==='A6').porque,/negativa/);
  const revisao=revisarParticao(km),industrial=revisao.bairros.find(b=>b.bairro==='Industrial');
  assert.ok(Math.abs(revisao.silhueta_media-.363745)<.000001);
  assert.ok(industrial.distancia_media_interna>industrial.distancia_media_alternativa);
});
test('HTML offline preserva dados e script válido, sem dependências de rede',()=>{
  const html=renderizar({manifesto:{origem:'Teste',criado_utc:'2026-11-05',totais:{peso_kg:920320.77,reciclavel_kg:233576.79,viagens:1252,canceladas:77}},resultados,km});
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];new vm.Script(script);
  assert.doesNotMatch(html,/<(?:script|link)[^>]*(?:src|href)=["']https?:/);
  assert.equal((html.match(/data:image\/png;base64/g)||[]).length,5);
});

test('React: valores ao passar o mouse, navegação, busca, filtros e paginação funcionam',async()=>{
  const domModulo=process.env.DOM_MODULE;
  const {parseHTML}=domModulo?await import(pathToFileURL(path.resolve(domModulo)).href):await import('linkedom');
  const html=renderizar({manifesto:{origem:'Teste',criado_utc:'2026-11-05',totais:{peso_kg:920320.77,reciclavel_kg:233576.79,viagens:1252,canceladas:77}},resultados,km});
  const {window}=parseHTML(html);
  // linkedom não implementa setter de value no select.
  Object.defineProperty(window.HTMLSelectElement.prototype,'value',{get(){const o=[...this.querySelectorAll('option')];return (o.find(x=>x.selected)||o[0])?.value||''},set(v){for(const o of this.querySelectorAll('option'))o.selected=o.value===String(v)},configurable:true});
  window.scrollTo=()=>{};
  window.document.oninput=null;
  const context=vm.createContext({document:window.document,window,navigator:{userAgent:'Node DOM test'},Intl,console,
    setTimeout,clearTimeout,setInterval,clearInterval,queueMicrotask,performance,TextEncoder,TextDecoder,URL,Blob});
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
  const tick=()=>new Promise(resolve=>setTimeout(resolve,15));
  assert.equal(window.document.querySelectorAll('.query-card').length,15);
  assert.equal(window.document.getElementById('V').hidden,false);
  const hover=(target,x=100,y=100)=>{const event=new window.Event('pointermove',{bubbles:true});Object.assign(event,{clientX:x,clientY:y});target.dispatchEvent(event)};
  const lineChart=window.document.querySelector('#V .trend-chart svg');
  lineChart.getBoundingClientRect=()=>({left:0,top:0,width:720,height:258});
  hover(lineChart,402,100);await tick();
  const july=monthly(query('E1'))[6];
  assert.match(window.document.querySelector('[role="tooltip"]').textContent,/Jul · 2025/);
  assert.ok(window.document.querySelector('[role="tooltip"]').textContent.includes(july.total.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+' t'));
  lineChart.dispatchEvent(new window.Event('pointerout',{bubbles:true}));await tick();
  assert.equal(window.document.querySelectorAll('[role="tooltip"]').length,0);
  const material=window.document.querySelector('#V .donut-legend>div');hover(material);await tick();
  assert.match(window.document.querySelector('[role="tooltip"]').textContent,/Peso coletado.*Participação/);
  material.dispatchEvent(new window.Event('pointerout',{bubbles:true}));await tick();
  const bar=window.document.querySelector('#V .bar-row');hover(bar);await tick();
  assert.match(window.document.querySelector('[role="tooltip"]').textContent,/Valor.*%/);
  bar.dispatchEvent(new window.Event('pointerout',{bubbles:true}));await tick();
  const quarter=window.document.querySelector('#E5 .quarter-stack>div');hover(quarter);await tick();
  assert.match(window.document.querySelector('[role="tooltip"]').textContent,/1º trimestre.*Ocorrências na região.*Total do trimestre/);
  quarter.dispatchEvent(new window.Event('pointerout',{bubbles:true}));await tick();
  window.document.querySelector('[data-tab="E"]').click();
  await tick();
  assert.equal(window.document.getElementById('E').hidden,false);
  assert.equal(window.document.getElementById('O').hidden,true);
  assert.match(window.document.querySelector('h1').textContent,/Decisões/);
  const filtro=window.document.querySelector('#E2 select');
  assert.equal(window.document.querySelectorAll('#E2 tbody tr:not([hidden])').length,8);
  window.document.querySelector('[aria-label="Próxima página de E2"]').click();await tick();
  assert.equal(window.document.querySelectorAll('#E2 tbody tr:not([hidden])').length,4);
  filtro.value='REGIAO';filtro.dispatchEvent(new window.Event('change'));
  filtro.dispatchEvent(new window.Event('change',{bubbles:true}));await tick();
  assert.equal(window.document.querySelectorAll('#E2 tbody tr').length,5);
  const busca=window.document.querySelector('#T1 input');
  const digitar=value=>{const previous=busca.value;busca.value=value;busca._valueTracker?.setValue(previous);busca.dispatchEvent(new window.Event('input',{bubbles:true}))};
  digitar('Novo Horizonte');
  busca.dispatchEvent(new window.Event('change',{bubbles:true}));await tick();
  assert.equal(window.document.querySelectorAll('#T1 tbody tr').length,2);
  assert.match(window.document.getElementById('T1').textContent,/2,23/);
  digitar('sem resultado xyz');busca.dispatchEvent(new window.Event('change',{bubbles:true}));await tick();
  assert.match(window.document.querySelector('#T1 .empty').textContent,/Nenhum registro/);
  assert.equal(window.document.querySelectorAll('.query-source,.sql-panel').length,0);
  assert.doesNotMatch(window.document.getElementById('conteudo').textContent,/\bOLTP\b|Data Warehouse|\bSQL\b|silhueta|StandardScaler|K-means|snapshot/i);
  window.document.querySelector('[data-tab="A"]').click();await tick();assert.equal(window.document.querySelectorAll('.action-card').length,6);
});

test('React: série mensal e composição conciliam coleta e recicláveis, sem classificar rejeito como reciclável',()=>{
  const series=monthly(query('E1'));
  assert.ok(Math.abs(series.reduce((s,r)=>s+r.total,0)-920.32077)<.02);
  assert.ok(Math.abs(series.reduce((s,r)=>s+r.reciclavel,0)-233.57679)<.01);
  assert.equal(composition(query('E1')).length,6);
  assert.equal(monthly([{mes:1,tipo_residuo:'Rejeito comum',toneladas:10}])[0].reciclavel,0);
});
test('React: exportação CSV preserva valores e protege fórmulas; ordenação trata números e nulos',()=>{
  const result=csvDownload([{bairro:'=1+1',valor:2.23},{bairro:'Novo, Horizonte',valor:0}]);
  assert.match(result,/"'=1\+1"/);assert.match(result,/"Novo, Horizonte"/);
  assert.deepEqual(sorted([{v:'10'},{v:null},{v:'2'}],'v').map(r=>r.v),['2','10',null]);
  assert.equal(filtered([{bairro:'Novo Horizonte'},{bairro:'Centro'}],'horizonte').length,1);
});
