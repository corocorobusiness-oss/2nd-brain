#!/usr/bin/env python3
"""予測vs実績の自動答え合わせ。

ネタストックシートの各行（予測再生数つき）を公開済み動画とタイトル照合し、
公開7日以上経過した動画の実績再生数を R〜T 列に記録する。
全体の的中率を data/prediction_log.json に蓄積し、モデル精度の推移を追う。

週次再学習(neta-model-retrain.sh)の直後に実行される想定。
fetch_channel_stats.py が先に走り channel_videos.json が最新である前提。
"""
import json
import re
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

DATA = Path("/Users/kabushikikaishakorokoro/.codex/skills/neta-research/data")
TOKEN_PATH = "/Users/kabushikikaishakorokoro/.config/google-sheets/token.json"
SHEET_ID = "1K_K7gs6l3n4GHixDT_iB_crpb2_ShXSnwRuqa8MOUAo"
LOG_PATH = DATA / "prediction_log.json"
JST = timezone(timedelta(hours=9))
MIN_DAYS = 7          # 公開後この日数を超えたら計測
MATCH_THRESHOLD = 0.45


def norm(s: str) -> str:
    s = re.sub(r"【.*?】", "", s)
    s = re.sub(r"2ちゃんねる.*$", "", s)
    s = re.sub(r"[wｗ草！？!?\s（）()「」]", "", s)
    return s


def similarity(neta: str, title: str) -> float:
    a, b = norm(neta), norm(title)
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    # 片方がもう片方をほぼ含む場合のブースト（ネタ名→正式タイトル化で語尾が変わるため）
    m = SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    contain = m.size / min(len(a), len(b))
    return max(ratio, contain * 0.9)


def main():
    videos = json.loads((DATA / "channel_videos.json").read_text())
    now = datetime.now(JST)

    with open(TOKEN_PATH) as f:
        td = json.load(f)
    creds = Credentials(token=td["token"], refresh_token=td["refresh_token"],
                        token_uri=td["token_uri"], client_id=td["client_id"],
                        client_secret=td["client_secret"], scopes=td["scopes"])
    service = build("sheets", "v4", credentials=creds)
    rows = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="ネタストック!A:T").execute().get("values", [])

    # ヘッダーにR〜T列が無ければ追加
    hdr = rows[0] if rows else []
    if len(hdr) < 20 or hdr[17:20] != ["実績再生数", "計測日", "的中判定"]:
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range="ネタストック!R1:T1",
            valueInputOption="USER_ENTERED",
            body={"values": [["実績再生数", "計測日", "的中判定"]]}).execute()

    updates, results = [], []
    for i, r in enumerate(rows[1:], start=2):
        neta = r[1] if len(r) > 1 else ""
        pred_raw = r[10] if len(r) > 10 else ""
        already = r[17] if len(r) > 17 else ""
        if not neta or not pred_raw or already:
            continue  # 予測なし or 計測済みはスキップ
        try:
            pred = int(str(pred_raw).replace(",", ""))
        except ValueError:
            continue

        # 公開動画とタイトル照合
        best, best_score = None, 0.0
        for v in videos:
            s = similarity(neta, v["title"])
            if s > best_score:
                best, best_score = v, s
        if not best or best_score < MATCH_THRESHOLD:
            continue
        pub = datetime.fromisoformat(best["published"].replace("Z", "+00:00")).astimezone(JST)
        days = (now - pub).days
        if days < MIN_DAYS:
            continue  # 初速が出きるまで待つ

        actual = int(best["views"])
        hit = (actual >= 10000) == (pred >= 10000)
        verdict = f"{'✅的中' if hit else '❌外れ'}（{days}日経過）"
        updates.append({"range": f"ネタストック!R{i}:T{i}",
                        "values": [[actual, now.strftime("%Y-%m-%d"), verdict]]})
        results.append({"neta": neta[:40], "pred": pred, "actual": actual,
                        "days": days, "hit": hit, "video": best["title"][:40],
                        "match_score": round(best_score, 2),
                        "measured_at": now.strftime("%Y-%m-%d")})

    if updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()

    # ログ蓄積 + 累計的中率
    log = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else {"entries": []}
    known = {e["neta"] for e in log["entries"]}
    log["entries"].extend([e for e in results if e["neta"] not in known])
    total = len(log["entries"])
    hits = sum(1 for e in log["entries"] if e["hit"])
    log["accuracy"] = {"total": total, "hits": hits,
                       "rate": round(hits / total, 3) if total else None,
                       "updated": now.strftime("%Y-%m-%d")}
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2))

    print(f"今回計測: {len(results)}件 / 累計: {total}件 / 累計的中率: "
          f"{hits}/{total}" + (f" ({hits/total*100:.0f}%)" if total else ""))
    for e in results:
        mark = "✅" if e["hit"] else "❌"
        print(f"  {mark} 予測{e['pred']:,} → 実績{e['actual']:,} | {e['neta']}")


if __name__ == "__main__":
    main()
