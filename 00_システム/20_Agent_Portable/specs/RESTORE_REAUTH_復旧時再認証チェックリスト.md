# 復旧時 再認証チェックリスト（もしもMacが死んだ時用）

> Driveのバックアップ（skills/scripts/memory/settings/plist）を新Macに展開した後、
> **鍵（トークン）はバックアップに入っていない**ので、ここに書いた順で再ログインすれば全部戻る。
> 鍵は「漏れたら危険・でも作り直せる」性質なので、あえてDriveに置かず再取得する設計。
> 最終更新: 2026-06-12

## 0. 前提（新Macでまず1回）
- [ ] Google Driveアプリにログイン（corocoro.business@gmail.com）→ Vaultとバックアップが見える
- [ ] nvmでnode、bun、python3を入れ直す（`migrate-manifest.txt` にバージョン記載）
- [ ] `claude` を起動してClaude Codeにログイン（claude.ai/Anthropicアカウント）※`.claude.json`は復元しないので再ログイン

## 1. Discord bot（このわたし＝あおいの入口）
- 必要なもの: `DISCORD_BOT_TOKEN`
- 取得元: https://discord.com/developers/applications → 該当アプリ → Bot → トークンをコピー（控えがあれば再発行不要）
- 設定: ターミナルで `/discord:configure` にトークンを貼る → `.claude/channels/discord/.env` に保存される
- 起動: launchdの常駐リスナーが自動で立ち上がる（plistは復元済み）
- ✅ 確認: Discordで話しかけて返事が来ればOK

## 2. freee（会計）
- 必要なもの: `config.json`（clientId / clientSecret）→ tokens.json は自動生成される
- 取得元: https://app.secure.freee.co.jp/developers/applications → アプリのclientId/clientSecret
  - `~/.config/freee-mcp/config.json` に clientId / clientSecret / callbackPort(54321) を書く
- 再認証: **ほぼ全自動**。手順は memory `reference_freee_token_reauth.md`（Playwright+Googleログイン）
- ✅ 確認: freee取引のGET APIが通ればOK

## 3. YouTube収益API（円ベース）
- 必要なもの: `client_secret.json`（Google CloudのOAuthクライアント）
- 取得元: https://console.cloud.google.com/apis/credentials → OAuth 2.0 クライアント → JSONダウンロード → `~/.config/youtube-revenue/client_secret.json`
- 再認証: `python3 ~/.config/youtube-revenue/reauth.py`（または get_token.py）→ Googleログインは**2chブランドアカウント**を選ぶ
- ✅ 確認: `fetch_daily.py` が円で収益を返せばOK（launchd 毎日12時）

## 4. Google Sheets（ネタ管理シート等）
- 必要なもの: OAuthクライアント（YouTubeと同じGoogle CloudプロジェクトでOK）
- 再認証: `python3 ~/.config/google-sheets/auth_setup.py` → Googleログイン
- ✅ 確認: シート読み書きが通ればOK

## 5. Google系 各種（Gmail / Drive / Calendar）
- これらは **claude.ai のコネクタ**経由。トークンファイルではなくclaude.ai側の連携
- 再認証: claude.ai → 設定 → Connectors（連携）で Gmail / Google Drive / Google Calendar を再接続
- ✅ 確認: メール検索・Drive保存・カレンダー登録が通ればOK

## 6. Uber（配達売上の自動取得）
- 仕組み: Playwright(MCPブラウザ)で drivers.uber.com にログイン
- 再認証: MCPブラウザで auth.uber.com → 「Googleで続行」（corocoro.business@gmail.com）→ **QR不要**
- ✅ 確認: drivers.uber.com の売上ページが開けばOK

## 7. Playwright ブラウザの Googleセッション（上の2・6の土台）
- MCPブラウザで一度 google.com にログイン（corocoro.business@gmail.com）しておくと、freee/Uberの再認証が「Googleで続行」だけで通る

---
## 鍵を控えておくと一番ラクなもの（任意・パスワードマネージャ推奨）
- Discord bot トークン（これだけ控えておけば手順1が一瞬で終わる）
- freee clientId / clientSecret
- Google Cloud の client_secret.json
※ これらは Vault にも Drive にも置かない。パスワードマネージャか安全な場所に。
