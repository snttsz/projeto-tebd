"""Dados abaixo são fixtures independentes; não são resultados do Ciclo Urbano."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import kmeans_bairros as km


def fixture():
    linhas = []
    # Dois perfis muito separados e pequenas variações dentro de cada perfil.
    for i in range(12):
        alto = i >= 6
        j = i % 6
        linhas.append({"ano": 2025, "id_bairro": i + 1, "bairro": f"Teste {i + 1:02}",
                       "regiao": "TESTE", "populacao": 1000, "variantes_cadastro": 1,
                       "peso_total_kg": 1000 + 8000 * alto + j * 5,
                       "peso_reciclavel_kg": (1000 + 8000 * alto + j * 5) * (.1 + .7 * alto + j * .0001),
                       "qtd_pesagens": 100, "viagens": 1000, "canceladas": 10 + 500 * alto + j,
                       "ocorrencias": 1 + 80 * alto + j})
    df = pd.DataFrame(linhas)
    for medida, total in km.TOTALS.items():
        df[total] = df[medida].sum()
    return df


class Preparacao(unittest.TestCase):
    def test_formulas_conhecidas(self):
        df, _ = km.preparar(fixture(), 2025)
        np.testing.assert_allclose(df.loc[0, km.FEATURES].to_numpy(dtype=float), [1, 10, 1, 1])
        self.assertEqual(len(df), 12)

    def test_rejeita_erros_materiais(self):
        alteracoes = {
            "duplicado": lambda d: pd.concat([d, d.iloc[[0]]]),
            "periodo_misto": lambda d: d.assign(ano=[2024] + [2025] * 11),
            "sem_populacao": lambda d: d.assign(populacao=0),
            "ausencia": lambda d: d.assign(peso_total_kg=np.nan),
            "infinito": lambda d: d.assign(peso_total_kg=np.inf),
            "reciclavel_maior": lambda d: d.assign(peso_reciclavel_kg=d.peso_total_kg + 1),
            "canceladas_maior": lambda d: d.assign(canceladas=1001),
            "medida_negativa": lambda d: d.assign(ocorrencias=-1),
            "fracao_contagem": lambda d: d.assign(viagens=10.5),
            "cadastro_conflitante": lambda d: d.assign(variantes_cadastro=2),
            "perda_juncao": lambda d: d.assign(total_viagens_periodo=1),
            "identidade_vazia": lambda d: d.assign(bairro=""),
            "coluna_ausente": lambda d: d.drop(columns="ocorrencias"),
        }
        for nome, modificar in alteracoes.items():
            with self.subTest(nome=nome), self.assertRaises(ValueError):
                km.preparar(modificar(fixture()), 2025)

    def test_zero_ocorrencias_por_bairro_e_valido(self):
        df = fixture()
        df.loc[0, "ocorrencias"] = 0
        df["total_ocorrencias_periodo"] = df.ocorrencias.sum()
        preparado, _ = km.preparar(df, 2025)
        self.assertEqual(preparado.loc[0, "ocorrencias_1000_hab"], 0)


class Agrupamento(unittest.TestCase):
    def test_recupera_perfis_e_reproduz_com_ordem_diferente(self):
        df, _ = km.preparar(fixture(), 2025)
        a = km.agrupar(df)
        embaralhado, _ = km.preparar(fixture().sample(frac=1, random_state=3), 2025)
        b = km.agrupar(embaralhado)
        self.assertEqual(a["k"], 2)
        self.assertEqual(adjusted_rand_score([0] * 6 + [1] * 6, a["bairros"].grupo), 1)
        np.testing.assert_array_equal(a["bairros"].grupo, b["bairros"].grupo)
        np.testing.assert_allclose(a["x"].mean(axis=0), 0, atol=1e-12)
        np.testing.assert_allclose(a["x"].std(axis=0), 1, atol=1e-12)
        for g in [1, 2]:
            media = a["bairros"].loc[a["bairros"].grupo.eq(g), a["ativas"]].mean()
            np.testing.assert_allclose(a["centroides"].set_index("grupo").loc[g], media)
        self.assertEqual(len(a["estabilidade"]), 10)
        self.assertEqual(len(a["sensibilidade"]), 12)

    def test_constantes_e_k_inviavel(self):
        df, _ = km.preparar(fixture(), 2025)
        df["ocorrencias_1000_hab"] = 0
        res = km.agrupar(df)
        self.assertNotIn("ocorrencias_1000_hab", res["ativas"])
        with self.assertRaises(ValueError):
            km.agrupar(df, k_forcado=9)
        df[km.FEATURES] = 1
        with self.assertRaises(ValueError):
            km.agrupar(df)

    def test_nao_forca_grupo_de_um_bairro(self):
        df, _ = km.preparar(fixture().iloc[:4].assign(
            total_peso_periodo=fixture().iloc[:4].peso_total_kg.sum(),
            total_viagens_periodo=4000, total_ocorrencias_periodo=10), 2025)
        # Três perfis idênticos e um isolado: única solução possível seria 3+1.
        df[km.FEATURES] = [[1, 1, 1, 1]] * 3 + [[9, 9, 9, 9]]
        with self.assertRaises(ValueError):
            km.agrupar(df)


class Integracao(unittest.TestCase):
    def test_csv_relatorio_graficos_e_hashes(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            csv = raiz / "entrada.csv"
            fixture().to_csv(csv, index=False, encoding="utf-8-sig")
            args = argparse.Namespace(csv=csv, ano=2025, semente=42, k=None, saida=raiz / "resultados")
            # O modo offline não pode tentar consultar o banco ou importar configuração.
            with patch.object(km, "ler_banco", side_effect=AssertionError("Tentativa indevida de conexão")):
                saida = km.executar(args)
            manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
            self.assertFalse(manifesto["extraido_agora_do_banco"])
            self.assertEqual(manifesto["k"], 2)
            for nome, sha in manifesto["sha256"].items():
                self.assertEqual(hashlib.sha256((saida / nome).read_bytes()).hexdigest(), sha)
            self.assertEqual(len(list(saida.glob("*.png"))), 5)
            texto = (saida / "relatorio.md").read_text(encoding="utf-8")
            self.assertIn("Dados sintéticos", texto)
            self.assertIn("não verificado por conexão", texto)
            for grafico in saida.glob("*.png"):
                self.assertIn(grafico.name, texto)

    def test_banco_usa_transacao_somente_leitura(self):
        # Verifica o contrato com psql sem precisar de um servidor.
        import types
        fake_config = types.SimpleNamespace(ENV={}, psql_base=lambda **kw: ["psql", "-d", "teste"])
        retorno = types.SimpleNamespace(returncode=0, stdout=fixture().to_csv(index=False))
        with patch.dict(sys.modules, {"config": fake_config}), patch.object(km.subprocess, "run", return_value=retorno) as run:
            base = km.ler_banco(km.consulta(2025))
        self.assertEqual(len(base), 12)
        comando = run.call_args.args[0]
        sql_enviado = run.call_args.kwargs["input"]
        self.assertIn("BEGIN READ ONLY;", sql_enviado)
        self.assertIn("ROLLBACK;", sql_enviado)
        self.assertIn("-X", comando)
        self.assertEqual(comando[-2:], ["-f", "-"])
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertIn("Não juntar fatos", sql_enviado)
        self.assertNotIn("__ANO__", sql_enviado)


if __name__ == "__main__":
    unittest.main()
