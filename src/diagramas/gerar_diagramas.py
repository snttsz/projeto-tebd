"""
Gera os diagramas do projeto (Graphviz) a partir do ESQUEMA REAL do PostgreSQL.

Requisitos : Graphviz (dot/neato), psql, banco 'cidades_sustentaveis' carregado
Uso        : python gerar_diagramas.py
Uso        : python src/diagramas/gerar_diagramas.py
Saída      : docs/diagramas/*.svg e *.png  (código-fonte .dot em src/diagramas/dot/)
Decisões   : ver docs/pesquisas/01_pesquisa_diagramas_ER.md
Conexão    : src/config.py (variáveis de ambiente ou arquivo .env)
"""
import os, subprocess, sys, html, pathlib
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import config  # configuração central (src/config.py)

AQUI = pathlib.Path(__file__).resolve().parent
DOTDIR = AQUI / "dot"
DOTDIR.mkdir(exist_ok=True)
SAIDA = config.DOCS / "diagramas"
SAIDA.mkdir(parents=True, exist_ok=True)
DOT, NEATO = config.DOT, config.NEATO
if not (DOT and NEATO):
    sys.exit("Graphviz não encontrado. Instale-o ou defina DOT e NEATO no .env.")

# ---- identidade visual -------------------------------------------------
INK, PAPER, GRID = "#12343B", "#FFFFFF", "#C9D3D6"
COR = {  # cor por subárea (código de cores da coleta seletiva como inspiração)
    "A": "#2F7D4F",  # planejamento e execução  - verde
    "B": "#2B6CB0",  # pesagem e destinação     - azul
    "C": "#B45309",  # território e cidadão     - âmbar escuro
    "FATO": "#12343B",
    "DIM": "#2F7D4F",
}
FONTE = "Segoe UI"
MONO = "Consolas"

# ---- leitura do catálogo -----------------------------------------------
SQL = r"""
SELECT n.nspname, c.relname, a.attnum, a.attname, format_type(a.atttypid,a.atttypmod),
 a.attnotnull::int,
 EXISTS(SELECT 1 FROM pg_constraint k WHERE k.conrelid=c.oid AND k.contype='p' AND a.attnum=ANY(k.conkey))::int,
 COALESCE((SELECT k.confrelid::regclass::text||'.'||(SELECT attname FROM pg_attribute WHERE attrelid=k.confrelid AND attnum=k.confkey[1])
           FROM pg_constraint k WHERE k.conrelid=c.oid AND k.contype='f' AND k.conkey[1]=a.attnum AND array_length(k.conkey,1)=1 LIMIT 1),''),
 EXISTS(SELECT 1 FROM pg_constraint k WHERE k.conrelid=c.oid AND k.contype='u' AND k.conkey=ARRAY[a.attnum])::int
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
WHERE n.nspname IN ('oltp','dw') AND c.relkind='r' ORDER BY n.nspname, c.oid, a.attnum;
"""

def carregar():
    out = subprocess.run(config.psql_base() + ["-c", SQL], capture_output=True, text=True,
                         env=config.ENV, encoding="utf-8", check=True).stdout
    tabelas = {}
    for linha in out.strip().splitlines():
        sch, tab, _, col, tipo, nn, pk, fk, uq = linha.split("\t")
        fk_tab, fk_col = (fk.split(".")[-2:] if fk else ("", ""))
        tabelas.setdefault(f"{sch}.{tab}", []).append(dict(
            col=col, tipo=abrevia(tipo), nn=nn == "1", pk=pk == "1", fk_tab=fk_tab, fk_col=fk_col, uq=uq == "1"))
    return tabelas

def abrevia(t):
    return (t.replace("character varying", "varchar").replace("character(", "char(")
             .replace("timestamp without time zone", "timestamp").replace("time without time zone", "time")
             .replace("boolean", "bool").replace("smallint", "int2").replace("integer", "int4"))

def esc(s):
    return html.escape(str(s), quote=True)

