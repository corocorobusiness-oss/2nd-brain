> [!warning] 【陳腐化注記 2026-06-28】このミラーは古い。現行入口 neta-forge / script-third-party-review / youtube-history-visual-planner が欠落し、退役スキル(neta-research入口/thread-research-planner)を現役扱いしている。install_to_codex.sh の実行は現状非推奨。正本=~/agent-skills から再生成が必要。

# Codex Skills Ready

このフォルダは、Claude時代のスキルをCodex向けに移植した現役候補一式。

## 目的

`archive/claude/skills/` は移植元の控え。
この `codex-skills-ready/` は、Codexの `~/.codex/skills/` に投入するための作業済みコピー。

## 含まれるスキル

- `automation-architect`
- `daily-knowledge-extract`
- `knowledge-gardener`
- `neta-research`
- `thread-research-planner`
- `uber-earnings`
- `uber-weekly-plan`
- `ymm4-dic-generator`
- `youtube-pipeline`
- `youtube-script-checker`
- `youtube-script-parts`
- `daily-target`
- `monthly-report`
- `process-receipt`
- `record-sales`
- `today-start`
- `fujin-ai`

## 反映方法

この環境からは `~/.codex/skills/` に直接書き込めないため、通常のMac権限で以下を実行する。

```bash
zsh "00_システム/20_Agent_Portable/codex-skills-ready/install_to_codex.sh"
```

反映後、Codexを再起動または新しいスレッドを開く。

## 注意

- `fujin-ai` は『Codexアプリの教科書』特典④（風神さんのクローンスキル、Drive共有「Fujin_AI_Skills」から2026-06-10取得）。README記載の `thinking.md` と `style.md` は共有元に未収録（完全版は購入者専用LINEオープンチャットで配布）。再配布・商用転売NG。
- Google、YouTube、freee、Discord、Uberなどの認証情報は含めていない。
- 外部サービス連携系スキルは、スキルとしては認識されても、実行時には再ログインや認証設定が必要。
- 旧パス `/Users/kojinn/...` は現在のMac miniパスへ置換済み。

