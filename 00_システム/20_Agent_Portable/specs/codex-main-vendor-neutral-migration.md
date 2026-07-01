# Codexメイン・ベンダー非依存化 移行設計

作成日: 2026-07-01
状態: 設計・段階移行中
関連:
- `agent-neutral-contract.md`
- `claude-code-codex-obsidian-operation.md`
- `IMPLEMENTATION_STATUS.md`
- `06_エージェント運用/50_レポート/2026-07-01_Codexメイン移行_Step5_Claude自動化棚卸し.md`

## 1. 案件分類

分類: **危険**

理由:
- 既存のAI実行系、launchd、Discord/Channels、会計、Gmail、Google Drive、自動投稿/通知にまたがる
- `~/.claude/scripts` や `~/Library/LaunchAgents` を誤って一括差し替えすると、サイレント停止、二重実行、外部投稿、会計事故が起きる
- Codex、Claude Code、Hermes、OpenClaw等の切替は、実行環境・権限・sandbox・認証の差が大きい

このため、**停止・起動・削除・本番差し替え・外部投稿・会計書込・Gmail削除は人間承認なしに行わない**。

## 2. Goal

Codexを日常のメイン入口にしつつ、Claude Codeに閉じた仕組みを `agent-run` 経由へ段階移行する。

最終的には、Claude Code / Codex / Hermes / OpenClaw 等のどれを使っても、Obsidian正本・スキル・ジョブ台帳・検証ゲートが同じように機能する状態を目指す。

ただし、短期の完成条件は「Claudeを完全撤去」ではない。短期MVPは次の状態。

- 普段の相談、設計、ファイル編集、検証はCodexを入口にする
- 既存のClaude依存ジョブは棚卸し済みで、危険度と移行順が分かる
- 新規ジョブは原則 `agent-run` 経由で作る
- Claude専用フラグはCodex実行時にfail-closeする
- 低リスクジョブから、dry-run、構造化出力検証、非更新確認、手動実行、launchd切替の順で移行する
- Channels/Discordは本線ではなく、受付・通知・過去ログ参照に限定する

## 3. 完成条件

「クロードコードでやっていたことが全部Codexでできる」は長期完成条件として扱う。

段階ごとの完成条件:

1. **入口完成**
   - `claude-code-codex-obsidian-operation.md` が「Codexメイン移行フェーズ1」を正本としている
   - 祐馬さんが日常依頼をCodexへ投げる運用になっている

2. **継ぎ目完成**
   - `~/agent-adapters/bin/agent-run` が唯一のvendor seamとして使われる
   - `AGENT_VENDOR=codex agent-run -p "..."` の最小実行が確認済み
   - Codex非対応のClaude専用フラグは成功扱いにせず止まる

3. **棚卸し完成**
   - launchd/cron/手動スクリプトのClaude依存が台帳化されている
   - 各ジョブが `低/中/高` リスク、外部送信有無、書込有無、認証有無で分類されている

4. **移行完成**
   - 低リスクから1件ずつCodex dry-runを通す
   - dry-runでは外部投稿・永続書込・削除をしない
   - 構造化出力が検証器を通る
   - 本番切替前にrollback手順とWatchtower/台帳更新がある

5. **脱ロックイン完成**
   - 新しいAIを足す時は、各ジョブを書き換えず `agent-run` のvendor分岐だけを追加する
   - Hermes/OpenClaw等は「本線の置換」ではなく、まずadapter候補として評価する

## 4. 非目標

今回いきなりやらないこと:

- Claude Codeの完全削除
- Claude Channels / Discord連携の即停止
- `com.claude.*` というlaunchdラベル名の一括変更
- 会計、Gmail削除、Drive証憑、Discord投稿を伴うジョブの即時Codex化
- 認証情報、Cookie、セッション、ログ生データをSecond Brainへ保存すること
- Hermes/OpenClawを、現時点でCodexより優先すること

## 5. 作業境界

今回の「触ってよい場所」は、AI関連4正本として次の4つと解釈する。

- `/Users/kojinn/2nd-Brain-master`
- `/Users/kojinn/Projects/youtube`
- `/Users/kojinn/agent-skills`
- `/Users/kojinn/agent-adapters`

ただし、このCodex環境で通常書き込みできるのは `/Users/kojinn/2nd-Brain-master`。`~/agent-skills`、`~/agent-adapters`、`~/.claude/scripts`、`~/Library/LaunchAgents` への書き込みや本番操作は、権限と人間承認を分けて扱う。

未確定項目:

- 触ってはいけない場所: 未指定のため、秘密情報、認証、Cookie、セッション、ログ生データ、外部サービス設定、会計本番書込、削除系を禁止側に倒す
- 外部送信・本番データ・認証・個人情報: `あり` と仮定する
- Hermes/OpenClaw: 公式情報の確認前なので、現時点ではadapter候補に留める。2026-07-01のローカル確認では `hermes` / `openclaw` CLI、該当アプリは見つからなかった

## 6. 現状証拠

2026-07-01時点の正本上の現在地:

- Codex = 日常のメイン入口（移行フェーズ1）
- Claude Code = 補助・退避先
- Claude Code Channels = 受付・通知・軽い指示
- `agent-run` と既存launchd/cron自動化は段階移行中

実機・台帳上の現在地:

- `~/agent-adapters/bin/agent-run` は存在する
- `agent-run` は `AGENT_VENDOR=codex` で `codex exec` を呼ぶ
- Codex分岐では `--permission-mode` / `--allowedTools` などClaude専用フラグをfail-closeする
- Claude依存のlaunchd系ジョブは棚卸し済み
- `thread-format-learning` はCodex任意切替のパイロットまで進んでいる
- launchdの定期実行デフォルトはまだClaude維持