# ---- tabela HTML (nó Graphviz) -----------------------------------------
def no_tabela(chave, cols, cor, titulo=None, atalho=False, mostrar=None, subtitulo=None, cols_fk_portas=True):
    """Nó plaintext com tabela HTML. 'mostrar' limita as colunas (ex.: atalhos)."""
    t = titulo or chave.split(".")[-1]
    borda = f'COLOR="{cor}"' + (' STYLE="dashed"' if atalho else "")
    head_bg = "#FFFFFF" if atalho else cor
    head_fg = cor if atalho else "#FFFFFF"
    linhas = [f'<TR><TD COLSPAN="3" BGCOLOR="{head_bg}" ALIGN="LEFT" CELLPADDING="5">'
              f'<FONT FACE="{FONTE} bold" COLOR="{head_fg}" POINT-SIZE="12"><B>{esc(t)}</B></FONT>'
              + (f' <FONT FACE="{FONTE}" COLOR="{head_fg}" POINT-SIZE="8">  atalho</FONT>' if atalho else "")
              + '</TD></TR>']
    if subtitulo:
        linhas.append(f'<TR><TD COLSPAN="3" ALIGN="LEFT" BGCOLOR="#F1F5F5"><FONT FACE="{FONTE}" POINT-SIZE="8" COLOR="#4A5B5F"><I>{esc(subtitulo)}</I></FONT></TD></TR>')
    for c in cols:
        if mostrar is not None and c["col"] not in mostrar:
            continue
        badge = ("PK" if c["pk"] else "") + ("FK" if c["fk_tab"] else "")
        badge = "PK·FK" if c["pk"] and c["fk_tab"] else badge
        cor_b = {"PK": "#8A5A00", "FK": "#2B6CB0", "PK·FK": "#6B3FA0"}.get(badge, "#FFFFFF")
        peso_i, peso_f = ("<B>", "</B>") if c["pk"] else ("", "")
        nome = f'{peso_i}{esc(c["col"])}{peso_f}'
        if not c["nn"] and not c["pk"]:
            nome += f' <FONT COLOR="#8A9A9E" POINT-SIZE="8">?</FONT>'
        porta = ""
        linhas.append(
            f'<TR><TD ALIGN="LEFT" WIDTH="28" PORT="{c["col"]}_l"><FONT FACE="{MONO}" POINT-SIZE="8" COLOR="{cor_b}">{("<B>"+badge+"</B>") if badge else "&nbsp;"}</FONT></TD>'
            f'<TD ALIGN="LEFT" WIDTH="118"><FONT FACE="{FONTE}" POINT-SIZE="10" COLOR="{INK}">{nome}</FONT></TD>'
            f'<TD ALIGN="LEFT" WIDTH="84" PORT="{c["col"]}_r"><FONT FACE="{MONO}" POINT-SIZE="8" COLOR="#6B7B7F">{esc(c["tipo"])}</FONT></TD></TR>')
    return (f'"{chave}" [label=<<TABLE BORDER="1" {borda} CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" BGCOLOR="#FFFFFF">'
            + "".join(linhas) + "</TABLE>>];")

def seta(pai, col_pai, filho, col_fk, opcional, rotulo=None, extra=""):
    """Pai -> filho. Cardinalidade: pai (exatamente um | zero ou um); filho (zero ou muitos)."""
    cauda = "teeodot" if opcional else "teetee"
    lab = f', label=<<FONT FACE="{FONTE}" POINT-SIZE="9" COLOR="#3A4C50"><I>{esc(rotulo)}</I></FONT>>' if rotulo else ""
    return (f'"{pai}":"{col_pai}":e -> "{filho}":"{col_fk}":w '
            f'[dir=both, arrowtail={cauda}, arrowhead=crowodot, color="{INK}", penwidth=1.2, '
            f'arrowsize=1.1{lab}{extra}];')

def renderizar(nome, dot_src, engine=DOT, dpi=200):
    src = DOTDIR / f"{nome}.dot"
    src.write_text(dot_src, encoding="utf-8")
    for fmt, extra in (("svg", []), ("png", [f"-Gdpi={dpi}"])):
        r = subprocess.run([engine, f"-T{fmt}", *extra, str(src), "-o", str(SAIDA / f"{nome}.{fmt}")],
                           capture_output=True, text=True)
        if r.returncode:
            print("ERRO", nome, r.stderr[:400]); sys.exit(1)
        if r.stderr.strip():
            print("aviso", nome, r.stderr.strip()[:200])
    print("ok", nome)

CAB = f'''graph [fontname="{FONTE}", bgcolor="#FFFFFF", pad=0.4, labelloc=t, labeljust=l, fontsize=15, fontcolor="{INK}"];
node [shape=plaintext, fontname="{FONTE}"];
edge [fontname="{FONTE}"];'''

