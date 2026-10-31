# Item 6 — mineração exploratória com K-means

Implementação completa para **executar sobre o DW do projeto**, sem alterar tabelas,
dados, views ou os documentos gerados da entrega parcial. O resultado é um relatório
Markdown com cinco gráficos, atribuição dos bairros, interpretação dos grupos e
diagnósticos, além de CSVs e um manifesto para reprodução.

**Execução concluída nesta máquina em 31/10/2026:** o banco `cidades_sustentaveis` foi
criado e carregado pelos scripts existentes; a mineração foi executada diretamente no DW.
O [relatório da execução](../../docs/analises/kmeans/kmeans_2025_20261031T122945_177876Z/relatorio.md)
e seus cinco gráficos usam os dados sintéticos do projeto: 12 bairros, k=3 e silhueta
média 0,3637. Industrial apresentou silhueta individual negativa; sua atribuição merece revisão.
Os testes automatizados continuam usando uma base artificial independente dos dados do projeto.

## Pergunta exploratória

Quais bairros apresentam perfis semelhantes de coleta, participação de recicláveis,
cancelamentos e ocorrências? A segmentação ajuda a formular prioridades de investigação
para ampliar a coleta seletiva e melhorar a regularidade. O programa não escolhe sozinho
onde investir nem estima ganhos ou custos.

O cliente é a Secretaria de Serviços Urbanos da Prefeitura fictícia de Cidade-Modelo.
A unidade de análise é **um bairro no ano de 2025**. Todos os dados do projeto são
**sintéticos**, com padrões deliberados. A mineração demonstra o método e sua aplicação;
os grupos não constituem descoberta sobre uma cidade real.

## Instalação na máquina que executará a mineração

