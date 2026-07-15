# AI社員・マルチエージェント・オーケストレーション設計

> 祐馬さんの事業ビジョン：「ヘルメスエージェント」のように事業別 AI社員を配置し、各社員が自律的に判断・実行・売上向上を責任を持つ

## 概要

- **Fable（司令塔）** = Claude Code（わたし）が全体調整・最終判断
- **各事業エージェント** = YouTube / Delivery / Roblox の AI社員が独立判断・実行
- **技術基盤** = Agent SDK（Anthropic Managed Agents）

---

## アーキテクチャ

```
🧠 Fable（司令塔・Claude Code）
  ├→ 📺 YouTube Agent
  │   ├ ネタリサーチ・企画・制作進捗管理
  │   ├ 目標：月 12 本・月収 ¥300,000
  │   └ Memory Store：過去 6 ヶ月の企画・KPI・制作ログ
  │
  ├→ 🛵 Delivery Agent
  │   ├ 稼働計画・売上管理・効率最適化
  │   ├ 目標：日 ¥○○ × 月間売上 ¥○○万
  │   └ Memory Store：日次売上・稼働時間・最適ルート
  │
  ├→ 🎮 Roblox Agent
  │   ├ ゲーム開発進捗・マネタイズ戦略
  │   ├ 目標：収益 ¥○○万
  │   └ Memory Store：開発ロードマップ・収益ログ
  │
  └→ **Fable の役割**
      ├ 朝 7:00 全エージェント standup（進捗確認）
      ├ 売上・進捗の KPI チェック → 指示・調整
      ├ 資源配分（人手・時間・優先度）の決定
      └ リスク検知・意思決定

```

---

## 技術選択肢の比較

| | **Option A: Agent SDK** | **Option B: Claude Code Subagents** | **Option C: Managed Agents** |
|---|---|---|---|
| **実行環境** | クラウド（Anthropic マネージド） | ローカル / Claude Code 上 | クラウド（Anthropic マネージド） |
| **複数エージェント** | ✅ ネイティブサポート | ✅ 簡易（Subagents） | ✅ フル機能 |
| **状態保持** | ✅ Memory Stores + Sessions | ✅ Memory（ローカル） | ✅ Memory Stores |
| **並列実行** | ✅ 完全並列 | ⚠️ 制限あり | ✅ 完全並列 |
| **スケール** | ✅ インフラ不要 | ⚠️ マシン依存 | ✅ 自動スケール |
| **推奨段階** | Phase 0 試験 → Phase 1 移行 | Phase 0 即実施可能 | Phase 2 本格運用 |
| **コスト感** | API 従量課金 | Claude Code 既存枠内 | 従量課金 + ライセンス |
| **難度** | 中（Python/TypeScript 必須） | 低（.agent.md だけ） | 高（リソース管理） |

**推奨フロー**：
```
Phase 0: Claude Code Subagents で試験
  ↓（4-5 日・動作確認・Memory 検証）
Phase 1: Agent SDK（Python）に移行 + 2 エージェント追加
  ↓（2 週間・本格実装・並列実行テスト）
Phase 2: Managed Agents へ昇格 + 自動化
  ↓（1 ヶ月・本番運用・ROI 分析）
```

---

## Phase 0：概念実証（1 週間・Option B）

**ゴール**：YouTube Agent 1 つで動作確認 + Memory Stores の検証

### 実装物

**ファイル：`.claude/agents/youtube.agent.md`**
```yaml
---
name: youtube-agent
model: claude-opus-4
description: "YouTube チャンネル事業エージェント"
tools: [read, write, web_search, bash]
memory: true
---

## Mission
月 12 本制作・月収 ¥300,000 達成

## Authority
- ネタリサーチ・企画 ✓
- 制作進捗管理 ✓
- 視聴率・収益レポート ✓

## Knowledge Base
- チャンネル KPI：登録者数・再生時間・CTR
- 過去 12 本の企画・視聴数・収益
- 制作パイプライン（ネタ → brief → 台本 → 編集 → 投稿）
- 制約：政治・宗教ネタ NG / 投稿は火・木・日 20:00

## Daily Standup
昨日の成果 + 今日の作業予定 + ボトルネック報告

## Rules
- 毎日 18:00 に YouTube Agent が自動稼働（制作状況レポート）
- 毎週日曜 21:00 に週単位の業績報告
```

**実行例**
```bash
# Fable が YouTube Agent に指示
claude --agent youtube-agent \
  --prompt "来週のネタをリサーチして、企画 3 つ提案してくれ"

# YouTube Agent が返す
# → 企画 3 つ（タイトル・キーワード・予測視聴数）
```

### 検証項目
- ✅ Memory が企画・KPI を正確に保持するか
- ✅ エージェントが「自分の月間目標」を意識した提案をするか
- ✅ 日次自動実行のスケジュール可能性
- ✅ Fable → YouTube Agent の指示・返信サイクル