def cabecalho(titulo, sub, estrela=False):
    leg = ("<B>PK</B> chave primária  ·  <B>FK</B> chave estrangeira  ·  ? aceita NULL  ·  "
           + ("cabeçalho escuro = FATO · verde = DIMENSÃO" if estrela else "tracejado = atalho de outra subárea")
           + "  ·  1 ‖ ○&lt; = um para zero ou muitos  ·  ‖○ = FK opcional")
    return (f'label=<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="2"><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="18" COLOR="{INK}"><B>{esc(titulo)}</B></FONT></TD></TR>'
            f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#4A5B5F">{esc(sub)}</FONT></TD></TR>'
            f'<TR><TD ALIGN="LEFT"><FONT FACE="{MONO}" POINT-SIZE="8" COLOR="#6B7B7F">{leg}</FONT></TD></TR></TABLE>>;')

def legenda_cardinalidade(prefixo="lg"):
    """Legenda compacta de pé-de-galinha."""
    itens = [("teetee", "crowodot", "1 : 0..*  (um para zero ou muitos)"),
             ("teeodot", "crowodot", "0..1 : 0..*  (FK opcional)")]
    s = f'subgraph cluster_{prefixo} {{ label=<<FONT POINT-SIZE="9" COLOR="{INK}"><B>Legenda</B></FONT>>; style="rounded"; color="{GRID}"; fontname="{FONTE}"; labeljust=l;\n'
    for i, (a, b, t) in enumerate(itens):
        s += (f'{prefixo}a{i} [shape=point, width=0.01, label=""]; {prefixo}b{i} [shape=plaintext, label=<<FONT POINT-SIZE="9" COLOR="#3A4C50">{esc(t)}</FONT>>];\n'
              f'{prefixo}a{i} -> {prefixo}b{i} [dir=both, arrowtail={a}, arrowhead={b}, color="{INK}", len=0.6, minlen=1];\n')
    s += (f'{prefixo}k [shape=plaintext, label=<<FONT FACE="{MONO}" POINT-SIZE="8" COLOR="#3A4C50">'
          f'<B>PK</B> chave primária  ·  <B>FK</B> chave estrangeira  ·  ? aceita NULL  ·  linha tracejada = atalho de outra subárea</FONT>>];\n')
    return s + "}\n"

# ======================================================================
# Diagramas com POSIÇÕES FIXAS (neato, pos em polegadas com "!")
# Regra: pai à esquerda/acima, filho à direita/abaixo, sem cruzamentos.
# ======================================================================
def ponto(x, y):
    return f'pos="{x},{y}!"'

def aresta(pai, col_pai, lado_pai, filho, col_fk, lado_filho, opcional, rotulo=None, ns_pai="oltp", ns_filho="oltp"):
    cauda = "teeodot" if opcional else "teetee"
    lab = (f', label=<<FONT FACE="{FONTE}" POINT-SIZE="9" COLOR="#3A4C50"><I>{esc(rotulo)}</I></FONT>>' if rotulo else "")
    sp = "l" if lado_pai == "w" else "r"
    sf = "l" if lado_filho == "w" else "r"
    return (f'"{ns_pai}.{pai}":"{col_pai}_{sp}":{lado_pai} -> "{ns_filho}.{filho}":"{col_fk}_{sf}":{lado_filho} '
            f'[dir=both, arrowtail={cauda}, arrowhead=crowodot, color="{INK}", penwidth=1.3, arrowsize=1.1{lab}];')

def abre(titulo, sub, estrela=False):
    return (f'digraph G {{ layout=neato; splines=line; overlap=true; pad=0.4;\n{CAB}\n'
            f'{cabecalho(titulo, sub, estrela)} labelloc=t; labeljust=l;\n')

def tabela_pos(T, tb, cor, x, y, atalho=False, mostrar=None, ns="oltp", **kw):
    chave = f"{ns}.{tb}"
    if atalho:
        corig = COR[[k for k, v in ORIGEM.items() if tb in v][0]]
        n = no_tabela(chave, T[f"oltp.{tb}"], corig, titulo=tb, atalho=True, mostrar=mostrar)
    else:
        n = no_tabela(chave, T[f"{ns}.{tb}"], cor, titulo=tb, **kw)
    return n.replace("];", f", {ponto(x, y)}];", 1) + "\n"

