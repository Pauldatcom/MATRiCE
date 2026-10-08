#!/usr/bin/env python3
"""I3 - Structuration de flux.

Pipeline: lecture -> validation -> normalisation -> deduplication -> sortie.

Usage:
    python3 pipeline.py [entree] [acceptes] [rejets] [stats]

Commande non interactive. Le meme fichier produit toujours le meme resultat,
sans dependance au fuseau horaire de la machine (dates en arithmetique
calendaire pure via datetime.date, pas d'operation locale).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

DOMAINES = {"web", "data", "ia", "design", "marketing", "cyber", "system", "projet"}
GROUPES = {"A", "B", "Promotion"}
MODES = {"DG", "CE", "AUTO"}
PERIODES = {"am": "am", "matin": "am", "pm": "pm", "apres-midi": "pm", "après-midi": "pm"}
STATUTS = {
    "propose": "proposed",
    "proposed": "proposed",
    "confirme": "confirmed",
    "confirmed": "confirmed",
}
FORMATEURS = {"t1", "t2", "t3"}


def normaliser_date(v: str) -> str:
    """YYYY-MM-DD ou DD/MM/YYYY -> YYYY-MM-DD ; verifie la validite calendaire."""
    s = v.strip()
    try:
        if "/" in s and "-" not in s:
            jour, mois, annee = s.split("/")
        elif "-" in s and "/" not in s:
            annee, mois, jour = s.split("-")
        else:
            raise ValueError("format de date non reconnu")
        d = date(int(annee), int(mois), int(jour))
    except (ValueError, TypeError) as e:
        raise ValueError(f"date calendaire invalide : {v!r}") from e
    return d.strftime("%Y-%m-%d")


def valider_et_normaliser(obj: Any, source_line: int) -> dict:
    """Valide et normalise un objet ; leve ValueError(motif) si invalide."""
    if not isinstance(obj, dict):
        raise ValueError("objet JSON invalide (pas un dictionnaire)")

    id_brut = obj.get("id")
    if not isinstance(id_brut, str) or id_brut.strip() == "":
        raise ValueError("id vide ou de type invalide")
    idn = id_brut.strip()

    title_brut = obj.get("title")
    if not isinstance(title_brut, str) or title_brut.strip() == "":
        raise ValueError("title vide ou de type invalide")
    titlen = title_brut.strip()

    date_brut = obj.get("date")
    if not isinstance(date_brut, str):
        raise ValueError("date: type invalide")
    daten = normaliser_date(date_brut)

    period_brut = obj.get("period")
    if not isinstance(period_brut, str):
        raise ValueError("period: type invalide")
    periodn = PERIODES.get(period_brut.strip())
    if periodn is None:
        raise ValueError(f"période invalide : {period_brut!r}")

    group_brut = obj.get("group")
    if not isinstance(group_brut, str) or group_brut.strip() not in GROUPES:
        raise ValueError(f"groupe invalide : {group_brut!r}")
    groupn = group_brut.strip()

    mode_brut = obj.get("mode")
    if not isinstance(mode_brut, str) or mode_brut.strip() not in MODES:
        raise ValueError(f"mode invalide : {mode_brut!r}")
    moden = mode_brut.strip()

    domain_brut = obj.get("domain")
    if not isinstance(domain_brut, str) or domain_brut.strip() not in DOMAINES:
        raise ValueError(f"domain invalide : {domain_brut!r}")
    domainn = domain_brut.strip()

    teacher_brut = obj.get("teacherId")
    if teacher_brut == "":
        raise ValueError("teacherId : chaîne vide invalide")
    if teacher_brut is not None and teacher_brut not in FORMATEURS:
        raise ValueError(f"teacherId invalide : {teacher_brut!r}")

    status_brut = obj.get("status")
    if not isinstance(status_brut, str):
        raise ValueError("status: type invalide")
    if status_brut.strip() not in STATUTS:
        raise ValueError(f"status invalide : {status_brut!r}")
    statusn = STATUTS[status_brut.strip()]

    # Contraintes croisees.
    if moden == "AUTO":
        if teacher_brut is not None or statusn != "proposed":
            raise ValueError("AUTO exige teacherId null et status « proposed »")
    if statusn == "confirmed" and teacher_brut not in FORMATEURS:
        raise ValueError("status « confirmed » exige un formateur (teacherId)")

    return {
        "id": idn,
        "date": daten,
        "period": periodn,
        "group": groupn,
        "mode": moden,
        "title": titlen,
        "domain": domainn,
        "teacherId": teacher_brut,
        "status": statusn,
        "source_line": source_line,
    }


def traiter(entree: Path) -> tuple[list[dict], list[dict], dict]:
    acceptes: list[dict] = []
    rejets: list[dict] = []
    vus: set[str] = set()
    lus = 0
    doublons = 0

    with entree.open(encoding="utf-8") as f:
        for no_ligne, brut in enumerate(f, start=1):
            if brut.strip() == "":
                # Ligne vide : ignoree, non comptee dans lus, mais source_line conserve.
                continue
            lus += 1
            try:
                obj = json.loads(brut)
            except json.JSONDecodeError:
                rejets.append({"source_line": no_ligne, "motif": "JSON malformé"})
                continue
            try:
                normalise = valider_et_normaliser(obj, no_ligne)
            except ValueError as e:
                rejets.append({"source_line": no_ligne, "motif": str(e)})
                continue
            if normalise["id"] in vus:
                doublons += 1
                continue
            vus.add(normalise["id"])
            acceptes.append(normalise)

    stats = {
        "lus": lus,
        "acceptes": len(acceptes),
        "rejets": len(rejets),
        "doublons": doublons,
    }
    # Invariant.
    assert stats["lus"] == stats["acceptes"] + stats["rejets"] + stats["doublons"], (
        f"invariant rompu : {stats}"
    )
    return acceptes, rejets, stats


def ecrire_sorties(
    acceptes: list[dict],
    rejets: list[dict],
    stats: dict,
    acceptes_path: Path,
    rejets_path: Path,
    stats_path: Path,
) -> None:
    with acceptes_path.open("w", encoding="utf-8") as f:
        for obj in acceptes:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    with rejets_path.open("w", encoding="utf-8") as f:
        for r in rejets:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def main(argv: list[str]) -> int:
    args = argv[1:]
    entree = Path(args[0]) if len(args) > 0 else Path("seances.ndjson")
    acceptes = Path(args[1]) if len(args) > 1 else Path("acceptes.ndjson")
    rejets = Path(args[2]) if len(args) > 2 else Path("rejets.ndjson")
    stats = Path(args[3]) if len(args) > 3 else Path("stats.json")

    acc, rej, sta = traiter(entree)
    ecrire_sorties(acc, rej, sta, acceptes, rejets, stats)
    print(
        f"lus={sta['lus']} acceptes={sta['acceptes']} "
        f"rejets={sta['rejets']} doublons={sta['doublons']} "
        f"-> {acceptes} | {rejets} | {stats}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))