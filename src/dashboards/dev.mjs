/** Preview local da interface React sobre os dados já preservados. */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {mineracao} from './dados.mjs';
import {prepararInterface,renderizar,fontesInterface} from './renderizar.mjs';
const raiz=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const snapshot=()=>JSON.parse(fs.readFileSync(path.join(raiz,'docs/entregas/final/resultados_dashboards.json'),'utf8'));
const km=mineracao(raiz);
const versao=()=>Math.max(...fontesInterface.map(n=>fs.statSync(path.join(raiz,n)).mtimeMs));
const port=Number(process.env.PORT||4173);
await prepararInterface();
const server=http.createServer(async(req,res)=>{
  if(req.url==='/_version'){res.writeHead(200,{'Content-Type':'text/plain','Cache-Control':'no-store'});return res.end(String(versao()))}
  if(req.url==='/favicon.ico'){res.writeHead(204);return res.end()}
  if(req.url!=='/'&&req.url!=='/painel.html'){res.writeHead(404);return res.end('Página não encontrada.')}
  try{
    await prepararInterface({forcar:true});
    const live=`<script>let v=${JSON.stringify(String(versao()))};setInterval(async()=>{try{if(await(await fetch('/_version')).text()!==v)location.reload()}catch{}},1500)</script>`;
    const html=renderizar({...snapshot(),km}).replace('</body>',live+'</body>');
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(html);
  }catch(e){res.writeHead(500,{'Content-Type':'text/plain; charset=utf-8'});res.end('Não foi possível compilar a interface: '+e.message)}
});
server.on('error',e=>{console.error(e.message);process.exitCode=1});
server.listen(port,'127.0.0.1',()=>console.log(`Ciclo Urbano · React\nLocal: http://127.0.0.1:${port}\nCtrl+C para encerrar. Alterações na interface recarregam a página.`));
