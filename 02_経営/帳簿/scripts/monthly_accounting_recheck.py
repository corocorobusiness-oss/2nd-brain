#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


BUSINESSES = ("Uber Eats", "出前館", "YouTube", "合計")
DRIVE_ROOT = Path(
    "/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ"
)


@dataclass
class Finding:
    severity: str
    check: str
    detail: str
    evidence: str = ""


def jst_now() -> dt.datetime:
    return dt.datetime.now(ZoneInfo("Asia/Tokyo"))


def vault_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monthly accounting independent recheck")
    parser.add_argument("--month", help="Target month as YYYY-MM. Default: previous month.")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD for verification.")
    parser.add_argument("--force", action="store_true", help="Run even if a PASS state exists.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary.")
    return parser.parse_args()


def month_bounds(month: str) -> tuple[dt.date, dt.date]:
    year, mon = [int(x) for x in month.split("-")]
    start = dt.date(year, mon, 1)
    if mon == 12:
        end = dt.date(year, 12, 31)
    else:
        end = dt.date(year, mon + 1, 1) - dt.timedelta(days=1)
    return start, end


def previous_month(today: dt.date) -> str:
    first = today.replace(day=1)
    prev = first - dt.timedelta(days=1)
    return f"{prev.year:04d}-{prev.month:02d}"


def yen_int(text: str) -> int | None:
    m = re.search(r"[-+]?\d[\d,]*", text.replace("，", ","))
    if not m:
        return None
    return int(m.group(0).replace(",", ""))


def read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_freee_export(vault: Path, start: dt.date, end: dt.date, today: dt.date) -> Path | None:
    base = vault / "02_経営/帳簿/freee_export"
    if not base.exists():
        return None
    dated: list[tuple[dt.date, Path]] = []
    for child in base.iterdir():
        if not child.is_dir():
            continue
        try:
            day = dt.date.fromisoformat(child.name)
        except ValueError:
            continue
        if day <= today:
            dated.append((day, child))
    if not dated:
        return None
    after_close = [(day, path) for day, path in dated if day >= end + dt.timedelta(days=1)]
    if after_close:
        return sorted(after_close)[-1][1]
    return sorted(dated)[-1][1]


def parse_daily_sales(vault: Path, start: dt.date, end: dt.date) -> tuple[dict[str, int], dict[str, int], list[str]]:
    totals = {name: 0 for name in BUSINESSES}
    first_half = {"出前館": 0}
    second_half = {"出前館": 0}
    missing: list[str] = []
    daily_dir = vault / "05_日誌"

    day = start
    while day <= end:
        path = daily_dir / f"{day.isoformat()}.md"
        if not path.exists():
            missing.append(path.name)
            day += dt.timedelta(days=1)
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 2 or cells[0] not in BUSINESSES:
                continue
            amount = yen_int(cells[1])
            if amount is None:
                continue
            totals[cells[0]] += amount
            if cells[0] == "出前館":
                if day.day <= 15:
                    first_half["出前館"] += amount
                else:
                    second_half["出前館"] += amount
        day += dt.timedelta(days=1)
    totals["_出前館_1_15"] = first_half["出前館"]
    totals["_出前館_16_end"] = second_half["出前館"]
    return totals, first_half, missing


def partner_name(deal: dict, partners: dict[int, str]) -> str:
    partner_id = deal.get("partner_id")
    if partner_id in partners:
        return partners[partner_id]
    for detail in deal.get("details") or []:
        detail_partner_id = detail.get("partner_id")
        if detail_partner_id in partners:
            return partners[detail_partner_id]
        desc = detail.get("description") or ""
        if "Google" in desc or "AdSense" in desc:
            return "Google"
    return "未設定"