ORIGEM = {"A": ["rota", "coleta", "coleta_equipe", "veiculo", "funcionario"],
          "B": ["coleta_item", "descarga", "tipo_residuo", "destino_final"],
          "C": ["bairro", "ponto_coleta", "ocorrencia"]}

def diagrama_conceitual(T):
    cor_de = {e: COR[k] for k, v in ORIGEM.items() for e in v}
    pos = {  # grade desenhada à mão (polegadas)
        "bairro": (0, 0), "ponto_coleta": (4.2, 3.0), "ocorrencia": (4.2, 0.4),
        "rota": (4.2, -2.4), "coleta": (8.6, -2.4), "veiculo": (8.6, -4.0), "funcionario": (4.2, -5.4),
        "coleta_equipe": (13.0, -5.2), "coleta_item": (8.6, 1.0), "tipo_residuo": (13.0, 3.0),
        "descarga": (13.0, -0.4), "destino_final": (17.4, -0.4),
    }
    s = abre("Modelo conceitual · visão geral",
             "12 entidades em 3 subáreas (cor da borda) · notação pé-de-galinha · atributos nos diagramas das subáreas")
    for e, (x, y) in pos.items():
        assoc = e == "coleta_equipe"
        extra = '<BR/><FONT POINT-SIZE="8">associativa N:N</FONT>' if assoc else ""
        s += (f'"{e}" [shape=box, style="{"rounded,dashed" if assoc else "rounded,filled"}", fillcolor="{cor_de[e]}14", '
              f'color="{cor_de[e]}", penwidth=2, fontcolor="{INK}", fontsize=13, width=1.9, height=0.62, fixedsize=true, '
              f'label=<<B>{e}</B>{extra}>, {ponto(x, y)}];\n')
    rels = [("bairro", "ponto_coleta", False, "contém"), ("bairro", "ocorrencia", False, "origina"),
            ("bairro", "rota", False, "é atendido por"), ("ponto_coleta", "ocorrencia", True, "é citado em"),
            ("rota", "coleta", False, "é executada em"), ("veiculo", "coleta", False, "realiza"),
            ("funcionario", "coleta", False, "dirige"), ("coleta", "coleta_equipe", False, "tem equipe"),
            ("funcionario", "coleta_equipe", False, "integra"), ("coleta", "coleta_item", False, "pesa"),
            ("ponto_coleta", "coleta_item", False, "origina"), ("tipo_residuo", "coleta_item", False, "classifica"),
            ("coleta", "descarga", False, "gera"), ("destino_final", "descarga", False, "recebe"),
            ("tipo_residuo", "descarga", False, "classifica")]
    for p, f, op, v in rels:
        s += (f'"{p}" -> "{f}" [dir=both, arrowtail={"teeodot" if op else "teetee"}, arrowhead=crowodot, color="{INK}", '
              f'penwidth=1.3, arrowsize=1.1, label=<<FONT POINT-SIZE="10" COLOR="#3A4C50"><I> {esc(v)} </I></FONT>>];\n')
    for i, (k, tit) in enumerate([("A", "A · Planejamento e execução"), ("B", "B · Pesagem e destinação"),
                                  ("C", "C · Território e cidadão")]):
        s += (f'"leg{k}" [shape=box, style="rounded,filled", fillcolor="{COR[k]}14", color="{COR[k]}", penwidth=2, width=2.6, '
              f'height=0.4, fixedsize=true, fontsize=10, fontcolor="{INK}", label="{tit}", {ponto(i * 3.0, -7.2)}];\n')
    s += "}\n"
    renderizar("01_er_conceitual_visao_geral", s, engine=NEATO)

