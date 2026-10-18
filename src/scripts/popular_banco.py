"""
Cria e popula o banco do projeto executando, em ordem, os scripts de src/sql, e confere o resultado.

    python src/scripts/popular_banco.py              cria o banco (se não existir) e executa 01, 02 e 03
    python src/scripts/popular_banco.py --recriar    apaga o banco e refaz tudo do zero
    python src/scripts/popular_banco.py --verificar  só confere se o banco atual está consistente
    python src/scripts/popular_banco.py --banco teste_limpo --recriar   usa outro nome de banco

Conexão (host, porta, usuário, senha, banco): src/config.py (variáveis de ambiente ou arquivo .env).

Ordem dos scripts:
    01_construcao_oltp_olap.sql     schemas oltp e dw, tabelas, índices, dados de exemplo e ETL
    02_dicionario_comentarios.sql   COMMENT ON de todas as tabelas e colunas (dicionário no catálogo)
    03_views_apoio.sql              views do schema bi para os dashboards
Se o 01 for executado de novo, as views do schema bi são apagadas junto: execute o 03 depois.
"""
import argparse, os, subprocess, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import config

SCRIPTS = ["01_construcao_oltp_olap.sql", "02_dicionario_comentarios.sql", "03_views_apoio.sql"]


def psql(sql=None, arquivo=None, banco=None, so_dados=True, parar_no_erro=True):
    args = config.psql_base(banco=banco, so_dados=so_dados)
    if parar_no_erro:
        args += ["-v", "ON_ERROR_STOP=1", "-q"]
    args += ["-f", str(arquivo)] if arquivo else ["-c", sql]
    return subprocess.run(args, capture_output=True, text=True, env=config.ENV, encoding="utf-8")


def banco_existe(nome):
    r = psql(f"SELECT 1 FROM pg_database WHERE datname = '{nome}'", banco="postgres")
    return r.stdout.strip() == "1"


def cria_banco(nome, recriar):
    if recriar and banco_existe(nome):
        psql(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{nome}' AND pid <> pg_backend_pid()", banco="postgres")
        r = psql(f'DROP DATABASE "{nome}"', banco="postgres")
        if r.returncode:
            sys.exit("Não foi possível apagar o banco:\n" + r.stderr)
        print(f"Banco {nome} apagado.")
    if not banco_existe(nome):
        r = psql(f"CREATE DATABASE \"{nome}\" ENCODING 'UTF8' TEMPLATE template0", banco="postgres")
        if r.returncode:
            sys.exit("Não foi possível criar o banco:\n" + r.stderr)
        print(f"Banco {nome} criado.")


def executa_scripts(banco):
    for nome in SCRIPTS:
        arquivo = config.SQL / nome
        print(f"Executando {nome} ...", end=" ", flush=True)
        r = psql(arquivo=arquivo, banco=banco)
        if r.returncode:
            print("ERRO")
            sys.exit(r.stderr)
        print("ok")


def consulta(sql, banco):
    r = psql(sql, banco=banco)
    if r.returncode:
        sys.exit(r.stderr)
    return [linha.split("\t") for linha in r.stdout.strip().splitlines()]


def verifica(banco):
    """Conferências de consistência. Devolve True se tudo passou."""
    ok = True

    def confere(descricao, condicao, detalhe=""):
        nonlocal ok
        print(("  [ok]    " if condicao else "  [FALHA] ") + descricao + (f"  ({detalhe})" if detalhe else ""))
        ok = ok and condicao

    print("Conferências no banco:", banco)
    pares = [("oltp.coleta_item", "dw.fato_coleta"), ("oltp.coleta", "dw.fato_viagem"),
             ("oltp.descarga", "dw.fato_destinacao"), ("oltp.ocorrencia", "dw.fato_ocorrencia")]
    for a, b in pares:
        na = int(consulta(f"SELECT COUNT(*) FROM {a}", banco)[0][0])
        nb = int(consulta(f"SELECT COUNT(*) FROM {b}", banco)[0][0])
        confere(f"{a} = {b}", na == nb, f"{na} e {nb}")

    kg_item, kg_fato, kg_viagem, kg_desc = [float(x) for x in consulta(
        "SELECT (SELECT SUM(peso_kg) FROM oltp.coleta_item), (SELECT SUM(peso_kg) FROM dw.fato_coleta), "
        "(SELECT SUM(peso_total_kg) FROM dw.fato_viagem), (SELECT SUM(peso_kg) FROM oltp.descarga)", banco)[0]]
    confere("peso total: itens = fato_coleta = fato_viagem", abs(kg_item - kg_fato) < 0.01 and abs(kg_item - kg_viagem) < 0.01,
            f"{kg_item:.2f} kg")
    confere("peso descarregado coincide com o coletado (tolerância de arredondamento)", abs(kg_item - kg_desc) < 5,
            f"diferença de {abs(kg_item - kg_desc):.2f} kg")

    canc_oltp = int(consulta("SELECT COUNT(*) FROM oltp.coleta WHERE status = 'CANCELADA'", banco)[0][0])
    canc_dw = int(consulta("SELECT SUM(qtd_cancelada) FROM dw.fato_viagem", banco)[0][0])
    confere("coletas canceladas: OLTP = DW", canc_oltp == canc_dw, f"{canc_oltp}")

    sem_comentario = int(consulta(
        "SELECT COUNT(*) FROM information_schema.columns c WHERE table_schema IN ('oltp','dw') AND "
        "col_description((table_schema||'.'||table_name)::regclass, ordinal_position) IS NULL", banco)[0][0])
    confere("todas as colunas têm descrição no dicionário (COMMENT ON)", sem_comentario == 0, f"{sem_comentario} sem descrição")

    n_views = int(consulta("SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'bi'", banco)[0][0])
    confere("views do schema bi criadas", n_views >= 6, f"{n_views} views")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recriar", action="store_true", help="apaga o banco antes de criar")
    ap.add_argument("--verificar", action="store_true", help="só confere o banco atual")
    ap.add_argument("--banco", default=config.PGDATABASE, help="nome do banco (padrão: o do .env)")
    a = ap.parse_args()
    if not a.verificar:
        cria_banco(a.banco, a.recriar)
        executa_scripts(a.banco)
    sys.exit(0 if verifica(a.banco) else 1)


if __name__ == "__main__":
    main()