def freee_month_summary(export_dir: Path, start: dt.date, end: dt.date) -> tuple[dict, list[Finding]]:
    findings: list[Finding] = []
    deals_path = export_dir / "deals.json"
    partners_path = export_dir / "partners.json"
    if not deals_path.exists():
        return {}, [Finding("FAIL", "freee_export", f"{deals_path} がありません")]
    if not partners_path.exists():
        return {}, [Finding("FAIL", "freee_export", f"{partners_path} がありません")]

    deals_data = read_json(deals_path)
    partners_data = read_json(partners_path)
    partners = {p["id"]: p["name"] for p in partners_data.get("partners", []) if "id" in p and "name" in p}
    monthly = [
        deal
        for deal in deals_data.get("deals", [])
        if start.isoformat() <= deal.get("issue_date", "") <= end.isoformat()
    ]
    aggregate: dict[str, dict[str, int]] = {"income": {}, "expense": {}}
    unpartnered: list[str] = []
    for deal in monthly:
        kind = deal.get("type", "unknown")
        name = partner_name(deal, partners)
        amount = int(deal.get("amount") or 0)
        aggregate.setdefault(kind, {})
        aggregate[kind][name] = aggregate[kind].get(name, 0) + amount
        if name == "未設定":
            unpartnered.append(f"{deal.get('issue_date')} ¥{amount:,} {deal.get('id')}")

    if unpartnered:
        findings.append(
            Finding(
                "WARN",
                "freee取引",
                "取引先未設定の月内取引があります",
                " / ".join(unpartnered[:5]),
            )
        )
    else:
        findings.append(Finding("OK", "freee取引", f"6月内取引 {len(monthly)}件を読取"))

    return {
        "monthly_deal_count": len(monthly),
        "aggregate": aggregate,
        "deals": monthly,
    }, findings


def compare_amount(check: str, left_label: str, left: int, right_label: str, right: int) -> Finding:
    if left == right:
        return Finding("OK", check, f"{left_label} と {right_label} が一致", f"¥{left:,}")
    return Finding(
        "FAIL",
        check,
        f"{left_label} と {right_label} が不一致",
        f"{left_label}=¥{left:,} / {right_label}=¥{right:,}",
    )


def amount_from_pdf_name(path: Path) -> int | None:
    m = re.search(r"_(\d+)\.pdf$", path.name)
    if not m:
        return None
    return int(m.group(1))


def cache_path(vault: Path) -> Path:
    return vault / "06_エージェント運用/30_ヘルスチェック/monthly_accounting_recheck_evidence_cache.json"


def load_cache(vault: Path) -> dict:
    path = cache_path(vault)
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def save_cache(vault: Path, cache: dict) -> None:
    write_json(cache_path(vault), cache)


def cached_or_found_pdf(
    vault: Path,
    cache: dict,
    cache_key: str,
    directory: Path,
    pattern: str,
) -> tuple[Path | None, int | None, bool]:
    pdfs = sorted(directory.glob(pattern)) if directory.exists() else []
    if pdfs:
        pdf = pdfs[-1]
        amount = amount_from_pdf_name(pdf)
        if amount is not None:
            cache[cache_key] = {"path": str(pdf), "amount": amount, "source": "drive-glob"}
        return pdf, amount, False
    cached = cache.get(cache_key) or {}
    if "path" in cached and "amount" in cached:
        return Path(cached["path"]), int(cached["amount"]), True
    return None, None, False


def check_demaecan_evidence(
    vault: Path,
    start: dt.date,
    end: dt.date,
    today: dt.date,
    daily_totals: dict[str, int],
    freee_summary: dict,
) -> list[Finding]:
    findings: list[Finding] = []
    year = start.year
    mon = start.month
    dem_dir = DRIVE_ROOT / "売上証憑/出前館" / str(year)
    cache = load_cache(vault)

    first_glob = f"{year}{mon:02d}01-{mon:02d}15_出前館_配達実績_*.pdf"
    first_key = f"{year}-{mon:02d}-demaecan-01-15"
    first_pdf, amount, from_cache = cached_or_found_pdf(vault, cache, first_key, dem_dir, first_glob)
    if first_pdf is None:
        findings.append(Finding("FAIL", "出前館上旬PDF", f"{first_glob} が見つかりません"))
    else:
        if amount is None:
            findings.append(Finding("FAIL", "出前館上旬PDF", "ファイル名から金額を読めません", first_pdf.name))
        else:
            source = "PDF金額(cache)" if from_cache else "PDF金額"
            finding = compare_amount(
                "出前館上旬PDF",
                "日誌1-15合計",
                daily_totals.get("_出前館_1_15", 0),
                source,
                amount,
            )
            if from_cache and finding.severity == "OK":
                finding.evidence = f"¥{amount:,} / Driveはlaunchdから読めないためVault内cache使用"
            findings.append(finding)
            dem_income = (freee_summary.get("aggregate") or {}).get("income", {}).get("出前館", 0)
            matching_deal = any(
                deal.get("type") == "income"
                and partner_amount_is_demaecan(deal)
                and int(deal.get("amount") or 0) == amount
                for deal in freee_summary.get("deals", [])
            )
            if matching_deal:
                findings.append(Finding("OK", "出前館上旬freee", "PDF金額と同額のfreee出前館取引があります", f"¥{amount:,}"))
            else:
                findings.append(
                    Finding(
                        "FAIL",
                        "出前館上旬freee",
                        "PDF金額と同額のfreee出前館取引が見つかりません",
                        f"PDF=¥{amount:,} / freee出前館合計=¥{dem_income:,}",
                    )
                )

    second_glob = f"{year}{mon:02d}16-{mon:02d}{end.day:02d}_出前館_配達実績_*.pdf"
    second_key = f"{year}-{mon:02d}-demaecan-16-end"
    second_pdf, amount, from_cache = cached_or_found_pdf(vault, cache, second_key, dem_dir, second_glob)
    if second_pdf is not None:
        if amount is None:
            findings.append(Finding("FAIL", "出前館下旬PDF", "ファイル名から金額を読めません", second_pdf.name))
        else:
            source = "PDF金額(cache)" if from_cache else "PDF金額"
            finding = compare_amount(
                "出前館下旬PDF",
                "日誌16-end合計",
                daily_totals.get("_出前館_16_end", 0),
                source,
                amount,
            )
            if from_cache and finding.severity == "OK":
                finding.evidence = f"¥{amount:,} / Driveはlaunchdから読めないためVault内cache使用"
            findings.append(finding)
    else:
        next_month_day = (end + dt.timedelta(days=1)).replace(day=1)
        severity = "WARN" if today.day <= 5 and today >= next_month_day else "FAIL"
        findings.append(
            Finding(
                severity,
                "出前館下旬PDF",
                "6/16-月末分PDFがまだ見つかりません",
                f"{second_glob} / 日誌16-end合計=¥{daily_totals.get('_出前館_16_end', 0):,}",
            )
        )
    save_cache(vault, cache)
    return findings


