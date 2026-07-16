# 経営ダッシュボード Phase 1

Second BrainとYouTube制作フォルダを読み取り、昨日までの経営状況をMac内だけで表示する。
既存データ、会計、制作物、launchd、認証情報には書き込まない。

## 起動

```bash
cd ~/2nd-Brain/01_プロジェクト/AI自動化/経営ダッシュボード
python3 dashboard.py
```

ブラウザで <http://127.0.0.1:8765> を開く。終了は `Control-C`。

## 表示する正本

- 配達予算・YouTube目標と投稿計画: `02_経営/目標と計画.md`
- 日別売上: `05_日誌/YYYY-MM-DD.md`
- 経費: `02_経営/帳簿/freee_export/` の最新ローカルスナップショット
- AIジョブ: `01_プロジェクト/AI自動化/導入済み.md`
- YouTube制作工程: `~/Projects/youtube/創作スレ下書き/`

集計基準日は常に昨日。欠損を0円と見なさず、`確定 / 暫定 / 未取得` を表示する。
YouTube収益はAPI反映が通常2〜3日遅れる。freee経費もスナップショット取得日時以降は含まない。

## Phase 1の境界

- チェックボックスは制作物から判定した表示専用。
- 外部公開、スマホからの外出先アクセス、自動起動は未設定。
- 本番タスク更新と外部アクセスは、別の危険操作承認後に実装する。

## 検証

```bash
python3 -m unittest -v test_dashboard.py
python3 dashboard.py --date 2026-07-16 --json
```
