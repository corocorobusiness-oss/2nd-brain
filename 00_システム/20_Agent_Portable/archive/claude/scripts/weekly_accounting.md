# 週次経理自動化タスク

毎週月曜に実行。freeeの仕訳チェックとGmailからの領収書取得を行い、Discordに報告する。

## 1. freee API認証情報

- トークン: `~/.config/freee-mcp/tokens.json` の `access_token` を使用
- 会社ID: `12511831`
- API: `https://api.freee.co.jp`

## 2. Gmailから請求書・領収書を検索

Gmail MCPを使って過去7日間の請求書・領収書メールを検索：

```
検索クエリ: (receipt OR 領収書 OR 請求書 OR invoice OR payment OR 明細) newer_than:7d
```

対象サービス：
- Anthropic (Claude) の領収書
- Brain の領収書
- Google AdSense の支払い通知
- ニコニコ（ドワンゴ）の領収書
- その他の請求書・領収書PDF

見つかったメールから：
1. 添付PDFがあればダウンロード
2. メール本文にPDFリンクがあれば記録
3. Google Drive に保存: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/経費精算/2026/MM/YYYYMMDD_取引先名_金額.pdf`
   - MMは月（01〜12）
   - ファイル名は日付_取引先_金額の形式

## 3. freee仕訳チェック

Bash toolでcurlを使ってfreee APIを叩く。

### 3-1. 未仕訳・取引先未設定の取引を確認

```bash
ACCESS_TOKEN=$(python3 -c "import json; d=json.load(open('$HOME/.config/freee-mcp/tokens.json')); print(d['access_token'])")
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://api.freee.co.jp/api/1/deals?company_id=12511831&limit=50&order=desc"
```

取引先（partner_id）が空の取引を見つけたら、口座明細の説明文から取引先を判定して紐付ける：

| キーワード | partner_id | 取引先名 |
|---|---|---|
| UBER / ＵＢＥＲ | 112727574 | Uber Eats |
| グ－グル / GOOGLE | 112727620 | Google |
| デマエカン / 出前館 | 112727657 | 出前館 |
| ENEOS / ＥＮＥＯＳ | 112727388 | ENEOS |
| ｱﾎﾟﾛ / アポロ / 出光 | 113065832 | 出光 |
| CLAUDE | 112727540 | Anthropic |
| Brain / Ｂｒａｉｎ | 112727498 | Brain |
| コロコロ | 112727698 | (株)ころころ |
| ニコニコ | 112730154 | ドワンゴ |
| ＧＭＯアオゾラネツト | 113066028 | GMOあおぞらネット銀行 |

紐付けにはPUT `/api/1/deals/{id}` を使用。

### 3-2. 勘定科目の正しさチェック

既存の仕訳ルール：
| パターン | 正しい勘定科目 | account_item_id |
|---|---|---|
| Uber Eats入金 | 売上高 | 1024926858 |
| Google入金 | 売上高 | 1024926858 |
| 出前館入金 | 売上高 | 1024926858 |
| ENEOS/出光 | 車両費 | 1024926897 |
| Claude AI | 通信費 | 1024926876 |
| ニコニコ | 通信費 | 1024926876 |
| Brain | 研修費 | 1024926935 |
| (株)ころころ | 短期貸付金 | 1024926802 |
| ATM引出し | 事業主貸 | 1024926833 |
| 利息 | 受取利息 | 1024926855 |
| Visaキャッシュバック | 雑収入 | 1024926864 |

間違いがあれば報告する（自動修正はしない）。

### 3-3. 減価償却費の確認

減価償却費（account_item_id: 1024926883）が当月計上されているか確認。

### 3-4. 経費率チェック

損益計算書から経費率を計算：
```
経費率 = 経費合計 / 売上高 × 100
```
80%を超えたら警告。

## 4. Discord報告

Discord チャンネル `1486946641389817899` に以下を報告：

```
📊 週次経理レポート（MM/DD〜MM/DD）

【収支サマリー】
- 収入: ○件 / ¥○○○
- 支出: ○件 / ¥○○○

【取得した領収書】
- ○○○.pdf → Google Drive保存済み
（なければ「今週は新規領収書なし」）

【仕訳チェック】
- 取引先紐付け: ○件更新
- 勘定科目: 問題なし or 要確認○件
- 減価償却: 計上済み or 未計上⚠️

【経費率】
- 今月の経費率: ○○%（正常 or ⚠️高め）

【要確認事項】
- （あれば記載）
```
