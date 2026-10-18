"""
Monta os documentos da entrega a partir de UM modelo e gera os PDFs em docs/entregas/.

  docs/entregas/professor/Entrega_19-10_PROFESSOR.md / .pdf          roteiro visual para mostrar o andamento
  docs/entregas/guia-completo/Entrega_19-10_GUIA_COMPLETO.md / .pdf  versão completa + capítulo 8 (guia para outra IA/chat)
  docs/entregas/anexo-dicionario/Entrega_19-10_ANEXO_DICIONARIO.md/.pdf  só o dicionário de dados (item 4)

Cada documento lista em "Referências" somente o que ele próprio cita, numerado pela ordem da primeira citação.

Requisitos : banco carregado (src/sql/01 e 02), psql, Edge/Chrome, pip install markdown pymupdf. Conexão: src/config.py
Uso        : python src/documentos/montar_entregas.py            (os três)
             python src/documentos/montar_entregas.py professor  (só um: professor | guia | anexo)

Marcações no modelo (src/documentos/modelo_entrega.md):
  <!--PROF--> ... <!--/PROF-->   só na versão do professor
  <!--GUIA--> ... <!--/GUIA-->   só no guia completo
  {{DICIONARIO}} {{CAP8}}        preenchidos pelo montador
Seções removidas do professor (por título): ver EXCLUIR_PROFESSOR.
"""
import os, pathlib, re, subprocess, sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent))
import config
import gerar_dicionario as gd

RAIZ = config.RAIZ

# seções que só existem no guia completo (identificadas pelo início do título, não pelo número)
EXCLUIR_PROFESSOR = ("Histórias de usuário", "Glossário do domínio", "Matriz de rastreabilidade",
                     "Divisão sugerida de tarefas", "Roteiro de 5 minutos", "Perguntas prováveis",
                     "Método de trabalho em grupo", "O DW em ação", "Cliente e partes interessadas",
                     "Decisões de modelagem", "ETL: do OLTP ao DW")
# capítulos inteiros que o PDF do professor não traz (ele é um roteiro visual para mostrar o andamento do grupo)
EXCLUIR_CAPITULOS_PROFESSOR = ("Script de construção e validação", "Situação do barema", "Dicionário de dados")
# referências cruzadas que ficariam apontando para algo removido
AJUSTES_PROFESSOR = {
    "| Capítulo 5 |": "| Anexo (PDF à parte) |",
    "| Capítulo 6 e pasta `src/sql/` |": "| Pasta `src/sql/` |",
    "Consulta de verificação no fim do script (capítulo 6).": "Consulta de verificação no fim do script de construção.",
    "cada uma indica quem a faz, onde está a resposta no banco e qual *view* a apoia.": "cada uma indica quem a faz e onde está a resposta no banco.",
}
VERSOES = {
    "professor": dict(arquivo="docs/entregas/professor/Entrega_19-10_PROFESSOR.md", sou="PROF", outra="GUIA", exemplo=False),
    "guia": dict(arquivo="docs/entregas/guia-completo/Entrega_19-10_GUIA_COMPLETO.md", sou="GUIA", outra="PROF", exemplo=True),
    # anexo: só o dicionário de dados (item 4 do barema), em PDF à parte para não pesar no roteiro visual
    "anexo": dict(arquivo="docs/entregas/anexo-dicionario/Entrega_19-10_ANEXO_DICIONARIO.md", sou="PROF", outra="GUIA", exemplo=False),
}


def aplica_marcas(txt, sou, outra):
    txt = re.sub(rf"<!--{outra}-->.*?<!--/{outra}-->\n?", "", txt, flags=re.S)
    return re.sub(rf"<!--/?{sou}-->\n?", "", txt)


def remove_secoes(txt, titulos):
    saida, pular = [], False
    for ln in txt.split("\n"):
        m = re.match(r"### \d+\.\d+ (.*)", ln)
        if ln.startswith("### "):
            pular = bool(m and m.group(1).startswith(titulos))
        elif ln.startswith("## ") or ln.strip() == "---":
            pular = False
        if not pular:
            saida.append(ln)
    return "\n".join(saida)


def remove_capitulos(txt, titulos):
    """Remove capítulos inteiros ('## N · Título') até o próximo '## ' que não seja um deles."""
    saida, pular = [], False
    for ln in txt.split("\n"):
        if ln.startswith("## "):
            m = re.match(r"## \d+ · (.*)", ln)
            pular = bool(m and m.group(1).startswith(titulos))
        if not pular:
            saida.append(ln)
    return "\n".join(saida)


