# Painéis e entrega final — itens 6 a 10

O painel agora é uma aplicação **React**, com Manrope local, ícones Lucide e gráficos SVG. Abra [o painel já compilado](../../docs/entregas/final/painel.html) diretamente no navegador: React, CSS, fontes, dados e imagens estão incorporados, sem CDN ou internet para apresentar.

A visão geral combina evolução mensal, composição dos resíduos, indicadores e participação de recicláveis nos bairros. Os três níveis têm cinco consultas cada, com busca, filtros, ordenação, paginação e exportação CSV. A interface usa linguagem de gestão; códigos SQL, detalhes do banco e diagnósticos do método ficam nos documentos técnicos. Perfis dos bairros e 5W2H têm telas próprias. A direção visual está em [DESIGN.md](DESIGN.md).

O [relatório final](../../docs/entregas/final/relatorio_final.md) reúne o trabalho e aponta os anexos dos itens 1 a 5. Os resultados são sintéticos de 2025. O painel é um snapshot e mostra a origem da extração.

## Desenvolver e compilar a interface React

Na raiz do repositório, com Node.js 20 ou superior:

```powershell
npm.cmd ci --prefix src/dashboards --no-audit --no-fund
npm.cmd --prefix src/dashboards run dev
```

Abra `http://127.0.0.1:4173`. Alterações em `ui/` recarregam a página. O servidor usa o snapshot existente; não consulta o PostgreSQL. Ctrl+C encerra o servidor. Para gerar novamente o arquivo offline, sem refazer a extração:

```powershell
npm.cmd --prefix src/dashboards run build
```

O build utiliza esbuild e atualiza o HTML e seu hash no manifesto. Os componentes ficam em `ui/App.jsx` e `ui/charts.jsx`, as transformações em `ui/model.mjs` e o visual em `ui/styles.css`. As fontes e os ícones são empacotados localmente.

## Atualizar a partir do PostgreSQL existente

Requer Node.js 20 ou superior, as dependências npm instaladas pelo comando acima e `psql` disponível. Reutiliza as variáveis de `src/config.py`: ambiente prevalece sobre `.env`, com os mesmos padrões de conexão. Se necessário, configure `PSQL` com o caminho do executável.

```powershell
node src/dashboards/gerar_paineis.mjs
```

O gerador usa uma única transação `REPEATABLE READ READ ONLY`, compara a base anual com a mineração e executa as 15 consultas no mesmo snapshot. Não cria nem altera tabelas. Se houver divergência com a base preservada da mineração, interrompe a geração; a equipe deve revisar as duas análises em conjunto.

## Reproduzir sem PostgreSQL instalado

O PGlite executa PostgreSQL embarcado em WebAssembly. Este modo recria os scripts **somente em um banco efêmero em memória**, sem acessar ou apagar o banco do usuário. Os arquivos SQL originais são executados sem adaptação. Na validação de 05/11, foi utilizado PostgreSQL 18.6/PGlite 0.5.15; a execução original da mineração permanece preservada.

```powershell
npm.cmd ci --prefix src/dashboards --no-audit --no-fund
node src/dashboards/gerar_paineis.mjs --reproduzir
```

Para outro destino: `--saida "caminho"`. A pasta padrão é `docs/entregas/final/`. A geração bem-sucedida atualiza os arquivos dessa pasta; preserve uma cópia antes de comparar execuções diferentes. Não execute duas gerações simultâneas no mesmo destino.

## Arquivos gerados

| Arquivo | Conteúdo |
|---|---|
| `painel.html` | Painéis interativos offline, mineração e ações |
| `consultas_dashboards.md` | Quinze enunciados, SQL, colunas e orientação de leitura |
| `resultados_dashboards.json` | Resultados completos e origem |
| `manifesto_dashboards.json` | Marcador de conclusão, versão, totais e hashes |
| `plano_5w2h.md` | Seis ações rastreáveis; custos e metas hipotéticos |
| `relatorio_final.md` | Síntese do projeto e conexão dos dez itens do barema |
| `roteiro_apresentacao.md` | Sequência de demonstração e perguntas para ensaio |

O manifesto com `status=concluido` registra a última geração completa. Confira os hashes antes de distribuir um pacote. Arquivos da entrega final são gerados; edite os fontes em `src/dashboards/`, `src/sql/05`–`07` e `src/documentos/modelo_final.md` / `roteiro_final.md`.

## Executar as consultas no pgAdmin

- [Operacional: O1–O5](../sql/05_dashboard_operacional.sql).
- [Tático: T1–T5](../sql/06_dashboard_tatico.sql).
- [Estratégico: E1–E5](../sql/07_dashboard_estrategico.sql).

Selecione um SELECT/CTE completo por vez. Os arquivos são somente leitura e não integram a carga 01–03. A referência operacional é 01/01/2026; últimos sete dias completos = 25 a 31/12/2025. O2 reconstrói a situação nessa referência e conta 54 pendências, incluindo uma resolvida posteriormente; T3 conta 53 sem resolução no estado final da base. Essa diferença está documentada no relatório.

E1 inclui os 12 meses para todos os tipos cadastrados; tipos sem coleta ficam em zero. E2 distingue bairros e subtotais regionais: não some os dois níveis. E3 usa a coorte de viagens de 2025 e acompanha suas descargas posteriores; E4 usa descargas ocorridas em 2025 e preserva capacidade uma vez por destino/mês. Barras mostram até 12 registros; E1 agrega meses e E5 agrega trimestres. As tabelas preservam todos os resultados, paginados em oito linhas. E2 abre no nível bairro e E4 em dezembro, alteráveis nos filtros.

## Testes

Após instalar as dependências de desenvolvimento:

```powershell
node --test src/dashboards/tests/dashboards.test.mjs
```

Os 15 testes verificam execução SQL, reconciliação de 84 medidas com o K-means, totais entre OLTP e DW, recorte temporal, percentuais, presença dos enunciados, rastreabilidade do 5W2H, integridade HTML e navegação/busca/filtros/paginação do React em DOM de teste. A interface também é conferida para não expor rótulos técnicos. Os testes conciliam as séries dos gráficos, distinguem rejeito de reciclável e verificam CSV e ordenação. O motor de testes fica em memória e não altera banco externo.

Essa verificação não substitui a conferência visual no navegador da apresentação. Nesta sessão, a conexão de automação de navegador não estava disponível; não se afirma inspeção visual nem teste no PostgreSQL original.

## Empacotar para entregar (Windows)

```powershell
& .\src\scripts\empacotar_entrega.ps1
```

O script confere os hashes dos dashboards, dos fontes usados e dos resultados da mineração. Gera em `output/` um ZIP com código, documentação, resultados e `.env.example`, além do hash do pacote. Não inclui `.env`, `.git`, `node_modules`, ambientes Python ou arquivos temporários. Preserva pacotes anteriores.
