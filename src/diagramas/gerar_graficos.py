"""Gráficos do DW (dados reais do banco) para o documento. Saída: docs/diagramas/graficos/*.svg e *.png
Uso: python src/diagramas/gerar_graficos.py   (conexão: src/config.py)"""
import os, subprocess, pathlib
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import config  # configuração central (src/config.py)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

SAIDA = config.DOCS / "diagramas" / "graficos"
SAIDA.mkdir(parents=True, exist_ok=True)
INK, MUTED, GRID = "#12343B", "#5C6F73", "#DDE4E5"
plt.rcParams.update({"font.family": "Segoe UI", "svg.fonttype": "none", "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})

def q(sql):
    out = subprocess.run(config.psql_base(so_dados=False) + ["-At", "-F", "|", "-c", sql],
                         capture_output=True, text=True, env=config.ENV, encoding="utf-8", check=True).stdout
    return [l.split("|") for l in out.strip().splitlines()]

def limpa(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)

def salva(fig, nome):
    fig.savefig(SAIDA / f"{nome}.svg", bbox_inches="tight", facecolor="white")
    fig.savefig(SAIDA / f"{nome}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("ok", nome)

# 1) toneladas por mês, por tipo de coleta (empilhado) ----------------------
rows = q("""select t.mes, r.tipo_coleta, round(sum(f.peso_kg)/1000,1)
            from dw.fato_coleta f join dw.dim_tempo t using(sk_tempo) join dw.dim_rota r using(sk_rota)
            group by 1,2 order by 1,2""")
meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
conv = [float(v) for m, t, v in rows if t == "CONVENCIONAL"]
sel = [float(v) for m, t, v in rows if t == "SELETIVA"]
fig, ax = plt.subplots(figsize=(7.2, 3.1))
x = range(12)
ax.bar(x, conv, width=0.62, color=INK, label="Convencional (orgânico + rejeito)", zorder=3)
ax.bar(x, sel, width=0.62, bottom=conv, color="#E6A817", label="Seletiva (recicláveis)", zorder=3,
       edgecolor="white", linewidth=1.5)
for i, (c, s) in enumerate(zip(conv, sel)):
    ax.text(i, c + s + 1, f"{c + s:.0f}", ha="center", fontsize=8, color=MUTED)
ax.set_xticks(list(x)); ax.set_xticklabels(meses, fontsize=9)
ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_ylabel("toneladas", fontsize=9); limpa(ax)
ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
ax.set_title("Toneladas coletadas por mês (2025)", loc="left", fontsize=11, fontweight="bold", color=INK)
salva(fig, "g1_toneladas_por_mes")

# 2) toneladas por tipo de resíduo ------------------------------------------
cores = {"Orgânico": "#7B5B3A", "Rejeito comum": "#6B7B7F", "Papel e papelão": "#2B6CB0",
         "Plástico": "#C0392B", "Vidro": "#2F7D4F", "Metal": "#E6A817"}
rows = q("""select tr.nome, round(sum(peso_kg)/1000,1) from dw.fato_coleta f
            join dw.dim_tipo_residuo tr using(sk_tipo_residuo) group by 1 order by 2 desc""")
nomes = [r[0] for r in rows][::-1]; vals = [float(r[1]) for r in rows][::-1]
fig, ax = plt.subplots(figsize=(7.2, 2.7))
ax.barh(nomes, vals, color=[cores[n] for n in nomes], height=0.58, zorder=3)
for i, v in enumerate(vals):
    ax.text(v + 4, i, f"{v:.0f} t", va="center", fontsize=9, color=INK)
ax.xaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_xlim(0, max(vals) * 1.15); ax.tick_params(axis="y", labelsize=9.5, labelcolor=INK); ax.set_xlabel("toneladas no ano", fontsize=9)
limpa(ax)
ax.set_title("Coleta por tipo de resíduo (cores inspiradas na coleta seletiva)", loc="left", fontsize=11, fontweight="bold", color=INK)
salva(fig, "g2_toneladas_por_tipo")

# 3) para onde foi o material (fato_destinacao) ------------------------------
rows = q("""select d.nome, round(sum(peso_kg)/1000,1) from dw.fato_destinacao f
            join dw.dim_destino d using(sk_destino) group by 1 order by 2 desc""")
nomes = [r[0] for r in rows][::-1]; vals = [float(r[1]) for r in rows][::-1]
tot = sum(vals)
fig, ax = plt.subplots(figsize=(7.2, 2.0))
ax.barh(nomes, vals, color=["#E6A817" if "Cooperativa" in n else INK for n in nomes], height=0.55, zorder=3)
for i, v in enumerate(vals):
    ax.text(v + 4, i, f"{v:.0f} t  ({100 * v / tot:.0f}%)", va="center", fontsize=9, color=INK)
ax.xaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_xlim(0, max(vals) * 1.3); ax.tick_params(axis="y", labelsize=9.5, labelcolor=INK); ax.set_xlabel("toneladas no ano", fontsize=9)
limpa(ax)
ax.set_title("Destinação final do que foi coletado (destaque: material que vai para reciclagem)", loc="left", fontsize=11, fontweight="bold", color=INK)
salva(fig, "g3_destinacao_final")
