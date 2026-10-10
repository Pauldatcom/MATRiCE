"""I3 pipeline tests (stdlib unittest).

Command: python3 -m unittest -v test_pipeline.py
"""

import tempfile
import unittest
from pathlib import Path

import pipeline


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_pipeline(self, content: str):
        entry = write(self.tmp, "entry.ndjson", content)
        acc, rej, sta = pipeline.process(entry)
        return acc, rej, sta

    # 1. Valid entry.
    def test_valid_entry_normalized(self) -> None:
        acc, rej, sta = self.run_pipeline(
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

    # 2. Invalid entry: non-calendar date.
    def test_invalid_date(self) -> None:
        acc, rej, sta = self.run_pipeline(
            '{"id":"bad","date":"2026-02-30","period":"am","group":"A",'
            '"mode":"DG","title":"x","domain":"web","teacherId":"t1","status":"proposed"}\n'
        )
        self.assertEqual(acc, [])
        self.assertEqual(len(rej), 1)
        self.assertIn("date", rej[0]["motif"])
        self.assertEqual(rej[0]["source_line"], 1)

    # 2b. Invalid entry: period out of domain.
    def test_invalid_period(self) -> None:
        acc, rej, sta = self.run_pipeline(
            '{"id":"bad","date":"2026-10-20","period":"soir","group":"A",'
            '"mode":"DG","title":"x","domain":"web","teacherId":"t1","status":"proposed"}\n'
        )
        self.assertEqual(acc, [])
        self.assertEqual(len(rej), 1)
        self.assertIn("period", rej[0]["motif"])

    # 3. Duplicate: counted in doublons, neither accepted nor rejected.
    def test_duplicate(self) -> None:
        line = (
            '{"id":"s01","date":"2026-10-19","period":"am","group":"A",'
            '"mode":"DG","title":"a","domain":"web","teacherId":"t1","status":"confirmed"}\n'
        )
        acc, rej, sta = self.run_pipeline(line + line)
        self.assertEqual(len(acc), 1)
        self.assertEqual(rej, [])
        self.assertEqual(sta["doublons"], 1)
        self.assertEqual(sta["lus"], 2)
        # invariant
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])

    # 4. Malformed JSON.
    def test_malformed_json(self) -> None:
        acc, rej, sta = self.run_pipeline('{"id":"bad4","title":"truncated JSON"\n')
        self.assertEqual(acc, [])
        self.assertEqual(len(rej), 1)
        self.assertEqual(rej[0]["motif"], "malformed JSON")
        self.assertEqual(rej[0]["source_line"], 1)

    # 5. Empty line ignored but line numbering preserved.
    def test_empty_line_ignored_source_line_preserved(self) -> None:
        valid_line = (
            '{"id":"s01","date":"2026-10-19","period":"am","group":"A",'
            '"mode":"DG","title":"a","domain":"web","teacherId":"t1","status":"confirmed"}\n'
        )
        content = "\n" + valid_line + "\n\n" + valid_line
        acc, rej, sta = self.run_pipeline(content)
        # 2 non-empty lines -> lus = 2; empty lines ignored.
        self.assertEqual(sta["lus"], 2)
        # First non-empty line is physical line 2.
        self.assertEqual(acc[0]["source_line"], 2)
        # The duplicate is physical line 4.
        self.assertEqual(sta["doublons"], 1)
        self.assertEqual(len(acc), 1)
        self.assertEqual(rej, [])
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])

    # 6. Processing continues after an incorrect line.
    def test_continuation_after_bad_line(self) -> None:
        valid = (
            '{"id":"s02","date":"2026-10-19","period":"am","group":"B",'
            '"mode":"DG","title":"b","domain":"web","teacherId":"t2","status":"confirmed"}\n'
        )
        content = "not JSON at all\n" + valid
        acc, rej, sta = self.run_pipeline(content)
        self.assertEqual(len(rej), 1)
        self.assertEqual(len(acc), 1)
        self.assertEqual(acc[0]["id"], "s02")
        self.assertEqual(acc[0]["source_line"], 2)
        self.assertEqual(sta["lus"], 2)
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])

    # 7. Invariant on the provided file (seances.ndjson).
    def test_provided_file(self) -> None:
        here = Path(__file__).resolve().parent
        entry = here / "seances.ndjson"
        acc, rej, sta = pipeline.process(entry)
        self.assertEqual(sta["lus"], 12)
        self.assertEqual(sta["acceptes"], 6)
        self.assertEqual(sta["doublons"], 2)
        self.assertEqual(sta["rejets"], 4)
        self.assertEqual(sta["lus"], sta["acceptes"] + sta["rejets"] + sta["doublons"])
        ids = [o["id"] for o in acc]
        self.assertEqual(ids, ["s01", "s02", "s03", "s04", "s05", "s06"])

    # 8. Determinism: two runs produce the same result.
    def test_determinism(self) -> None:
        here = Path(__file__).resolve().parent
        entry = here / "seances.ndjson"
        a1, r1, s1 = pipeline.process(entry)
        a2, r2, s2 = pipeline.process(entry)
        self.assertEqual((a1, r1, s1), (a2, r2, s2))


if __name__ == "__main__":
    unittest.main()
