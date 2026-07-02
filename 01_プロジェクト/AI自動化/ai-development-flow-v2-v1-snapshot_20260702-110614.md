# ai-development-flow V1 snapshot 20260702-110614

## 目的

`ai-development-flow` V2反映前に、現行V1を復旧可能な形で退避した証跡。

このsnapshotはV1退避の記録であり、V2反映・試用開始・正式採用の記録ではない。

## 承認

```text
危険操作承認:
承認者: 池田祐馬
承認日時: 2026-07-02
対象操作: ai-development-flow V1をlegacy配下へ退避し、manifest.sha256とVault snapshotを作る
対象ファイル/対象サービス: /Users/kojinn/agent-skills/ai-development-flow/SKILL.md, /Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml
差分: 現行V1は変更せず、legacy/v1_legacy_YYYYMMDD-HHMMSS/ にコピーを追加する。V2反映はしない
影響範囲: ai-development-flowの退避記録のみ。現行入口はV1のまま
戻し方: legacyコピーを使わず現行V1をそのまま維持する。問題があれば作成したlegacy退避フォルダとVault snapshotを未採用扱いにする
実行タイミング: 承認後すぐ
二重実行防止: 退避先にtimestampを付け、既存退避先がある場合は上書きしない
```

## 退避先

```text
/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/
```

退避ファイル:

```text
/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/SKILL.md
/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/agents/openai.yaml
/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/manifest.sha256
```

## hash

現行V1:

```text
b07bd51d29c93854985e771c7f52a7e158e55a8d83218b4e86337e9b74ab4f83  /Users/kojinn/agent-skills/ai-development-flow/SKILL.md
8ce4dec09d2b79c0f9aa2203b8a5f46355b86889c2137da1e120ba361c6056cd  /Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml
```

退避コピー:

```text
b07bd51d29c93854985e771c7f52a7e158e55a8d83218b4e86337e9b74ab4f83  /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/SKILL.md
8ce4dec09d2b79c0f9aa2203b8a5f46355b86889c2137da1e120ba361c6056cd  /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/agents/openai.yaml
```

manifest.sha256:

```text
b07bd51d29c93854985e771c7f52a7e158e55a8d83218b4e86337e9b74ab4f83  SKILL.md
8ce4dec09d2b79c0f9aa2203b8a5f46355b86889c2137da1e120ba361c6056cd  agents/openai.yaml
```

判定:

```text
退避hash一致: PASS
manifest作成: PASS
```

## symlink

```text
/Users/kojinn/.codex/skills/ai-development-flow -> /Users/kojinn/agent-skills/ai-development-flow
SYMLINK_OK
```

## file mode

```text
-rw-r--r-- 503:20 /Users/kojinn/agent-skills/ai-development-flow/SKILL.md
-rw-r--r-- 503:20 /Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml
-rw-r--r-- 503:20 /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/SKILL.md
-rw-r--r-- 503:20 /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/agents/openai.yaml
-rw-r--r-- 503:20 /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/manifest.sha256
```

## 運用正本hash

```text
243830e9f2c719ba8f4e2570f9507b49a19efef085ba56ba850d4c853bb48bc3  01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md
9189e83676f61b3b693ee7ed027aae32ed8b2bbc213ae650f093341aa77259c1  01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md
3710259f36470522769a13c01d9b46ad6f9fda001fe435a902540002ca2776c9  01_プロジェクト/AI自動化/ai-development-flow-v2移行設計_2026-07-02.md
```

## 現時点

```text
V1退避済み
V1退避hash PASS確認待ち
V2反映: 未実施
試用開始: 未実施
正式採用: 未実施
```

次に進むには、人間が `V1退避hash PASS` を確認したうえで、別途 `V2反映承認` を出す。
