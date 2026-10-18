"""
Gera o PDF da entrega a partir do Markdown (identidade visual "Ciclo Urbano").

Requisitos : pip install markdown pymupdf   +   Microsoft Edge (ou Chrome) instalado
Uso        : python src/documentos/gerar_pdf.py caminho/do/arquivo.md   (normalmente chamado por montar_entregas.py)
Entrada    : um .md; as imagens são resolvidas a partir da pasta do próprio .md
Saída      : mesmo nome, extensão .pdf, na mesma pasta

Convenções do Markdown:
  <!-- INICIO -->          o que vem antes vira a CAPA (título + tabela de metadados)
  ## N · Título            abre um capítulo numerado (página nova, número grande)
  ## Título                seção sem número (ex.: Resumo executivo, Referências)
  *Neste capítulo: ...*    primeiro parágrafo vira o "lead" do capítulo
  > [!NOTE] / [!TIP] / [!IMPORTANT] / [!WARNING]   caixas de destaque
  ![Figura N · legenda](caminho.png)               figura numerada com legenda
  ## N · Dicionário de dados   esse capítulo é impresso em página paisagem
"""
import html, os, re, subprocess, sys, pathlib, tempfile
import markdown
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import config  # configuração central (src/config.py)

if len(sys.argv) < 2:
    sys.exit("Uso: python src/documentos/gerar_pdf.py caminho/do/arquivo.md")
MD = pathlib.Path(sys.argv[1]).resolve()
PDF = MD.with_suffix(".pdf")
EDGE = config.NAVEGADOR
PAPEL_LAND = "Dicionário de dados"   # capítulos com este título saem em página paisagem

# ---- cores (coleta seletiva: papel azul, plástico vermelho, vidro verde, metal amarelo, orgânico marrom, rejeito cinza)
DONUT = [("Orgânico", 354.6, "#7B5B3A"), ("Rejeito comum", 332.2, "#6B7B7F"), ("Papel", 59.6, "#2B6CB0"),
         ("Vidro", 58.5, "#2F7D4F"), ("Metal", 57.7, "#E6A817"), ("Plástico", 57.7, "#C0392B")]