## 7. 推奨アーキテクチャ

```text
祐馬さん
  -> Codex（日常メイン入口）
      -> Obsidian正本 / 06_エージェント運用
      -> agent-skills
      -> agent-run
          -> Claude
          -> Codex
          -> 将来: Hermes
          -> 将来: OpenClaw
      -> 検証器 / dry-run wrapper / Watchtower

スマホ・通知
  -> Channels / Discord / 将来のHermes/OpenClaw
      -> Inbox化
      -> Obsidianへ戻す
      -> 重い作業はCodexまたはagent-runへ渡す
```

原則:

- 知識はObsidian
- スキルは `~/agent-skills`
- 実行入口は `~/agent-adapters/bin/agent-run`
- 作業場は `~/Projects/youtube`
- エージェント固有キャッシュは正本にしない

## 8. エージェント編成

危険案件なので、1人のAIに全部任せない。

標準編成:

- Commander: Codex。Goal、非目標、承認ゲート、最終判断を持つ
- Evidence: ローカル実機、台帳、launchd、既存スクリプト、git差分を確認する
- Implementer: 小さい差分だけを実装する
- QA: dry-run、構文チェック、出力検証、非更新確認を行う
- Independent Reviewer: 実装者と別視点で、外部送信・書込・削除・会計・認証事故を確認する

外部エージェントを使う場合:

- 渡すのは設計・仕様・匿名化したエラーだけ
- 認証情報、個人情報、ログ生データ、会計明細、Discord本文の生データは渡さない
- 外部エージェントの結論は採用せず、Codex側でローカル証拠に照合してから反映する

## 9. 1ジョブごとの移行ゲート

各ジョブはこの順番を飛ばさない。

1. 対象を1件だけ選ぶ
2. 外部送信、永続書込、削除、会計、Gmail、Drive、認証、個人情報の有無を分類する
3. Claude専用フラグ、プロンプト、作業ディレクトリ、読み取り対象を特定する
4. dry-run入口を作る
5. dry-runでは外部投稿、永続書込、削除、会計書込を止める
6. Codex `read-only` sandboxで実行する
7. 構造化出力を検証する
8. 出力がない時はfail-closeする
9. 既存ファイルのmtime、diff、ログ、通知有無を確認する
10. 人間承認後に手動本番相当実行を1回だけ行う
11. launchdの定期実行はデフォルトClaudeのまま、任意変数でCodexを試す
12. 1〜2周期のshadow確認後にデフォルトをCodexへ切り替える
13. Watchtower、台帳、NOW、必要ならlearning-logを更新する

## 10. 移行順

優先順:

1. `thread-format-learning`
   - 既に `agent-run` 経由
   - Codex任意切替のパイロット済み
   - ただし本番実行はウォッチリスト更新やDiscord提案に進むため、人間承認が必要

2. `script-learning` / `daily-knowledge-extract` / `knowledge-gardener`
   - 提案・整理・レポート寄り
   - 書込先と外部通知をdry-runで止めやすい

3. `corpus-collect` / `daily-dashboard` / `uber-earnings` / `uber-weekly-plan`
   - 外部データ・通知が絡むため中リスク
   - read-only確認と投稿停止dry-runが必須

4. `weekly-accounting` / `monthly-accounting` / `gmail-cleanup` / `trash-cleanup` / `vault-snapshot` / `discord-monitor` / `listener-watchdog`
   - 高リスク
   - すぐ触らない
   - 会計、削除、TCC、Channels依存があるため別案件として扱う

## 11. 停止条件

次のどれかが出たら、そのジョブは本番移行しない。

- Codexが必須ファイルを読めない
- `sandbox-exec` や権限エラーが出る
- Claude専用フラグをCodexへ渡す必要が残っている
- dry-runで外部投稿、削除、永続書込、会計書込が発生する
- 検証器が `OK` を出さない
- 出力が自然文だけで、wrapperが安全に解釈できない
- rollback手順がない
- Watchtower/台帳の更新先が決まっていない

## 12. Hermes / OpenClaw の扱い

HermesやOpenClawは、Codexの代わりに即メインへ据える対象ではなく、まず次の順で評価する。

1. 公式情報とローカル導入状況を確認する
2. 受付、通知、常駐、ブラウザ操作、長時間実行など、Codexと役割が違う部分だけを候補にする
3. `agent-run` の新しいvendor分岐として小さく接続する
4. 同じdry-run、構造化出力、fail-close、台帳更新ゲートを通す

本線は「どのAIでも動く仕組み」であり、「特定AIに再ロックインすること」ではない。

## 13. 次にやること

完了済み:

- 古い台帳・ロードマップの「Claude Codeメイン / Codex補助」表現を、現在の正本へ合わせた

短期の次アクション:

1. `thread-format-learning` の次に移す候補を1件だけ選ぶ
2. 選んだジョブにdry-run wrapperを作る
3. `read-only` でCodex実行し、外部投稿・永続書込なしを確認する
4. 独立レビューで本番切替可否を判定する

祐馬さんの承認が必要なもの:

- Claude Channels / Discord受付を止めるかどうか
- Hermes/OpenClawを調査対象に入れるかどうか
- 会計、Gmail、削除、Drive証憑、外部投稿を伴うジョブのCodex化
- `~/.claude/scripts` や `~/Library/LaunchAgents` の本番差し替え
