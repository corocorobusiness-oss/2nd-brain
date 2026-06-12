# Codex App Setup Status

最終更新: 2026-06-11

Brain購入記事「Codexアプリの教科書」の推奨に沿って、現MacのCodex環境を確認・反映した記録。

## 完了

- モデル: `gpt-5.5`
- 推論レベル: `high`
- おすすめプロンプト / 提案: `config.toml` 側はオン
- 作業フォルダ: Google Drive内 `2nd-Brain`
- 2nd-Brainプロジェクト: trusted
- 有効プラグイン:
  - Browser
  - Chrome
  - Computer Use
  - Documents
  - Spreadsheets
  - Presentations
  - Canva
- グローバルAGENTS:
  - `/Users/kabushikikaishakorokoro/.codex/AGENTS.md`
- プロジェクトAGENTS:
  - `AGENTS.md`
  - MacBook Air時代の `kojinn` パスを現Macのユーザー名へ修正済み
- Codexスキル:
  - `~/.codex/skills` にSecond Brainの `codex-skills-ready` から移植済み
- 週次記帳:
  - `com.korokoro.kicho-weekly`
  - 毎週月曜 9:30
  - 稼働中
- ランタイムバックアップ:
  - 日本語パス文字化け対策としてASCII入口を作成
  - `/Users/kabushikikaishakorokoro/.codex/bin/agent_runtime_backup.sh`
  - 手動ドライラン・手動本番実行は成功

## 要手動確認

CodexアプリUIでしか確実に変更できない項目。

- 作業モード: 日常業務向け
  - ファイルから `everyday` に変更しても、起動中のCodexアプリが `coding` に書き戻すためUI変更が必要
- おすすめプロンプト / 提案
  - `config.toml` 側はオンだが、オンボーディング状態は起動中アプリがオフへ書き戻すためUIで確認
- メニューバーに表示: オン
- ポップアップウィンドウのホットキー: 任意の使いやすいキーに設定

## 要再登録

`com.yuma.agent-runtime-backup` は日本語パス文字化けで一度失敗し、Codex内からのlaunchd再登録とTerminal操作は権限で止まった。

登録用スクリプトもASCIIパスで作成済みなので、ターミナルで以下を1回実行すれば復旧する。

```zsh
zsh "/Users/kabushikikaishakorokoro/.codex/bin/register_agent_runtime_backup.sh"
```

復旧後の確認:

```zsh
launchctl print gui/$(id -u)/com.yuma.agent-runtime-backup
```
