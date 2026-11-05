import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export const arquivosSQL = ['05_dashboard_operacional.sql', '06_dashboard_tatico.sql', '07_dashboard_estrategico.sql'];
export const hash = texto => crypto.createHash('sha256').update(texto).digest('hex');
export function consultas(raiz) {
  return arquivosSQL.flatMap(arquivo => {
    const texto = fs.readFileSync(path.join(raiz, 'src/sql', arquivo), 'utf8');
    return texto.split(/^-- @consulta /m).slice(1).map(bloco => {
      const fim = bloco.indexOf('\n');
      const [id, titulo, leitura, eixo, medida] = bloco.slice(0, fim).trim().split(' | ');
      const sql = bloco.slice(fim).trim();
      if (!/^[OTE][1-5]$/.test(id) || !medida || !/^(SELECT|WITH)\s/i.test(sql)) throw Error(`Consulta inválida: ${arquivo}`);
      return {id, titulo, leitura, eixo, medida, sql, arquivo};
    });
  });
}

// CSV RFC 4180: preserva vírgulas, aspas, BOM e quebras dentro dos campos.
export function csv(texto) {
  const linhas = []; let linha = [], campo = '', aspas = false;
  texto = texto.replace(/^\uFEFF/, '');
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (c === '"') {
      if (aspas && texto[i + 1] === '"') { campo += '"'; i++; }
      else aspas = !aspas;
    } else if (c === ',' && !aspas) { linha.push(campo); campo = ''; }
    else if ((c === '\n' || c === '\r') && !aspas) {
      if (c === '\r' && texto[i + 1] === '\n') i++;
      linha.push(campo); if (linha.some(v => v !== '')) linhas.push(linha);
      linha = []; campo = '';
    } else campo += c;
  }
  if (aspas) throw Error('CSV com aspas não fechadas.');
  if (campo || linha.length) { linha.push(campo); linhas.push(linha); }
  const campos = linhas.shift() || [];
  return linhas.map(l => {
    if (l.length !== campos.length) throw Error('CSV com número incorreto de colunas.');
    return Object.fromEntries(campos.map((k, i) => [k, l[i]]));
  });
}

export function mineracao(raiz) {
  const pasta = path.join(raiz, 'docs/analises/kmeans');
  const candidatos = fs.existsSync(pasta) ? fs.readdirSync(pasta).filter(n => n.startsWith('kmeans_2025_')).sort().reverse() : [];
  for (const nome of candidatos) {
    const dir = path.join(pasta, nome), arq = path.join(dir, 'manifesto.json');
    if (!fs.existsSync(arq)) continue;
    const manifesto = JSON.parse(fs.readFileSync(arq, 'utf8'));
    if (manifesto.status !== 'concluido') continue;
    for (const [nomeArquivo, esperado] of Object.entries(manifesto.sha256)) {
      if (path.basename(nomeArquivo) !== nomeArquivo) throw Error('Nome inválido no manifesto da mineração.');
      if (hash(fs.readFileSync(path.join(dir, nomeArquivo))) !== esperado) throw Error(`Hash divergente na mineração: ${nomeArquivo}`);
    }
    return {dir, manifesto, base: csv(fs.readFileSync(path.join(dir, 'base_bairros.csv'), 'utf8')),
      bairros: csv(fs.readFileSync(path.join(dir, 'bairros_grupos.csv'), 'utf8')),
      centroides: csv(fs.readFileSync(path.join(dir, 'centroides.csv'), 'utf8')),
      avaliacao: csv(fs.readFileSync(path.join(dir, 'avaliacao_k.csv'), 'utf8')),
      graficos: Object.fromEntries(Object.keys(manifesto.sha256).filter(n => n.endsWith('.png')).map(n =>
        [n, `data:image/png;base64,${fs.readFileSync(path.join(dir, n)).toString('base64')}`]))};
  }
  throw Error('Não há execução concluída do K-means em docs/analises/kmeans.');
}

export function reconciliar(atual, anterior) {
  if (atual.length !== anterior.length) throw Error('Número de bairros diverge da mineração.');
  const campos = ['populacao', 'qtd_pesagens', 'viagens', 'canceladas', 'ocorrencias', 'peso_total_kg', 'peso_reciclavel_kg'];
  let comparacoes = 0;
  for (const linha of atual) {
    const referencia = anterior.find(b => Number(b.id_bairro) === Number(linha.id_bairro));
    if (!referencia || referencia.bairro !== linha.bairro || referencia.regiao !== linha.regiao) throw Error('Identidade do bairro divergente.');
    for (const campo of campos) {
      if (!Number.isFinite(Number(linha[campo])) || Math.abs(Number(linha[campo]) - Number(referencia[campo])) > .005)
        throw Error(`Base diferente da mineração: ${linha.bairro}, ${campo}.`);
      comparacoes++;
    }
  }
  return comparacoes;
}

// Recalcula silhuetas por distâncias euclidianas, sem scikit-learn.
// A distância média a um grupo não é a distância ao seu centroide.
export function revisarParticao(km) {
  const m=km.manifesto, features=m.variaveis;
  const pontos=km.bairros.map(b=>({bairro:b.bairro,grupo:Number(b.grupo),
    esperado:Number(b.silhueta_individual),x:features.map((f,i)=>(Number(b[f])-m.scaler_media[i])/m.scaler_escala[i])}));
  const grupos=[...new Set(pontos.map(b=>b.grupo))];
  const distancia=(a,b)=>Math.sqrt(a.reduce((s,v,i)=>s+(v-b[i])**2,0));
  const revisao=pontos.map(p=>{
    const proprios=pontos.filter(q=>q!==p&&q.grupo===p.grupo);
    if(!proprios.length)throw Error('Grupo unitário na mineração preservada.');
    const interna=proprios.reduce((s,q)=>s+distancia(p.x,q.x),0)/proprios.length;
    const outros=grupos.filter(g=>g!==p.grupo).map(g=>{
      const membros=pontos.filter(q=>q.grupo===g);
      return {grupo:g,distancia_media:membros.reduce((s,q)=>s+distancia(p.x,q.x),0)/membros.length};
    }).sort((a,b)=>a.distancia_media-b.distancia_media);
    const externa=outros[0].distancia_media;
    const silhueta=(externa-interna)/Math.max(interna,externa);
    if(Math.abs(silhueta-p.esperado)>1e-9)throw Error(`Silhueta não confere: ${p.bairro}.`);
    return {bairro:p.bairro,grupo:p.grupo,silhueta,distancia_media_interna:interna,
      grupo_alternativo:outros[0].grupo,distancia_media_alternativa:externa};
  });
  return {metodo:'Distâncias euclidianas após padronização com parâmetros preservados; cálculo independente do scikit-learn.',
    silhueta_media:revisao.reduce((s,r)=>s+r.silhueta,0)/revisao.length,bairros:revisao};
}
