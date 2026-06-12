---
name: uber-earnings
description: >-
  Uber Eatsの当日売上（配達＋プロモ/クエスト）をdrivers.uber.comから取得し、
  デイリーノートに記入・予算比較してDiscord #お金 に投稿するスキル。
  「Uber更新」「Uber売上」「デリバリー集計」や、launchdの定期実行から呼ばれる。
  出前館は対象外（手入力）。
---

# Uber売上 自動取得スキル

drivers.uber.com の収益ページを**ブラウザで見に行って**（人間の閲覧と同じ・低頻度）、
当日のUber売上を集計し、デイリーノート記入＋Discord報告まで行う。

## 安全運用ルール（重要）
- **方式は「サイトを見に行く」**（ページを開いて読む）。内部API直叩きは規約グレーなので使わない
- **頻度は1日1回程度**（定期実行 or 手動「Uber更新」時のみ）。高頻度ポーリング禁止
- 自分（オーナー）の売上データのみ。他用途・転売しない

## 手順

### 1. 収益ページを開く
`mcp__playwright__browser_navigate` で `https://drivers.uber.com/earnings/activities` を開く。

### 2. ログイン状態を確認
ページに「ログイン」「電話番号」「サインイン」等が出ていたら**未ログイン**。
その場合は集計せず、Discord #お金 (chat_id: 1512911463180800120) に
「⚠️ Uberのログインが切れてます。再ログインが必要です（QRで対応できます）」と投稿して終了。

### 3. 対象日（当日）の週を選択
日付ピッカー `input[aria-label="Select a date range."]` をクリックしてカレンダーを開き、
当日を含む週（月曜〜日曜）を選択。当日が表示される範囲ならデフォルトのままでよい。

### 4. 全件ロード
「さらに読み込む」ボタンを無くなるまでクリック。

### 5. 当日分を集計（重複排除）
各配達行の **View Detailsのtripリンク（/earnings/trips/UUID）でユニーク判定**して重複を除く
（ページは同じ行を2回描画することがあるため、単純なテキスト抽出だと二重計上になる）。
- `activityTitle` が **Delivery** = 配達売上
- `activityTitle` が **クエスト/〇〇回乗車クエスト** = プロモ収益（別集計）
- 当日（JST）の `recognizedAt` のものだけ合計
- 金額は `formattedTotal`（￥x,xxx）。クエストは進捗カウンターが混ざるので breakdownDetails / 実額に注意

集計結果: 当日の「配達計」「プロモ計」「Uber合計（配達＋プロモ）」

### 6. デイリーノートに記入
`/Users/kojinn/2nd-Brain/05_日誌/YYYY-MM-DD.md`（無ければ
`00_システム/Templates/Daily_Note_Template.md` から作成）の売上テーブルを更新：
- Uber Eats 行に当日のUber合計
- メモ欄に「配達¥○○＋プロモ¥○○」の内訳
- 出前館行は触らない（手入力のまま）
- デリバリー計・合計を再計算（出前館が既に入っていれば加算）

### 7. 予算比較
`2nd-Brain/02_経営/目標と計画.md` の当月日割りから当日予算を取得し、
当日の差（実績−予算）と月間累計（デリバリー実績/目標）を算出。
ルール参照: [[daily-budget-display-format]]（日毎テーブル＋備考、経費も）

### 8. Discordに投稿
`mcp__plugin_discord_discord__reply` で chat_id=1512911463180800120 (#お金) に：
```
🛵 Uber売上 自動集計（M/D）
配達: ¥○○○ ／ プロモ: ¥○○○ → Uber計 ¥○○○
予算 ¥○○○ に対し {+/−}¥○○○

📊 6月デリバリー累計: ¥○○ / ¥○○（○○%）
※出前館があれば「出前館 ○○」と送ってね（手入力で足すよ）
```

## 関連メモ
- 取得方法の詳細: [[uber-earnings-fetch]]（reference_uber_earnings_fetch.md）
- 表示ルール: [[daily-budget-display-format]] [[expense-in-sales-report]]
- 売上報告ルール: [[sales-report-rules]]
