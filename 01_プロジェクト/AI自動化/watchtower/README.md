# Yuma OS Watchtower

祐馬さんのSecond Brainと自動化の状態を毎朝確認する見張り役。

> 2026-06-27追記: 旧「AI帳簿/weekly-kicho」は会計正本freee運用から外し、実機停止済み。Watchtowerの経理チェックは、freee正本・weekly-accounting・補助台帳・証憑の状態確認へ寄せる。

## 役割

- 今日のデイリーノート確認
- freee経理・weekly-accounting・補助台帳の状態確認
- 自動化台帳の要注意項目確認
- YouTube制作タスク確認
- 今日の日誌に見るべきことを追記
- ヘルスチェックログへ結果を保存

## 実行

手動実行:

```sh
python3 watchtower.py
```

スケジュールON:

```sh
./watchtower_on.sh
```

CodexからONできない場合:

```sh
cd "/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/01_プロジェクト/AI自動化/watchtower"
./watchtower_on.sh
```

スケジュールOFF:

```sh
./watchtower_off.sh
```

## launchd

- ジョブ名: `com.korokoro.yuma-watchtower`
- 実行時刻: 毎日 8:30
- 出力先:
  - `05_日誌/YYYY-MM-DD.md`
  - `06_エージェント運用/30_ヘルスチェック/ヘルスチェックログ.md`
- `01_プロジェクト/AI自動化/watchtower/logs/watchtower.log`

## 現在の注意

2026-06-27時点で `com.korokoro.yuma-watchtower` はlaunchd登録済み。
残りの論点は自動起動ではなく、`~/.claude/scripts/watchtower_local.py` の `EXPECTED_JOBS` と `導入済み.md` の整合。

- 期待リストから外す候補: 停止済み `com.korokoro.kicho-weekly`、退避済み `com.claude.channel-lifecycle`
- 期待リストへ追加候補: `com.claude.corpus-collect` / `com.claude.thread-format-learning` / `com.claude.demaecan-reminder` / `com.claude.satellite-autocommit`
- Codex環境からホーム配下の本体編集は権限制限で未実施

## 禁止事項

Watchtowerは見張り役。以下は行わない。

- ファイル削除
- 外部投稿
- 会計確定
- SNS投稿
- 新規ジョブ作成