### 期間
**7 月 15 日（火） ~ 7 月 22 日（火）**

---

## Phase 1：複数エージェント実装（2 週間・Option A + CLI）

**ゴール**：3 エージェント（YouTube / Delivery / Roblox）が並列に動作

### 実装物

**1. Agent SDK (Python 化)**

```python
# ~/agent-run/youtube_agent.py
from anthropic import Anthropic

client = Anthropic()

# セッション作成（永続化）
session_config = {
    "model": "claude-opus-4",
    "system": """
あなたは YouTube チャンネル事業の AI 責任者。
月 12 本・月収 ¥300,000 達成が目標。
ネタリサーチ・企画・制作進捗を自分で判断して実行。
毎日 18:00 と毎週日曜 21:00 に業績を自動報告。
""",
    "tools": ["web_search", "file_editor", "bash"],
    "memory_store": "youtube_memory_001",
}

# Fable からの指示を受け取る
response = client.messages.create(
    model="claude-opus-4",
    max_tokens=2048,
    messages=[
        {"role": "user", "content": "来週のネタをリサーチして"}
    ],
    system=session_config["system"]
)
```

**2. 管理スクリプト**

```bash
# ~/.claude/scripts/agent-manager.sh

case $1 in
  start)
    python3 ~/agent-run/${2}_agent.py &
    ;;
  
  standup)
    # 全エージェントから日次報告を一括取得
    for agent in youtube delivery roblox; do
      python3 ~/agent-run/${agent}_standup.py >> daily_report.md
    done
    ;;
  
  status)
    # 各エージェントの現在地を表示
    echo "YouTube: $(cat ~/.cache/youtube_status.json)"
    echo "Delivery: $(cat ~/.cache/delivery_status.json)"
    echo "Roblox: $(cat ~/.cache/roblox_status.json)"
    ;;
esac
```

### 各エージェントの定義

**YouTube Agent**
- 目標：月 12 本・月収 ¥300,000
- 権限：ネタリサーチ・企画・制作進捗・視聴率レポート
- Memory：過去 6 ヶ月の企画・KPI・制作ログ

**Delivery Agent**
- 目標：月間売上 ¥○○万
- 権限：稼働計画・効率最適化・売上記録・ルート提案
- Memory：日次売上・稼働時間・ガソリン代・配達実績

**Roblox Agent**
- 目標：月収 ¥○○万
- 権限：開発進捗・マネタイズ戦略・ユーザー分析
- Memory：開発ロードマップ・収益・ユーザー数

### 検証項目
- ✅ 3 エージェントが並列に動作
- ✅ 各エージェントが独立した Memory を持つ
- ✅ Fable が全エージェント standup を一括取得可能
- ✅ CLI 管理が安定している

### 期間
**7 月 22 日（火） ~ 8 月 5 日（火）**

---

## Phase 2：状態管理・自動化（1 ヶ月・Memory Stores + Fable 調整ロジック）

**ゴール**：Fable が KPI を自動判定して指示・調整する仕組み

### 実装物

**1. Fable の Daily Workflow**

```python
# ~/.claude/scripts/fable_daily_standup.py

# 全エージェントから報告を取得
youtube_status = call_agent("youtube", "昨日の成果と今日の予定")
delivery_status = call_agent("delivery", "昨日の売上と今日の最適稼働")
roblox_status = call_agent("roblox", "開発進捗と次週の予定")

# KPI 判定
def judge_kpi(agent_name, current_value, target_value):
    ratio = current_value / target_value
    if ratio < 0.75:
        return "🔴 要対策"
    elif ratio < 0.90:
        return "🟡 要注視"
    else:
        return "🟢 順調"

# 例
youtube_progress = 10 / 12  # 10 本企画済み / 目標 12 本
youtube_judgment = judge_kpi("youtube", youtube_progress, 1.0)
# → "🟡 要注視"（83%）

# Fable が指示を判定・送信
if youtube_judgment == "🟡 要注視":
    fable_instruction = """
    YouTube さんへ：企画が 83% の進捗だね。
    残り 2 本を来週までに企画しないと月間目標未達になるよ。
    ボトルネックが何かレポートして、対策を提案してくれ。
    """
    send_message("youtube_agent", fable_instruction)
```

**2. Second Brain との連携**

```
06_エージェント運用/
├ 01_YouTube/
│  ├ KPI.md ← Fable が毎朝更新
│  ├ monthly_target.md（月間 12 本・¥300,000）
│  ├ ideas_pending.md（未企画ネタ）
│  └ production_log.md（日報・制作ログ）
│
├ 02_Delivery/
│  ├ KPI.md
│  ├ daily_target.md（日次目標・実績）
│  ├ weekly_schedule.md（稼働計画）
│  └ earnings_ledger.md（売上記録）
│
└ 03_Roblox/
   ├ KPI.md
   ├ dev_roadmap.md（開発予定）
   └ monetization_log.md（収益ログ）
```

