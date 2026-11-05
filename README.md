# Ciclo Urbano — Laboratório de Dados para Cidades Sustentáveis

**Entrega final (06/11):** abra o [painel React offline](docs/entregas/final/painel.html), com visão geral, dashboards operacional, tático e estratégico, mineração e 5W2H. Consulte o [relatório final](docs/entregas/final/relatorio_final.md), as [15 consultas](docs/entregas/final/consultas_dashboards.md), o [roteiro de apresentação](docs/entregas/final/roteiro_apresentacao.md) e as [instruções para desenvolver em React e reproduzir os dados](src/dashboards/README.md). Os documentos de 19/10 preservam o histórico da entrega parcial.

Projeto da disciplina **Tópicos Especiais em Banco de Dados** (ODS 11): gestão de resíduos sólidos urbanos e coleta seletiva, com ambientes **OLTP** (12 tabelas, 3FN) e **OLAP** (Data Warehouse com 4 estrelas) em PostgreSQL.

## Estrutura

```
.
├── README.md               este arquivo
├── .env.example            modelo da configuração local (copie para .env)
├── src/                    CÓDIGO
│   ├── config.py           configuração central (conexão e caminhos)
│   ├── sql/                scripts do banco (01 construção, 02 dicionário, 03 views)
│   ├── scripts/            popular_banco.py e cadastro do pgAdmin
│   ├── diagramas/          geradores de diagramas e gráficos
│   └── documentos/         geradores dos PDFs e modelos de texto
└── docs/                   DOCUMENTOS
    ├── README.md           como ler os documentos
    ├── enunciado/          enunciado do professor e artigo do método PBL
    ├── entregas/           professor/ · anexo-dicionario/ · guia-completo/   (PDF + Markdown)
    ├── diagramas/          PNG e SVG dos diagramas; graficos/
    ├── roteiros/           roteiro de demonstração do checkpoint
    ├── analises/           análise de complexidade e auditoria do enunciado
    └── pesquisas/          pesquisas na web com fontes
```

## Começar rápido

```bash
cp .env.example .env                              # ajuste porta, usuário e senha do seu PostgreSQL
pip install -r requirements.txt                   # dependências do Python
python src/scripts/popular_banco.py --recriar     # cria o banco, executa os scripts e confere
```

## Programas necessários

| Programa | Para quê | Obrigatório? |
|---|---|---|
| **PostgreSQL** 15 ou mais novo | O banco do projeto | Sim |
| **Python** 3 (testado com a versão 3.14), com `pip install -r requirements.txt` | Scripts de `src/` | Sim |
| **Graphviz** | Gerar os diagramas | Só para regenerar os diagramas |
| **Microsoft Edge ou Google Chrome** | Gerar os PDFs | Só para regenerar os PDFs |
| **pgAdmin 4** | Visualizar o banco e o ERD | Opcional (vem com o instalador do PostgreSQL) |

## Documentos principais

| Quero... | Abrir |
|---|---|
| Mostrar o andamento ao professor | `docs/entregas/professor/` e `docs/roteiros/roteiro_demonstracao_checkpoint.md` |
| Consultar o dicionário de dados | `docs/entregas/anexo-dicionario/` |
| Continuar o projeto (inclusive com outra IA) | `docs/entregas/guia-completo/`, capítulo 8 |
| Saber como ler cada documento | `docs/README.md` |
| Saber o que cada script faz | `src/README.md` |

## Regenerar tudo

```bash
python src/diagramas/gerar_diagramas.py    # precisa de Graphviz e do banco carregado
python src/diagramas/gerar_graficos.py     # precisa de matplotlib e do banco carregado
python src/documentos/montar_entregas.py   # gera os 3 documentos (PDF e Markdown) em docs/entregas/
```

O texto de todos os documentos mora em `src/documentos/modelo_entrega.md`. **Edite o modelo, não os arquivos gerados.**

## Mineração exploratória — item 6

A implementação K-means está em [`src/mineracao/`](src/mineracao/README.md).
Lê o DW em modo somente leitura ou um CSV exportado da outra máquina e gera relatório,
gráficos e diagnósticos. Veja o README da mineração para instalação e execução.
Execução com os dados sintéticos do banco em 31/10/2026:
[relatório e gráficos](docs/analises/kmeans/kmeans_2025_20261031T122945_177876Z/relatorio.md).
