---
name: knowledge-gardener
description: >-
  2nd-Brain(Obsidian vault)全体を定期的に読み、関連ノートを[[リンク]]で繋ぎ、
  重複の統合提案・古い情報の更新・MEMORY.md indexの整備を行うスキル。
  "勝手に育つ第2の脳"のVault自動メンテ担当。毎週の定期実行、または
  「Vault整理」「ナレッジ整理」「第2の脳メンテ」で発動。
---

# ナレッジ・ガーデナー（Vault全体の自動メンテ）

2nd-Brainを庭のように手入れする。孤立したノートを繋ぎ、重複を見つけ、
古い情報を更新して、知識ベースが"育つ"状態を保つ。

## 対象
- `/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/` 全体（特に 03_知識ベース、01_プロジェクト、02_経営）
- Claudeメモリ `~/.codex/projects/-Users-kojinn/memory/`（MEMORY.md index）

## 手順
1. 2nd-Brainの主要ノートをGlob/Readで俯瞰（量が多いので要点・見出し中心）
2. **① 自動リンク（安全・即実行）**
   - 内容が関連するノート同士に `[[ノート名]]` リンクを追記する
   - 例: 「Roblox事業」の各ノート間、「YouTube」関連ノート間を相互リンク
3. **② 重複・統合の検出（提案のみ・実行しない）**
   - 同じテーマが複数ノートに散らばっていたら「統合候補」としてリストアップ
   - 実際の統合・削除は**しない**（#レポートで提案→ユーザー承認後に別途）
4. **③ 古い情報の検出**
   - 日付が古く現状と矛盾しそうな記述を「要更新」としてフラグ
   - 明らかな事実更新（パスや設定変更等）は追記で補足、判断が要るものは提案
5. **④ メモリindex整備**
   - MEMORY.md に未登録の重要メモがあれば1行追記
   - 死んだ/不要なメモがあれば提案
6. Discord #レポート (chat_id 1512911466628386837) に整理結果を報告：
   「🌳 Vault整理（M/D）：リンクN本追加／統合候補X件／要更新Y件」

## 安全ルール
- **リンク追加は自動OK**（非破壊）
- **削除・統合・大幅書き換えは提案のみ**（承認制）。勝手に消さない
- 不可逆操作なし。迷ったら"提案"に倒す

## 関連
[[autonomy-drive-forward]] / daily-knowledge-extract（日誌→知識） / [[Obsidian Vault完全参照]]