def donut_svg(tam=300):
    import math
    cx = cy = tam / 2
    r, w = tam * 0.38, tam * 0.15
    total = sum(v for _, v, _ in DONUT)
    ang, partes = -90.0, []
    for nome, v, cor in DONUT:
        a1 = ang + 360 * v / total - 1.8
        x0, y0 = cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang))
        x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
        grande = 1 if (a1 - ang) > 180 else 0
        partes.append(f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 {grande} 1 {x1:.1f},{y1:.1f}" '
                      f'fill="none" stroke="{cor}" stroke-width="{w:.1f}" stroke-linecap="butt"/>')
        ang += 360 * v / total
    return (f'<svg viewBox="0 0 {tam} {tam}" xmlns="http://www.w3.org/2000/svg">{"".join(partes)}'
            f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-family="Sora" font-weight="700" font-size="34" fill="#F6F3EC">920 t</text>'
            f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" font-family="Sora" font-size="11" fill="#9FB4B8" letter-spacing="1.5">COLETADAS EM 2025</text></svg>')


CSS = r"""
:root{--ink:#12343B;--ink2:#2A4A51;--leaf:#2F7D4F;--amber:#E6A817;--amberd:#B45309;--paper:#F6F3EC;--mut:#5C6F73;--line:#D8DFDD;--blue:#2B6CB0}
@page{size:A4;margin:24mm 18mm 20mm 18mm;
  @top-left{content:"CICLO URBANO";font:600 7.5pt Sora,'Segoe UI',sans-serif;letter-spacing:.16em;color:#12343B;border-bottom:.6pt solid #D8DFDD;padding-bottom:2mm;vertical-align:bottom}
  @top-right{content:"Entrega parcial · 19/10/2026";font:400 7.5pt 'Source Serif 4',Georgia,serif;color:#5C6F73;border-bottom:.6pt solid #D8DFDD;padding-bottom:2mm;vertical-align:bottom}
  @bottom-left{content:"Laboratório de Dados para Cidades Sustentáveis · ODS 11";font:400 7.5pt 'Source Serif 4',Georgia,serif;color:#5C6F73;vertical-align:top;padding-top:3mm}
  @bottom-right{content:counter(page);font:700 9pt Sora,'Segoe UI',sans-serif;color:#B45309;vertical-align:top;padding-top:3mm}}
@page cover{margin:0;@top-left{content:none;border:0}@top-right{content:none;border:0}@bottom-left{content:none}@bottom-right{content:none}}
@page land{size:A4 landscape;margin:22mm 14mm 18mm 14mm}
html{font-size:10pt}
body{font-family:'Source Serif 4',Georgia,serif;color:#1c2b2e;line-height:1.5;margin:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
h1,h2,h3,h4,.sans,th,figcaption,.callout .ct,.toc,.cover{font-family:Sora,'Segoe UI',sans-serif}
code{font-family:'JetBrains Mono',Consolas,monospace;font-size:.84em;background:#EEF2F1;padding:.05em .3em;border-radius:3px;color:#12343B}
pre{background:#12343B;color:#E8EFEE;border-radius:6px;padding:10px 14px;font-size:8.4pt;line-height:1.45;white-space:pre-wrap;break-inside:auto}
pre code{background:none;color:inherit;padding:0;font-size:inherit}
p{margin:.55em 0}
strong{color:#12343B}
a{color:var(--blue)}
hr{display:none}

/* ---------- capa ---------- */
.cover{page:cover;break-after:page;height:297mm;box-sizing:border-box;padding:22mm 20mm 0 20mm;background:#12343B;color:#F6F3EC;position:relative;overflow:hidden}
.cover .kicker{font-size:8.5pt;letter-spacing:.2em;color:#E6A817;font-weight:600}
.cover h1{font-size:50pt;line-height:1;margin:16mm 0 4mm;letter-spacing:-.02em;color:#F6F3EC;border:0;font-weight:700}
.cover .sub{font-size:15pt;line-height:1.3;color:#C9D6D8;max-width:105mm;font-weight:400}
.cover .tema{max-width:92mm;line-height:1.4;margin-top:9mm;font-size:10.5pt;color:#E6A817;font-weight:600;letter-spacing:.04em}
.cover .donut{position:absolute;right:-24mm;top:84mm;width:124mm}
.cover .donut-cap{position:absolute;left:112mm;top:208mm;font-size:6.8pt;color:#9FB4B8;line-height:1.6;max-width:80mm}
.cover .donut-cap i{display:inline-block;width:7px;height:7px;margin:0 3px 0 0;border-radius:2px}.cover .donut-cap span{margin-right:9px;white-space:nowrap}
.cover .meta{position:absolute;left:20mm;bottom:34mm;width:84mm;font-size:8.8pt;line-height:1.45}
.cover .meta div{display:flex;gap:6mm;padding:1.6mm 0;border-top:.6pt solid #2f5560}
.cover .meta b{flex:0 0 26mm;color:#E6A817;font-weight:600;letter-spacing:.04em;font-size:7.4pt;text-transform:uppercase;padding-top:.5mm}
.cover .meta span{color:#E8EFEE;font-family:'Source Serif 4',Georgia,serif}
.cover .bars{position:absolute;left:0;right:0;bottom:0;height:13mm;display:flex}
.cover .bars i{flex:1}

/* ---------- sumário ---------- */
.toc{break-after:page}
.toc h2{font-size:22pt;margin:0 0 8mm;color:#12343B;border:0}
.toc .l1{display:flex;align-items:baseline;gap:2mm;margin:3.6mm 0 .8mm;font-weight:700;font-size:10.5pt;color:#12343B}
.toc .l1 .n{color:#B45309;min-width:9mm;font-size:10.5pt}
.toc .l2{display:flex;align-items:baseline;gap:2mm;margin:.5mm 0 .5mm 11mm;font-size:8.8pt;color:#2A4A51;font-weight:400}
.toc .dots{flex:1;border-bottom:1.2pt dotted #B9C4C3;transform:translateY(-1.5pt)}
.toc .pg{font-variant-numeric:tabular-nums;color:#5C6F73}
.toc .l1 .pg{color:#12343B}

/* ---------- capítulos ---------- */
.chapter{break-before:page}
.chapter.land{page:land}
.opener{display:flex;align-items:flex-end;gap:6mm;margin:0 0 5mm;padding-bottom:4mm;border-bottom:2.2pt solid #12343B}
.opener .num{font:700 58pt/1 Sora,sans-serif;color:#E6A817;letter-spacing:-.04em;margin-bottom:-2.5mm}
.opener h2{margin:0;font-size:22pt;line-height:1.1;color:#12343B;letter-spacing:-.01em;border:0;padding:0}
.opener.front .num{display:none}
p.lead{font-size:11pt;line-height:1.5;color:#2A4A51;border-left:3pt solid #E6A817;padding:1mm 0 1mm 5mm;margin:0 0 6mm;font-style:italic}
h3{font-size:12.5pt;color:#166534;margin:7mm 0 2mm;break-after:avoid;letter-spacing:-.005em}
h3 .sn{color:#B45309;margin-right:2mm}
h4{font-size:9.6pt;margin:6mm 0 1.5mm;break-after:avoid;color:#12343B;background:#EEF2F1;padding:1.6mm 3mm;border-left:3pt solid #12343B}
h4 code{background:none;font-size:1em;font-weight:700}
.tag{display:inline-block;font:600 6.5pt Sora,sans-serif;letter-spacing:.1em;text-transform:uppercase;padding:.4mm 2mm;border-radius:2mm;margin-right:1.5mm;vertical-align:1pt;color:#fff}
.tag-oltp{background:#2F7D4F}.tag-dw{background:#B45309}

/* ---------- tabelas ---------- */
table{border-collapse:collapse;width:100%;margin:3mm 0 4mm;font-size:8.6pt;line-height:1.38}
thead{display:table-header-group}
th{font:600 6.9pt Sora,sans-serif;letter-spacing:.07em;text-transform:uppercase;color:#12343B;text-align:left;padding:2mm 2.4mm;border-bottom:1.6pt solid #12343B;background:#F6F3EC}
td{padding:1.7mm 2.4mm;border-bottom:.5pt solid #D8DFDD;vertical-align:top}
tr{break-inside:avoid}
tbody tr:nth-child(even) td{background:#FAF8F3}
td:first-child{font-weight:600;color:#12343B}
.chapter.land table{font-size:7.4pt}
.chapter.land td:first-child{font-weight:400}
.chapter.land td code{font-size:.92em}

/* ---------- figuras ---------- */
figure{margin:5mm 0;break-inside:avoid;text-align:center}
figure img{max-width:100%;max-height:205mm;border:.6pt solid #D8DFDD;border-radius:3px;background:#fff}
figure.chart img{border:0}
figure.wide{page:land;break-before:page;break-after:page;margin:0}
figure.wide img{max-height:158mm;width:auto;max-width:100%}
figcaption{font-size:8pt;color:#5C6F73;margin-top:2mm;text-align:left;line-height:1.35}
figcaption b{color:#B45309;letter-spacing:.04em}

/* ---------- caixas ---------- */
.callout{break-inside:avoid;margin:4mm 0;padding:2.6mm 4mm 2.6mm 4.5mm;border-radius:2px 5px 5px 2px;border-left:3.2pt solid;font-size:9.2pt;line-height:1.45}
.callout p{margin:0 0 1.2mm}.callout p:last-child{margin:0}
.callout .ct{display:block;font-weight:700;font-size:6.9pt;letter-spacing:.14em;text-transform:uppercase;margin-bottom:1mm}
.c-note{background:#EAF4EE;border-color:#2F7D4F}.c-note .ct{color:#2F7D4F}
.c-warning{background:#FDF3DC;border-color:#E6A817}.c-warning .ct{color:#B45309}
.c-important{background:#E7EEF0;border-color:#12343B}.c-important .ct{color:#12343B}
.c-tip{background:#E8F0FA;border-color:#2B6CB0}.c-tip .ct{color:#2B6CB0}
blockquote.pull{margin:4mm 0;padding:3mm 5mm;background:#12343B;color:#F6F3EC;border-radius:5px;font-family:Sora,sans-serif;font-size:10.5pt;line-height:1.45;break-inside:avoid}
blockquote.pull strong{color:#E6A817}
blockquote.pull p{margin:0}
ul,ol{margin:.5em 0 .5em 1.2em;padding:0}
li{margin:.2em 0}
"""

ALERTAS = {"NOTE": ("c-note", "Decisão de projeto"), "TIP": ("c-tip", "Dica de apresentação"),
           "IMPORTANT": ("c-important", "Regra de negócio"), "WARNING": ("c-warning", "Limitação")}


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub("<.*?>", "", t)).lower()).strip("-")


