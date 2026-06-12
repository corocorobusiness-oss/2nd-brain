---
name: today-start
description: >-
  今日のデイリーノートを作成または確認し、日割り目標、月次進捗、
  今日のタスク候補を整理する朝ルーティンスキル。
  「/today-start」「今日始める」「朝のブリーフィング」「今日の方針」などで使用する。
---

# Today Start スキル

## トリガー
- ユーザーが `/today-start` を入力したとき

## 手順

### ステップ1：デイリーノートの準備
1. 今日の日付を確認（YYYY-MM-DD）
2. `/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/05_日誌/YYYY-MM-DD.md` が存在するか確認
3. 存在しない場合は `/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/Templates/Daily_Note_Template.md` をコピーして作成

### ステップ2：日割り目標の取得
1. `/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/02_経営/目標と計画.md` を読み込む
2. 当月の日割り計画テーブルから今日の目標金額を取得
3. 土日・祝日・休みの日は「稼働なし」と表示
4. 次の稼働日と目標金額も取得しておく

### ステップ3：月次進捗の計算
1. 当月1日〜昨日のデイリーノートを全て読み込む
2. 各ノートの「デリバリー計」行から実績金額を集計（累計）
3. 日割り計画から「今日まで」の計画累計を計算
4. 差分（実績累計 − 計画累計）を算出
   - プラスなら「✅ プラス推移」
   - マイナスなら「📉 マイナス推移」

### ステップ4：ブリーフィングをノートに書き込む
以下のフォーマットでデイリーノートの「☕ アオイのブリーフィング」セクションに書き込む：

```
**🎯 今日の日割り目標**
[曜日] ¥XX,XXX（または「土日休み」「祝日休み」）

**次の稼働日**（稼働日の場合はスキップ）
MM/DD（曜）¥XX,XXX

**📊 MM月の進捗（DD日目/31日）**
| 項目 | 累計 | 目標 | 達成率 | 差分 |
|------|-----:|-----:|------:|-----:|
| デリバリー | ¥X,XXX | ¥XXX,XXX | XX% | [+/-]¥X,XXX |

[✅ プラス推移 or 📉 マイナス推移]（差分の説明1行）
```

### ステップ5：Discordに送信
上記ブリーフィング内容をDiscordメインチャンネル（`1486946641389817899`）に送信する。

フォーマット：
```
☀️ おはよう！今日のブリーフィングだよ

🎯 今日の日割り目標
[今日の目標]

📊 [月]月の進捗（[日]日目/[月末日]日）
デリバリー: ¥累計 / ¥目標（達成率%）
[プラス/マイナス推移と差分]
```
