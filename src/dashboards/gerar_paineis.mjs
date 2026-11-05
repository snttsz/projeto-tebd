/** Gera os itens 7–9 e suas evidências. Banco externo sempre em transação READ ONLY.
 * node src/dashboards/gerar_paineis.mjs [--reproduzir] [--pglite caminho] [--saida pasta]
 * --reproduzir cria banco efêmero em memória, executa 01–03 e nunca acessa seu PostgreSQL.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {consultas, mineracao, reconciliar, revisarParticao, hash} from './dados.mjs';
import {prepararInterface,renderizar,fontesInterface} from './renderizar.mjs';
import {acoes, markdownAcoes} from './acoes.mjs';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const args = process.argv.slice(2);
function opcao(nome) {
  const i = args.indexOf(nome);
  if (i < 0) return null;
  if (!args[i + 1] || args[i + 1].startsWith('--')) throw Error(`Falta valor de ${nome}`);
  return args[i + 1];
}
let db;
try {
  const km = mineracao(raiz), lista = consultas(raiz);
  await prepararInterface();
  const revisaoKmeans = revisarParticao(km);
  if (lista.length !== 15 || new Set(lista.map(q => q.id)).size !== 15) throw Error('Esperadas 15 consultas distintas.');
  const config = {};
  const envPath = path.join(raiz, '.env');
  if (fs.existsSync(envPath)) for (const l of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const m = l.trim().match(/^([A-Z_]+)\s*=\s*(.*)$/);
    if (m) config[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
  const valor = (chave, padrao) => process.env[chave] || config[chave] || padrao;
  let query, origem;
  if (args.includes('--reproduzir')) {
    const modulo = opcao('--pglite');
    const {PGlite} = modulo ? await import(pathToFileURL(path.resolve(modulo)).href) : await import('@electric-sql/pglite');
    db = new PGlite();
    await db.waitReady;
    for (const n of ['01_construcao_oltp_olap.sql', '02_dicionario_comentarios.sql', '03_views_apoio.sql']) {
      console.log(`Reprodução isolada: ${n}`);
      await db.exec(fs.readFileSync(path.join(raiz, 'src/sql', n), 'utf8'));
    }
    await db.exec('BEGIN READ ONLY');
    query = async sql => (await db.query(sql)).rows;
    origem = 'Reprodução isolada dos scripts 01–03 em PostgreSQL embarcado (PGlite 0.5.15), reconciliada com a base do K-means de 31/10. Não é conexão ao banco original.';
  } else {
    let psql = valor('PSQL', 'psql');
    if (process.platform === 'win32' && psql === 'psql' && fs.existsSync('C:/Program Files/PostgreSQL')) {
      const versoes = fs.readdirSync('C:/Program Files/PostgreSQL').sort((a,b) => Number(b)-Number(a));
      const encontrado = versoes.map(v => `C:/Program Files/PostgreSQL/${v}/bin/psql.exe`).find(p => fs.existsSync(p));
      if (encontrado) psql = encontrado;
    }
    // Uma única transação mantém as quinze consultas e a reconciliação no mesmo snapshot.
    const baseSql = fs.readFileSync(path.join(raiz, 'src/mineracao/preparar_bairros.sql'), 'utf8').replaceAll('__ANO__', '2025');
    const pacote = [baseSql, ...lista.map(q => q.sql), 'SELECT version() AS versao'];
    const sql = 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n' + pacote.map(s =>
      `SELECT COALESCE(json_agg(r), '[]'::json) FROM (${s.trim().replace(/;\s*$/, '')}) r;`).join('\n') + '\nROLLBACK;';
    const r = spawnSync(psql, ['-X', '-w', '-qAt', '-v', 'ON_ERROR_STOP=1', '-h', valor('PGHOST','localhost'),
      '-p', valor('PGPORT','5432'), '-U', valor('PGUSER','postgres'), '-d', valor('PGDATABASE','cidades_sustentaveis')],
    {input: sql, encoding:'utf8', maxBuffer: 16*1024*1024, env: {...process.env,
      PGPASSWORD:valor('PGPASSWORD','postgres'), PGCLIENTENCODING:'UTF8', PGCONNECT_TIMEOUT:'10'}});
    if (r.error || r.status !== 0) throw Error('Falha ao executar psql. Confira instalação, .env e acesso ao banco. ' + (r.error?.code || ''));
    const respostas = r.stdout.trim().split(/\r?\n/).map(l => JSON.parse(l));
    if (respostas.length !== pacote.length) throw Error('Resposta incompleta do psql.');
    let i = 0; query = async () => respostas[i++];
    origem = 'Snapshot do PostgreSQL configurado no .env, em uma transação REPEATABLE READ READ ONLY.';
  }
  const baseSql = fs.readFileSync(path.join(raiz, 'src/mineracao/preparar_bairros.sql'), 'utf8').replaceAll('__ANO__', '2025');
  const base = await query(baseSql);
  const comparacoes = reconciliar(base, km.base);
  console.log(`Reconciliação: ${base.length} bairros, ${comparacoes} medidas conferidas com o K-means.`);
  const resultados = [];
  for (const q of lista) {
    const rows = await query(q.sql);
    resultados.push({...q, rows});
    console.log(`${q.id}: ${rows.length} registros`);
  }
  const versao = (await query('SELECT version() AS versao'))[0].versao;
  const numeros = base.reduce((a,b) => ({peso_kg:a.peso_kg+Number(b.peso_total_kg),
    reciclavel_kg:a.reciclavel_kg+Number(b.peso_reciclavel_kg), viagens:a.viagens+Number(b.viagens),
    canceladas:a.canceladas+Number(b.canceladas), ocorrencias:a.ocorrencias+Number(b.ocorrencias)}),
    {peso_kg:0,reciclavel_kg:0,viagens:0,canceladas:0,ocorrencias:0});
  const manifesto = {status:'concluido', criado_utc:new Date().toISOString(), dados:'sinteticos', ano:2025,
    referencia_operacional:'2026-01-01', origem, versao, bairros:base.length, comparacoes_kmeans:comparacoes,
    consultas:resultados.map(q => ({id:q.id,linhas:q.rows.length,sha256_sql:hash(q.sql)})), totais:numeros};
  manifesto.interface={framework:'React',compilado_utc:new Date().toISOString(),offline:true};
  manifesto.fontes_sha256 = Object.fromEntries([
    ...['01_construcao_oltp_olap.sql','02_dicionario_comentarios.sql','03_views_apoio.sql',
      '05_dashboard_operacional.sql','06_dashboard_tatico.sql','07_dashboard_estrategico.sql'].map(n => 'src/sql/'+n),
    'src/documentos/modelo_final.md','src/documentos/roteiro_final.md',
    'src/dashboards/gerar_paineis.mjs','src/dashboards/renderizar.mjs','src/dashboards/dados.mjs','src/dashboards/acoes.mjs',...fontesInterface
  ].map(n => [n,hash(fs.readFileSync(path.join(raiz,n)))]));
  manifesto.mineracao = {pasta:path.relative(raiz,km.dir).replaceAll('\\','/'),sha256_manifesto:hash(fs.readFileSync(path.join(km.dir,'manifesto.json'))),arquivos_conferidos:Object.keys(km.manifesto.sha256).length};
  manifesto.revisao_kmeans = revisaoKmeans;
  const fmt = n => Number(n).toLocaleString('pt-BR',{maximumFractionDigits:3});
  const linhas = id => resultados.find(q => q.id === id).rows;
  const grupos = km.centroides.map(c => `| ${c.grupo} | ${km.bairros.filter(b => b.grupo===c.grupo).map(b => b.bairro).join(', ')} | ${fmt(c.pct_reciclaveis)}% | ${fmt(c.pct_canceladas)}% | ${fmt(c.ocorrencias_1000_hab)} |`).join('\n');
  const industrial = revisaoKmeans.bairros.find(b => b.bairro === 'Industrial');
  const substituicoes = {
    ORIGEM:origem,
    TOTAIS:'| Medida | Valor |\n|---|---|\n'+[
      ['Peso coletado',fmt(numeros.peso_kg/1000)+' t'],['Peso reciclável coletado',fmt(numeros.reciclavel_kg/1000)+' t'],
      ['Participação de recicláveis antes da triagem',fmt(100*numeros.reciclavel_kg/numeros.peso_kg)+'%'],
      ['Viagens programadas',fmt(numeros.viagens)],['Viagens canceladas',fmt(numeros.canceladas)],['Ocorrências registradas',fmt(numeros.ocorrencias)]
    ].map(([k,v])=>`| ${k} | ${v} |`).join('\n'),
    GRUPOS:'| Grupo | Bairros | Recicláveis (média) | Cancelamentos (média) | Ocorrências por mil hab. (média) |\n|---|---|---|---|---|\n'+grupos,
    REVISAO_INDUSTRIAL:`Recalculamos independentemente as silhuetas dos 12 bairros por distância euclidiana padronizada; todas conferiram com os CSVs (tolerância de 1e-9). A média foi ${revisaoKmeans.silhueta_media.toLocaleString('pt-BR',{maximumFractionDigits:6})}. Para Industrial, a distância média aos demais membros do grupo ${industrial.grupo} é ${fmt(industrial.distancia_media_interna)}, maior que a distância média ao grupo ${industrial.grupo_alternativo}, ${fmt(industrial.distancia_media_alternativa)}. Isso explica a silhueta negativa. Distância média aos membros é diferente de distância ao centroide; a partição do K-means não precisa maximizar silhueta individual. Mantemos o resultado registrado, com ressalva explícita, e usamos indicadores diretos para decidir sobre Industrial.`,
    CONSULTAS:'| Nível / ID | Pergunta de gestão | Registros na execução |\n|---|---|---|\n'+resultados.map(q=>`| ${{O:'Operacional',T:'Tático',E:'Estratégico'}[q.id[0]]} / ${q.id} | ${q.titulo} | ${q.rows.length} |`).join('\n'),
    ACHADOS:[
      `- **Regularidade:** ${linhas('T2')[0].turno_dia} tem ${fmt(linhas('T2')[0].cancelamento_pct)}% de cancelamentos (${linhas('T2')[0].canceladas}/${linhas('T2')[0].viagens_planejadas}).`,
      `- **Atendimento:** ${linhas('O2').length} registros estavam sem resolução há mais de 72 horas na referência.`,
      `- **Produtividade:** ${linhas('T1')[0].rota} tem ${fmt(linhas('T1')[0].kg_por_km)} kg/km.`,
      `- **Triagem:** ${linhas('E3')[0].material} tem ${fmt(linhas('E3')[0].rejeito_pct)}% de rejeito no modelo de destinação.`,
      '- **Perfil territorial:** o grupo 1 combina menor participação média de recicláveis com mais cancelamentos; é um ponto de partida para diagnóstico conjunto, não uma ordem automática de investimento.'
    ].join('\n')
  };
  const relatorio=fs.readFileSync(path.join(raiz,'src/documentos/modelo_final.md'),'utf8').replace(/\{\{([A-Z_]+)\}\}/g,(_,k)=>{
    if(!(k in substituicoes))throw Error(`Marcador desconhecido no relatório: ${k}`);return substituicoes[k];
  });
  const destino = path.resolve(opcao('--saida') || path.join(raiz, 'docs/entregas/final'));
  fs.mkdirSync(destino, {recursive:true});
  fs.writeFileSync(path.join(destino,'manifesto_dashboards.json'), JSON.stringify({status:'em_andamento',criado_utc:manifesto.criado_utc}));
  fs.writeFileSync(path.join(destino,'resultados_dashboards.json'), JSON.stringify({manifesto, resultados}, null, 2));
  fs.writeFileSync(path.join(destino,'consultas_dashboards.md'), '# Ciclo Urbano — 15 consultas de gestão\n\nDados sintéticos de 2025. Operacional: últimos sete dias completos antes de 01/01/2026; O2: situação na referência.\n\n' +
    origem + '\n\n' + resultados.map(q => `## ${q.id} — ${q.titulo}\n\n${q.leitura}\n\n\`\`\`sql\n${q.sql}\n\`\`\`\n\nColunas: ${Object.keys(q.rows[0] || {}).join(', ')}.\n\nExecução: ${q.rows.length} registros. Resultados completos no painel e em resultados_dashboards.json.\n`).join('\n'));
  fs.writeFileSync(path.join(destino,'painel.html'), renderizar({manifesto, resultados, km}));
  fs.writeFileSync(path.join(destino,'plano_5w2h.md'), markdownAcoes(acoes(resultados, km)));
  fs.writeFileSync(path.join(destino,'relatorio_final.md'),relatorio);
  fs.copyFileSync(path.join(raiz,'src/documentos/roteiro_final.md'),path.join(destino,'roteiro_apresentacao.md'));
  manifesto.sha256 = Object.fromEntries(['painel.html','consultas_dashboards.md','resultados_dashboards.json','plano_5w2h.md','relatorio_final.md','roteiro_apresentacao.md'].map(n =>
    [n, hash(fs.readFileSync(path.join(destino,n)))]));
  fs.writeFileSync(path.join(destino,'manifesto_dashboards.json'), JSON.stringify(manifesto,null,2));
  console.log(`Concluído: ${path.join(destino,'painel.html')}`);
} catch (e) {
  console.error(`Geração não concluída: ${e.message}`); process.exitCode = 1;
} finally { if (db) await db.close(); }
