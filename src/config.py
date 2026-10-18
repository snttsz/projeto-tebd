"""
Configuração central do projeto: conexão com o banco, caminhos de ferramentas e pastas.

Ordem de prioridade para cada valor:
  1) variável de ambiente (ex.: PGPORT=5433)
  2) arquivo .env na raiz do projeto (copie .env.example para .env e ajuste)
  3) valor padrão abaixo

Nenhum outro script do projeto deve ter porta, senha ou caminho de programa escritos no código.
"""
import glob, os, pathlib, shutil

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SRC = RAIZ / "src"
DOCS = RAIZ / "docs"
SQL = SRC / "sql"


def _le_env():
    valores = {}
    arq = RAIZ / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                valores[k.strip()] = v.strip().strip('"').strip("'")
    return valores


_ENV = _le_env()


def _valor(chave, padrao):
    return os.environ.get(chave) or _ENV.get(chave) or padrao


# ---- banco de dados -----------------------------------------------------------------------------
PGHOST = _valor("PGHOST", "localhost")
PGPORT = _valor("PGPORT", "5432")
PGUSER = _valor("PGUSER", "postgres")
PGPASSWORD = _valor("PGPASSWORD", "postgres")
PGDATABASE = _valor("PGDATABASE", "cidades_sustentaveis")

# variáveis de ambiente repassadas aos programas do PostgreSQL (psql lê PGPASSWORD daqui)
ENV = dict(os.environ, PGPASSWORD=PGPASSWORD, PGCLIENTENCODING="UTF8")


def _acha_programa(nome, variavel, padroes_windows):
    """Procura um programa: variável de ambiente/.env > PATH > pastas comuns do Windows."""
    explicito = _valor(variavel, "")
    if explicito and os.path.exists(explicito):
        return explicito
    no_path = shutil.which(nome)
    if no_path:
        return no_path
    for padrao in padroes_windows:
        achados = sorted(glob.glob(padrao), reverse=True)
        if achados:
            return achados[0]
    return None


PSQL = _acha_programa("psql", "PSQL", [r"C:\Program Files\PostgreSQL\*\bin\psql.exe"])
DOT = _acha_programa("dot", "DOT", [r"C:\Program Files\Graphviz*\bin\dot.exe"])
NEATO = _acha_programa("neato", "NEATO", [r"C:\Program Files\Graphviz*\bin\neato.exe"])
NAVEGADOR = _acha_programa("msedge", "NAVEGADOR", [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"])


def psql_base(banco=None, so_dados=True):
    """Lista de argumentos de linha de comando do psql para conectar ao banco do projeto."""
    if not PSQL:
        raise SystemExit("psql não encontrado. Instale o PostgreSQL ou defina PSQL no .env.")
    args = [PSQL, "-h", PGHOST, "-p", PGPORT, "-U", PGUSER, "-d", banco or PGDATABASE]
    return args + (["-At", "-F", "\t"] if so_dados else [])
