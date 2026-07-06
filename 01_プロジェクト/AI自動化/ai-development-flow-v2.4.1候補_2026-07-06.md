---
status: 候補
doc_type: ルール
version: v2.4.1-candidate-2
maintainer: あおい
last_review: 2026-07-06
next_review: 2026-08-01
---

# ai-development-flow V2.4.1 候補 2026-07-06

対応指摘: `REV-20260704-b1-08`（plan_only許可リストの粒度）／`REV-20260704-b1-10`（外部AI除染の環境詳細）
経緯: Trial-004 V2.3の`wc -l` WARN承認（池田祐馬・2026-07-04）の再点検条件「b1-08正本化」を消化する。文言の明確化のみで挙動変更なし。
本ファイルは**候補**。従ってはいけない。反映はステージ2の危険操作承認後のみ。

## 反映対象

編集2ファイル・6箇所＋付随2点（完全版の版更新 v1.7→v1.8／指摘台帳のb1-08・b1-10行を新行で「反映先=V2.4.1・反映済み」に更新）。新規作成1件（編集前SKILL.mdの退避コピー `legacy/v2.4_legacy_<timestamp>/SKILL.md`）。sentinel文字列は変更しない。

設計判断: `git log` はWARN承認の直接対象（`wc -l`・`git status --short`）に含まれない同クラス拡張だが、読み取り専用状態確認として明示的に許可リストへ含め、本候補の危険操作承認で人間がまとめて承認する。

### 変更1: SKILL.md — plan_only許可リストの粒度明確化（b1-08）

変更前（この4行を置換）:

```text
- Only reading files and searching are allowed (file views, text search,
  directory listings). Do not execute anything else: no tests, no scripts,
  no shell commands, no writes, no external sending. A script or command
  that looks read-only is still not run during plan_only.
```

変更後:

```text
- Only read-type operations are allowed: file views, text search,
  directory listings, read-only aggregation over file contents (line or
  match counts such as wc / grep -c), and read-only state inspection
  (git status / git log in forms that change nothing). Do not execute
  anything outside these classes: no tests, no scripts, no state-changing
  commands, no writes, no external sending. A command that looks
  read-only but is not in the classes above is still not run.
```

### 変更2: 完全版 §2.1 ※注 — 同内容の日本語（b1-08）

変更前（※注の先頭3行を置換。完了主張の2行は不変）:

```text
※ handoff_mode の「実装・書き込みなし」は「設計に必要なファイルの読み取り・検索・一覧以外は
何も実行しない」を意味する。テスト実行・スクリプト実行・シェルコマンド・書き込み・外部送信は禁止
（読み取り専用に見えるスクリプトやコマンドも、plan_only中は実行しない）。
```

変更後:

```text
※ handoff_mode の「実装・書き込みなし」は「設計に必要な読み取り系以外は何も実行しない」を意味する。
読み取り系＝ファイル閲覧・テキスト検索・一覧、読み取り専用の集計（wc・grep -c 等、ファイル内容に対する行数/件数カウント）、
読み取り専用の状態確認（git status / git log 等・変更を伴わない形のみ）。
それ以外のテスト実行・スクリプト実行・状態を変えるコマンド・書き込み・外部送信は禁止
（読み取り専用に見えても上記クラスに入らないものは実行しない）。
```

### 変更3: SKILL.md — External AI Rule への追記（b1-10）

挿入位置: 一意な文 `If decontamination is not confirmed, the review is invalid.` の直後。

```text
Environment-identifying details count as sensitive here: credential file
paths, internal service IDs, and code snippets that extract tokens must
be masked before external sending. Distinguish a locally-resident agent
(running on this machine with vault access — raw local artifacts may be
shared) from a true external AI (anything that sends data off this
machine — decontamination is mandatory and raw transcripts are never
handed over). If an agent is ambiguous — it runs on this machine but its
processing sends data off it — treat it as a true external AI.
```

### 変更4: 完全版 §6 — 渡してはいけないものリストへの追記（b1-10）

