#!/usr/bin/env python3
"""Read stock sheet, score each row, write predictions back to columns K/L/M/N.

Sheet layout (A:J existing) → adds:
  K: 予測再生数
  L: 1万超え確率
  M: スコア根拠
  N: スコアリング日時
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/Users/kojinn/.claude/skills/neta-research/scripts")
from predict_score import score_title, load_db
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/Users/kojinn/.config/google-sheets/token.json"
SHEET_ID = "1K_K7gs6l3n4GHixDT_iB_crpb2_ShXSnwRuqa8MOUAo"

HEADER_ROW = ["予測再生数", "1万超え確率", "スコア根拠", "スコアリング日時"]


def get_service():
    td = json.loads(Path(TOKEN_PATH).read_text())
    creds = Credentials(
        token=td["token"], refresh_token=td["refresh_token"],
        token_uri=td["token_uri"], client_id=td["client_id"],
        client_secret=td["client_secret"], scopes=td["scopes"],
    )
    return build("sheets", "v4", credentials=creds)


def main():
    svc = get_service()
    db = load_db()

    # Read A:J (existing columns before score output)
    data = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="ネタストック!A:J").execute()
    rows = data.get("values", [])
    if not rows:
        print("Empty sheet")
        return

    header = rows[0]
    idx_title = header.index("ネタ名")
    idx_taiga = header.index("大河連動")

    today = datetime.now().strftime("%Y-%m-%d")
    out_rows = [HEADER_ROW]  # header row K:N
    for r in rows[1:]:
        if len(r) <= idx_title or not r[idx_title]:
            out_rows.append(["", "", "", ""])
            continue
        title = r[idx_title]
        taiga = len(r) > idx_taiga and r[idx_taiga] == "◯"
        result = score_title(title, db, taiga_linked=taiga)
        if result.get("reject"):
            out_rows.append(["NG", "0%", result["reason"], today])
        else:
            out_rows.append([
                result["predicted_views"],
                f"{result['over_10k_prob']*100:.0f}%",
                result["rationale"],
                today,
            ])

    # Write K:N
    range_end = f"N{len(out_rows)}"
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"ネタストック!K1:{range_end}",
        valueInputOption="USER_ENTERED",
        body={"values": out_rows},
    ).execute()
    print(f"Scored {len(out_rows)-1} rows, wrote to K1:{range_end}")

    # Print top 10 by predicted views
    scored = [(i, r[idx_title], out_rows[i]) for i, r in enumerate(rows[1:], 1)
              if len(r) > idx_title and r[idx_title] and isinstance(out_rows[i][0], int)]
    scored.sort(key=lambda x: -x[2][0])
    print("\n=== TOP 10 予測再生数 ===")
    for rank, (i, title, pred_row) in enumerate(scored[:10], 1):
        print(f"{rank:2d}. #{rows[i][0]:>3s}  予測{pred_row[0]:>7,}  p10k={pred_row[1]:>4s}  {title}")


if __name__ == "__main__":
    main()
