#!/usr/bin/env python3
"""Yuma OS Watchtower（ローカルインフラ監視官＋自己修復）

2026-06-12 設計転換: Google Drive内のVaultはlaunchd起動プロセスから読めない（macOS TCC）。
そこでWatchtowerは「ローカルインフラ（launchdジョブ・スクリプト・ログ・台帳）の健全性監視」に専念する。
Vaultコンテンツ（日誌・売上・YouTube）の監視はあおい（claude経由でVault読める）の領分。

2026-06-12 ロードマップ#8拡張（祐馬さん合意済み）:
  - 監視を全launchdジョブに拡大＋「期待リスト vs 実体」の双方向突合（#11型のジョブ消失を検知）
  - 自己修復: 冪等ジョブ（バックアップ/スナップショット/ダッシュボード系）のみ、失敗検知時に
    1日1回だけ自動kickstart。経理系は二重計上リスクがあるため通知のみ
  - freeeトークン鮮度の事前チェック（refresh死を突然死前に検知）
  - 報告: 異常時のみ#レポートへ即通知＋日曜は全OKでも週1サマリ（生存確認を兼ねる）

やること: 検査・記録・通知・冪等ジョブの再実行まで。
やらないこと: 削除・外部投稿（通知除く）・会計確定・新規ジョブ作成・Vaultへの書き込み。
リスナーの再起動はlistener-watchdog（5分毎）の領分なのでここでは手を出さない。

2026-06-13 品質プランv2.2 柱⓪: Vaultのローカル正本化（2nd-Brain-master）でTCC問題が
消えたため、「ローカル正本の読み取りのみ」解禁。期日超過タスク（- [ ] YYYY-MM-DD …）を
検知し、完了[x]かスキップ[-]まで毎朝#一般へ再督促する（詳細: vault_task_overdue.py）。
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
from pathlib import Path

import sys
sys.path.insert(0, str(Path.home() / ".claude" / "scripts"))

SCRIPTS = Path.home() / ".claude" / "scripts"
ENV_FILE = Path.home() / ".claude" / "channels" / "discord" / ".env"
REPORT_CHANNEL = "1512911466628386837"  # #レポート
GENERAL_CHANNEL = "1486946641389817899"  # #一般（期日タスク督促の宛先。レポートだと読まれない）
RUNTIME_LOG = SCRIPTS / "watchtower.log"
REPAIR_STATE = SCRIPTS / "watchtower-repair-state.json"
# P41（2026-06-28）: 朝8:30の単発発火だとMacが休止/オフの朝に督促が丸ごと落ちるため、
# plist(com.korokoro.yuma-watchtower)のStartCalendarIntervalを配列化して昼13:00の
# 補完回を追加した。ただしWatchtowerの通知（期日督促・warnサマリ・日曜サマリ）は毎回
# 無条件に飛ぶ実装なので、素直に2回走らせると同日重複通知になる。そこで
# 「その日に一度でも通知ラウンドを完走したら、後続回は通知系だけサイレントにする」
# 同日ガードを入れた。朝が落ちた日はstate未記録なので昼回が初回扱いで通知＝補完が効く。
# 検査・ログ書き込み・自己修復kickstartはこのガードと無関係に毎回走る
# （kickstartの重複はREPAIR_STATEが別途1日1回に抑止済み）。
DAILY_NOTIFY_STATE = SCRIPTS / "watchtower-daily-notify-state.json"
FREEE_TOKENS = Path.home() / ".config" / "freee-mcp" / "tokens.json"
LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"

# 監視対象のlaunchdジョブ（ラベル: 説明）— 全ジョブの期待リスト（正本）
# 新ジョブを作ったらここに1行足すこと。足し忘れは「台帳外ジョブ」警告が教えてくれる
#
# ★出荷ゲート（品質プランv2.2 柱②・2026-06-13）: ここに新ジョブを登録する前に必ず——
#   1. 実物ログ確認: 実データでの初回実行ログ・生成物パスを作業ログの完了報告に添付したか
#   2. 確認者分離: 初回ログを実装者と別の方（ツバキ⇔あおい）が見たか。金系は祐馬さん必須
#   3. ③連動: このジョブが生む新しいstate/台帳ファイルを③の鍵ファイルリストに追加したか
#   4. 並走判定日: シャドー並走するなら判定日を期日タスク（- [ ] YYYY-MM-DD）でVaultに書いたか
#   5. 金クラス（freee等に書く）は並走なしハードカットオーバー（切替と同時に旧系停止）
EXPECTED_JOBS = {
    "com.claude.discord-monitor": "あおい常駐リスナー",
    "com.claude.listener-watchdog": "リスナー死活監視(5分毎)",
    "com.claude.weekly-accounting": "週次経理(月9:05)",
    "com.claude.monthly-accounting": "月次経理(1日10:00)",
    "com.claude.monthly-accounting-recheck": "月次経理の独立再検証(1〜5日11:05・READのみ)",
    "com.claude.uber-earnings": "Uber売上(夜)",
    "com.claude.daily-knowledge-extract": "日誌→ナレッジ",
    "com.claude.knowledge-gardener": "Vault整理(週次)",
    "com.korokoro.yuma-watchtower": "このWatchtower自身",
    "com.claude.nightly-refresh": "夜間リフレッシュ(3:10/3:50)",
    "com.claude.daily-dashboard": "朝ダイジェスト(4:00)",
    "com.claude.ssd-backup": "SSDオフサイトコピー(マウント時)",
    "com.claude.vault-snapshot": "週次Vaultスナップショット",
    "com.claude.monthly-backup": "月次~/.claudeバックアップ",
    "com.claude.restore-drill": "復元演習(柱③・月次2日4:30・バックアップ中身照合)",
    "com.claude.gmail-cleanup": "週次Gmail整理",
    "com.claude.trash-cleanup": "月次ゴミ箱削除",
    "com.claude.uber-weekly-plan": "週次稼働プラン(日曜夜)",
    "com.claude.youtube-revenue": "YouTube収益記録(毎日12:00)",
    "com.claude.neta-retrain": "ネタ評価の再学習",
    "com.claude.neta-slate-reminder": "月末ネタ草案リマインド(25日10:00・半手動アシスト)",
    "com.claude.script-learning": "台本スタイル学習",
    "com.claude.corpus-collect": "創作スレ学習コーパス週次収集(日21:00)",
    "com.claude.thread-format-learning": "創作スレ文体の週次学習(日22:00)",
    "com.claude.demaecan-reminder": "出前館実績PDF DLリマインド(1日/16日10:00)",
    "com.claude.weekly-stocktake": "週次棚卸し質問(日曜20:00・📥から5件をやる/いつか/捨てるで聞く)",
    "com.claude.vault-autocommit": "Vault正本の10分毎git commit(06-13ローカル正本化)",
    "com.claude.satellite-autocommit": "skills/adapters/youtube の10分毎git commit",
    "com.claude.vault-mirror": "Vault正本→Drive片方向ミラー(15分毎)",
    "com.claude.youtube-drafts-ssd-mirror": "創作スレ下書き→SSD常駐ミラー(30秒監視/削除なし)",
    "com.claude.freee-uncleared-monitor": "freee消込待ち明細モニター(1日10:45・READのみ/督促通知)",
}

# 自己修復（自動kickstart）を許可する冪等ジョブのホワイトリスト。
# 経理系（weekly/monthly-accounting）は再実行で取引の二重登録があり得るため絶対に入れない。
# daily-dashboardは再実行でDiscord投稿が重複し得るが、ダイジェスト欠落より軽傷と判断して許可。
REPAIRABLE_JOBS = {
    "com.claude.ssd-backup",
    "com.claude.vault-snapshot",
    "com.claude.monthly-backup",
    "com.claude.daily-dashboard",
}

# ログ鮮度チェック（ファイル: 何日以上古いと警告か）
# exit code監視は「失敗」を捉えるが「そもそも発火しなくなった」は捉えられないため、
# 定期ジョブはstate/logの鮮度でも見る（周期＋数日の猶予で設定）
LOG_FRESHNESS = {
    SCRIPTS / "listener-watchdog.log": 1,
    SCRIPTS / "weekly_accounting.log": 9,
    Path("/Users/kojinn/2nd-Brain-master/06_エージェント運用/30_ヘルスチェック/monthly_accounting_recheck_state.json"): 35,
    SCRIPTS / "vault-snapshot-state.json": 9,       # 週次（日曜4:30）
    SCRIPTS / "monthly-backup-state.json": 35,      # 月次（1日4:00）
    SCRIPTS / "restore-drill-state.json": 35,       # 月次（2日4:30）柱③復元演習
    SCRIPTS / "ssd-backup-state.json": 9,           # SSDマウント時＋各バックアップ末尾（週1は動くはず）
    SCRIPTS / "vault-mirror-state.txt": 1,          # 15分毎（1日古い=ミラー死亡。vault-snapshotはミラーを撮るので特に重要）
    SCRIPTS / "youtube-drafts-ssd-mirror.log": 1,   # 常駐30秒監視。1日古い=下書きSSD追従が止まっている兆候
    Path("/Users/kojinn/.claude/skills/neta-forge/data/slate_state.json"): 35,  # 月次（25日リマインド→人が起動）半手動ネタ草案。35日無更新=その月の草案が出てない
    SCRIPTS / "corpus_collect.log": 9,              # 週次（スレコーパス収集）。7日周期＋2日猶予=9日無更新で警告
}

# git fetch鮮度チェック（P28検知2026-06-28・根治2026-06-29）: pull方向の最新性検知。
# 旧根本原因: autocommitはpush専用でfetch/pullを一切しなかったため各リポのリモート追従が
# 黙って停滞していた（FETCH_HEADが何日も更新されない／衛星3リポは未fetch）。別端末追加・
# 復旧時に「ローカルが古いことに気づけない」事故の芽だった。
# 根治: vault/satellite-autocommit.sh が origin 設定時に3日毎 git fetch --all --prune を打つ
# ようにした（merge/pullはしない＝ローカル正本は書き換えない）。この検査はその死活アラーム係。
# 検査は読み取りのみ（git fetchは打たない＝外部発信なし）。FETCH_HEADのmtimeだけを見る。
# 整合: fetch周期3日 < 本閾値7日。1回寝落ちしても誤警報せず、機構が本当に死んだ時だけwarn。
# リポ: (表示名, リポのルートパス)
GIT_FETCH_REPOS = [
    ("vault正本", Path.home() / "2nd-Brain-master"),
    ("agent-skills", Path.home() / "agent-skills"),
    ("agent-adapters", Path.home() / "agent-adapters"),
    ("youtube作業場", Path.home() / "Projects" / "youtube"),
]
GIT_FETCH_MAX_DAYS = 7  # FETCH_HEADがこれ以上古い/未fetch=pull方向の最新性検知が死んでいる兆候

# 日次GitHub push鮮度チェック（P27・2026-06-28）: オフサイト保護(GitHub private)の生存確認。
# 根本原因: vault/satellite autocommit は「pushを試みて失敗したとき」だけ#一般へ🔴を出す。
# しかし鍵失効・権限喪失・origin外れ・autocommit自体の停止では、pushが“静かに”止まる
# （試行に到達しない／成功扱いにならない）→ push状態ファイルの中身(最終push成功epoch)が
# 黙って古いまま固まる。GitHubは3拠点バックアップ(ローカルgit→GitHub→Driveミラー)の唯一の
# オフサイト層なので、ここが止まると遠隔災害時の最後の砦が消える。
# autocommitスクリプトは push 成功時に PUSH_STATE へ最終成功epoch(date +%s)を書く。
# この検査はその中身を読むだけ(git push もファイル書き換えもしない＝外部発信なし)。
# 閾値はpush周期(24h)＋猶予で2日。autocommit側の🔴(4日継続失敗)より早く前兆を掴む役。
# 注意: origin未設定リポはautocommitがそもそもpushしない設計なので、状態ファイルが
#   無い＝「まだGitHubに繋いでいない」可能性があり、failではなくinfoで知らせるに留める。
# (表示名, push状態ファイルのパス)
GITHUB_PUSH_STATES = [
    ("vault正本", SCRIPTS / "vault-push-state.txt"),
    ("agent-skills", SCRIPTS / "satellite-push-state-agent-skills.txt"),
    ("agent-adapters", SCRIPTS / "satellite-push-state-agent-adapters.txt"),
    ("youtube作業場", SCRIPTS / "satellite-push-state-youtube.txt"),
]
GITHUB_PUSH_MAX_DAYS = 2  # 最終push成功からこれ以上経過=オフサイト保護が静かに止まっている兆候


def now_jst() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Asia/Tokyo"))
    except Exception:
        return dt.datetime.now()


def check_launchd_jobs() -> tuple[list[tuple[str, str, str]], list[str]]:
    """期待リストと実体を双方向で突合。返り値: (検査結果, 異常終了したラベル一覧)"""
    results: list[tuple[str, str, str]] = []
    failed: list[str] = []
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        return [("warn", "launchctl", f"launchctl list失敗: {e}")], []

    loaded = {}
    for line in out.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 3:
            loaded[parts[2]] = (parts[0], parts[1])  # label -> (pid, exit_code)

    for label, desc in EXPECTED_JOBS.items():
        if label not in loaded:
            plist = LAUNCH_AGENTS / f"{label}.plist"
            if plist.exists():
                results.append(("warn", desc, f"{label} が未ロード（plistは存在→ launchctl load で復旧可）"))
            else:
                results.append(("warn", desc, f"{label} がplistごと消失（#11型の事故。バックアップから復元が必要）"))
            continue
        _, exit_code = loaded[label]
        # 0=正常, 143/-15=SIGTERM(再起動の正常な印), それ以外は異常
        if exit_code not in ("0", "143", "-15"):
            results.append(("warn", desc, f"{label} の最終終了コードが {exit_code}（異常）"))
            failed.append(label)
        else:
            results.append(("ok", desc, f"{label} 正常"))

    # 逆向きの突合: launchdに居るのに期待リストに無い自前ジョブ（足し忘れ or 野良ジョブ）
    ours = {l for l in loaded if l.startswith(("com.claude.", "com.korokoro."))}
    for label in sorted(ours - set(EXPECTED_JOBS)):
        results.append(("warn", "台帳外ジョブ", f"{label} が期待リストに無い（新ジョブならEXPECTED_JOBSに追記して）"))
    return results, failed


def repair_failed_jobs(failed: list[str], now: dt.datetime) -> list[tuple[str, str, str]]:
    """冪等ジョブだけ1日1回自動kickstart。結果検証は翌朝の検査に委ねる（claude -p型は数分かかるため）"""
    results = []
    try:
        state = json.load(REPAIR_STATE.open(encoding="utf-8"))
    except Exception:
        state = {}
    today = now.strftime("%Y-%m-%d")
    for label in failed:
        if label not in REPAIRABLE_JOBS:
            continue  # 通知のみ（check結果のwarnが既に出ている）
        if state.get(label) == today:
            results.append(("warn", "自己修復", f"{label} は今日すでに再実行済みなのに失敗のまま（人の確認が必要）"))
            continue
        try:
            subprocess.run(["launchctl", "kickstart", f"gui/{os.getuid()}/{label}"],
                           capture_output=True, text=True, timeout=15, check=True)
            state[label] = today
            results.append(("info", "自己修復", f"{label} を自動再実行した（結果は次回検査で確認）"))
        except Exception as e:
            results.append(("warn", "自己修復", f"{label} のkickstart失敗: {e}"))
    REPAIR_STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return results


def check_freee_token(now: dt.datetime) -> tuple[str, str, str]:
    """freeeトークンの鮮度＋refresh連鎖の能動確認（P32・根治側の定期監視強化 2026-06-28）。

    背景: freeeのアクセストークンは expires_in=6時間 と短命。旧実装は created_at が3日以上古いか
    だけを見ていたため、6時間で切れたトークンを「鮮度OK」と緑誤認していた（実測: created 15.6h前で
    緑判定なのに expires_at は9.6h前＝とっくに失効）。短命トークンの突然死は「refreshの連鎖が
    どこかで失敗したまま放置」で起きる。そこで読み取りだけで連鎖の健全性を能動確認する:
      ① refresh_token が無い → 自動更新の鍵が消えている（最重大。これだけは必ず再認証が要る）
      ② expires_at(=created_at+expires_in) を計算し、すでに失効＆長時間放置 → refresh連鎖が
         止まっている兆候（daily-dashboard等が毎日APIを叩いて更新するはずなので、半日以上
         失効が続くのは異常）。短命トークンに合わせ猶予はEXPIRED_GRACE_Hで判定。
    freeeへの書き込み・API呼び出しは一切しない（tokens.jsonを読むだけ）。P44(export側の401止血)
    とは役割が違い、こちらは毎朝の定期監視で突然死を事前検知する係。"""
    EXPIRED_GRACE_H = 12   # 失効してから何時間放置されたらrefresh連鎖の停止とみなすか（短命6h×2の猶予）
    STALE_REFRESH_DAYS = 3  # 旧来の鮮度基準（created_atの停滞）も残す（refreshが全く回っていない検知）
    try:
        d = json.load(FREEE_TOKENS.open(encoding="utf-8"))
    except FileNotFoundError:
        return ("warn", "freeeトークン", "tokens.json が見つからない")
    except Exception:
        return ("warn", "freeeトークン", "tokens.json が読めない/壊れている")

    # ① refresh_token の欠落 = 自動更新の鎖が切れている（最重大。再認証以外で復旧不可）
    if not d.get("refresh_token"):
        return ("warn", "freeeトークン",
                "refresh_token が無い＝自動更新の鎖が切れている（このまま失効すると必ず再認証が要る。"
                "手順: reference_freee_token_reauth）")

    created_ts = d.get("created_at")
    expires_in = d.get("expires_in")

    # ② expires_at を計算して実際の失効状態を能動確認（短命トークン対応の本体）
    if isinstance(created_ts, (int, float)) and isinstance(expires_in, (int, float)):
        expires_at = dt.datetime.fromtimestamp(created_ts + expires_in, tz=now.tzinfo)
        created = dt.datetime.fromtimestamp(created_ts, tz=now.tzinfo)
        remain_h = (expires_at - now).total_seconds() / 3600
        age_days = (now - created).total_seconds() / 86400
        if remain_h <= -EXPIRED_GRACE_H:
            return ("warn", "freeeトークン",
                    f"アクセストークンが{-remain_h:.0f}時間前に失効したまま（猶予{EXPIRED_GRACE_H}h超）。"
                    f"refresh連鎖が止まっている疑い。次に経理ジョブが叩くと401になる前兆——"
                    f"daily-dashboard等のrefreshが回っているか確認を（手順: reference_freee_token_reauth）")
        if age_days >= STALE_REFRESH_DAYS:
            return ("warn", "freeeトークン",
                    f"最終更新が{age_days:.0f}日前でrefreshが回っていない（短命6hトークンなのに{STALE_REFRESH_DAYS}日"
                    f"更新なし＝連鎖停止の疑い。手順: reference_freee_token_reauth）")
        if remain_h >= 0:
            return ("ok", "freeeトークン", f"有効（あと{remain_h:.1f}h・refresh連鎖も生存）")
        # 失効はしているが猶予内＝次のrefreshで自然回復する範囲。緑にせずinfoで様子見を促す
        return ("info", "freeeトークン",
                f"失効後{-remain_h:.1f}h（猶予{EXPIRED_GRACE_H}h内・次のrefreshで回復見込み。継続したら要確認）")

    # フォールバック: created_at だけで旧来の鮮度判定（フィールド欠損時）
    if isinstance(created_ts, (int, float)):
        age_days = (now - dt.datetime.fromtimestamp(created_ts, tz=now.tzinfo)).total_seconds() / 86400
        if age_days >= STALE_REFRESH_DAYS:
            return ("warn", "freeeトークン",
                    f"最終更新が{age_days:.0f}日前（expires_in欠損で失効時刻は不明だがrefresh停滞の疑い。"
                    f"手順: reference_freee_token_reauth）")
        return ("ok", "freeeトークン", f"鮮度OK（{age_days*24:.0f}時間前に更新・expires_in欠損で失効時刻は未算出）")
    return ("warn", "freeeトークン", "created_at が無く鮮度を判定できない（tokens.jsonの構造が想定外）")


def check_log_freshness(now: dt.datetime) -> list[tuple[str, str, str]]:
    results = []
    for path, max_days in LOG_FRESHNESS.items():
        if not path.exists():
            results.append(("warn", path.name, "ログが未生成"))
            continue
        age = now - dt.datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
        if age.total_seconds() / 86400 >= max_days:
            results.append(("warn", path.name, f"最終更新が{age.days}日前（ジョブ停止の可能性）"))
        else:
            results.append(("ok", path.name, "鮮度OK"))
    return results


def check_git_fetch_freshness(now: dt.datetime) -> list[tuple[str, str, str]]:
    """P28: pull方向の最新性検知。各リポの .git/FETCH_HEAD のmtimeが停滞していないか軽量確認。
    読み取り専用（git fetchは打たない＝外部発信なし）。未fetch/長期停滞をwarnで知らせる。
    fetch本体はautocommitが3日毎に実行（2026-06-29根治）。この検査は機構が死んだ時のアラーム係。"""
    results: list[tuple[str, str, str]] = []
    for name, repo in GIT_FETCH_REPOS:
        git_dir = repo / ".git"
        if not git_dir.exists():
            results.append(("warn", "git鮮度", f"{name}: gitリポが見つからない（{repo}）"))
            continue
        fetch_head = git_dir / "FETCH_HEAD"
        if not fetch_head.exists():
            # 一度もfetchされていない＝autocommitのfetchがまだ回っていない/失敗が続いている兆候。
            results.append(("warn", "git鮮度",
                            f"{name}: 一度もfetchされていない（FETCH_HEAD無し）。"
                            f"autocommitの3日毎fetchが未稼働/失敗中の疑い"))
            continue
        age = now - dt.datetime.fromtimestamp(fetch_head.stat().st_mtime, tz=now.tzinfo)
        age_days = age.total_seconds() / 86400
        if age_days >= GIT_FETCH_MAX_DAYS:
            results.append(("warn", "git鮮度",
                            f"{name}: 最終fetchが{age.days}日前（{GIT_FETCH_MAX_DAYS}日基準）。"
                            f"pull方向の最新性が停滞——別端末追加/復旧時にローカルが古い恐れ"))
        else:
            results.append(("ok", "git鮮度", f"{name}: fetch鮮度OK（{age.days}日前）"))
    return results


def check_github_push_freshness(now: dt.datetime) -> list[tuple[str, str, str]]:
    """P27: 日次GitHub push鮮度の監視。オフサイト保護(GitHub private)が静かに止まっていないか。
    各autocommitが push 成功時に書く push状態ファイルの中身(最終push成功epoch秒)を読むだけ。
    git push もファイル書き換えもしない（読み取り専用＝外部発信なし）。
    鍵失効・権限喪失・origin外れ・autocommit停止では中身が古いまま固まる→ それを可視化する係。
    閾値はGITHUB_PUSH_MAX_DAYS(2日)。autocommit側の🔴(4日継続失敗)より早く前兆を掴む。"""
    results: list[tuple[str, str, str]] = []
    for name, state_path in GITHUB_PUSH_STATES:
        if not state_path.exists():
            # origin未設定だとautocommitはpushしない設計＝状態ファイルが無いのは
            # 「まだGitHubに繋いでいない」可能性。failではなくinfoで気づかせるに留める。
            results.append(("info", "GitHub push",
                            f"{name}: push状態ファイルが無い（{state_path.name}）。"
                            f"origin未設定＝まだGitHubに繋いでいないか、一度もpush成功していない可能性"))
            continue
        try:
            last_epoch = float(state_path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            results.append(("warn", "GitHub push",
                            f"{name}: push状態ファイルが読めない/壊れている（{state_path.name}）"))
            continue
        last_push = dt.datetime.fromtimestamp(last_epoch, tz=now.tzinfo)
        age = now - last_push
        age_days = age.total_seconds() / 86400
        if age_days >= GITHUB_PUSH_MAX_DAYS:
            results.append(("warn", "GitHub push",
                            f"{name}: 最後のGitHub push成功が{age.days}日前（{GITHUB_PUSH_MAX_DAYS}日基準）。"
                            f"鍵失効/権限喪失/autocommit停止の疑い——オフサイト保護(GitHub private)が"
                            f"静かに止まっているかも（ローカルgitは継続中で安全）"))
        else:
            results.append(("ok", "GitHub push", f"{name}: push鮮度OK（{age.days}日前に成功）"))
    return results


def check_restore_drill() -> tuple[str, str, str]:
    """柱③復元演習の結果監視。result=FAILなら解消（次回PASS）まで毎朝再警告。
    鮮度自体はLOG_FRESHNESSが別途見る（ここは「中身NG」の理由を出す担当）。"""
    p = SCRIPTS / "restore-drill-state.json"
    try:
        d = json.load(p.open(encoding="utf-8"))
    except FileNotFoundError:
        return ("warn", "復元演習", "restore-drill-state.json が未生成（一度も走っていない）")
    except Exception:
        return ("warn", "復元演習", "restore-drill-state.json が壊れている")
    if d.get("result") == "FAIL":
        reasons = "／".join(d.get("fails", [])) or "理由不明"
        return ("warn", "復元演習", f"最新FAIL（{d.get('last_run','?')}）: {reasons}　← バックアップの中身に問題。要確認")
    return ("ok", "復元演習", f"PASS（checksum{d.get('files_verified',0)}件照合・{d.get('last_run','?')}）")


def check_registry() -> tuple[str, str, str]:
    p = SCRIPTS / "freee_registered_txns.json"
    try:
        d = json.load(p.open(encoding="utf-8"))
        return ("ok", "処理済み台帳", f"{len(d.get('txns', {}))}件・JSON健全")
    except FileNotFoundError:
        return ("warn", "処理済み台帳", "freee_registered_txns.json が見つからない")
    except Exception:
        return ("warn", "処理済み台帳", "台帳JSONが壊れている")


def check_redrive(now: dt.datetime) -> list[tuple[str, str, str]]:
    """limit-redrive（上限ストール時の依頼預かり・自動配達）の滞留監視（本丸5・2026-06-12）"""
    base = Path.home() / ".claude" / "redrive"
    results = []
    dlq = list((base / "dlq").glob("*.json"))
    if dlq:
        results.append(("warn", "redrive配達", f"DLQに{len(dlq)}件（自動処理できなかった依頼。中身確認→手動対応か削除依頼を）"))
    if (base / "confirm-mode.flag").exists():
        results.append(("warn", "redrive配達", "確認モード中（預かりが多すぎ/古すぎで自動配達を停止中。あおいに「預かり分やって」で再開）"))
    queue = list((base / "queue").glob("*.json"))
    stuck = list((base / "working").glob("*.json"))
    if queue or stuck:
        oldest_h = (now.timestamp() - min(f.stat().st_mtime for f in queue + stuck)) / 3600
        if oldest_h > 2:
            results.append(("warn", "redrive配達", f"預かり依頼{len(queue) + len(stuck)}件が{oldest_h:.1f}時間滞留（配達が回ってない疑い）"))
        else:
            results.append(("ok", "redrive配達", f"預かり{len(queue) + len(stuck)}件・配達進行中"))
    if not results:
        results.append(("ok", "redrive配達", "預かり0件・DLQ空"))
    return results


def check_listener_process() -> tuple[str, str, str]:
    try:
        out = subprocess.run(["pgrep", "-f", "claude.*--channels"], capture_output=True, text=True, timeout=10)
        if out.stdout.strip():
            return ("ok", "あおいプロセス", "リスナー稼働中")
        return ("warn", "あおいプロセス", "リスナーが見つからない（ウォッチドッグが復旧するはず）")
    except Exception as e:
        return ("warn", "あおいプロセス", f"確認失敗: {e}")


def check_session_bloat() -> tuple[str, str, str]:
    """あおいのセッション肥大検知（5MB超で再起動推奨）。lsofで本人のトランスクリプトを特定"""
    try:
        pid = subprocess.run(["pgrep", "-f", "claude.*--channels"], capture_output=True, text=True, timeout=10).stdout.split()
        if not pid:
            return ("ok", "セッション肥大", "リスナー不在のため判定なし")
        r = subprocess.run(["python3", str(SCRIPTS / "find_listener_session.py")],
                           capture_output=True, text=True, timeout=20)
        path = r.stdout.strip()
        if not path:
            return ("ok", "セッション肥大", "セッション未開始（コンテキスト空）")
        size_mb = Path(path).stat().st_size / 1_048_576
        if size_mb >= 5:
            return ("warn", "セッション肥大", f"あおいのセッションが{size_mb:.1f}MB。ヒマなタイミングでDiscordに「再起動」と送ると頭がスッキリするよ（夜間リフレッシュが届かなかった日の保険）")
        return ("ok", "セッション肥大", f"セッション{size_mb:.1f}MB（健全）")
    except Exception as e:
        return ("warn", "セッション肥大", f"判定失敗: {e}")


def check_overdue_tasks(now: dt.datetime) -> tuple[list[tuple[str, str, str]], list[dict]]:
    """品質プランv2.2 柱⓪: 期日超過タスクの検知。
    返り値: (検査結果, 督促対象タスク一覧)。督促はmain()で#一般に送る（#レポートだと読まれず強制点にならない）。
    緑誤認ガード: スキャン不能・走査僅少はwarn（「超過なし」と混同しない）"""
    try:
        import vault_task_overdue
        r = vault_task_overdue.scan(today=now.date())
    except Exception as e:
        return [("warn", "期日タスク", f"スキャナ自体が失敗: {e}（超過なしと誤認しないこと）")], []
    results = [("warn", "期日タスク", f"走査異常: {msg}") for msg in r["errors"]]
    if r["overdue"]:
        results.append(("warn", "期日タスク", f"期日超過{len(r['overdue'])}件→#一般へ督促"))
    elif not r["errors"]:
        results.append(("ok", "期日タスク", f"超過なし（{r['scanned']}ファイル走査）"))
    return results, r["overdue"]


def notify_discord(text: str, channel: str = REPORT_CHANNEL) -> None:
    token = None
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("DISCORD_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
    if not token:
        return
    import urllib.request
    data = json.dumps({"content": text}, ensure_ascii=False).encode()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel}/messages",
        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json",
                 "User-Agent": "DiscordBot (watchtower, 1.0)"}, data=data)
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception:
        pass


def already_notified_today(today: str) -> bool:
    """P41の同日ガード: 今日すでに通知ラウンドを完走したか。
    朝8:30が正常に通知判断まで到達していればTrue→昼13:00の補完回は通知を抑止する。
    朝が落ちた日はstate未記録でFalse→昼回が初回扱いで通知して督促を補完する。
    判定不能（state壊れ等）は「未通知」に倒す＝督促が消えるより重複の方が安全側。"""
    try:
        d = json.load(DAILY_NOTIFY_STATE.open(encoding="utf-8"))
        return d.get("last_notified_date") == today
    except FileNotFoundError:
        return False
    except Exception:
        return False  # 壊れていたら未通知扱い（督促を落とさない安全側）


def mark_notified_today(today: str) -> None:
    """今日の通知ラウンド完走を記録（後続回の同日ガード用）。"""
    try:
        DAILY_NOTIFY_STATE.write_text(
            json.dumps({"last_notified_date": today}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass  # state書き込み失敗は致命でない（最悪、昼に重複通知するだけ）


def main() -> int:
    now = now_jst()
    checks: list[tuple[str, str, str]] = []
    job_results, failed = check_launchd_jobs()
    checks += job_results
    checks += repair_failed_jobs(failed, now)
    checks.append(check_freee_token(now))
    checks += check_log_freshness(now)
    checks += check_git_fetch_freshness(now)
    checks += check_github_push_freshness(now)
    checks += check_redrive(now)
    checks.append(check_restore_drill())
    checks.append(check_registry())
    checks.append(check_listener_process())
    checks.append(check_session_bloat())
    task_results, overdue_tasks = check_overdue_tasks(now)
    checks += task_results

    warns = [c for c in checks if c[0] == "warn"]
    infos = [c for c in checks if c[0] == "info"]
    ok_count = sum(1 for c in checks if c[0] == "ok")

    if RUNTIME_LOG.exists() and RUNTIME_LOG.stat().st_size > 512_000:
        tail = RUNTIME_LOG.read_text(encoding="utf-8").splitlines()[-200:]
        RUNTIME_LOG.write_text("\n".join(tail) + "\n", encoding="utf-8")

    with RUNTIME_LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n=== {now.strftime('%Y-%m-%d %H:%M:%S')} 状態:{'要確認' if warns else '正常'} "
                f"(OK {ok_count}/注意 {len(warns)}/修復 {len(infos)}) ===\n")
        for status, label, msg in checks:
            f.write(f"  [{status.upper()}] {label}: {msg}\n")

    # P41の同日ガード: 朝8:30と昼13:00の2回発火するので、今日すでに通知ラウンドを
    # 完走していれば後続回（昼）の通知系はサイレントにして重複督促を防ぐ。検査・ログ書き込みは
    # 上で既に済ませてあるので、ここでは通知の有無だけを切り替える。
    today = now.strftime("%Y-%m-%d")
    if already_notified_today(today):
        print(f"Watchtower: 検査完了（本日{today}は通知済みのため補完回の通知はスキップ・"
              f"OK {ok_count}/注意 {len(warns)}/修復 {len(infos)}）")
        return 0

    # 期日タスク督促は#一般へ（v2.2柱⓪: 完了[x]かスキップ[-]にするまで毎朝再発火）
    if overdue_tasks:
        lines = [f"・**{t['date']}**（{t['days']}日超過）{t['text']}　`{t['file']}`"
                 for t in overdue_tasks[:8]]
        if len(overdue_tasks) > 8:
            lines.append(f"…ほか{len(overdue_tasks) - 8}件")
        notify_discord("⏰ 期日が過ぎてるタスクがあるよ（毎朝言うからね）:\n" + "\n".join(lines) +
                       "\n終わったら `[x]`、やらないと決めたら `[-]` にしてくれたら止まるよ",
                       channel=GENERAL_CHANNEL)

    if warns or infos:
        lines = [f"⚠️ {label}: {msg}" for _, label, msg in warns]
        lines += [f"🔧 {label}: {msg}" for _, label, msg in infos]
        body = "🗼 Watchtower: インフラに注意項目があるよ\n\n" + "\n".join(lines)
        notify_discord(body)
        print(f"Watchtower: 注意{len(warns)}件/修復{len(infos)}件（Discord通知済み）")
    elif now.weekday() == 6:  # 日曜: 全OKでも週1サマリ（Watchtower自身の生存確認を兼ねる）
        notify_discord(f"🗼 週間サマリ: 今週は全{len(checks)}項目正常だったよ（監視{len(EXPECTED_JOBS)}ジョブ＋トークン・台帳・リスナー）")
        print(f"Watchtower: 全{len(checks)}項目正常（週間サマリ送信）")
    else:
        print(f"Watchtower: 全{len(checks)}項目正常")

    # 通知判断まで完走したので今日の発火を記録（後続回＝昼の同日ガード用）。
    # warn/info無し・平日で「通知本文を一度も出さなかった」場合も完走記録は付ける——
    # その日の生存確認は取れているので、昼に改めて静かに走り直す必要はない。
    mark_notified_today(today)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
