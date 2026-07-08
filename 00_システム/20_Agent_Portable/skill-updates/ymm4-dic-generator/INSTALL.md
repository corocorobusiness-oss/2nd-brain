# ymm4-dic-generator v3.0.0 の反映手順（ローカルエージェント向け）

作成: 2026-07-08 あおい（Fable・リモートセッション、ブランチ `claude/dic-skill-gaps-s6vl98`）
根拠: `01_プロジェクト/AI自動化/YMM4_dicスキル漏れ監査_2026-06-30.md` と
`01_プロジェクト/AI自動化/YMM4_dic漏れゼロ改善案_天才会議_2026-06-30.md`（天才会議の実装依頼草案どおり）

## 何が変わるか（v2.2.0 → v3.0.0）

1. **SKILL.md v3.0.0**
   - カテゴリG（単漢字・自然物・生活語彙）とカテゴリH（史料名・書名・著者名・出版社名＋文脈キュー）を新設
   - 「過剰登録OK」前提を廃止（OpenJTalk誤読固定事故対策）。候補は広く・登録は慎重に
   - 候補を must / review / reject に分類し、reject にも理由を残す
   - 完了条件を fail-close 化：validator v2 の FAIL 0 まで完了報告禁止
   - dicの責務を「候補抽出・dic生成・漏れ検出・証拠レポート」に限定
     （最終読みは reading_fix.py / per-line override / Hatsuon / YMM4実機）
2. **scripts/validate_dic.py v2**（形式チェック→漏れ・誤読検出器へ昇格）
   - required_if_present（known_readings＋high_risk must が台本に出たら登録必須）
   - known_readings 読み照合（村岡素一郎=むらおかそいちろう を FAIL にできる）
   - bad_readings 再登録の即FAIL、known_readings 内の読み衝突FAIL
   - 候補抽出層（dic未カバーの漢字連続・単漢字・数詞助数詞を WARN で列挙）
   - FAIL/WARN/INFO の3段階判定、`--json` レポート出力
3. **data/ 読み資産（新規）**
   - `known_readings.tsv`（家康回の検証済み22語をシード）
   - `bad_readings.tsv`（村岡素一郎誤読）
   - `high_risk_terms.tsv` / `ignore_terms.tsv` / `dic_history/`
4. **tests/ 家康回帰テスト（新規）**
   - 家康回で実際に漏れた6語（葦・三河後風土記・天海・隆慶一郎・大火傷・広忠）が
     漏れたdicで FAIL になること、誤読固定が FAIL になることを固定化

## 反映手順

```bash
# 0) 事前確認: 正本の現状を退避（agent-skillsはgit管理）
cd ~/agent-skills
git status && git stash list   # 作業中でないこと
cp -r ymm4-dic-generator /tmp/ymm4-dic-generator.bak-$(date +%Y%m%d)

# 1) 正本側に既存の scripts/validate_dic.py（v1）や独自変更があれば差分確認
diff -ru ymm4-dic-generator ~/2nd-Brain/00_システム/20_Agent_Portable/skill-updates/ymm4-dic-generator | head -50

# 2) パッケージを正本へ反映（丸ごと置き換え。dic_history等の既存資産があれば残す）
rsync -av --exclude '__pycache__' \
  ~/2nd-Brain/00_システム/20_Agent_Portable/skill-updates/ymm4-dic-generator/ \
  ~/agent-skills/ymm4-dic-generator/

# 3) 回帰テスト（6件全部PASSすること）
cd ~/agent-skills/ymm4-dic-generator && python3 tests/test_validate_dic.py

# 4) 実台本でスモーク（任意・推奨）: 家康回の実物dicに対して実行
python3 scripts/validate_dic.py \
  ~/Projects/youtube/創作スレ下書き/2026-06-28_家康影武者説/ymm4_user.dic \
  --script ~/Projects/youtube/創作スレ下書き/2026-06-28_家康影武者説/2026-06-28_家康影武者説_台本.csv
# → 監査どおりならFAILが出るのが正しい（漏れ6語＋村岡素一郎誤読）

# 5) 正本をコミット
cd ~/agent-skills && git add ymm4-dic-generator && git commit -m "ymm4-dic-generator v3.0.0: validator v2 fail-close化＋読み資産＋家康回帰テスト"

# 6) 後始末: パッケージをアーカイブへ移動し、作業ログに記録
mkdir -p ~/2nd-Brain/99_アーカイブ/skill-updates
mv ~/2nd-Brain/00_システム/20_Agent_Portable/skill-updates/ymm4-dic-generator \
   ~/2nd-Brain/99_アーカイブ/skill-updates/ymm4-dic-generator-v3.0.0-applied-$(date +%Y%m%d)
```

## 反映後の運用メモ

- 次回のdic生成から、完了条件は「validator v2 FAIL 0＋WARN全件判断済み」
- 誤読事故が起きたら `data/bad_readings.tsv` に1行足す（それだけで再発が機械的に止まる）
- Web裏取りまで済んだ安定読みは `data/known_readings.tsv` へ昇格（昇格条件はSKILL.mdステップ8）
- 週1または5本制作ごとに、読み資産（known/bad/context/dic_history）の独立監査を回す
  （天才会議ドキュメントの「定期独立監査」チェックリスト参照）
