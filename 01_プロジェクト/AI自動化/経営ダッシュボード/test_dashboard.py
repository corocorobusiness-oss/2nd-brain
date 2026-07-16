import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import dashboard


class DashboardTests(unittest.TestCase):
    def test_yen_blank_is_missing(self):
        self.assertIsNone(dashboard.yen("円"))
        self.assertEqual(dashboard.yen("¥12,345"), 12345)

    def test_sales_note_keeps_missing_separate_from_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "note.md"
            path.write_text("""## 💰 今日の売上
| 事業 | 売上 | メモ |
|---|---:|---|
| Uber Eats | ¥5,000 | 12:00時点 |
| 出前館 | 円 | |
| YouTube | 円 | |
""", encoding="utf-8")
            result = dashboard.parse_sales_note(path)
            self.assertEqual(result["delivery"], 5000)
            self.assertFalse(result["has_youtube"])
            self.assertTrue(result["provisional"])

    def test_real_snapshot_is_cut_off_at_yesterday(self):
        data = dashboard.build_dashboard(
            Path("~/2nd-Brain").expanduser(),
            Path("~/Projects/youtube").expanduser(),
            dt.date(2026, 7, 16),
        )
        self.assertEqual(data["cutoff"], "2026-07-15")
        self.assertEqual(len(data["daily"]), 15)
        self.assertEqual(data["youtube"]["schedule"][0]["title"], "毛利軍｜秀吉を追撃しなかった理由")
        self.assertEqual(data["jobs"]["counts"], {"running": 27, "watch": 2, "stopped": 4})
        json.dumps(data, ensure_ascii=False)

    def test_mobile_breakpoints_exist(self):
        html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:520px)", html)
        self.assertIn('name="viewport"', html)


if __name__ == "__main__":
    unittest.main()