Na raiz `projeto-tebd`, com Python 3.10 ou mais recente:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src/mineracao/requirements.txt
```

Não é necessário ativar o ambiente. No Linux/macOS, use `.venv/bin/python`.
As dependências da mineração ficam em seu próprio `requirements.txt`, pois não são
necessárias para recriar o banco ou gerar os documentos anteriores.

Nesta sessão, o ambiente `.venv` foi criado com acesso de leitura aos pacotes Python
já instalados (`--system-site-packages`); matplotlib e suas dependências ausentes foram
instalados apenas dentro dele. Na outra máquina, o comando acima cria um ambiente isolado.
Não copie a pasta `.venv` entre computadores: recrie-a.

## Caminho A — executar onde o PostgreSQL está disponível

1. O DW deve estar carregado pelo fluxo já existente do projeto. A mineração não recria o banco.
2. Configure o `.env` como descrito no README principal. A conexão reutiliza `src/config.py`.
3. Rode:

```powershell
.\.venv\Scripts\python.exe src/mineracao/kmeans_bairros.py --ano 2025
```

O programa chama o `psql` configurado no projeto e executa a extração em uma transação
**READ ONLY**. Precisa apenas de permissões de leitura nas tabelas `dw.*` utilizadas.
Não precisa de psycopg, SQLAlchemy, dashboards, internet ou servidor web.
Usa `-X` para ignorar configurações pessoais do psql, não solicita senha interativamente
e não grava os dados da conexão no relatório.

## Caminho B — exportar da outra máquina e executar por CSV

1. No pgAdmin da máquina que tem o banco, abra `src/mineracao/preparar_bairros.sql`.
2. Substitua **todas** as ocorrências de `__ANO__` por `2025` e execute o SELECT.
3. Exporte **todo o resultado**, com todas as colunas e linhas, em CSV UTF-8,
   com cabeçalho, separador **vírgula** e separador decimal **ponto**. Não exporte somente
   as quatro variáveis: contagens e totais são necessários para conferir as junções.
4. Transfira o CSV para a máquina de execução e rode, ajustando o caminho:

```powershell
.\.venv\Scripts\python.exe src/mineracao/kmeans_bairros.py --csv "C:\caminho\bairros_2025.csv" --ano 2025
```

No modo CSV, não são necessários PostgreSQL, `psql` nem `.env`. O relatório identifica
que houve leitura de um arquivo exportado e não uma consulta ao banco nesta execução.

## Preparação das variáveis

| Variável | Cálculo | Unidade e significado |
| --- | --- | --- |
| `kg_coletados_hab` | peso coletado / população do bairro | kg por habitante no ano; não é geração total de resíduos |
| `pct_reciclaveis` | 100 × peso reciclável coletado / peso total coletado | %; não é reciclagem efetiva após a triagem |
| `pct_canceladas` | 100 × viagens canceladas / todas as viagens | %; canceladas permanecem no denominador |
| `ocorrencias_1000_hab` | 1.000 × ocorrências abertas no ano / população | registros por mil habitantes; não é quantidade ainda em aberto |

O código usa as tabelas fato, sem arredondamentos intermediários. Cada processo é
agregado separadamente antes da junção por bairro, evitando multiplicar pesagens,
viagens ou ocorrências. A população é obtida uma vez por bairro a partir de `dim_local`,
incluindo os membros "bairro inteiro", sem somar suas repetições por ponto.

As viagens são identificadas por bairro/região de `dim_rota`, pois essa dimensão não
guarda a chave de bairro. Duplicações no cadastro e divergências entre os totais
agregados e os totais independentes interrompem a execução. O código também rejeita
ausências, valores infinitos, medidas negativas, denominadores zero e contagens inválidas.
Não há exclusão de bairros nem imputação silenciosa. Zero ocorrências por bairro é
mantido como zero; ausência de dados de pesagem ou viagens interrompe a execução.
As verificações do CSV não substituem uma auditoria do ETL ou da sua exportação.

## Como o K-means é aplicado

1. **Padronização:** `StandardScaler` transforma cada variável ativa em desvios padrão
   em torno de sua média. Sem isso, diferenças de unidade dominariam as distâncias.
2. **Agrupamento:** K-means alterna a atribuição de bairros ao centro mais próximo e
   o recálculo dos centroides, buscando minimizar as distâncias quadráticas internas.
   Cada bairro tem peso igual; população não é usada como peso do ajuste.
3. **Parâmetros:** inicialização `k-means++`, `n_init=50`, `max_iter=500`, algoritmo
   Lloyd e semente 42. Variáveis constantes são retiradas e identificadas no relatório.
4. **Número de grupos:** testa k de 2 até `min(5, n−1, perfis distintos)`. Soluções
   com grupo de um único bairro são exibidas, mas não elegíveis. Entre as demais,
   escolhe a maior silhueta média; empate exato favorece o menor k. Caso não exista
   solução elegível, informa o problema e não força uma conclusão.
5. **Cotovelo:** mostra a inércia para k=1 até o máximo. A redução da curva é uma
   verificação visual complementar; o programa não inventa uma localização do cotovelo.
6. **Interpretação:** apresenta médias nas unidades originais, perfis padronizados e
   bairros de cada grupo. Recomendações são hipóteses relativas às médias dos bairros.
7. **Sensibilidade:** compara dez sementes adicionais e refaz a análise retirando
   um bairro por vez, usando ARI. Mantém o mesmo k no teste de retirada. Estabilidade
   de sementes não é prova de validade externa; ARI não é acurácia.

É possível definir um k manual viável após avaliar os gráficos:

```powershell
.\.venv\Scripts\python.exe src/mineracao/kmeans_bairros.py --csv "C:\caminho\bairros_2025.csv" --ano 2025 --k 3
```

O relatório preserva o k sugerido e o manifesto registra a escolha manual. A equipe
deve justificar essa escolha. Os IDs dos grupos não são um ranking de qualidade.

## Saídas e uso na entrega

Cada execução cria uma nova pasta em `docs/analises/kmeans/kmeans_2025_<data UTC>/`.
Para outro diretório, use `--saida "caminho"`. Resultados anteriores são preservados.

| Arquivo | Conteúdo |
| --- | --- |
| `relatorio.md` | Problema, método explicado, resultados, interpretação, diagnósticos e limitações |
| `01_escolha_k.png` | Curvas de cotovelo e silhueta |
| `02_perfis_bairros.png` | Quatro variáveis em unidades originais por bairro |
| `03_centroides.png` | Perfil padronizado dos grupos |
| `04_projecao_pca.png` | Projeção em duas dimensões; PCA serve apenas à visualização |
| `05_silhuetas.png` | Silhueta individual de cada bairro |
| `base_bairros.csv` | Entrada validada, incluindo denominadores e totais de reconciliação |
| `bairros_grupos.csv`, `centroides.csv` | Atribuições e médias dos grupos |
| `variaveis_padronizadas.csv`, `avaliacao_k.csv` | Valores efetivamente usados e critérios para k |
| `estatisticas_descritivas.csv`, `correlacoes.csv` | Estatísticas das variáveis antes da padronização |
| `estabilidade_sementes.csv`, `sensibilidade_bairros.csv` | Diagnósticos de robustez |
| `consulta_preparacao.sql` | Consulta de referência com o ano preenchido; no modo CSV não comprova execução na origem |
| `manifesto.json` | Conclusão da execução, parâmetros, versões, avisos e SHA-256 dos artefatos |

O marcador de execução completa é `manifesto.json` com `status="concluido"`. Uma falha
pode deixar arquivos parciais em uma pasta nova; sem esse marcador, não use a pasta como entrega.

Leia os grupos junto com os dashboards e os padrões P1–P6. A partir deles, formule ações
5W2H que citem o resultado que as motivou. O agrupamento não mede automaticamente rejeito
de triagem, adesão individual, causalidade ou potencial de recuperação. Não estima o indicador
11.6.1, pois faltam dados de geração total. A agregação anual oculta sazonalidade e apenas
12 bairros não sustentam generalizações robustas. Valores extremos e variáveis correlacionadas
podem dominar as distâncias mesmo depois da padronização.

Não edite os Markdown gerados de `docs/entregas/` para incluir resultados. A eventual
incorporação à entrega final deve ocorrer no modelo de documentos, após execução e revisão.

## Verificação do programa

Os testes usam `unittest` da biblioteca padrão e uma base de teste artificial, **sem
reconstruir ou substituir os dados do projeto**. Na raiz:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s src/mineracao/tests -v
```

