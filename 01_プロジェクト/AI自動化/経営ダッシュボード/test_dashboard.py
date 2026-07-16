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
        expected_profit = None if data["finance"]["expense_partial"] else data["finance"]["revenue"] - data["finance"]["expenses"]
        self.assertEqual(data["finance"]["profit"], expected_profit)
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
            self.assertEqual(result["ambiguous_count"], 1)
            self.assertEqual(result["pending_count"], 1)
            self.assertEqual(result["pending"], 4000)
            self.assertEqual(result["total"], 8000)
            self.assertEqual(result["status"], "要確認")

    def test_duplicate_receipt_files_are_counted_once_and_foreign_amount_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "expenses/2026/07"
            root.mkdir(parents=True)
            (root / "20260716_出光_3,500.jpg").write_bytes(b"same receipt")
            (root / "20260716_出光_3,500.pdf").write_bytes(b"same receipt")
            (root / "20260716_OpenAI_USD88.30.pdf").write_bytes(b"usd")
            drive = dashboard.parse_drive_expenses(root.parents[1], "2026-07", dt.date(2026, 7, 16))
            self.assertEqual(len(drive["receipts"]), 1)
            self.assertEqual(drive["duplicate_count"], 1)
            self.assertEqual(drive["unparsed_count"], 1)

    def test_same_named_receipts_with_different_contents_are_not_silently_merged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "expenses/2026/07"
            root.mkdir(parents=True)
            (root / "20260716_出光_3,500.jpg").write_bytes(b"first purchase")
            (root / "20260716_出光_3,500.pdf").write_bytes(b"second purchase")
            drive = dashboard.parse_drive_expenses(root.parents[1], "2026-07", dt.date(2026, 7, 16))
            self.assertEqual(len(drive["receipts"]), 2)
            self.assertEqual(drive["duplicate_count"], 0)

    def test_card_statement_date_can_lag_receipt_by_three_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deal = self.freee_expense(amount=4000, partner_id=20)
            deal["issue_date"] = "2026-07-18"
            self.write_freee_snapshot(root, [deal], [{"id": 20, "name": "ENEOS"}])
            receipt_dir = root / "expenses/2026/07"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "20260716_エネオス_4,000.jpg").write_bytes(b"receipt")
            freee = dashboard.parse_freee_expenses(root, "2026-07", dt.date(2026, 7, 19))
            drive = dashboard.parse_drive_expenses(root / "expenses", "2026-07", dt.date(2026, 7, 19))
            result = dashboard.reconcile_expenses(freee, drive)
            self.assertEqual(result["matched_receipt_count"], 1)
            self.assertEqual(result["pending"], 0)
            self.assertEqual(result["total"], 4000)

    def test_date_window_matching_maximizes_one_to_one_matches(self):
        freee = {
            "available": True, "total": 8000,
            "categories": [{"name": "車両費", "amount": 8000, "status": "確認済み"}],
            "matching_deals": [
                {"id": 1, "date": "2026-07-03", "amount": 4000, "merchant": "ENEOS", "merchant_key": "eneos", "merchant_reliable": True},
                {"id": 2, "date": "2026-07-07", "amount": 4000, "merchant": "ENEOS", "merchant_key": "eneos", "merchant_reliable": True},
            ],
            "as_of": "2026-07-08", "updated_at": None, "source": "テスト",
            "latest_bank_date": "2026-07-08", "stale": False, "bank_stale": False,
            "latest_check_failed": False, "warnings": [],
        }
        drive = {
            "available": True,
            "receipts": [
                {"date": "2026-07-01", "merchant": "ENEOS", "merchant_key": "eneos", "amount": 4000, "updated_at": None, "file_name": "a.jpg"},
                {"date": "2026-07-04", "merchant": "ENEOS", "merchant_key": "eneos", "amount": 4000, "updated_at": None, "file_name": "b.jpg"},
            ],
            "updated_at": None, "unparsed_count": 0, "duplicate_count": 0,
        }
        result = dashboard.reconcile_expenses(freee, drive)
        self.assertEqual(result["matched_receipt_count"], 2)
        self.assertEqual(result["pending"], 0)
        self.assertEqual(result["total"], 8000)

    def test_missing_freee_and_empty_drive_are_not_reported_as_zero(self):
        freee = {
            "available": False, "total": 0, "categories": [], "matching_deals": [],
            "as_of": None, "updated_at": None, "source": "未取得",
            "latest_bank_date": None, "stale": True, "bank_stale": True,
            "latest_check_failed": True, "warnings": ["未取得"],
        }
        drive = {
            "available": True, "receipts": [], "updated_at": None,
            "unparsed_count": 0, "duplicate_count": 0,
        }
        result = dashboard.reconcile_expenses(freee, drive)
        self.assertIsNone(result["confirmed"])
        self.assertIsNone(result["total"])
        self.assertTrue(result["partial"])

    def test_unknown_freee_merchant_stays_for_review(self):
        freee = {
            "available": True, "total": 4000,
            "categories": [{"name": "車両費", "amount": 4000, "status": "確認済み"}],
            "matching_deals": [{
                "id": 1, "date": "2026-07-16", "amount": 4000,
                "merchant": "", "merchant_key": "", "merchant_reliable": False,
            }],
            "as_of": "2026-07-16", "updated_at": None, "source": "テスト",
            "latest_bank_date": "2026-07-16", "stale": False, "bank_stale": False,
            "latest_check_failed": False, "warnings": [],
        }
        drive = {
            "available": True,
            "receipts": [{
                "date": "2026-07-16", "merchant": "ENEOS", "merchant_key": "eneos",
                "amount": 4000, "updated_at": None, "file_name": "receipt.jpg",
            }],
            "updated_at": None, "unparsed_count": 0, "duplicate_count": 0,
        }
        result = dashboard.reconcile_expenses(freee, drive)
        self.assertEqual(result["matched_receipt_count"], 0)
        self.assertEqual(result["ambiguous_count"], 1)
        self.assertEqual(result["pending"], 0)
        self.assertEqual(result["total"], 4000)
        self.assertEqual(result["status"], "要確認")

    def test_failed_live_check_keeps_fresh_cache_in_review_state(self):
        freee = {
            "available": True, "total": 0, "categories": [], "matching_deals": [],
            "as_of": "2026-07-16", "updated_at": None, "source": "直前の確認",
            "latest_bank_date": "2026-07-16", "stale": False, "bank_stale": False,
            "latest_check_failed": True, "warnings": ["最新確認失敗"],
        }
        drive = {
            "available": True, "receipts": [], "updated_at": None,
            "unparsed_count": 0, "duplicate_count": 0,
        }
        result = dashboard.reconcile_expenses(freee, drive)
        self.assertTrue(result["partial"])
        self.assertEqual(result["status"], "要確認")

    def test_auto_refresh_and_expense_labels_exist(self):
        html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("freee確認済み", html)
        self.assertIn("freee反映待ち", html)
        self.assertIn("setInterval(()=>loadDashboard(true),60000)", html)
        self.assertIn("go(activePage,false)", html)


if __name__ == "__main__":
    unittest.main()
