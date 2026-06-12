# 月次経理自動化タスク

毎月1日に実行。各サービスからの領収書ダウンロード、月次収支レポート作成を行い、Discordに報告する。

## 1. freee API認証情報

- トークン: `~/.config/freee-mcp/tokens.json` の `access_token` を使用
- 会社ID: `12511831`
- API: `https://api.freee.co.jp`
- Google Drive保存先:
  - 領収書: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/経費精算/YYYY/MM/`
  - 請求書: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/経費精算/請求書/YYYY/`
  - 収支レポート: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/経費精算/収支レポート/YYYY/`

## 2. 各サイトから前月分の領収書ダウンロード

### Gmailから領収書を検索・取得

Gmail MCPで前月の領収書メールを検索：
```
検索クエリ: (receipt OR 領収書 OR 請求書 OR invoice OR payment) after:YYYY/MM/01 before:YYYY/MM+1/01
```

対象：
- Anthropic (Claude) → 件名に "receipt" や "invoice"
- Brain → 件名に "Brain" や "領収書"
- Google (AdSense) → 件名に "payment" や "お支払い"
- ドワンゴ (ニコニコ) → 件名に "ニコニコ" や "領収書"

添付PDFをダウンロードしてGoogle Driveに保存：
- 領収書 → `経費精算/YYYY/MM/YYYYMMDD_取引先名_金額.pdf`
- 請求書（invoice） → `経費精算/請求書/YYYY/YYYYMMDD_取引先名_金額.pdf`

### 各サイトからの直接ダウンロード（Playwright使用）

※ Playwrightが利用可能な場合のみ実行。利用不可なら「Playwright未使用のためスキップ」と報告。

1. **Anthropic (console.anthropic.com)**
   - Settings → Billing → Invoices から前月分の領収書PDFをダウンロード
   - 保存先: `経費精算/請求書/YYYY/YYYYMMDD_Anthropic_金額.pdf`

2. **Google AdSense**
   - お支払い → 取引 から前月分の売上明細を取得
   - 保存先: `経費精算/請求書/YYYY/YYYYMMDD_GoogleAdSense_金額.pdf`

## 3. freee月次チェック

### 3-1. 月間収支サマリー

損益計算書APIから取得：
```bash
ACCESS_TOKEN=$(python3 -c "import json; d=json.load(open('$HOME/.config/freee-mcp/tokens.json')); print(d['access_token'])")
# 損益計算書
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://api.freee.co.jp/api/1/reports/trial_pl?company_id=12511831&fiscal_year=YYYY&start_month=MM&end_month=MM"
# 貸借対照表
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://api.freee.co.jp/api/1/reports/trial_bs?company_id=12511831&fiscal_year=YYYY"
```

### 3-2. 未処理取引の洗い出し

前月の全取引を取得して：
- 取引先が未設定のものをリストアップ
- 勘定科目が正しいかチェック（週次と同じルール）

### 3-3. Google Driveの領収書と突合

Google Drive内の前月フォルダの領収書と、freeeの取引を照合：
- 領収書はあるが仕訳がない → 報告
- 仕訳はあるが領収書がない → 報告（銀行明細で証拠があれば問題なし）

### 3-4. 減価償却費の確認

車両運搬具の減価償却費が前月分計上されているか確認。

### 3-5. 経費率チェック（年間累計）

年初からの累計で経費率を計算。80%超で警告。

## 4. Discord報告

Discord チャンネル `1486946641389817899` に以下を報告：

```
📊 月次経理レポート（YYYY年MM月）

【月間収支】
- 売上高: ¥○○○,○○○
- 経費合計: ¥○○○,○○○
- 利益: ¥○○○,○○○

【科目別内訳】
- 車両費: ¥○○○
- 通信費: ¥○○○
- 研修費: ¥○○○
- 減価償却費: ¥○○○
- その他: ¥○○○

【経費率】
- 当月: ○○%
- 年間累計: ○○%
（80%超なら⚠️警告）

【前月比】
- 売上: ○○% (↑/↓)
- 経費: ○○% (↑/↓)

【取得した領収書】
- ○○○.pdf → Google Drive保存済み
- ○○○.pdf → Google Drive保存済み

【未処理・要確認】
- ○月○日 ○○○円 取引先不明
- （あれば記載、なければ「問題なし」）

【口座残高】
- GMOあおぞらネット: ¥○,○○○
```

## 5. 月次レポートをGoogle Driveに保存

Discord報告と同じ内容をMarkdownファイルとしてGoogle Driveに保存：
```
保存先: 経費精算/収支レポート/YYYY/YYYY年MM月_月次レポート.md
```

ファイル内容はDiscord報告と同様のフォーマット（月間収支・科目別内訳・経費率・前月比・未処理事項）。

## 6. 確定申告リマインド（1月・2月のみ）

1月実行時：
→ 「確定申告の準備を始めましょう！年間の仕訳チェックを始めますか？」

2月実行時：
→ 「確定申告の提出期限は3月15日です。不足書類がないか最終チェックしましょう！」