def ajusta_referencias(txt):
    """Mantém em 'Referências' só as obras citadas no texto, numeradas pela ordem da primeira citação."""
    m = re.search(r"^## Referências\s*$", txt, flags=re.M)
    if not m:
        return txt
    corpo, refs = txt[:m.start()], txt[m.start():].split("\n")
    itens, resto = {}, []
    for ln in refs[1:]:
        mm = re.match(r"(\d+)\. (.*)", ln)
        if mm:
            itens[int(mm.group(1))] = mm.group(2)
        else:
            resto.append(ln)
    ordem = []

    def renumera_citacao(mc):
        n = int(mc.group(1))
        if n not in itens:
            return mc.group(0)
        if n not in ordem:
            ordem.append(n)
        return f"[{ordem.index(n) + 1}]"

    saida, em_codigo = [], False
    for ln in corpo.split("\n"):
        if ln.strip().startswith("```"):
            em_codigo = not em_codigo
        saida.append(ln if em_codigo else re.sub(r"\[(\d+)\]", renumera_citacao, ln))
    novas = [f"{i + 1}. {itens[n]}" for i, n in enumerate(ordem)]
    return "\n".join(saida) + "\n" + refs[0] + "\n\n" + "\n".join(novas) + "\n" + "\n".join(resto)


def renumera(txt):
    cap, k, saida = 0, 0, []
    for ln in txt.split("\n"):
        mc = re.match(r"## (\d+) · ", ln)
        if mc:
            cap, k = int(mc.group(1)), 0
        mh = re.match(r"### (\d+)\.(\d+) (.*)", ln)
        if mh:
            k += 1
            ln = f"### {cap}.{k} {mh.group(3)}"
        saida.append(ln)
    return "\n".join(saida)


def monta(chave, dados):
    cfg = VERSOES[chave]
    modelo = (AQUI / "modelo_entrega.md").read_text(encoding="utf-8")
    cap8 = (AQUI / "modelo_cap8_guia.md").read_text(encoding="utf-8")
    txt = aplica_marcas(modelo, cfg["sou"], cfg["outra"])
    if chave == "anexo":
        cab, _, corpo = txt.partition("<!-- INICIO -->")
        cab = re.sub(r"<!-- KICKER: .*? -->", "<!-- KICKER: ANEXO · DICIONÁRIO DE DADOS (ITEM 4 DO BAREMA) -->", cab)
        cab = re.sub(r"<!-- ROTULO: .*? -->", "<!-- ROTULO: Anexo · Dicionário de dados -->", cab)
        m = re.search(r"^## \d+ · Dicionário de dados.*?(?=^## |\Z)", corpo, flags=re.S | re.M)
        cap = re.sub(r"^## \d+ · ", "## 1 · ", m.group(0), count=1, flags=re.M)
        txt = cab + "<!-- INICIO -->\n\n" + cap
    elif chave == "professor":
        txt = remove_secoes(txt, EXCLUIR_PROFESSOR)
        txt = remove_capitulos(txt, EXCLUIR_CAPITULOS_PROFESSOR)
        for velho, novo in AJUSTES_PROFESSOR.items():
            assert velho in txt, f"ajuste não encontrado: {velho}"
            txt = txt.replace(velho, novo)
        txt = "\n".join(l for l in txt.split("\n") if "| `docs/pesquisas/`" not in l)
        txt = txt.replace("{{CAP8}}", "")
    elif chave == "guia":
        txt = txt.replace("{{CAP8}}", cap8.replace("{{ESQUEMA_RESUMO}}", gd.esquema_resumo(dados)))
    txt = txt.replace("{{DICIONARIO}}", gd.dicionario(com_exemplo=cfg["exemplo"], dados=dados))
    txt = renumera(txt)
    txt = ajusta_referencias(txt)
    txt = re.sub(r"\n{4,}", "\n\n\n", txt)
    destino = RAIZ / cfg["arquivo"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    # imagens: no modelo os caminhos partem de docs/; aqui viram relativos à pasta do documento gerado
    prefixo = os.path.relpath(config.DOCS, destino.parent).replace("\\", "/")
    txt = txt.replace("](diagramas/", f"]({prefixo}/diagramas/")
    destino.write_text(txt, encoding="utf-8")
    print("Markdown:", destino.name, f"({len(txt):,} caracteres)")
    subprocess.run([sys.executable, "-I", str(AQUI / "gerar_pdf.py"), str(destino)], check=True)


if __name__ == "__main__":
    escolha = sys.argv[1:] or list(VERSOES)
    dados = gd.carrega()          # uma consulta ao catálogo serve a todas as versões
    for chave in escolha:
        monta(chave, dados)
