"""Tests du pipeline I3 (stdlib unittest).

Commande: python3 -m unittest -v test_pipeline.py
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

import pipeline


def ecrire(tmp: Path, nom: str, contenu: str) -> Path:
    p = tmp / nom
    p.write_text(contenu, encoding="utf-8")
    return p


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def lancer(self, contenu: str):
        entree = ecrire(self.tmp, "entree.ndjson", contenu)
        acc, rej, sta = pipeline.traiter(entree)
        return acc, rej, sta

    # 1. Entree valide.
    def test_entree_valide_normalisee(self) -> None:
        acc, rej, sta = self.lancer(
            '{"id":"s01","date":"19/10/2026","period":"matin","group":"A",'
            '"mode":"DG","title":"React composants","domain":"web",'
            '"teacherId":"t1","status":"confirme"}\n'
        )
        self.assertEqual(rej, [])
        self.assertEqual(len(acc), 1)
        o = acc[0]
        self.assertEqual(o["date"], "2026-10-19")
        self.assertEqual(o["period"], "am")
        self.assertEqual(o["status"], "confirmed")
        self.assertEqual(o["id"], "s01")
        self.assertEqual(o["source_line"], 1)

    # 2. Entree invalide : date non calendaire.
    def test_date_invalide(self) -> None:
        acc, rej, sta = self.lancer(
            '{"id":"bad","date":"2026-02-30","period":"am","group":"A",'
            '"mode":"DG","title":"x","domain":"web","teacherId":"t1","status":"proposed"}\n'
        )
        self.assertEqual(acc, [])
        self.assertEqual(len(rej), 1)
        self.assertIn("date", rej[0]["motif"])
        self.assertEqual(rej[0]["source_line"], 1)

    # 2b. Entree invalide : periode hors domaine.
    def test_periode_invalide(self) -> None:
        acc, rej, sta = self.lancer(
            '{"id":"bad","date":"2026-10-20","period":"soir","group":"A",'
            '"mode":"DG","title":"x","domain":"web","teacherId":"t1","status":"proposed"}\n'
        )
        self.assertEqual(acc, [])
        self.assertEqual(len(rej), 1)
        self.assertIn("période", rej[0]["motif"])

    # 3. Doublon : compteur dedoublons, ni accepte ni rejete.
    def test_doublon(self) -> None:
        ligne = (
            '{"id":"s01","date":"2026-10-19","period":"am","group":"A",'
            '"mode":"DG","title":"a","domain":"web","teacherId":"t1","status":"confirmed"}\n'
        )
        acc, rej, sta = self.lancer(ligne + ligne)
        self.assertEqual(len(acc), 1)
        self.assertEqual(rej, [])
        self.assertEqual(sta["doublons"], 1)
        self.assertEqual(sta["lus"], 2)
        # invariant
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])

    # 4. JSON malforme.
    def test_json_malforme(self) -> None:
        acc, rej, sta = self.lancer('{"id":"bad4","title":"JSON tronqué"\n')
        self.assertEqual(acc, [])
        self.assertEqual(len(rej), 1)
        self.assertEqual(rej[0]["motif"], "JSON malformé")
        self.assertEqual(rej[0]["source_line"], 1)

    # 5. Ligne vide ignoree mais numerotation conservee.
    def test_ligne_vide_ignoree_mais_source_line_conservee(self) -> None:
        ligne_vide = (
            '{"id":"s01","date":"2026-10-19","period":"am","group":"A",'
            '"mode":"DG","title":"a","domain":"web","teacherId":"t1","status":"confirmed"}\n'
        )
        contenu = "\n" + ligne_vide + "\n\n" + ligne_vide
        acc, rej, sta = self.lancer(contenu)
        # 2 lignes non vides -> lus = 2 ; lignes vides ignorees.
        self.assertEqual(sta["lus"], 2)
        # La 1re ligne non vide est la ligne physique 2.
        self.assertEqual(acc[0]["source_line"], 2)
        # Le doublon est la ligne physique 4.
        self.assertEqual(sta["doublons"], 1)
        self.assertEqual(len(acc), 1)
        self.assertEqual(rej, [])
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])

    # 6. Poursuite du traitement apres une ligne incorrecte.
    def test_poursuite_apres_ligne_incorrecte(self) -> None:
        valide = (
            '{"id":"s02","date":"2026-10-19","period":"am","group":"B",'
            '"mode":"DG","title":"b","domain":"web","teacherId":"t2","status":"confirmed"}\n'
        )
        contenu = "pas du tout du JSON\n" + valide
        acc, rej, sta = self.lancer(contenu)
        self.assertEqual(len(rej), 1)
        self.assertEqual(len(acc), 1)
        self.assertEqual(acc[0]["id"], "s02")
        self.assertEqual(acc[0]["source_line"], 2)
        self.assertEqual(sta["lus"], 2)
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])

    # 7. Invariant sur le fichier fourni (seances.ndjson).
    def test_fichier_fourni(self) -> None:
        ici = Path(__file__).resolve().parent
        entree = ici / "seances.ndjson"
        acc, rej, sta = pipeline.traiter(entree)
        self.assertEqual(sta["lus"], 12)
        self.assertEqual(sta["acceptes"], 6)
        self.assertEqual(sta["doublons"], 2)
        self.assertEqual(sta["rejets"], 4)
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])
        ids = [o["id"] for o in acc]
        self.assertEqual(ids, ["s01", "s02", "s03", "s04", "s05", "s06"])

    # 8. Determinisme : deux runs donnent le meme resultat.
    def test_determinisme(self) -> None:
        ici = Path(__file__).resolve().parent
        entree = ici / "seances.ndjson"
        a1, r1, s1 = pipeline.traiter(entree)
        a2, r2, s2 = pipeline.traiter(entree)
        self.assertEqual((a1, r1, s1), (a2, r2, s2))


if __name__ == "__main__":
    unittest.main()