def capa(head_md):
    titulo = re.search(r"^# (.+)$", head_md, re.M).group(1)
    nome, _, sub = titulo.partition(" — ")
    tema = re.search(r"^\*\*(.+)\*\*\s*$", head_md, re.M)
    meta = re.findall(r"^\| \*\*(.+?)\*\* \| (.+?) \|$", head_md, re.M)
    linhas = "".join(f"<div><b>{html.escape(k)}</b><span>{html.escape(v.strip().strip('_'))}</span></div>" for k, v in meta)
    leg = "".join(f'<span><i style="background:{c}"></i>{n}</span>' for n, _, c in DONUT)
    barras = "".join(f'<i style="background:{c}"></i>' for c in ("#2B6CB0", "#C0392B", "#2F7D4F", "#E6A817", "#7B5B3A", "#6B7B7F"))
    kicker = re.search(r"<!-- KICKER: (.+?) -->", head_md)
    kicker = kicker.group(1) if kicker else "TÓPICOS ESPECIAIS EM BANCO DE DADOS · ENTREGA PARCIAL"
    return (f'<section class="cover"><div class="kicker">{html.escape(kicker)}</div>'
            f'<h1>{html.escape(nome)}</h1><div class="sub">{html.escape(sub)}</div>'
            f'<div class="tema">{html.escape(tema.group(1) if tema else "")}</div>'
            f'<div class="donut">{donut_svg()}</div>'
            f'<div class="donut-cap">Coleta de 2025 por tipo de resíduo<br>(dados sintéticos do projeto)<br>{leg}</div>'
            f'<div class="meta">{linhas}</div><div class="bars">{barras}</div></section>')


