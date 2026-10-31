"""Item 6: mineração exploratória de bairros, sem escrita no PostgreSQL.

Execução a partir da raiz: python src/mineracao/kmeans_bairros.py --help
Os dados do projeto são sintéticos; os resultados não descrevem uma cidade real.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

SRC = Path(__file__).resolve().parents[1]
SQL_PATH = Path(__file__).with_name("preparar_bairros.sql")
FEATURES = ["kg_coletados_hab", "pct_reciclaveis", "pct_canceladas", "ocorrencias_1000_hab"]
LABELS = ["kg coletados/hab", "Recicláveis coletados (%)", "Cancelamentos (%)", "Ocorrências/1.000 hab"]
COUNTS = ["id_bairro", "populacao", "variantes_cadastro", "qtd_pesagens", "viagens", "canceladas", "ocorrencias"]
TOTALS = {"peso_total_kg": "total_peso_periodo", "viagens": "total_viagens_periodo",
          "ocorrencias": "total_ocorrencias_periodo"}
NUMERIC = COUNTS + ["peso_total_kg", "peso_reciclavel_kg"] + list(TOTALS.values())
REQUIRED = ["ano", "bairro", "regiao"] + NUMERIC
COLORS = ["#245A81", "#BA7618", "#8B5088", "#627B35", "#B95229"]
REFERENCES = """- [KMeans — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)
- [StandardScaler — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [Silhueta — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)
- [Índice Rand ajustado — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html)"""


def consulta(ano: int) -> str:
    return SQL_PATH.read_text(encoding="utf-8").replace("__ANO__", str(int(ano)))


def ler_banco(sql: str) -> pd.DataFrame:
    """COPY TO STDOUT usa o mesmo SELECT e uma transação READ ONLY.

    -X desabilita psqlrc; timeout e -w impedem espera indefinida por senha.
    Credenciais são obtidas de src/config.py, nunca registradas nas saídas.
    """
    sys.path.insert(0, str(SRC))
    import config
    env = dict(config.ENV, PGCONNECT_TIMEOUT="10")
    comando = "BEGIN READ ONLY; COPY (\n" + sql.rstrip().rstrip(";") + ") TO STDOUT WITH CSV HEADER; ROLLBACK;"
    proc = subprocess.run(
        config.psql_base(so_dados=False) + ["-X", "-w", "-q", "-v", "ON_ERROR_STOP=1", "-f", "-"],
        # No Windows, SQL com acentos em -c pode passar pela página de código
        # do executável. stdin preserva os bytes UTF-8 declarados ao servidor.
        input=comando, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    if proc.returncode:
        # Não ecoar stderr: ele pode conter detalhes da conexão.
        raise ValueError("Não foi possível ler o banco. Confira .env, psql, permissões SELECT e carga do DW.")
    return pd.read_csv(io.StringIO(proc.stdout))


def preparar(base: pd.DataFrame, ano: int) -> tuple[pd.DataFrame, list[str]]:
    """Valida a base no grão bairro/ano e calcula as quatro variáveis."""
    faltantes = sorted(set(REQUIRED) - set(base.columns))
    if faltantes:
        raise ValueError("Colunas ausentes no CSV: " + ", ".join(faltantes))
    df = base[REQUIRED].copy()
    if len(df) < 4:
        raise ValueError("São necessários pelo menos quatro bairros para comparar valores de k.")
    for c in ["ano"] + NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="raise")
        if not np.isfinite(df[c].to_numpy(dtype=float)).all():
            raise ValueError(f"{c}: há valores ausentes ou não finitos. Não serão imputados silenciosamente.")
    for c in ["bairro", "regiao"]:
        if df[c].isna().any() or df[c].astype(str).str.strip().eq("").any():
            raise ValueError(f"{c}: há identificações vazias.")
        df[c] = df[c].astype(str).str.strip()
    if not df["ano"].eq(ano).all():
        raise ValueError("O ano da base difere de --ano ou mistura períodos.")
    if df["id_bairro"].duplicated().any() or df.duplicated(["bairro", "regiao"]).any():
        raise ValueError("Bairros duplicados: a entrada deve ter uma linha por bairro/ano.")
    if not df["variantes_cadastro"].eq(1).all():
        raise ValueError("Há atributos territoriais conflitantes em dim_local.")
    for c in COUNTS + ["ano", "total_viagens_periodo", "total_ocorrencias_periodo"]:
        if not np.equal(df[c], np.floor(df[c])).all():
            raise ValueError(f"{c}: contagem/identificador deve ser inteiro.")
    if (df[NUMERIC] < 0).any().any():
        raise ValueError("A base contém medidas negativas.")
    for c in ["id_bairro", "populacao", "peso_total_kg", "viagens", "qtd_pesagens"]:
        if df[c].le(0).any():
            raise ValueError(f"{c}: valor zero impede uma comparação válida de todos os bairros.")
    if df["peso_reciclavel_kg"].gt(df["peso_total_kg"] + 1e-8).any():
        raise ValueError("Peso de recicláveis superior ao peso total.")
    if df["canceladas"].gt(df["viagens"]).any():
        raise ValueError("Cancelamentos superiores ao número de viagens.")
    for medida, total in TOTALS.items():
        if df[total].nunique() != 1 or not np.isclose(df[medida].sum(), df[total].iloc[0], rtol=0, atol=0.01):
            raise ValueError(f"Reconciliação falhou para {medida}: confira perda ou multiplicação nas junções.")
    df["kg_coletados_hab"] = df.peso_total_kg / df.populacao
    df["pct_reciclaveis"] = 100 * df.peso_reciclavel_kg / df.peso_total_kg
    df["pct_canceladas"] = 100 * df.canceladas / df.viagens
    df["ocorrencias_1000_hab"] = 1000 * df.ocorrencias / df.populacao
    avisos = ["Dados sintéticos com padrões deliberados; não são evidência sobre uma cidade real."]
    if len(df) != 12:
        avisos.append(f"A entrada contém {len(df)} bairros; a documentação descreve 12. Confira a cobertura.")
    if len(df) <= 12:
        avisos.append("Amostra territorial pequena: agrupamentos são exploratórios e sensíveis às variáveis.")
    if df["ocorrencias"].sum() == 0:
        avisos.append("Nenhuma ocorrência no período: verificar se a carga está completa; não inferir qualidade do atendimento.")
    return df.sort_values("id_bairro").reset_index(drop=True), avisos


def ajustar(x: np.ndarray, k: int, seed: int) -> KMeans:
    return KMeans(n_clusters=k, init="k-means++", n_init=50,
                  max_iter=500, random_state=seed, algorithm="lloyd").fit(x)


def agrupar(df: pd.DataFrame, seed: int = 42, k_forcado: int | None = None) -> dict:
    ativas = [c for c in FEATURES if df[c].nunique() > 1]
    if len(ativas) < 2:
        raise ValueError("Menos de duas variáveis variam entre bairros; K-means não é informativo.")
    scaler = StandardScaler()
    x = scaler.fit_transform(df[ativas])
    distintos = len(np.unique(x, axis=0))
    kmax = min(5, len(df) - 1, distintos)
    if kmax < 2:
        raise ValueError("Não há perfis distintos suficientes para o agrupamento.")
    modelos, linhas = {}, []
    with threadpool_limits(limits=1):
        # k=1 só entra no cotovelo; silhueta não é definida para um grupo.
        for k in range(1, kmax + 1):
            modelo = ajustar(x, k, seed)
            modelos[k] = modelo
            score = float(silhouette_score(x, modelo.labels_)) if k > 1 else np.nan
            minimo = int(np.bincount(modelo.labels_).min())
            linhas.append({"k": k, "inercia": float(modelo.inertia_), "silhueta": score,
                           "menor_grupo": minimo, "elegivel": k > 1 and minimo >= 2})
        metricas = pd.DataFrame(linhas)
        elegiveis = metricas.loc[metricas.elegivel]
        if elegiveis.empty:
            raise ValueError("Nenhum k avaliado evita grupos de um único bairro; revise a base e as variáveis.")
        sugerido = int(elegiveis.sort_values(["silhueta", "k"], ascending=[False, True]).iloc[0].k)
        escolhido = sugerido if k_forcado is None else k_forcado
        if escolhido not in elegiveis.k.tolist():
            raise ValueError("--k deve estar entre 2 e 5, ser viável para a amostra e não gerar grupos unitários.")
        modelo = modelos[escolhido]
        # IDs estáveis: ordenar centroides pelo percentual de recicláveis (ou primeira variável ativa).
        eixo = ativas.index("pct_reciclaveis") if "pct_reciclaveis" in ativas else 0
        ordem = sorted(range(escolhido), key=lambda i: (modelo.cluster_centers_[i, eixo], tuple(modelo.cluster_centers_[i])))
        mapa = {antigo: novo + 1 for novo, antigo in enumerate(ordem)}
        labels = np.array([mapa[int(i)] for i in modelo.labels_])
        estabilidade = []
        for outra_seed in range(seed + 1, seed + 11):
            outra = ajustar(x, escolhido, outra_seed)
            estabilidade.append({"semente": outra_seed,
                                 "ari": float(adjusted_rand_score(labels, outra.labels_))})
        # Leave-one-out: refaz scaler e k-means sem cada bairro e compara os demais.
        sensibilidade = []
        for i in range(len(df)):
            manter = np.arange(len(df)) != i
            sub = StandardScaler().fit_transform(df.loc[manter, ativas])
            if len(np.unique(sub, axis=0)) < escolhido:
                sensibilidade.append({"bairro_retirado": df.iloc[i].bairro, "ari": None})
                continue
            outra = ajustar(sub, escolhido, seed)
            sensibilidade.append({"bairro_retirado": df.iloc[i].bairro,
                                  "ari": float(adjusted_rand_score(labels[manter], outra.labels_))})
    saida = df.copy()
    saida["grupo"] = labels
    saida["silhueta_individual"] = silhouette_samples(x, labels)
    centros = pd.DataFrame(scaler.inverse_transform(modelo.cluster_centers_[ordem]), columns=ativas)
    centros.insert(0, "grupo", np.arange(1, escolhido + 1))
    return {"bairros": saida, "ativas": ativas, "x": x, "scaler": scaler,
            "centroides": centros, "centroides_z": modelo.cluster_centers_[ordem],
            "metricas": metricas, "k": escolhido, "k_sugerido": sugerido,
            "estabilidade": pd.DataFrame(estabilidade), "sensibilidade": pd.DataFrame(sensibilidade)}


def tabela(df: pd.DataFrame) -> str:
    """Markdown sem dependência opcional tabulate; protege separadores e novas linhas."""
    def cel(v):
        if pd.isna(v):
            return "—"
        if isinstance(v, (float, np.floating)):
            return f"{v:.4f}"
        return str(v).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "| " + " | ".join(["---"] * len(df.columns)) + " |"]
    linhas += ["| " + " | ".join(cel(v) for v in row) + " |" for row in df.itertuples(index=False, name=None)]
    return "\n".join(linhas)


def graficos(res: dict, pasta: Path, ano: int) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    df, met = res["bairros"], res["metricas"]
    def salvar(fig, nome):
        fig.suptitle(f"Ciclo Urbano • {ano} • dados sintéticos", fontsize=11)
        fig.savefig(pasta / f"{nome}.png", dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    axes[0].plot(met.k, met.inercia, "o-", color=COLORS[0])
    axes[0].set(xlabel="Número de grupos (k)", ylabel="Soma das distâncias quadráticas", title="Cotovelo (inspeção visual)")
    m = met.loc[met.k > 1]
    axes[1].plot(m.k, m.silhueta, "o-", color=COLORS[1])
    for row in m.itertuples():
        if not row.elegivel:
            axes[1].annotate("grupo unitário", (row.k, row.silhueta), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8)
    axes[1].set(xlabel="Número de grupos (k)", ylabel="Silhueta média", ylim=(-1.05, 1.05), title="Separação entre grupos")
    for ax in axes:
        ax.set_xticks(met.k if ax is axes[0] else m.k)
        ax.axvline(res["k"], color="#444444", linestyle="--", linewidth=1)
        ax.grid(axis="y", alpha=.2)
    salvar(fig, "01_escolha_k")
    fig, axes = plt.subplots(2, 2, figsize=(12, 11), layout="constrained")
    ordem = df.sort_values(["grupo", "id_bairro"])
    nomes = [f"G{g} · {bairro}" for g, bairro in zip(ordem.grupo, ordem.bairro)]
    for ax, c, label in zip(axes.flat, FEATURES, LABELS):
        bars = ax.barh(nomes, ordem[c], color=[COLORS[g - 1] for g in ordem.grupo])
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=8)
        ax.set(xlabel=label, xlim=(0, max(float(ordem[c].max()) * 1.25, 1)))
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=.15)
    salvar(fig, "02_perfis_bairros")
    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    # Perfil dos centroides; cor e valor numérico permitem leitura sem depender da cor.
    z = res["centroides_z"]
    limite = max(float(np.abs(z).max()), 1)
    im = ax.imshow(z, cmap="BrBG", vmin=-limite, vmax=limite, aspect="auto")
    ax.set_xticks(range(len(res["ativas"])), [LABELS[FEATURES.index(c)].replace(" ", "\n", 1) for c in res["ativas"]])
    ax.set_yticks(range(res["k"]), [f"Grupo {g}" for g in range(1, res["k"] + 1)])
    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            ax.text(j, i, f"{z[i,j]:+.2f}", ha="center", va="center",
                    color="white" if abs(z[i,j]) > limite * .65 else "#222222")
    fig.colorbar(im, ax=ax, label="Desvios padrão em relação à média dos bairros")
    ax.set_title("Centroides padronizados")
    salvar(fig, "03_centroides")
    pca = PCA(n_components=2)
    pontos = pca.fit_transform(res["x"])
    fig, ax = plt.subplots(figsize=(10, 7), layout="constrained")
    for g in range(1, res["k"] + 1):
        mask = df.grupo.eq(g).to_numpy()
        ax.scatter(pontos[mask, 0], pontos[mask, 1], label=f"Grupo {g}", color=COLORS[g - 1], marker=["o", "s", "^", "D", "P"][g - 1], s=75)
    # IDs curtos evitam sobreposição de nomes; tabela do relatório fornece o vínculo.
    for (px, py), ident in zip(pontos, df.id_bairro):
        ax.annotate(str(int(ident)), (px, py), xytext=(5, 5), textcoords="offset points")
    ev = pca.explained_variance_ratio_ * 100
    ax.set(xlabel=f"Componente 1 ({ev[0]:.1f}% da variância)", ylabel=f"Componente 2 ({ev[1]:.1f}% da variância)",
           title="Projeção PCA para visualização; números identificam bairros")
    ax.legend(frameon=False)
    ax.grid(alpha=.15)
    salvar(fig, "04_projecao_pca")
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    ordem = df.sort_values(["grupo", "silhueta_individual"])
    nomes = [f"G{g} · {bairro}" for g, bairro in zip(ordem.grupo, ordem.bairro)]
    bars = ax.barh(nomes, ordem.silhueta_individual, color=[COLORS[g - 1] for g in ordem.grupo])
    ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=8)
    ax.set(xlabel="Silhueta individual", xlim=(-1.1, 1.1), title="Bairros próximos às fronteiras dos grupos")
    ax.axvline(0, color="#444444", linewidth=1)
    ax.invert_yaxis()
    salvar(fig, "05_silhuetas")


def relatorio(res: dict, avisos: list[str], ano: int, origem: str, seed: int) -> str:
    df, centros = res["bairros"], res["centroides"]
    met = res["metricas"].set_index("k").loc[res["k"]]
    decisoes = []
    medias = df[FEATURES].mean()
    for g, grupo in df.groupby("grupo", sort=True):
        recic = grupo.pct_reciclaveis.mean()
        cancel = grupo.pct_canceladas.mean()
        ocorr = grupo.ocorrencias_1000_hab.mean()
        acoes = []
        if recic < medias.pct_reciclaveis:
            acoes.append("investigar acesso à seletiva e qualidade da separação antes de propor expansão")
        else:
            acoes.append("avaliar manutenção da coleta seletiva e acompanhamento da qualidade da triagem")
        if cancel > medias.pct_canceladas:
            acoes.append("investigar regularidade das viagens antes de ampliar a operação")
        if ocorr > medias.ocorrencias_1000_hab:
            acoes.append("examinar tipos de ocorrência e canais de atendimento")
        decisoes.append(f"### Grupo {g}\n\nBairros: {', '.join(grupo.bairro)}. "
                        f"Médias dos bairros: {recic:.2f}% de recicláveis coletados, "
                        f"{cancel:.2f}% de cancelamentos e {ocorr:.2f} ocorrências/1.000 habitantes. "
                        "Hipóteses para orientar uma ação 5W2H: " + "; ".join(acoes) + ". "
                        "Comparação relativa à média não ponderada dos bairros, sem meta externa ou evidência causal.")
    removidas = sorted(set(FEATURES) - set(res["ativas"]))
    return f"""# Ciclo Urbano — mineração exploratória com K-means

**Dados sintéticos de {ano}.** Este resultado descreve a simulação do projeto e seus padrões deliberados.
Fonte: {origem}. População analisada: {len(df)} bairros, uma observação por bairro/ano.

## Problema e método

Quais bairros apresentam perfis semelhantes de coleta, participação de recicláveis,
regularidade das viagens e demanda registrada pelo cidadão? O objetivo é apoiar a
Secretaria na investigação de prioridades para coleta seletiva e regularidade do serviço.

K-means é um método não supervisionado: escolhe k centros, atribui cada bairro ao centro
mais próximo por distância euclidiana e recalcula os centros como médias. Repete o processo
até convergir, minimizando a soma das distâncias quadráticas dentro dos grupos.
Não prevê o futuro nem demonstra causas. Cada bairro tem o mesmo peso no ajuste.

## Preparação e definições

Os três fatos foram agregados separadamente antes de se reunir uma linha por bairro.
A população foi obtida uma vez por bairro, sem somar suas repetições em dim_local.
Ocorrências são contadas pela data de abertura, inclusive as ainda não resolvidas.
Canceladas integram o denominador das viagens. Não foram usadas as views arredondadas.
Nenhum bairro foi excluído e nenhum valor ausente foi imputado.

| Variável | Fórmula | Limite da interpretação |
| --- | --- | --- |
| kg_coletados_hab | peso total / população | Coleta registrada, não geração total de resíduos |
| pct_reciclaveis | 100 × peso reciclável / peso total | Material coletado, não reciclagem efetiva após triagem |
| pct_canceladas | 100 × viagens canceladas / viagens | Regularidade registrada no período |
| ocorrencias_1000_hab | 1.000 × ocorrências / população | Demanda registrada, sujeita a acesso aos canais |

As variáveis ativas foram padronizadas com StandardScaler: z = (valor − média) / desvio padrão.
Isso evita que unidades diferentes dominem a distância. Não foram removidos valores extremos.
Variáveis constantes retiradas do ajuste: {', '.join(removidas) or 'nenhuma'}.

## Escolha de k

Escolhido **k = {res['k']}**, com silhueta média **{met.silhueta:.4f}**.
Foram avaliados k=2 até min(5, n−1, perfis distintos); k=1 aparece apenas no cotovelo.
A regra automática seleciona a maior silhueta entre soluções sem grupos unitários;
em empate exato, prefere k menor. O cotovelo é apresentado para inspeção visual e não
é declarado automaticamente. Melhor k sugerido pela regra: {res['k_sugerido']}.
Uma opção manual --k fica registrada no manifesto e deve ser justificada pela equipe.
Silhueta perto de 1 indica separação, perto de zero indica sobreposição; valores negativos
sugerem bairros próximos a outro grupo. Ela não mede acurácia nem valida a existência de grupos reais.

{tabela(res['metricas'])}

![Cotovelo e silhueta](01_escolha_k.png)

## Resultados e interpretação

Os números dos grupos são identificadores, não um ranking de qualidade. Sua ordenação
usa o centroide de recicláveis quando essa variável varia; caso contrário, a primeira variável ativa.
Centroides abaixo são médias não ponderadas dos bairros, nas unidades originais.

{tabela(centros)}

{chr(10).join(decisoes)}

![Variáveis por bairro](02_perfis_bairros.png)
![Perfis dos grupos](03_centroides.png)

### Atribuição de cada bairro

{tabela(df[['id_bairro', 'bairro', 'regiao', 'grupo'] + FEATURES + ['silhueta_individual']])}

![Visualização PCA](04_projecao_pca.png)

A PCA comprime as variáveis para desenhar os bairros em duas dimensões; **não entra no
ajuste do K-means**. Distâncias aparentes nessa projeção podem ocultar diferenças.

![Silhueta por bairro](05_silhuetas.png)

## Sensibilidade e limites

Dez inicializações adicionais foram comparadas com a partição principal usando o índice
Rand ajustado (ARI). Valor 1 significa partições iguais, independentemente dos nomes dos grupos.
Também foi retirado um bairro de cada vez, refazendo a padronização e mantendo o mesmo k;
o ARI compara a partição dos bairros restantes. Estes diagnósticos não são intervalos de
confiança e não demonstram generalização para cidades reais.

ARI entre sementes: mínimo {res['estabilidade'].ari.min():.4f}, média {res['estabilidade'].ari.mean():.4f}.
ARI sem um bairro: mínimo {res['sensibilidade'].ari.min():.4f}, média {res['sensibilidade'].ari.mean():.4f}.
Resultados completos em estabilidade_sementes.csv e sensibilidade_bairros.csv.

{chr(10).join('- ' + a for a in avisos)}

- K-means impõe uma partição mesmo quando os perfis formam um contínuo. A pequena amostra
  não permite conclusões inferenciais robustas. Variáveis correlacionadas podem reforçar uma dimensão.
- A agregação anual esconde sazonalidade. Os registros cobrem os pontos simulados e não
  toda a geração municipal; o indicador kg/hab não é uma estimativa dessa geração.
- O percentual de recicláveis não mede adesão individual, potencial recuperável nem o indicador ODS 11.6.1.
- Recomendações são hipóteses exploratórias, sem custo, benefício financeiro ou ganho causal estimado.
  Antes do 5W2H, confronte os grupos com rotas, turnos, rejeitos da triagem e conhecimento operacional.

## Reprodução e evidências

Semente: {seed}; n_init=50; max_iter=500; algoritmo Lloyd; inicialização k-means++.
base_bairros.csv preserva a entrada validada; consulta_preparacao.sql preserva a consulta de referência
(no modo CSV, sua execução na origem não é confirmada);
manifesto.json registra hashes, parâmetros, período, data UTC e versões do ambiente.
Os arquivos CSV com centroides, variáveis padronizadas, correlações e diagnósticos
permitem conferir os números sem depender dos gráficos.

## Referências do método

{REFERENCES}
"""


def executar(args: argparse.Namespace) -> Path:
    sql = consulta(args.ano)
    if args.csv:
        base = pd.read_csv(args.csv, encoding="utf-8-sig")
        origem = "CSV exportado do DW (conteúdo não verificado por conexão nesta execução)"
    else:
        base = ler_banco(sql)
        origem = "SELECT no DW do PostgreSQL, em transação somente leitura"
    df, avisos = preparar(base, args.ano)
    res = agrupar(df, args.semente, args.k)
    if res["metricas"].set_index("k").loc[res["k"], "silhueta"] <= 0:
        avisos.append("Silhueta média não positiva: a separação não sustenta perfis bem definidos.")
    if (res["bairros"].silhueta_individual < 0).any():
        avisos.append("Há bairros com silhueta negativa; revise-os antes de usar os grupos em decisões.")
    corr = df[res["ativas"]].corr().abs()
    pares = [f"{a} × {b}" for i, a in enumerate(corr.columns)
             for b in corr.columns[i + 1:] if corr.loc[a, b] >= .85]
    if pares:
        avisos.append("Correlação absoluta de Pearson ≥ 0,85 (alerta descritivo, sem teste de significância): "
                      + "; ".join(pares) + ". Confira possível peso repetido de um mesmo aspecto nas distâncias.")
    # Novo diretório por execução: não substitui resultados anteriores.
    destino = args.saida / f"kmeans_{args.ano}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S_%fZ}"
    destino.mkdir(parents=True, exist_ok=False)
    df[REQUIRED].to_csv(destino / "base_bairros.csv", index=False, encoding="utf-8-sig")
    (destino / "consulta_preparacao.sql").write_text(sql, encoding="utf-8")
    for nome, valor in [("bairros_grupos", res["bairros"]), ("centroides", res["centroides"]),
                        ("avaliacao_k", res["metricas"]), ("estabilidade_sementes", res["estabilidade"]),
                        ("sensibilidade_bairros", res["sensibilidade"]),
                        ("estatisticas_descritivas", df[FEATURES].describe().T),
                        ("correlacoes", df[FEATURES].corr())]:
        valor.to_csv(destino / f"{nome}.csv", index=nome in ["estatisticas_descritivas", "correlacoes"], encoding="utf-8-sig")
    pad = pd.DataFrame(res["x"], columns=res["ativas"])
    pad.insert(0, "id_bairro", df.id_bairro)
    pad.to_csv(destino / "variaveis_padronizadas.csv", index=False, encoding="utf-8-sig")
    # Falha visual não produz um relatório que pareça completo.
    graficos(res, destino, args.ano)
    (destino / "relatorio.md").write_text(relatorio(res, avisos, args.ano, origem, args.semente), encoding="utf-8")
    import matplotlib
    arquivos = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destino.iterdir()) if p.is_file()}
    manifesto = {"status": "concluido", "dados": "sinteticos", "ano": args.ano,
                 "extraido_agora_do_banco": not bool(args.csv), "origem": origem,
                 "criado_utc": datetime.now(timezone.utc).isoformat(), "bairros": len(df),
                 "k": res["k"], "k_sugerido": res["k_sugerido"], "k_manual": args.k,
                 "semente": args.semente, "n_init": 50, "max_iter": 500,
                 "variaveis": res["ativas"], "scaler_media": res["scaler"].mean_.tolist(),
                 "scaler_escala": res["scaler"].scale_.tolist(), "avisos": avisos,
                 "versoes": {"python": platform.python_version(), "numpy": np.__version__,
                             "pandas": pd.__version__, "scikit-learn": sklearn.__version__,
                             "matplotlib": matplotlib.__version__}, "sha256": arquivos}
    (destino / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="CSV produzido pelo SELECT preparar_bairros.sql; dispensa PostgreSQL.")
    parser.add_argument("--ano", type=int, default=2025)
    parser.add_argument("--k", type=int, help="Escolha manual, sujeita aos mesmos critérios de viabilidade.")
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--saida", type=Path, default=SRC.parent / "docs" / "analises" / "kmeans")
    args = parser.parse_args()
    if not 1900 <= args.ano <= 2100 or not 0 <= args.semente < 2**32 - 11:
        parser.error("Use ano entre 1900 e 2100 e semente entre 0 e 4294967284.")
    try:
        pasta = executar(args)
    except (ValueError, OSError, subprocess.TimeoutExpired, ImportError) as exc:
        print(f"Análise não concluída: {exc}", file=sys.stderr)
        return 1
    print(f"Concluído. Relatório: {pasta / 'relatorio.md'}")
    print("Dados sintéticos; a interpretação é exploratória.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