def partner_amount_is_demaecan(deal: dict) -> bool:
    if deal.get("partner_id") == 112727657:
        return True
    for detail in deal.get("details") or []:
        if detail.get("partner_id") == 112727657:
            return True
    return False


def check_monthly_report(start: dt.date, today: dt.date) -> list[Finding]:
    report_dir = DRIVE_ROOT / "経費精算/収支レポート" / str(start.year)
    report = report_dir / f"{start.year}年{start.month:02d}月_月次レポート.md"
    if report.exists():
        return [Finding("OK", "月次レポート", "Drive月次レポートが存在します", str(report))]
    severity = "WARN" if today.day <= 5 else "FAIL"
    return [Finding(severity, "月次レポート", "Drive月次レポートが未生成です", str(report))]


def check_monthly_log(today: dt.date) -> list[Finding]:
    log = Path("/Users/kojinn/.claude/scripts/monthly_accounting.log")
    if not log.exists():
        severity = "WARN" if today.day <= 5 else "FAIL"
        return [Finding(severity, "monthly_accounting.log", "ログが未生成です", str(log))]
    text = log.read_text(encoding="utf-8", errors="replace")[-2000:]
    if "weekly limit" in text or "usage limit" in text or "limit" in text.lower():
        severity = "WARN" if today.day <= 5 else "FAIL"
        return [
            Finding(
                severity,
                "monthly_accounting.log",
                "月次経理本体がLLM利用上限で止まっています",
                "ログ末尾に limit 文言あり",
            )
        ]
    return [Finding("OK", "monthly_accounting.log", "月次経理ログに利用上限停止は見当たりません", str(log))]


def run_seed_check(today: dt.date) -> Finding:
    quarterly_seed_months = {1, 4, 7, 10}
    if today.month not in quarterly_seed_months:
        return Finding("OK", "シード照合", "今月は四半期シード月ではないためスキップ")
    seeded = compare_amount("seed:出前館既知不一致", "seed日誌", 9438, "seedPDF", 9437)
    if seeded.severity == "FAIL":
        return Finding("OK", "シード照合", "既知の不一致を検知できました", seeded.evidence)
    return Finding("FAIL", "シード照合", "既知の不一致を検知できませんでした")


