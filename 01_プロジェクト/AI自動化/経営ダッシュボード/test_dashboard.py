from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import dashboard


class DashboardTests(unittest.TestCase):
    def write_freee_snapshot(self, vault: Path, deals: list[dict], partners: list[dict] | None = None):
        snapshot = vault / "02_経営/帳簿/freee_export/2026-07-16"
        snapshot.mkdir(parents=True)
        files = {
            "deals.json": {"deals": deals},
            "account_items.json": {"account_items": [{"id": 10, "name": "車両費"}]},
            "partners.json": {"partners": partners or []},
            "wallet_txns.json": {"wallet_txns": [{"date": "2026-07-16", "walletable_type": "bank_account"}]},
        }
        for name, payload in files.items():
            (snapshot / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def freee_expense(self, *, amount: int, partner_id: int | None = None) -> dict:
        return {
            "id": 1,
            "type": "expense",
            "issue_date": "2026-07-16",
            "amount": amount,
            "partner_id": partner_id,
            "details": [{
                "entry_side": "debit",
                "account_item_id": 10,
                "amount": amount,
                "description": "",
            }],
        }

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
        self.assertEqual(data["jobs"]["groups"]["running"][0]["name"], "スマホの相談窓口")
        self.assertEqual(data["youtube"]["target_to_date"], 20968)
        self.assertEqual(data["youtube"]["calendar_target_to_date"], 24194)
        self.assertEqual(data["youtube"]["daily_target_average"], 1613)
        self.assertEqual(sum(row["youtube_target"] for row in data["daily"]), 24194)
        self.assertEqual(
            sum(row["youtube_actual"] or 0 for row in data["daily"]),
            data["youtube"]["actual"],
        )
        self.assertTrue(all(
            row["youtube_difference"] is None
            for row in data["daily"] if row["youtube_actual"] is None
        ))
        self.assertTrue(data["today_note"]["tasks"])
        json.dumps(data, ensure_ascii=False)

    def test_mobile_breakpoints_exist(self):
        html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:520px)", html)
        self.assertIn('name="viewport"', html)

    def test_drive_receipt_is_added_as_pending_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt_dir = root / "expenses/2026/07"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "20260716_ENEOS_4,000.jpg").write_bytes(b"receipt")
            drive = dashboard.parse_drive_expenses(root / "expenses", "2026-07", dt.date(2026, 7, 16))
            freee = {
                "available": False, "total": 0, "categories": [], "matching_deals": [],
                "as_of": None, "updated_at": None, "source": "未取得",
                "latest_bank_date": None, "stale": True, "bank_stale": True,
                "warnings": ["freeeの経費データを確認できません"],
            }
            result = dashboard.reconcile_expenses(freee, drive)
            self.assertEqual(result["total"], 4000)
            self.assertEqual(result["pending"], 4000)
            self.assertEqual(result["pending_count"], 1)
            self.assertEqual(result["status"], "未取得あり")

    def test_freee_match_replaces_pending_without_double_counting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_freee_snapshot(
                root,
                [self.freee_expense(amount=4000, partner_id=20)],
                [{"id": 20, "name": "ENEOS"}],
            )
            receipt_dir = root / "expenses/2026/07"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "20260716_エネオス_4,000.jpg").write_bytes(b"receipt")
            freee = dashboard.parse_freee_expenses(root, "2026-07", dt.date(2026, 7, 16))
            drive = dashboard.parse_drive_expenses(root / "expenses", "2026-07", dt.date(2026, 7, 16))
            result = dashboard.reconcile_expenses(freee, drive)
            self.assertEqual(result["confirmed"], 4000)
            self.assertEqual(result["pending"], 0)
            self.assertEqual(result["total"], 4000)
            self.assertEqual(result["matched_receipt_count"], 1)
            self.assertEqual(sum(row["amount"] for row in result["breakdown"]), result["total"])

    def test_ambiguous_same_day_amount_stays_visible_for_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_freee_snapshot(root, [self.freee_expense(amount=4000)])
            receipt_dir = root / "expenses/2026/07"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "20260716_店A_4,000.jpg").write_bytes(b"a")
            (receipt_dir / "20260716_店B_4,000.jpg").write_bytes(b"b")
            freee = dashboard.parse_freee_expenses(root, "2026-07", dt.date(2026, 7, 16))
            drive = dashboard.parse_drive_expenses(root / "expenses", "2026-07", dt.date(2026, 7, 16))
            result = dashboard.reconcile_expenses(freee, drive)
            self.assertEqual(result["matched_receipt_count"], 0)
            self.assertEqual(result["ambiguous_count"], 2)
            self.assertEqual(result["pending_count"], 2)
            self.assertEqual(result["status"], "要確認")

    def test_duplicate_receipt_files_are_counted_once_and_foreign_amount_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "expenses/2026/07"
            root.mkdir(parents=True)
            (root / "20260716_出光_3,500.jpg").write_bytes(b"jpg")
            (root / "20260716_出光_3,500.pdf").write_bytes(b"pdf")
            (root / "20260716_OpenAI_USD88.30.pdf").write_bytes(b"usd")
            drive = dashboard.parse_drive_expenses(root.parents[1], "2026-07", dt.date(2026, 7, 16))
            self.assertEqual(len(drive["receipts"]), 1)
            self.assertEqual(drive["duplicate_count"], 1)
            self.assertEqual(drive["unparsed_count"], 1)

    def test_auto_refresh_and_expense_labels_exist(self):
        html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("freee確認済み", html)
        self.assertIn("freee反映待ち", html)
        self.assertIn("setInterval(()=>loadDashboard(true),60000)", html)
        self.assertIn("go(activePage,false)", html)


if __name__ == "__main__":
    unittest.main()