挿入位置: 一意な行 `- 認証済みURL` の直後。

```text
- 認証ファイルパス・内部サービスID（会社ID等）・トークン抽出コードスニペット（マスクなしでの受け渡し）
- transcript（セッション記録）の生渡し

※ ローカル同居エージェント（このMac上でvaultを読める相棒AI）と、外部送信を伴う真の外部AIを区別する。
前者へはローカル成果物をそのまま渡してよいが、後者へは除染なしに何も渡さない。
両方に該当する・判定に迷う場合は、真の外部AI扱い（除染必須）に倒す。
```

### 変更5: 完全版 §2.1 — 不採用リスト行の整合（b1-08・独立レビューP1-1対応）

変更前（この2行を置換）:

```text
- plan_only中に読み取り・検索以外のツール実行（テスト・スクリプト・シェルコマンド）を行う、
  または実ツール結果なしに「実行済み・テスト済み」と主張する
```

変更後:

```text
- plan_only中に読み取り系（※注の定義: 閲覧・検索・一覧・読み取り専用の集計・読み取り専用の状態確認）
  以外のツール実行を行う、または実ツール結果なしに「実行済み・テスト済み」と主張する
```

### 変更6: SKILL.md — stale判定の参照追記（台帳 fable5-02-r2 の残対応）

挿入位置: Source Of Truth節の一意な文 `If any file is missing or appears stale, say so.` を含む段落の直後。

```text
Stale is judged per 標準テンプレ §1.5: soft-stale (next_review passed, or
status header missing) — declare it and continue no further than
plan-only; hard-stale (廃止 / superseded_by set / a 候補 referenced as
正本 / file missing) — stop as above. When in doubt, treat as hard-stale.
```

⚠️ 反映順の依存: 変更6は標準テンプレ§1.5（A2A3候補）の反映と同時、またはその後に適用する。

## 反映時の検証（REQ表）

| REQ | 内容 | 方法 |
|---|---|---|
| 0 | 全アンカー `grep -c` =1（≠1なら反映中止） | 反映前に機械確認 |
| 1 | SKILL.mdに集計/状態確認の許可クラス | `grep "read-only aggregation"` ≥1 |
| 2 | 完全版※注に同内容＋版v1.8 | `grep "読み取り専用の集計"` ≥1 |
| 3 | 除染追記が両ファイルに存在 | `grep "credential file"` / `grep "生渡し"` |
| 4 | sentinel出現数が不減 | grep -c比較 |
| 5 | 差分がSKILL.md・完全版・legacy・本候補のみ | git確認 |
| 6 | 退避hash一致 | sha256 |
| 7 | Trial-002スモーク1本PASS（許可リストに触れる唯一のTrial） | 確立済みプロトコル（隔離＋固定入力＋保存トリガー語彙禁止＋sandbox宣言） |
| 8 | 完全版内の矛盾ゼロ（※注と不採用リストの許可クラスが一致） | 目視＋grep |
| 9 | 台帳のb1-08/b1-10に「反映先=V2.4.1・反映済み」の新行 | 台帳確認 |

## 変更メモ

- candidate-2: 独立レビューP1 1件（不採用リスト行の矛盾→変更5新設）＋P2 4件（英日の対象限定・git log明示・ローカル/外部tie-break・台帳更新手順）を解消。fable5-02-r2の残対応（SKILL.md stale参照）を変更6として追加。

## 戻し方

SKILL.mdはlegacy書き戻し（hash照合）＝V2.4復帰。完全版は該当hunkのrevert。挙動変更なしの文言明確化のため、戻してもV2.4の運用に影響しない。

## 独立レビュー用採点基準

1. 許可の拡大が「読み取り専用クラスの明文化」を超えていないか（書き込み・実行系が紛れたらP0）
2. sentinel不変か（P1）
3. 最小差分か（P1）
4. 英日の意味一致（P1）
5. アンカーexact一致（P1）
6. b1-10の「ローカル同居/真外部」区別が既存の除染ルールを弱めていないか（弱めていればP0）