def diagramas_subareas(T):
    cA, cB, cC = COR["A"], COR["B"], COR["C"]
    # ---- A: planejamento e execução ------------------------------------
    s = abre("Subárea A · Planejamento e execução da coleta",
             "Quem coleta, com qual veículo, em qual rota e em qual dia. Cada execução de uma rota é uma linha de coleta.")
    s += tabela_pos(T, "bairro", cA, -1.2, 3.2, atalho=True, mostrar=["id_bairro", "nome", "regiao"], ns="atalho")
    s += tabela_pos(T, "rota", cA, 5.0, 3.2)
    s += tabela_pos(T, "veiculo", cA, 5.0, -0.1)
    s += tabela_pos(T, "funcionario", cA, 5.0, -3.2)
    s += tabela_pos(T, "coleta", cA, 10.0, 1.2)
    s += tabela_pos(T, "coleta_equipe", cA, 15.0, -3.6)
    s += aresta("bairro", "id_bairro", "e", "rota", "id_bairro", "w", False, "é atendido por", "atalho", "oltp") + "\n"
    s += aresta("rota", "id_rota", "e", "coleta", "id_rota", "w", False, "é executada em") + "\n"
    s += aresta("veiculo", "id_veiculo", "e", "coleta", "id_veiculo", "w", False, "realiza") + "\n"
    s += aresta("funcionario", "id_funcionario", "e", "coleta", "id_motorista", "w", False, "dirige (motorista)") + "\n"
    s += aresta("coleta", "id_coleta", "e", "coleta_equipe", "id_coleta", "w", False, "tem equipe") + "\n"
    s += aresta("funcionario", "id_funcionario", "e", "coleta_equipe", "id_funcionario", "w", False, "integra") + "\n}\n"
    renderizar("02_er_logico_A_planejamento_execucao", s, engine=NEATO)
    # ---- B: pesagem e destinação ----------------------------------------
    s = abre("Subárea B · Pesagem e destinação",
             "O que foi pesado em cada ponto, por tipo de resíduo, e para onde foi descarregado.")
    s += tabela_pos(T, "ponto_coleta", cC, -5.2, 0.0, atalho=True, mostrar=["id_ponto", "id_bairro", "tipo_ponto"], ns="atalho")
    s += tabela_pos(T, "coleta_item", cB, 0, 0.0)
    s += tabela_pos(T, "coleta", cA, 5.0, 4.2, atalho=True, mostrar=["id_coleta", "id_rota", "data_coleta", "status"], ns="atalho")
    s += tabela_pos(T, "tipo_residuo", cB, 5.0, -4.4)
    s += tabela_pos(T, "descarga", cB, 10.0, 0.0)
    s += tabela_pos(T, "destino_final", cB, 15.0, 0.0)
    s += aresta("ponto_coleta", "id_ponto", "e", "coleta_item", "id_ponto", "w", False, "origina", "atalho", "oltp") + "\n"
    s += aresta("coleta", "id_coleta", "w", "coleta_item", "id_coleta", "e", False, "pesa", "atalho", "oltp") + "\n"
    s += aresta("tipo_residuo", "id_tipo_residuo", "w", "coleta_item", "id_tipo_residuo", "e", False, "classifica") + "\n"
    s += aresta("coleta", "id_coleta", "e", "descarga", "id_coleta", "w", False, "gera", "atalho", "oltp") + "\n"
    s += aresta("tipo_residuo", "id_tipo_residuo", "e", "descarga", "id_tipo_residuo", "w", False, "classifica") + "\n"
    s += aresta("destino_final", "id_destino", "w", "descarga", "id_destino", "e", False, "recebe") + "\n}\n"
    renderizar("03_er_logico_B_pesagem_destinacao", s, engine=NEATO)
    # ---- C: território e cidadão ----------------------------------------
    s = abre("Subárea C · Território e atendimento ao cidadão",
             "Base territorial do município e as ocorrências registradas pelos moradores.")
    s += tabela_pos(T, "bairro", cC, 0, 0)
    s += tabela_pos(T, "ocorrencia", cC, 5.4, -0.9)
    s += tabela_pos(T, "ponto_coleta", cC, 10.8, 2.6)
    s += aresta("bairro", "id_bairro", "e", "ponto_coleta", "id_bairro", "w", False, "contém") + "\n"
    s += aresta("bairro", "id_bairro", "e", "ocorrencia", "id_bairro", "w", False, "origina") + "\n"
    s += aresta("ponto_coleta", "id_ponto", "w", "ocorrencia", "id_ponto", "e", True, "é citado em") + "\n}\n"
    renderizar("04_er_logico_C_territorio_cidadao", s, engine=NEATO)

