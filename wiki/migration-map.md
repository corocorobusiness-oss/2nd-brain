---
title: Migration Map
type: business
sources: []
related: ["[[business-dashboard]]", "[[index]]"]
created: 2026-06-15
updated: 2026-06-15
confidence: high
---

# Migration Map

このページは、既存のObsidian構造と新しい社長室AI構造の対応表です。

## Migration Policy

- 既存フォルダはすぐに移動・削除しない。
- 新しい `inbox/`、`raw/`、`wiki/`、`outputs/` は上位の読み取りレイヤーとして追加する。
- AIはまず `AGENTS.md`、`CLAUDE.md`、`wiki/index.md`、`wiki/business-dashboard.md` を読む。
- 詳細な元資料や過去ログは、既存フォルダへ遡って読む。

## Old to New Mapping

| 既存フォルダ | 新しい役割 | 備考 |
|---|---|---|
| `00_システム/` | system / agent rules | 既存のAI設定・テンプレートは維持する |
| `01_プロジェクト/` | raw/projects + project knowledge | すぐには移動しない。必要に応じてwikiへ要約する |
| `02_経営/` | raw/business, raw/finance, wiki/finance | 帳簿・月次・収支は元資料として扱う |
| `03_知識ベース/` | raw/articles + wiki sources | 既存ナレッジは残し、重要ページだけwikiへ昇格する |
| `04_アウトプット/` | outputs / publishing assets | SNS、Note、メルマガの出力置き場として維持する |
| `05_日誌/` | raw/daily-notes | 日誌は重要な一次情報として扱う |
| `06_エージェント運用/` | agent operations | 現在地、実行キュー、判断ログは維持する |
| `99_アーカイブ/` | archive | 参照のみ。原則変更しない |

## New Reading Layer

| 新フォルダ | 役割 |
|---|---|
| `inbox/` | 未整理の入力口 |
| `raw/` | 元資料の新しい正本レイヤー |
| `wiki/` | AIが最初に読む整理済み知識 |
| `outputs/` | AIの点検結果・レポート |

## Business Entry Points

- `wiki/business-dashboard.md`
- `wiki/business-principles.md`
- `wiki/offers.md`
- `wiki/customers.md`
- `wiki/sales-and-marketing.md`
- `wiki/operations.md`
- `wiki/finance.md`
- `wiki/decision-log.md`

## Next Migration Work

1. `02_経営/` から `wiki/finance.md` に重要な要約を作る。
2. `01_プロジェクト/` から主要事業ごとのwikiページを作る。
3. `05_日誌/` から判断・顧客理解・売上機会を抽出する。
4. `03_知識ベース/` の重要ページを `wiki/` に昇格する。
5. すべてGit差分で確認してからコミットする。