### 検証項目
- ✅ Fable が毎朝 KPI を自動判定
- ✅ 目標未達リスクを 1 週間前に検知
- ✅ 各エージェントが Fable の指示に従う
- ✅ Second Brain の KPI 更新が自動化

### 期間
**8 月 5 日（火） ~ 9 月 5 日（金）**

---

## Phase 3：本番運用・ROI 分析（継続・Managed Agents へ昇格）

**ゴール**：各エージェント投資の ROI を見える化 + 本番スケール

### 実装物

**1. Managed Agents への昇格**
- Anthropic Console で各エージェントを正式登録
- トークン予算・優先度・アラートを設定
- Webhook で重要な報告を Discord に自動転送

**2. 月次 ROI 分析**

| エージェント | 稼働日数 | 売上 | API コスト | ROI |
|---|---|---|---|---|
| YouTube | 30 日 | ¥300,000 | ¥5,000 | 60 倍 |
| Delivery | 30 日 | ¥200,000 | ¥3,000 | 67 倍 |
| Roblox | 30 日 | ¥150,000 | ¥4,000 | 37.5 倍 |
| **計** | | **¥650,000** | **¥12,000** | **54 倍** |

**3. 継続改善**
- 売上が目標未達なら予算・権限を調整
- 高 ROI エージェントには優先度を上げる
- 新規事業の AI 社員を追加（e.g., Twitter AI）

### 期間
**9 月 6 日（土） 以降・継続**

---

## 各 Phase の判断基準（GO/NO GO）

| Phase | GO の条件 | NO GO の条件 |
|---|---|---|
| **Phase 0 → 1** | ✅ YouTube Agent が 1 週間安定稼働 + Memory 正確 | ❌ エージェントが指示を理解できない or Memory が頻繁に間違う |
| **Phase 1 → 2** | ✅ 3 エージェント並列実行 OK + CLI 管理が安定 | ❌ エージェント間の競合・リソース枯渇 or API エラー多発 |
| **Phase 2 → 3** | ✅ Fable の KPI 判定が実際に効果的（売上向上） | ❌ 指示が機能しない or コスト > 効果 |

---

## 実装に必要な準備物

### 1. Second Brain の整備
- `06_エージェント運用/` の各フォルダ・テンプレート作成
- KPI.md・月間目標・制約をファイル化

### 2. Claude API 登録
- API キー取得
- Billing 設定（従量課金有効化）
- Agent SDK の Python 環境セットアップ

### 3. 各エージェントの「ルール・目標」の明文化
- YouTube：過去 12 本の企画・視聴数・KPI を集計
- Delivery：日次売上目標・稼働時間・効率目標を定義
- Roblox：開発ロードマップ・マネタイズ戦略を明確化

### 4. Fable の指揮スクリプト
- Daily Standup スクリプト（朝 7:00 自動実行）
- KPI 判定ロジック
- Discord / Slack 連携（報告受信）

---

## 制限・注意点

| 項目 | 現状 | 対策 |
|---|---|---|
| **Agent SDK の成熟度** | Beta（仕様変更の可能性） | Phase 0-1 で実装・動作確認 |
| **Memory Store 容量** | 制限未公開 | KPI + 最新 30 日分のみ保持。過去ログは Second Brain へ |
| **エージェント間通信** | 直接通信なし（Fable 経由） | すべて中央集約型・通信コスト注意 |
| **コスト** | Token 従量課金 | 月間 ¥12,000 程度（粗算） |
| **権限分離** | 未実装 | Phase 2 で settings.json 調整（各エージェントの API 権限を分離） |

---

## 次のアクション

**即座にやること：**
1. 祐馬さんと「Phase 0 から始める」を確認
2. YouTube Agent の CLAUDE.md 作成（ネタリサーチ・企画・制作ログのルール化）
3. ~7 月 22 日までに Phase 0 の動作確認

**1 週間後：**
4. Delivery / Roblox Agent の定義
5. Agent SDK（Python）に移行

**1 ヶ月後：**
6. Fable の Daily Workflow が自動実行開始
7. Phase 2 本稼働

---

## 参考資料

- [Claude Agent SDK - Docs](https://platform.claude.com/docs/en/managed-agents/)
- [Multiagent Orchestration](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration.md)
- [Memory Stores](https://platform.claude.com/docs/en/managed-agents/memory-stores.md)
- [Anthropic API Pricing](https://www.anthropic.com/pricing)

---

**作成日**：2026-07-15
**ステータス**：Phase 0 実装前
**所有者**：祐馬 + Fable
