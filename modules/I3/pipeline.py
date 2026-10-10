#!/usr/bin/env python3
"""I3 - Stream structuring.

Pipeline: read -> validate -> normalize -> deduplicate -> output.

Usage:
    python3 pipeline.py [input] [acceptes] [rejets] [stats]

Non-interactive command. The same file always produces the same result,
with no timezone dependency (dates as pure calendar arithmetic via
datetime.date, no local operations).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

DOMAINS = {"web", "data", "ia", "design", "marketing", "cyber", "system", "projet"}
GROUPS = {"A", "B", "Promotion"}
MODES = {"DG", "CE", "AUTO"}
PERIODS = {"am": "am", "matin": "am", "pm": "pm", "apres-midi": "pm", "après-midi": "pm"}
STATUSES = {
    "propose": "proposed",
    "proposed": "proposed",
    "confirme": "confirmed",
    "confirmed": "confirmed",
}
TEACHERS = {"t1", "t2", "t3"}


def normalize_date(v: str) -> str:
    """YYYY-MM-DD or DD/MM/YYYY -> YYYY-MM-DD; checks calendar validity."""
    s = v.strip()
    try:
        if "/" in s and "-" not in s:
            day, month, year = s.split("/")
        elif "-" in s and "/" not in s:
            year, month, day = s.split("-")
        else:
            raise ValueError("unrecognized date format")
        d = date(int(year), int(month), int(day))
    except (ValueError, TypeError) as e:
        raise ValueError(f"invalid calendar date: {v!r}") from e
    return d.strftime("%Y-%m-%d")


def validate_and_normalize(obj: Any, source_line: int) -> dict:
    """Validates and normalizes an object; raises ValueError(reason) if invalid."""
    if not isinstance(obj, dict):
        raise ValueError("invalid JSON object (not a dict)")

    raw_id = obj.get("id")
    if not isinstance(raw_id, str) or raw_id.strip() == "":
        raise ValueError("id empty or invalid type")
    norm_id = raw_id.strip()

    raw_title = obj.get("title")
    if not isinstance(raw_title, str) or raw_title.strip() == "":
        raise ValueError("title empty or invalid type")
    norm_title = raw_title.strip()

    raw_date = obj.get("date")
    if not isinstance(raw_date, str):
        raise ValueError("date: invalid type")
    norm_date = normalize_date(raw_date)

    raw_period = obj.get("period")
    if not isinstance(raw_period, str):
        raise ValueError("period: invalid type")
    norm_period = PERIODS.get(raw_period.strip())
    if norm_period is None:
        raise ValueError(f"invalid period: {raw_period!r}")

    raw_group = obj.get("group")
    if not isinstance(raw_group, str) or raw_group.strip() not in GROUPS:
        raise ValueError(f"invalid group: {raw_group!r}")
    norm_group = raw_group.strip()

    raw_mode = obj.get("mode")
    if not isinstance(raw_mode, str) or raw_mode.strip() not in MODES:
        raise ValueError(f"invalid mode: {raw_mode!r}")
    norm_mode = raw_mode.strip()

    raw_domain = obj.get("domain")
    if not isinstance(raw_domain, str) or raw_domain.strip() not in DOMAINS:
        raise ValueError(f"invalid domain: {raw_domain!r}")
    norm_domain = raw_domain.strip()

    raw_teacher = obj.get("teacherId")
    if raw_teacher == "":
        raise ValueError("teacherId: empty string is invalid")
    if raw_teacher is not None and raw_teacher not in TEACHERS:
        raise ValueError(f"invalid teacherId: {raw_teacher!r}")

    raw_status = obj.get("status")
    if not isinstance(raw_status, str):
        raise ValueError("status: invalid type")
    if raw_status.strip() not in STATUSES:
        raise ValueError(f"invalid status: {raw_status!r}")
    norm_status = STATUSES[raw_status.strip()]

    # Cross-constraints.
    if norm_mode == "AUTO":
        if raw_teacher is not None or norm_status != "proposed":
            raise ValueError("AUTO requires teacherId null and status 'proposed'")
    if norm_status == "confirmed" and raw_teacher not in TEACHERS:
        raise ValueError("status 'confirmed' requires a teacher (teacherId)")

    return {
        "id": norm_id,
        "date": norm_date,
        "period": norm_period,
        "group": norm_group,
        "mode": norm_mode,
        "title": norm_title,
        "domain": norm_domain,
        "teacherId": raw_teacher,
        "status": norm_status,
        "source_line": source_line,
    }


def process(input_path: Path) -> tuple[list[dict], list[dict], dict]:
    acceptes: list[dict] = []
    rejets: list[dict] = []
    seen: set[str] = set()
    lus = 0
    doublons = 0

    with input_path.open(encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            if raw.strip() == "":
                # Empty line: ignored, not counted in lus, but source_line preserved.
                continue
            lus += 1
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                rejets.append({"source_line": line_no, "motif": "malformed JSON"})
                continue
            try:
                normalized = validate_and_normalize(obj, line_no)
            except ValueError as e:
                rejets.append({"source_line": line_no, "motif": str(e)})
                continue
            if normalized["id"] in seen:
                doublons += 1
                continue
            seen.add(normalized["id"])
            acceptes.append(normalized)

    stats = {
        "lus": lus,
        "acceptes": len(acceptes),
        "rejets": len(rejets),
        "doublons": doublons,
    }
    # Invariant.
    assert stats["lus"] == stats["acceptes"] + stats["rejets"] + stats["doublons"], (
        f"invariant broken: {stats}"
    )
    return acceptes, rejets, stats


def write_outputs(
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
    input_path = Path(args[0]) if len(args) > 0 else Path("seances.ndjson")
    acceptes_path = Path(args[1]) if len(args) > 1 else Path("acceptes.ndjson")
    rejets_path = Path(args[2]) if len(args) > 2 else Path("rejets.ndjson")
    stats_path = Path(args[3]) if len(args) > 3 else Path("stats.json")

    acc, rej, sta = process(input_path)
    write_outputs(acc, rej, sta, acceptes_path, rejets_path, stats_path)
    print(
        f"lus={sta['lus']} acceptes={sta['acceptes']} "
        f"rejets={sta['rejets']} doublons={sta['doublons']} "
        f"-> {acceptes_path} | {rejets_path} | {stats_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
