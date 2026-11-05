import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {acoes} from './acoes.mjs';

const aqui=path.dirname(fileURLToPath(import.meta.url));
let compilado;
export const fontesInterface=['src/dashboards/ui/main.jsx','src/dashboards/ui/App.jsx','src/dashboards/ui/charts.jsx',
  'src/dashboards/ui/model.mjs','src/dashboards/ui/styles.css','src/dashboards/package.json','src/dashboards/package-lock.json'];

export async function prepararInterface({forcar=false}={}) {
  if(compilado&&!forcar)return compilado;
  const resultado=await build({absWorkingDir:aqui,entryPoints:['ui/main.jsx'],bundle:true,write:false,
    outfile:'bundle.js',format:'iife',platform:'browser',target:['es2020'],minify:true,jsx:'automatic',
    define:{'process.env.NODE_ENV':'"production"'},loader:{'.woff2':'dataurl','.woff':'dataurl'},
    legalComments:'inline',charset:'utf8',logLevel:'silent'});
  compilado={js:resultado.outputFiles.find(f=>f.path.endsWith('.js')).text,
    css:resultado.outputFiles.find(f=>f.path.endsWith('.css'))?.text||''};
  return compilado;
}

export function renderizar({manifesto,resultados,km}) {
  if(!compilado)throw Error('Compile a interface React com prepararInterface() antes de renderizar.');
  const dados={manifesto,resultados,km:{manifesto:km.manifesto,bairros:km.bairros,centroides:km.centroides,
    avaliacao:km.avaliacao,graficos:km.graficos},plano:acoes(resultados,km)};
  const json=JSON.stringify(dados).replaceAll('<','\\u003c');
  const js=compilado.js.replace(/<\/script/gi,'<\\/script');
  return `<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><meta name="theme-color" content="#5865df"><meta name="description" content="Ciclo Urbano: dashboards de gestão de resíduos, mineração de bairros e plano de ação. Dados sintéticos de 2025."><title>Ciclo Urbano — painéis de gestão</title><style>${compilado.css}</style></head><body><div id="root"></div><noscript>Ative o JavaScript para explorar os painéis. Os enunciados, SQL e resultados completos também estão em consultas_dashboards.md e resultados_dashboards.json, na mesma pasta.</noscript><script type="application/json" id="dados">${json}</script><script>${js}</script></body></html>`;
}