def preprocessa_alertas(md_txt):
    """Converte blocos '> [!TIPO]' em <div class="callout"> antes do Markdown (blocos vizinhos não se fundem)."""
    linhas, saida, i = md_txt.split("\n"), [], 0
    while i < len(linhas):
        m = re.match(r"> \[!(NOTE|TIP|IMPORTANT|WARNING)\]\s*$", linhas[i])
        if not m:
            saida.append(linhas[i]); i += 1; continue
        cls, rot = ALERTAS[m.group(1)]
        i += 1
        corpo = []
        while i < len(linhas) and linhas[i].startswith(">"):
            corpo.append(linhas[i][1:].lstrip()); i += 1
        txt = " ".join(corpo)
        txt = re.sub(r"^\*\*(Decisão de projeto|Limitação|Dica de apresentação)\s*[—.]*\s*", "**", txt)
        txt = re.sub(r"^\*\*\.?\s*\*\*", "", txt)
        saida += [f'<div class="callout {cls}" markdown="1"><span class="ct">{rot}</span>', "", txt, "", "</div>", ""]
    return "\n".join(saida)


def converte_corpo(md_txt):
    md_txt = preprocessa_alertas(md_txt)
    h = markdown.markdown(md_txt, extensions=["tables", "fenced_code", "sane_lists", "md_in_html"])
    h = re.sub(r"<blockquote>(.*?)</blockquote>", lambda m: f'<blockquote class="pull">{m.group(1)}</blockquote>', h, flags=re.S)
    # figuras
    def fig(m):
        alt, src = html.unescape(m.group(1)), m.group(2)
        alt_src = src
        if "diagramas/" in src and "/graficos/" not in src:
            src = src.replace(".png", ".svg")
        url = (MD.parent / src).resolve().as_uri()
        n, _, leg = alt.partition(" · ")
        chart = " chart" if "/graficos/" in src else ""
        if re.search(r"diagramas/0[1-8]_", alt_src):
            chart += " wide"
        return f'<figure class="{chart.strip()}"><img src="{url}" alt="{html.escape(alt)}"><figcaption><b>{html.escape(n.upper())}</b> · {html.escape(leg)}</figcaption></figure>'
    h = re.sub(r'<p><img alt="(.*?)" src="(.*?)" ?/?></p>', fig, h)
    h = re.sub(r"<p>(<em>Neste capítulo:.*?</em>)</p>", r'<p class="lead">\1</p>', h, flags=re.S)
    return h


