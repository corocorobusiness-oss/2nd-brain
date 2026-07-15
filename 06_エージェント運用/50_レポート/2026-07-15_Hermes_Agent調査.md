# Hermes Agent 調査レポート（AI Company基盤としての適性評価）

作成: 2026-07-15 あおい（Fable）
依頼: 祐馬さん（Discord #一般「調べて」）
関連: [[AI_Company構想_ChatGPT版_2026-07-15]] / [[AI社員・マルチエージェント構想]] / codex-main-vendor-neutral-migration.md §12（Hermes=adapter候補判定）

---

## 結論（3行）

- Hermes Agent＝Nous Researchのオープンソース自己改善エージェント（2026-02公開・MIT・GitHub 180k星超）。**AI Company構想の「常駐AI社員の基盤」として設計思想がドンピシャ**
- ただし公開5ヶ月の若いソフト（デスクトップは6月からのpublic preview）。**いきなり本線化はNG、検証スプリント1週間→段階昇格**が正しい順番
- コストはソフト本体無料＋LLM API従量（OpenRouter等）or Nous Portalサブスク。既存Claude/Codexと財布が別になる点は要試算

## 1. 実物の特定

| 項目 | 内容 |
|---|---|
| 開発元 | Nous Research（$1.5B評価で資金調達交渉中・TechCrunch 2026-07-13） |
| 公開 | 2026-02-25。4ヶ月で180k GitHub星＝2026年最速成長のOSSエージェント |
| ライセンス | MIT・完全OSS・テレメトリなし・データ全ローカル |
| 最新版 | v2026.7.7.2（2026-07-07）。v2026.7.1「Judgment Release」で追跡中P0/P1全消化 |
| 対応OS | Linux / macOS / WSL2（デスクトップアプリはmac/Win/Linux・6/5公開） |
| 導入 | curl一発インストーラ（uv/Python3.11/Node等を自動導入） |

## 2. AI Company構想へのフィット

| 構想の要素 | Hermesの対応機能 | フィット |
|---|---|---|
| Mac miniに常駐する「本番会社」 | サーバ常駐デーモン＋gateway常駐プロセス | ◎ |
| AI社員（事業責任者AI等） | personalityプロフィール切替＋隔離subagentの並列実行 | ◎ |
| COOプロフィール独立 | `/personality [name]` でプロフィール独立可・デスクトップは同時複数プロフィール | ◎ |
| 社員が「育つ」 | 学習ループ内蔵：経験→スキル自動生成・使用中に自己改善・セッション横断記憶 | ◎（Hermes最大の売り） |
| Discord受付 | Discord/Telegram/Slack/WhatsApp/Signal/CLIを単一gatewayで | ◎ |
| 定時業務（standup・レポート） | cronスケジューラ内蔵 | ◎ |
| 高リスク操作はCEO承認 | command approval・allowlist・DMペアリング・コンテナ隔離 | ○（要実地確認） |
| AIは交換可能（neutral-contract） | モデル非依存（Nous Portal/OpenRouter/OpenAI互換/ローカルvLLM）・スキルはagentskills.io標準 | ◎（うちの`~/agent-skills`と同標準） |

## 3. 懸念（ここを検証で潰す）

1. **若さ**: 公開5ヶ月・活発すぎる開発ペース（月次で破壊的変更あり得る）。会社の土台に据えるには枯れてない
2. **自己改善の暴走リスク**: 「スキルを勝手に作って育つ」は諸刃。承認ゲート・allowlistがどこまで効くか実地確認必須
3. **記憶の二重化**: Hermes内蔵メモリが2nd-Brain正本と別の「第2の記憶」になると正本が割れる。**2nd-Brainを読ませ、Hermesメモリは作業メモ扱いに制限する設計が必要**
4. **財布の分離**: Claude(定額)＋Codexに加えてLLM API従量が乗る。常駐×自己改善はトークンを食う型。検証中に実測する
5. **セキュリティ**: Discord直結の常駐デーモン＝攻撃面が増える。DMペアリング・チャンネル制限・コンテナ隔離の設定を最初から固める（既存の役割分離ゲート＝金・インフラは人間承認、を必ず移植）

## 4. 検証スプリント案（1週間・低権限）

**場所**: Mac mini／**権限**: 2nd-Brain読み取り専用＋書込はサンドボックス作業dirのみ／**Discord**: サブチャンネル(`1486953436212625458`)限定／**金・インフラ操作**: 一切なし

| Day | 検証 | 合格条件 |
|---|---|---|
| 1 | インストール＋モデル接続（OpenRouter） | 起動・応答・モデル切替OK |
| 2 | 2nd-Brain読取＋agent-neutral-contract遵守テスト | NOW.md/契約を読んで正しく行動宣言。**記憶の住み分け遵守**（正本=2nd-Brain・Hermesメモリ=作業メモ。重要事項は2nd-Brainへ書き出す昇格フローが機能し、Hermesメモリは消えても困らない状態を保てること）＝2026-07-15祐馬さん質疑で確定した設計 |
| 3 | Discordゲートウェイ（サブch限定）＋承認ゲート | 危険コマンドがapproval待ちで止まる |
| 4 | personalityプロフィール＝「事業責任者AI」試作1体 | 役割・KPI・権限境界を守って提案が出る |
| 5 | スキル自動生成＋agentskills.io互換（`~/agent-skills`読込） | 既存スキルを読める・生成スキルが妥当 |
| 6 | cron定時タスク（日次standupのdry-run） | 定時に構造化レポートが出る |
| 7 | コスト実測＋総合判定レポート | 週次トークン費が予算内・GO/NO GO判定 |

**GO判定→** adapter候補から「AI社員基盤・段階導入」へ昇格（agent-run配線・neutral-contract拡張＝会社憲章化）
**NO GO→** Claude Subagents（構想メモのPhase 0案）へフォールバック

## 5. コスト粗算

- 本体: ¥0（OSS）
- LLM: OpenRouter従量。事業責任者AI 1体・日次稼働で月$10-40目安（モデル次第・検証で実測）
- インフラ: Mac mini常駐なら追加¥0

## 情報源

- https://hermes-agent.org/ / https://hermes-agent.org/about/
- https://github.com/nousresearch/hermes-agent
- https://hermes-ai.net/news/（リリース履歴）
- https://techcrunch.com/2026/07/13/hermes-agent-maker-nous-research-in-talks-for-new-funding-at-1-5b-valuation/