Cobrem cálculos com denominadores conhecidos, falhas de integridade, reprodutibilidade,
identificação de dois perfis conhecidos e geração dos arquivos a partir de um CSV.
Esses testes não certificam a execução SQL no PostgreSQL da outra máquina.

Verificação realizada em 31/10/2026: testes automatizados, fluxo CSV com fixtures e
execução direta no banco do projeto, com geração do relatório e dos cinco gráficos.
Ambiente: Python 3.12.7, NumPy 2.3.2, pandas 2.3.1,
scikit-learn 1.7.1 e matplotlib 3.11.2. Os oito testes passaram. A consulta também
foi executada no PostgreSQL local, com reconciliação de totais; os gráficos da execução
do projeto foram inspecionados visualmente. O envio do SQL usa stdin UTF-8 para preservar
os acentos no Windows, em vez de passar a consulta como argumento `-c`.
As cinco medidas de entrada dos 12 bairros (pesos total e reciclável, viagens,
cancelamentos e ocorrências) foram reconciliadas com uma consulta independente
ao OLTP. As silhuetas individuais foram recalculadas por distâncias euclidianas
sem usar a função de silhueta do scikit-learn; a média conferiu em 0,363745.
Os hashes dos artefatos também foram conferidos contra o manifesto.

## Referências técnicas

- [KMeans — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)
- [StandardScaler — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [Silhueta — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)
- [Índice Rand ajustado — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html)
