"""
Gera, a partir do catálogo do PostgreSQL, (1) o dicionário de dados em Markdown e
(2) um resumo compacto do esquema (para colar em chats com IA).

Requisitos : psql e o banco carregado (scripts 01 e 02 de src/sql). Conexão: src/config.py
Uso        : importado por montar_entregas.py  (ou: python src/documentos/gerar_dicionario.py)
"""
import os, re, subprocess
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import config  # configuração central (src/config.py)

SQL_COLUNAS = r"""
SELECT n.nspname, c.relname, a.attnum, a.attname, format_type(a.atttypid, a.atttypmod),
       CASE WHEN a.attnotnull THEN 'S' ELSE 'N' END,
       COALESCE((SELECT string_agg(
            CASE k.contype
              WHEN 'p' THEN CASE WHEN array_length(k.conkey,1)>1 THEN 'PK (composta)' ELSE 'PK' END
              WHEN 'u' THEN CASE WHEN array_length(k.conkey,1)>1 THEN 'UNIQUE (composta)' ELSE 'UNIQUE' END
              WHEN 'f' THEN 'FK → ' || regexp_replace(k.confrelid::regclass::text,'^(oltp|dw)\.','') || '.' ||
                            (SELECT attname FROM pg_attribute WHERE attrelid=k.confrelid AND attnum=k.confkey[1])
              WHEN 'c' THEN 'CHECK ' || regexp_replace(pg_get_constraintdef(k.oid),'^CHECK ','')
            END, '; ' ORDER BY k.contype DESC)
          FROM pg_constraint k WHERE k.conrelid=c.oid AND a.attnum = ANY(k.conkey)
            AND NOT (k.contype='c' AND array_length(k.conkey,1)>1)), ''),
       COALESCE(pg_get_expr(d.adbin,d.adrelid),''),
       COALESCE(col_description(c.oid,a.attnum),''),
       COALESCE(obj_description(c.oid,'pg_class'),'')
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
WHERE n.nspname IN ('oltp','dw') AND c.relkind='r'
ORDER BY n.nspname DESC, c.oid, a.attnum;
"""


def psql(sql):
    """Executa o SQL via arquivo temporário (evita limite de tamanho e problemas de codificação no Windows)."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
    try:
        r = subprocess.run(config.psql_base() + ["-f", f.name],
                           capture_output=True, text=True, env=config.ENV, encoding="utf-8", check=True)
    finally:
        os.unlink(f.name)
    return [l.split("\t") for l in r.stdout.splitlines() if l.strip()]


def carrega():
    linhas = psql(SQL_COLUNAS)
    partes = []
    for sch, tab, _, col, *_ in linhas:
        t = f"{sch}.{tab}"
        def sub(off):
            return f'(SELECT "{col}"::text FROM {t} WHERE "{col}" IS NOT NULL ORDER BY ctid OFFSET {off} LIMIT 1)'
        partes.append(f"SELECT '{sch}','{tab}','{col}',COALESCE({sub(7)},{sub(0)},'')")
    exemplos = {(r[0], r[1], r[2]): (r[3] if len(r) > 3 else "") for r in psql(" UNION ALL ".join(partes))}
    return linhas, exemplos


def limpa_check(s):
    m = re.search(r"ARRAY\[(.*?)\]\)", s)
    col = re.search(r"\(\((\w+)\)::text", s)
    if m and col:
        return "CHECK %s IN (%s)" % (col.group(1), ", ".join(re.findall(r"'([^']+)'", m.group(1))))
    s = re.sub(r"::\w+( \w+)?", "", s).replace("'", "").replace("(", "").replace(")", "")
    return re.sub(r"^CHECK\s*", "CHECK ", s)


def tipo_curto(t):
    return (t.replace("character varying", "varchar").replace("character(", "char(")
             .replace("timestamp without time zone", "timestamp").replace("time without time zone", "time"))


def dicionario(com_exemplo=True, dados=None):
    linhas, exemplos = dados or carrega()
    out, atual = [], None
    for sch, tab, n, col, typ, nn, cons, dflt, desc, tdesc in linhas:
        if (sch, tab) != atual:
            atual = (sch, tab)
            out.append(f"\n#### <span class='tag tag-{sch}'>{sch}</span> `{tab}`\n\n{tdesc}\n")
            cab = "| Atributo | Tipo | Nulo? | Restrições | Descrição |" + (" Exemplo |" if com_exemplo else "")
            out.append(cab + "\n|---|---|---|---|---|" + ("---|" if com_exemplo else ""))
        partes = [limpa_check(p) if p.startswith("CHECK") else p for p in cons.split("; ") if p]
        if "nextval" in dflt:
            partes.insert(0, "serial")
        elif dflt:
            partes.append("DEFAULT " + dflt.replace("::character varying", "").replace("::text", ""))
        r = "<br>".join(partes) if partes else "—"
        linha = "| `%s` | %s | %s | %s | %s |" % (col, tipo_curto(typ), "Não" if nn == "S" else "Sim", r.replace("|", "\\|"), desc)
        if com_exemplo:
            e = exemplos.get((sch, tab, col), "")
            e = e if len(e) <= 28 else e[:26] + "…"
            linha += f" {'`' + e + '`' if e else '—'} |"
        out.append(linha)
    return "\n".join(out) + "\n"


def esquema_resumo(dados=None):
    linhas, _ = dados or carrega()
    tabelas = {}
    for sch, tab, n, col, typ, nn, cons, *_ in linhas:
        marca = col
        if "PK" in cons:
            marca += " PK"
        m = re.search(r"FK → (\w+)\.(\w+)", cons)
        if m:
            marca += f" →{m.group(1)}"
        if nn == "N":
            marca += "?"
        tabelas.setdefault(f"{sch}.{tab}", []).append(marca)
    return "\n".join(f"{t}({', '.join(c)})" for t, c in tabelas.items())


if __name__ == "__main__":
    import sys; sys.stdout.reconfigure(encoding="utf-8")
    d = carrega()
    print(esquema_resumo(d))