def monta_secoes(h):
    """Divide em capítulos por <h2>, numera h3 e devolve (html, índice para o sumário)."""
    partes = re.split(r"(?=<h2>)", h)
    saida, indice = [], []
    for p in partes:
        m = re.match(r"<h2>(.*?)</h2>", p, re.S)
        if not m:
            saida.append(p); continue
        titulo = m.group(1)
        n = re.match(r"(\d+) · (.*)", titulo)
        num, nome = (n.group(1), n.group(2)) if n else ("", titulo)
        land = " land" if "Dicionário de dados" in titulo else ""
        sid = f"c-{slug(nome)}"
        indice.append(("h2", num, nome, sid))
        corpo = p[m.end():]

        def h3(mm):
            t = mm.group(1)
            mn = re.match(r"(\d+\.\d+) (.*)", t)
            s = f"s-{slug(t)}"
            indice.append(("h3", mn.group(1) if mn else "", mn.group(2) if mn else t, s))
            return f'<h3 id="{s}">' + (f'<span class="sn">{mn.group(1)}</span>{mn.group(2)}' if mn else t) + "</h3>"
        corpo = re.sub(r"<h3>(.*?)</h3>", h3, corpo, flags=re.S)
        front = "" if num else " front"
        saida.append(f'<section class="chapter{land}" id="{sid}"><div class="opener{front}"><div class="num">{num.zfill(2) if num else ""}</div>'
                     f'<h2>{nome}</h2></div>{corpo}</section>')
    return "".join(saida), indice


def sumario(indice, paginas):
    itens = ""
    for nivel, num, nome, sid in indice:
        pg = paginas.get(sid, "")
        if nivel == "h2":
            itens += (f'<div class="l1"><span class="n">{num}</span><span>{nome}</span><span class="dots"></span><span class="pg">{pg}</span></div>')
        else:
            itens += (f'<div class="l2"><span>{num} {nome}</span><span class="dots"></span><span class="pg">{pg}</span></div>')
    return f'<section class="toc"><h2>Sumário</h2>{itens}</section>'


def pagina_html(capa_html, toc_html, corpo_html):
    fontes = ("https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family="
              "Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap")
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Ciclo Urbano — Entrega 19/10</title>'
            f'<link rel="stylesheet" href="{fontes}"><style>{CSS}</style></head><body>{capa_html}{toc_html}{corpo_html}</body></html>')


def renderiza(html_txt, destino):
    tmp = pathlib.Path(tempfile.gettempdir()) / "ciclo_urbano.html"
    tmp.write_text(html_txt, encoding="utf-8")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=60000",
                    f"--print-to-pdf={destino}", tmp.as_uri()], capture_output=True)


def paginas_dos_titulos(pdf, indice):
    """Acha a página de cada título olhando o tamanho da fonte (evita casar com o texto corrido)."""
    import pymupdf
    d = pymupdf.open(pdf)
    cache = []
    for i in range(len(d)):
        linhas = []
        for bl in d[i].get_text("dict")["blocks"]:
            for ln in bl.get("lines", []):
                txt = "".join(sp["text"] for sp in ln["spans"]).strip()
                if txt:
                    linhas.append((txt, max(sp["size"] for sp in ln["spans"])))
        cache.append(linhas)
    achados, inicio = {}, 2
    for nivel, num, nome, sid in indice:
        alvo = html.unescape(re.sub("<.*?>", "", nome)).strip()[:40]
        minimo = 18 if nivel == "h2" else 11.5
        for i in range(inicio, len(d)):
            if any(alvo in t and sz >= minimo for t, sz in cache[i]):
                achados[sid] = i + 1
                inicio = i
                break
    return achados


def main():
    if not EDGE:
        sys.exit("Edge/Chrome não encontrado.")
    global CSS
    txt = MD.read_text(encoding="utf-8")
    cab, _, corpo = txt.partition("<!-- INICIO -->")
    rotulo = re.search(r"<!-- ROTULO: (.+?) -->", cab)
    if rotulo:   # texto do canto superior direito de cada página
        CSS = CSS.replace("Entrega parcial · 19/10/2026", rotulo.group(1))
    corpo_html, indice = monta_secoes(converte_corpo(corpo))
    capa_html = capa(cab)
    renderiza(pagina_html(capa_html, sumario(indice, {}), corpo_html), PDF)          # 1ª passada
    pags = paginas_dos_titulos(PDF, indice)                                          # descobre as páginas
    renderiza(pagina_html(capa_html, sumario(indice, pags), corpo_html), PDF)        # 2ª passada, com o sumário
    print("PDF gerado:", PDF)


if __name__ == "__main__":
    main()
