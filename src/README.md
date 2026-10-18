# Código do projeto (`src/`)

| Pasta / arquivo | O que faz |
|---|---|
| `config.py` | **Configuração central**: conexão com o banco e caminhos de programas. Lê variáveis de ambiente ou o arquivo `.env` da raiz. Nenhum outro arquivo guarda porta, senha ou caminho |
| `sql/` | Os scripts SQL do banco (tabela abaixo) |
| `scripts/popular_banco.py` | Cria e popula o banco executando os scripts SQL em ordem, e confere o resultado |
| `scripts/pgadmin_servidor.json` | Cadastro do servidor para importar no pgAdmin (sem senha) |
| `diagramas/` | `gerar_diagramas.py` (diagramas ER e estrelas, a partir do esquema real) e `gerar_graficos.py`; `dot/` guarda os `.dot` gerados |
| `documentos/` | `montar_entregas.py` (gera os 3 documentos), `gerar_pdf.py`, `gerar_dicionario.py` e os modelos de texto (`modelo_entrega.md`, `modelo_cap8_guia.md`) |

## Como configurar (uma vez)

1. Copie `.env.example` (na raiz) para `.env` e ajuste porta, usuário e senha do **seu** PostgreSQL.
2. Instale as dependências do Python: `pip install -r requirements.txt` (na raiz do projeto).
3. Para gerar diagramas e PDFs, precisa também de Graphviz e de um navegador Edge ou Chrome (detectados automaticamente).

## Como popular o banco

```bash
python src/scripts/popular_banco.py --recriar     # cria do zero, executa 01, 02 e 03 e confere
python src/scripts/popular_banco.py --verificar   # só confere o banco atual
```

Sem o script, o equivalente manual é executar os três arquivos de `src/sql/`, nesta ordem, com `psql -f`.

## Os scripts SQL (`sql/`)

| Ordem | Arquivo | O que faz | Observações |
|---|---|---|---|
| 1 | `01_construcao_oltp_olap.sql` | Cria os schemas `oltp` e `dw` (12 tabelas, 8 dimensões, 4 fatos), restrições e índices; **gera os dados de exemplo**; executa o **ETL** do OLTP para o DW e mostra a conferência de volumes | É o arquivo do **item 5 do barema**. Começa com `DROP SCHEMA … CASCADE`, então pode ser reexecutado |
| 2 | `02_dicionario_comentarios.sql` | `COMMENT ON` de todas as tabelas e colunas (o dicionário de dados no catálogo) | Executar depois do 01 |
| 3 | `03_views_apoio.sql` | Schema `bi` com 6 views para os dashboards | Executar depois do 01 e do 02. É apagado se o 01 for reexecutado |

Os **dados de exemplo** estão dentro do 01 (parte 3), são determinísticos (mesmos números a cada execução) e trazem padrões deliberados (blocos P1 a P6 comentados no próprio arquivo).

## Sobre "migrations" (alterações do banco)

O projeto **não usa migrations incrementais** (como `ALTER TABLE` versionados ou ferramentas como Flyway). A estratégia é **recriação completa**: o 01 apaga e refaz os schemas. Para um trabalho acadêmico com dados sintéticos isso é mais simples e menos sujeito a erro. Na prática:

| Se você precisa... | Faça |
|---|---|
| Mudar uma tabela ou coluna | Edite o `01_construcao_oltp_olap.sql` (e o `02`, se houver comentário), rode `popular_banco.py --recriar` |
| Atualizar diagramas e documentos | `python src/diagramas/gerar_diagramas.py` e `python src/documentos/montar_entregas.py` |
| Conferir se scripts e banco estão alinhados | `popular_banco.py --banco teste_limpo --recriar` cria um banco limpo só com os scripts e confere; compare com o banco de trabalho |

Se um dia o banco passar a guardar dados reais que não podem ser apagados, será preciso migrations incrementais; isso **não** é o caso hoje.
