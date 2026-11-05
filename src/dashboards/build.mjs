/** Atualiza apenas a interface usando o snapshot existente; não consulta banco. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {mineracao,hash} from './dados.mjs';
import {prepararInterface,renderizar,fontesInterface} from './renderizar.mjs';

const raiz=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const destino=path.join(raiz,'docs/entregas/final');
try {
  const snapshot=JSON.parse(fs.readFileSync(path.join(destino,'resultados_dashboards.json'),'utf8'));
  const manifesto=JSON.parse(fs.readFileSync(path.join(destino,'manifesto_dashboards.json'),'utf8'));
  if(manifesto.status!=='concluido')throw Error('O snapshot não está concluído. Execute o gerador de dados.');
  if(hash(fs.readFileSync(path.join(destino,'resultados_dashboards.json')))!==manifesto.sha256['resultados_dashboards.json'])throw Error('O snapshot foi alterado após a geração.');
  await prepararInterface();
  const html=renderizar({...snapshot,km:mineracao(raiz)});
  fs.writeFileSync(path.join(destino,'painel.html'),html);
  manifesto.interface={framework:'React',compilado_utc:new Date().toISOString(),offline:true};
  manifesto.sha256['painel.html']=hash(html);
  for(const n of [...fontesInterface,'src/dashboards/renderizar.mjs'])manifesto.fontes_sha256[n]=hash(fs.readFileSync(path.join(raiz,n)));
  fs.writeFileSync(path.join(destino,'manifesto_dashboards.json'),JSON.stringify(manifesto,null,2));
  console.log(`React compilado: ${path.join(destino,'painel.html')} (${Math.round(Buffer.byteLength(html)/1024)} KB, offline).`);
}catch(e){console.error(`Build não concluído: ${e.message}`);process.exitCode=1}
