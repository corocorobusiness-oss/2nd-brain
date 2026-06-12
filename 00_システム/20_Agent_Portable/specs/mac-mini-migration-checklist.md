# Mac mini Migration Checklist

最終更新: 2026-06-11

MacBook Airで作っていたAI事業環境を、Mac miniで再現するためのチェックリスト。

## 1. 必須アプリ

- Google Drive for desktop
- Obsidian
- Codex desktop app
- Claude Desktop / Claude Code
- Chrome
- Git
- Node.js / npm / bun
- Python
- YMM4利用環境はWindows側またはWindows PCで別管理

## 2. Second Brain

Google Driveの以下を同期する。

```text
マイドライブ/2nd-Brain
```

Mac上では必要に応じて短いパスを作る。

```text
/Users/kojinn/2nd-Brain
```

注意:
- ObsidianのVaultはこのSecond Brainを開く
- 複数端末で同時編集しない
- `.claude` や `.codex` のキャッシュ全体はDrive同期しない

## 3. エージェント初期設定

新しいエージェントには、まず以下を読ませる。

```text
00_システム/10_Agent/
00_システム/20_Agent_Portable/
00_システム/00_UserProfile/
06_エージェント運用/00_司令塔/NOW.md
```

## 4. 移行する資産

すでにSecond Brainへ保存済み:

```text
00_システム/20_Agent_Portable/archive/claude/skills/
00_システム/20_Agent_Portable/archive/claude/agents/
00_システム/20_Agent_Portable/archive/claude/scripts/
00_システム/20_Agent_Portable/archive/claude/launchagents/
00_システム/20_Agent_Portable/archive/antigravity/.agent/
00_システム/20_Agent_Portable/archive/codex/
00_システム/20_Agent_Portable/archive/obsidian/
99_アーカイブ/Local_Work/youtube-work/
01_プロジェクト/YouTube/制作アーカイブ/平将門_script/
```

## 5. 再設定が必要なもの

以下はSecond Brainに実体を保存しない。Mac miniで再ログインまたは再設定する。

- Googleアカウント
- Google Sheets / YouTube API OAuth
- freee OAuth
- Discord Bot Token
- Chromeログイン状態
- Claude / Codex のログイン状態
- launchd自動実行の有効化

## 6. Claude Code Channels / Discord

今後は原則使わない。

保存するもの:
- 仕組みの設計
- 事業スキル
- 自動化の考え方

保存しないもの:
- Discord token
- Discord inbox添付
- Discordセッション
- Claude Channelsの一時状態

## 7. Mac miniでの再現順序

1. Google Driveで `2nd-Brain` を同期
2. ObsidianでVaultを開く
3. Codexを入れて `2nd-Brain` をプロジェクトとして開く
4. Codexに `agent-neutral-contract.md` と `06_エージェント運用/00_司令塔/NOW.md` を読ませる
5. 必要なClaudeスキルをCodex向けに移植する
6. Google / YouTube / freee などの認証を再設定する
7. 自動化は必要なものだけ再作成する

## 8. 再作成候補の自動化

優先度高:
- デイリーノート作成
- 売上記録
- Uber週次プラン
- YouTube制作フロー
- ナレッジ抽出

優先度低:
- Discord監視
- Gmail掃除
- ゴミ箱掃除
- Claude Channels連携

## 9. 端末ローカルに残すもの

以下はMac miniで再ログイン・再生成する。Second Brainへコピーしない。

```text
~/.codex/auth.json
~/.codex/*.sqlite
~/.claude/settings.local.json
~/.claude/history.jsonl
~/.config/freee-mcp/tokens.json
~/.config/google-sheets/token.json
~/.config/youtube-revenue/token*.json
~/.config/youtube-revenue/client_secret.json
~/.playwright-mcp/
```

理由:
- 認証情報を含む
- セッションやキャッシュを含む
- 新Macでパスやログイン状態が変わる
- Google Drive同期に向かない