def estrela(T, nome, titulo, sub, fato, dims, grao, medidas, pos, papeis=None):
    """Estrela: fato no centro, dimensões em volta; linhas retas até a borda das tabelas (sem cruzar)."""
    s = abre(titulo, sub, estrela=True)
    s += tabela_pos(T, fato, COR["FATO"], *pos[fato], ns="dw", subtitulo="GRÃO: " + grao)
    for d in dims:
        s += tabela_pos(T, d, COR["DIM"], *pos[d], ns="dw")
    papeis = papeis or {}
    for d in dims:
        for c in T[f"dw.{fato}"]:
            if c["fk_tab"] != d:
                continue
            lab = f'<FONT POINT-SIZE="10" COLOR="#3A4C50"><I> {esc(c["col"])} </I></FONT>'
            cauda = "teeodot" if not c["nn"] else "teetee"
            if c["col"] in papeis:  # papel adicional: desvio por nó invisível
                mx, my = papeis[c["col"]]
                s += (f'"via_{c["col"]}" [shape=point, width=0.01, style=invis, {ponto(mx, my)}];\n'
                      f'"dw.{d}" -> "via_{c["col"]}" [dir=back, arrowtail={cauda}, color="{INK}", penwidth=1.3];\n'
                      f'"via_{c["col"]}" -> "dw.{fato}" [dir=forward, arrowhead=crowodot, color="{INK}", penwidth=1.3, arrowsize=1.1, label=<{lab}>];\n')
            else:
                s += (f'"dw.{d}" -> "dw.{fato}" [dir=both, arrowtail={cauda}, arrowhead=crowodot, color="{INK}", '
                      f'penwidth=1.3, arrowsize=1.1, label=<{lab}>];\n')
    nx, ny = pos["nota"]
    linhas = "".join(f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="{INK}">{m}</FONT></TD></TR>' for m in medidas)
    s += (f'nota [shape=note, style=filled, fillcolor="#FFF7E0", color="#B45309", {ponto(nx, ny)}, '
          f'label=<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="1"><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="{INK}"><B>Medidas e decisões</B></FONT></TD></TR>'
          f'{linhas}</TABLE>>];\n}}\n')
    renderizar(nome, s, engine=NEATO)

def diagramas_estrela(T):
    estrela(T, "05_estrela_1_coleta", "Estrela 1 · Coleta de resíduos",
            "Quanto de cada tipo de resíduo foi coletado, onde, quando, por qual rota, veículo e motorista.",
            "fato_coleta", ["dim_tempo", "dim_local", "dim_tipo_residuo", "dim_rota", "dim_veiculo", "dim_funcionario"],
            "um tipo de resíduo coletado em um ponto, durante uma coleta",
            ["peso_kg · aditiva (soma em qualquer dimensão)", "qtd_registros · aditiva (contagem de atendimentos)",
             "dim_funcionario atua no papel de <I>motorista</I>", "SCD: dimensões tipo 1 (sobrescreve o valor)"],
            {"fato_coleta": (0, 0), "dim_tempo": (-5.6, 4.4), "dim_local": (0, 4.9), "dim_tipo_residuo": (5.6, 4.4),
             "dim_rota": (-5.6, -4.3), "dim_veiculo": (0, -4.0), "dim_funcionario": (5.6, -4.3), "nota": (-9.6, 0)})
    estrela(T, "08_estrela_4_viagem", "Estrela 4 · Viagem de coleta (produtividade)",
            "Cada coleta como uma viagem do veículo: quilômetros, duração, peso total, pontos atendidos e cancelamentos.",
            "fato_viagem", ["dim_tempo", "dim_rota", "dim_veiculo", "dim_funcionario"],
            "uma coleta (viagem de um veículo em uma rota, em uma data), inclusive as canceladas",
            ["km_percorridos, duracao_min, peso_total_kg, qtd_pontos_atendidos · aditivas",
             "qtd_cancelada · aditiva (0/1): SUM = nº de cancelamentos",
             "km e duração são NULL nas coletas canceladas (não rodaram)",
             "Base do dashboard tático: kg/km, kg/h, taxa de cancelamento"],
            {"fato_viagem": (0, 0), "dim_tempo": (-5.4, 3.9), "dim_rota": (0, 4.9), "dim_veiculo": (5.6, 3.4),
             "dim_funcionario": (0, -3.4), "nota": (-9.4, -0.6)})
    estrela(T, "06_estrela_2_destinacao", "Estrela 2 · Destinação final",
            "Quanto de cada tipo de resíduo chegou a cada destino: aterro, cooperativa, usina ou central de perigosos.",
            "fato_destinacao", ["dim_tempo", "dim_destino", "dim_tipo_residuo", "dim_rota", "dim_veiculo"],
            "um tipo de resíduo descarregado em um destino, por coleta",
            ["peso_kg · aditiva", "Dimensões conformes com a Estrela 1:", "tempo, tipo de resíduo, rota e veículo"],
            {"fato_destinacao": (0, 0), "dim_tempo": (-5.4, 3.8), "dim_destino": (0, 3.4), "dim_tipo_residuo": (5.4, 3.8),
             "dim_rota": (-3.6, -4.0), "dim_veiculo": (3.6, -3.7), "nota": (-9.2, -0.4)})
    estrela(T, "07_estrela_3_ocorrencias", "Estrela 3 · Atendimento ao cidadão (ocorrências)",
            "Quantas ocorrências, de que tipo e canal, em que local, e quanto tempo levou para resolvê-las.",
            "fato_ocorrencia", ["dim_tempo", "dim_local", "dim_ocorrencia"],
            "uma ocorrência registrada por um cidadão",
            ["qtd_ocorrencias · aditiva", "tempo_resolucao_horas · semiaditiva (usar média, não soma)",
             "dim_tempo em 2 papéis: abertura e fechamento", "(fechamento NULL = ocorrência em aberto)"],
            {"fato_ocorrencia": (0, 0), "dim_tempo": (-5.0, 3.6), "dim_local": (5.0, 3.0), "dim_ocorrencia": (0, -3.6),
             "nota": (-9.2, -1.6)},
            papeis={"sk_tempo_fechamento": (-3.7, 0.5)})

# ----------------------------------------------------------------------
def diagrama_arquitetura():
    s = f'''digraph G {{ rankdir=LR; nodesep=0.5; ranksep=0.7; splines=ortho;
{CAB}
label=<<FONT POINT-SIZE="16"><B>Arquitetura do ecossistema de dados</B></FONT><BR ALIGN="LEFT"/><FONT POINT-SIZE="10" COLOR="#4A5B5F">Mesmo SGBD (PostgreSQL), dois ambientes lógicos: operação (oltp) e análise (dw)</FONT><BR ALIGN="LEFT"/>>;
node [shape=box, style="rounded,filled", fontsize=11, margin="0.18,0.1", penwidth=1.6, fontcolor="{INK}"];
edge [color="{INK}", penwidth=1.4, arrowsize=0.9];
subgraph cluster_fontes {{ label=<<FONT POINT-SIZE="10" COLOR="#4A5B5F"><B>QUEM ALIMENTA</B></FONT>>; style="rounded"; color="{GRID}";
  op [label=<<B>Equipe operacional</B><BR/><FONT POINT-SIZE="9">motoristas · coletores · fiscais</FONT>>, fillcolor="#FFFFFF", color="{COR['A']}"];
  ci [label=<<B>Cidadão</B><BR/><FONT POINT-SIZE="9">app · telefone · presencial</FONT>>, fillcolor="#FFFFFF", color="{COR['C']}"];
  pe [label=<<B>Pesagem</B><BR/><FONT POINT-SIZE="9">balança no destino</FONT>>, fillcolor="#FFFFFF", color="{COR['B']}"];
}}
oltp [label=<<B>OLTP</B> · schema oltp<BR/><FONT POINT-SIZE="9">12 tabelas · 3FN<BR/>registro diário</FONT>>, fillcolor="{COR['A']}1A", color="{COR['A']}"];
etl [label=<<B>ETL em SQL</B><BR/><FONT POINT-SIZE="9">dimensões → fatos<BR/>chaves substitutas</FONT>>, shape=box, fillcolor="#FFF7E0", color="#B45309"];
dw [label=<<B>OLAP</B> · schema dw<BR/><FONT POINT-SIZE="9">8 dimensões · 4 fatos<BR/>esquema estrela</FONT>>, fillcolor="{COR['B']}1A", color="{COR['B']}"];
subgraph cluster_uso {{ label=<<FONT POINT-SIZE="10" COLOR="#4A5B5F"><B>QUEM CONSOME (entrega de 06/11)</B></FONT>>; style="rounded"; color="{GRID}";
  d1 [label=<<B>Dashboard operacional</B><BR/><FONT POINT-SIZE="9">dia a dia · supervisores</FONT>>, fillcolor="#FFFFFF", color="{INK}"];
  d2 [label=<<B>Dashboard tático</B><BR/><FONT POINT-SIZE="9">rotas e turnos · coordenação</FONT>>, fillcolor="#FFFFFF", color="{INK}"];
  d3 [label=<<B>Dashboard estratégico</B><BR/><FONT POINT-SIZE="9">metas e expansão · secretaria</FONT>>, fillcolor="#FFFFFF", color="{INK}"];
  mi [label=<<B>Mineração de dados</B><BR/><FONT POINT-SIZE="9">análise exploratória</FONT>>, fillcolor="#FFFFFF", color="{INK}"];
}}
op -> oltp; ci -> oltp; pe -> oltp; oltp -> etl -> dw; dw -> d1; dw -> d2; dw -> d3; dw -> mi;
d3 -> pl [style=dashed];
pl [label=<<B>Plano de ação 5W2H</B><BR/><FONT POINT-SIZE="9">decisões</FONT>>, fillcolor="#FFFFFF", color="#B45309", shape=box];
}}'''
    renderizar("00_arquitetura_ecossistema", s)

def diagrama_fluxo():
    s = f'''digraph G {{ rankdir=TB; nodesep=0.7; ranksep=0.75; splines=ortho; newrank=true;
{CAB}
label=<<FONT POINT-SIZE="16"><B>Fluxo do resíduo e dos dados</B></FONT><BR ALIGN="LEFT"/><FONT POINT-SIZE="10" COLOR="#4A5B5F">Do ponto de coleta ao destino final; cada etapa vira registro no banco (tabela entre parênteses)</FONT><BR ALIGN="LEFT"/>>;
node [shape=box, style="rounded,filled", fillcolor="#FFFFFF", fontsize=12, penwidth=1.8, margin="0.2,0.12", fontcolor="{INK}", width=2.5];
edge [color="{INK}", penwidth=1.5, arrowsize=0.9, fontsize=10, fontcolor="#3A4C50"];
g [label=<<B>1 · Geração</B><BR/><FONT POINT-SIZE="10">moradores, comércio, PEV<BR/>(ponto_coleta)</FONT>>, color="{COR['C']}"];
p [label=<<B>2 · Planejamento</B><BR/><FONT POINT-SIZE="10">rota semanal por bairro<BR/>(rota)</FONT>>, color="{COR['A']}"];
c [label=<<B>3 · Coleta</B><BR/><FONT POINT-SIZE="10">veículo + motorista + equipe<BR/>(coleta, coleta_equipe)</FONT>>, color="{COR['A']}"];
w [label=<<B>4 · Pesagem por ponto</B><BR/><FONT POINT-SIZE="10">peso_kg por tipo de resíduo<BR/>(coleta_item)</FONT>>, color="{COR['B']}"];
d [label=<<B>5 · Descarga</B><BR/><FONT POINT-SIZE="10">destino conforme o tipo<BR/>(descarga)</FONT>>, color="{COR['B']}"];
f1 [label=<<B>Aterro</B><BR/><FONT POINT-SIZE="10">rejeito</FONT>>, fillcolor="#F1F5F5", color="{INK}", width=1.8];
f2 [label=<<B>Cooperativa</B><BR/><FONT POINT-SIZE="10">recicláveis</FONT>>, fillcolor="#F1F5F5", color="{INK}", width=1.8];
f3 [label=<<B>Usina de compostagem</B><BR/><FONT POINT-SIZE="10">orgânico</FONT>>, fillcolor="#F1F5F5", color="{INK}", width=1.8];
o [label=<<B>Ocorrência do cidadão</B><BR/><FONT POINT-SIZE="10">reclamação / solicitação<BR/>(ocorrencia)</FONT>>, color="{COR['C']}", style="rounded,filled,dashed"];
r [label=<<B>Resolução</B><BR/><FONT POINT-SIZE="10">tempo_resolucao_horas</FONT>>, color="{COR['C']}", style="rounded,filled,dashed"];
{{rank=same; g; p; c;}}
{{rank=same; w; d;}}
{{rank=same; f1; f2; f3;}}
{{rank=same; o; r;}}
g -> p [label=" define "]; p -> c [label=" executa "];
c -> w; w -> d; d -> f1; d -> f2; d -> f3;
g -> o [style=dashed, label=" se a coleta falhar "]; o -> r [style=dashed]; r -> p [style=dashed, label=" ajusta a rota "];
}}'''
    renderizar("09_fluxo_do_residuo", s)

if __name__ == "__main__":
    T = carregar()
    diagrama_arquitetura()
    diagrama_fluxo()
    diagrama_conceitual(T)
    diagramas_subareas(T)
    diagramas_estrela(T)
