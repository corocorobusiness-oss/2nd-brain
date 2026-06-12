---
description: コンテキストの統合(Integrate)と適用(Apply)を一括で行うワークフロー。中間に承認ステップを含む。
---

# Context Update Pipeline

## 1. 準備 (Preparation)
まず、統合したいテキストファイル群（.txt, .mdなど）を以下のフォルダに格納してください。
`03_知識ベース/00_コンテキストログ`

準備ができたら、このワークフローを実行します。

## 2. 統合案の作成 (Drafting Phase)
### Agent Action
1.  **Integratorの起動**:
    *   プロンプト: `00_システム/01_Prompts/Workflow_Prompts/Context_Update/01_Context_Integrator.md`
    *   入力: ユーザー指定ファイル or `00_コンテキストログ` 全体。
2.  **提案書の保存**:
    *   結果を `99_Sbox/Context_Update_Proposal.md` に保存します。

## 3. ユーザー承認 (Approval Phase)
### Agent Action
1.  `notify_user` ツールを使用し、ユーザーに提案書のレビューを依頼します。
    *   **BlockedOnUser**: true
    *   **ReviewPath**: `Context_Update_Proposal.md`
    *   **Message**: "提案書を作成しました。内容を確認・修正してください。問題なければ『承認（Proceed）』と返信してください。中止する場合は『中止』と言ってください。"

## 4. 適用 (Commit Phase)
### Agent Action
1.  ユーザーが承認した場合、**Applier** を起動します。
    *   プロンプト: `00_システム/01_Prompts/Workflow_Prompts/Context_Update/02_Context_Applier.md`
    *   入力: 承認済み提案書 (`Context_Update_Proposal.md`)
2.  各ターゲットファイル（UserProfile）への書き込みを実行します。
3.  **完了報告と片付け**:
    *   処理に使用したコンテキスト元データ（テキストファイル群）を以下のフォルダに移動（アーカイブ）します。
        *   移動先: `03_知識ベース/00_コンテキストログ/既に読み込ませたデータ`
    *   完了報告を行います。
