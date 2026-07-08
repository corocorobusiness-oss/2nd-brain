#!/usr/bin/env python3
"""validate_dic.py v2 の回帰テスト。

家康回（2026-06-28_家康影武者説）で実際に起きた漏れ・誤読を fixture 化してあり、
このテストが通らない validator は配布してはいけない。

実行:
  cd <skill-root> && python3 tests/test_validate_dic.py
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ieyasu"

spec = importlib.util.spec_from_file_location(
    "validate_dic", SKILL_ROOT / "scripts" / "validate_dic.py"
)
validate_dic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_dic)

# 家康回で実際に漏れた6語（監査 2026-06-30）。これが FAIL にならない validator は不合格。
IEYASU_LEAKED_TERMS = {"葦", "三河後風土記", "天海", "隆慶一郎", "大火傷", "広忠"}


def run(dic, extra_args=()):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)
    rc = validate_dic.main(
        [str(dic), "--script", str(FIXTURES / "script.csv"), "--json", str(report_path)]
        + list(extra_args)
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report_path.unlink()
    return rc, report


class TestIeyasuRegression(unittest.TestCase):
    def test_good_dic_passes(self):
        rc, report = run(FIXTURES / "ymm4_user_good.dic")
        self.assertEqual(rc, 0, msg=json.dumps(report["fail"], ensure_ascii=False))
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["missing_must_candidates"], 0)
        self.assertEqual(report["wrong_known_readings"], 0)

    def test_leaky_dic_fails_on_all_leaked_terms(self):
        rc, report = run(FIXTURES / "ymm4_user_leaky.dic")
        self.assertEqual(rc, 1)
        missing = {f["surface"] for f in report["fail"] if f["code"] == "missing_must"}
        self.assertTrue(
            IEYASU_LEAKED_TERMS <= missing,
            msg=f"検出漏れ: {IEYASU_LEAKED_TERMS - missing}",
        )

    def test_leaky_dic_fails_on_wrong_reading(self):
        # 村岡素一郎=むらおかそいちろう は「登録済みだが誤読」。漏れより危険な誤読固定として FAIL。
        rc, report = run(FIXTURES / "ymm4_user_leaky.dic")
        self.assertEqual(rc, 1)
        wrong = {f["surface"] for f in report["fail"] if f["code"] == "wrong_known_reading"}
        self.assertIn("村岡素一郎", wrong)
        bad = {f["surface"] for f in report["fail"] if f["code"] == "bad_reading_registered"}
        self.assertIn("村岡素一郎", bad)


class TestFormatChecks(unittest.TestCase):
    def _run_inline(self, dic_text):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".dic", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(dic_text)
            dic_path = Path(tmp.name)
        rc, report = run(dic_path)
        dic_path.unlink()
        return rc, report

    def test_batting_entry_requires_regex_flag(self):
        rc, report = self._run_inline("1\t0\t2（二）\t2ばんせかんど\t\t1\n")
        codes = {f["code"] for f in report["fail"]}
        self.assertIn("regex_flag_missing", codes)

    def test_kanji_in_reading_fails(self):
        rc, report = self._run_inline("1\t0\t葦\t葦\t\t1\n")
        codes = {f["code"] for f in report["fail"]}
        self.assertIn("kanji_in_reading", codes)

    def test_duplicate_surface_fails(self):
        rc, report = self._run_inline(
            "1\t0\t葦\tあし\t\t1\n1\t0\t葦\tよし\t\t1\n"
        )
        codes = {f["code"] for f in report["fail"]}
        self.assertIn("duplicate_surface", codes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