def status_from(findings: list[Finding]) -> str:
    if any(f.severity == "FAIL" for f in findings):
        return "FAIL"
    if any(f.severity == "WARN" for f in findings):
        return "WARN"
    return "PASS"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_report(
    vault: Path,
    month: str,
    today: dt.date,
    export_dir: Path | None,
    daily_totals: dict[str, int],
    freee_summary: dict,
    findings: list[Finding],
) -> Path:
    report_dir = vault / "02_経営/帳簿/レポート"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"月次経理独立再検証_{month}.md"
    status = status_from(findings)
    income = (freee_summary.get("aggregate") or {}).get("income", {})
    expense = (freee_summary.get("aggregate") or {}).get("expense", {})

    rows = "\n".join(
        f"| {f.severity} | {md_escape(f.check)} | {md_escape(f.detail)} | {md_escape(f.evidence)} |"
        for f in findings
    )
    body = f"""# 月次経理独立再検証 {month}

- 実行日: {today.isoformat()}
- 判定: **{status}**
- freeeスナップショット: `{export_dir if export_dir else 'なし'}`
- 方針: 読み取り専用。freee・Drive・Discordへの書き込みなし。

## 日誌売上合計

| 事業 | 金額 |
|---|---:|
| Uber Eats | ¥{daily_totals.get('Uber Eats', 0):,} |
| 出前館 | ¥{daily_totals.get('出前館', 0):,} |
| YouTube | ¥{daily_totals.get('YouTube', 0):,} |
| 出前館 1-15 | ¥{daily_totals.get('_出前館_1_15', 0):,} |
| 出前館 16-end | ¥{daily_totals.get('_出前館_16_end', 0):,} |

## freee月内取引集計

### 収入
{format_amount_map(income)}

### 支出
{format_amount_map(expense)}

## 検証結果

| 判定 | 項目 | 内容 | 根拠 |
|---|---|---|---|
{rows}

## 次アクション

{next_actions(findings)}
"""
    report.write_text(body.rstrip() + "\n", encoding="utf-8")
    return report


def format_amount_map(items: dict[str, int]) -> str:
    if not items:
        return "- なし"
    return "\n".join(f"- {name}: ¥{amount:,}" for name, amount in sorted(items.items()))


def next_actions(findings: list[Finding]) -> str:
    actionable = [f for f in findings if f.severity in {"WARN", "FAIL"}]
    if not actionable:
        return "- なし"
    return "\n".join(f"- [{f.severity}] {f.check}: {f.detail}" for f in actionable)


def main() -> int:
    args = parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else jst_now().date()
    month = args.month or previous_month(today)
    start, end = month_bounds(month)
    vault = vault_root()
    state_path = vault / "06_エージェント運用/30_ヘルスチェック/monthly_accounting_recheck_state.json"

    if state_path.exists() and not args.force:
        state = read_json(state_path)
        month_state = (state.get("months") or {}).get(month, {})
        if month_state.get("status") == "PASS":
            message = {
                "status": "SKIP",
                "reason": "PASS state exists",
                "month": month,
                "report": month_state.get("report"),
            }
            print(json.dumps(message, ensure_ascii=False) if args.json else f"SKIP {month}: PASS state exists")
            return 0

    findings: list[Finding] = []
    daily_totals, _first_half, missing_notes = parse_daily_sales(vault, start, end)
    if missing_notes:
        findings.append(Finding("WARN", "日誌", "月内の日誌が欠けています", ", ".join(missing_notes[:10])))
    else:
        findings.append(Finding("OK", "日誌", "月内の日誌ファイルを全日読取"))

    export_dir = find_freee_export(vault, start, end, today)
    freee_summary: dict = {}
    if export_dir is None:
        findings.append(Finding("FAIL", "freee_export", "月次検証に使えるfreeeスナップショットがありません"))
    else:
        findings.append(Finding("OK", "freee_export", "freeeスナップショットを使用", str(export_dir)))
        freee_summary, freee_findings = freee_month_summary(export_dir, start, end)
        findings.extend(freee_findings)

    findings.extend(check_demaecan_evidence(vault, start, end, today, daily_totals, freee_summary))
    findings.extend(check_monthly_report(start, today))
    findings.extend(check_monthly_log(today))
    findings.append(run_seed_check(today))

    report = write_report(vault, month, today, export_dir, daily_totals, freee_summary, findings)
    status = status_from(findings)
    state = read_json(state_path) if state_path.exists() else {"months": {}}
    state.setdefault("months", {})[month] = {
        "status": status,
        "last_run_at": jst_now().isoformat(),
        "report": str(report),
        "freee_export": str(export_dir) if export_dir else None,
        "finding_counts": {
            "OK": sum(1 for f in findings if f.severity == "OK"),
            "WARN": sum(1 for f in findings if f.severity == "WARN"),
            "FAIL": sum(1 for f in findings if f.severity == "FAIL"),
        },
    }
    state["last_month"] = month
    state["last_status"] = status
    write_json(state_path, state)

    payload = {"status": status, "month": month, "report": str(report), "state": str(state_path)}
    print(json.dumps(payload, ensure_ascii=False) if args.json else f"{status} {month} report={report}")
    return 2 if status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
