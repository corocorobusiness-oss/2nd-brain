---
description: /multi-use - マスターワークフロー。テキストまたは音声を起点に、メルマガ、Xポスト、Note記事を一括生成します。
---

# マルチユース・ワークフロー (Master Controller)

このワークフローは、コンテンツ生成の「司令塔」です。
**各フェーズで必ず中間ファイルを確認し、ステップをスキップせずに順次実行してください。抽象的な指示ではなく、以下の具体的なプロンプトファイルを必ず読み込んで実行してください。**

## Phase 1: 入力ソースの確定 (Input)
1.  **音声の場合**: ユーザーが音声ファイルを提供した場合。
    *   Command: `.\00_システム\devtools\start_ears.bat` を実行。
    *   **Check**: `.\03_知識ベース\00_文字起こしログ` に新しい `.md` が生成されるまで待機（ポーリング）。
    *   Target: 新規生成されたトランスクリプトを `TARGET_SOURCE` とする。
2.  **テキストの場合**: ユーザーが `.md` を指定した場合。
    *   Target: そのファイルを `TARGET_SOURCE` とする。

## Phase 2: メルマガ生成ライン (Mail)
**抽象的な「メルマガ作成」ではなく、以下の手順でファイルを読み込み、工場ラインのように実行してください。**

1.  **Step 1: 構成案作成**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\メルマガ作成ワークフロー\1_メルマガ構成案作成プロンプト.md`
    *   Action: プロンプトを実行し、`TARGET_SOURCE` から構成案を作成。
    *   Output: `.\04_アウトプット\Mail_Draft_Structure.md`

2.  **Step 2: 執筆**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\メルマガ作成ワークフロー\2_メルマガ執筆プロンプト.md`
    *   Action: Step 1の構成案を元にドラフトを作成。
    *   Output: `.\04_アウトプット\Mail_Draft_v1.md`

3.  **Step 3: 推敲・調整**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\メルマガ作成ワークフロー\3_メルマガ推敲・リズム調整プロンプト.md`
    *   Action: ドラフトを推敲。
    *   Output: `.\04_アウトプット\Mail_Draft_Refined.md`

4.  **Step 4: 最終仕上げ**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\メルマガ作成ワークフロー\4_メルマガ最終仕上げプロンプト.md`
    *   Action: 最終版を作成。
    *   **Move to Output**: 最終稿を `.\04_アウトプット\00_メルマガ\Mail_[YYYYMMDD]_Final.md` に移動/保存。

## Phase 3: Xポスト生成ライン (X Post - Parallel Production)
**重要: ここでも必ずプロンプトファイルを読み込んで実行してください。**

1.  **Step 1: テーマ抽出 (Extraction)**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\1_長文ポスト抽出プロンプト.md`
    *   Action: `TARGET_SOURCE` から **2つの独立したテーマ** を抽出。
    *   Output: `.\04_アウトプット\X_Theme_Parallel.md`

2.  **Step 2: テーマ1の作成 (Theme 1 Production)**
    *   **2-1. Draft**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\2_長文ポスト生成プロンプト.md` を読み込み、Theme 1のドラフトを作成。
        *   Output: `.\04_アウトプット\X_Post_Theme1_Draft.md`
    *   **2-2. Quality Check**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\3_長文ポスト品質チェックプロンプト.md` を読み込み、Draftを監査。
        *   Output: `.\04_アウトプット\X_Post_Theme1_Check.md`
    *   **2-3. Rank Eval**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\4_長文ポストランク評価プロンプト.md` を読み込み、ポテンシャルを評価。
        *   Output: `.\04_アウトプット\X_Post_Theme1_Rank.md`
    *   **2-4. Refine (必須)**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\5_長文ポストディテール強化プロンプト.md` を読み込み、Check/Rankの結果を踏まえてTheme 1を強化。
        *   Output: `.\04_アウトプット\X_Post_Theme1_Refined.md`

3.  **Step 3: テーマ2の作成 (Theme 2 Production)**
    *   **3-1. Draft**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\2_長文ポスト生成プロンプト.md` を読み込み、Theme 2のドラフトを作成。
        *   Output: `.\04_アウトプット\X_Post_Theme2_Draft.md`
    *   **3-2. Quality Check**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\3_長文ポスト品質チェックプロンプト.md` を読み込み、Draftを監査。
        *   Output: `.\04_アウトプット\X_Post_Theme2_Check.md`
    *   **3-3. Rank Eval**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\4_長文ポストランク評価プロンプト.md` を読み込み、ポテンシャルを評価。
        *   Output: `.\04_アウトプット\X_Post_Theme2_Rank.md`
    *   **3-4. Refine (必須)**: `.\00_システム\01_Prompts\X長文ポスト作成プロンプト\5_長文ポストディテール強化プロンプト.md` を読み込み、Check/Rankの結果を踏まえてTheme 2を強化。
        *   Output: `.\04_アウトプット\X_Post_Theme2_Refined.md`

4.  **Step 4: 最終出力 (Final Output)**
    *   **Move to Output**: 完成した2つのポスト (`*_Refined.md`) を `.\04_アウトプット\01_Xポスト\X_[YYYYMMDD]_Theme[N].md` に移動/保存。

## Phase 4: Note記事生成ライン (Note)
**ここでも「Note作成」と省略せず、以下の4ステップを確実に実行してください。**

1.  **Step 1: 構成案作成**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\Note記事作成ワークフロー\1_Note構成案作成プロンプト.md`
    *   Action: `TARGET_SOURCE` から構成案を作成。
    *   Output: `.\04_アウトプット\Note_Draft_Structure.md`

2.  **Step 2: 原稿執筆**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\Note記事作成ワークフロー\2_Note執筆プロンプト.md`
    *   Action: 構成案から初稿を作成。
    *   Output: `.\04_アウトプット\Note_Draft_v1.md`

3.  **Step 3: 推敲・強化**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\Note記事作成ワークフロー\3_Note推敲・強化プロンプト.md`
    *   Action: 初稿を推敲。
    *   Output: `.\04_アウトプット\Note_Draft_Refined.md`

4.  **Step 4: 最終仕上げ**
    *   Tool: `read_file` -> `.\00_システム\01_Prompts\Note記事作成ワークフロー\4_Note最終仕上げプロンプト.md`
    *   Action: 最終版を作成。
    *   **Move to Output**: 最終稿を `.\04_アウトプット\03_Note\Note_[YYYYMMDD]_Final.md` に移動/保存。

## Phase 5: 完了確認とクリーンアップ (Finalize & Cleanup)
1.  **成果物リストの表示**: 以下のディレクトリに保存された最終成果物のリストをユーザーに表示。
    *   `.\04_アウトプット\00_メルマガ\`
    *   `.\04_アウトプット\01_Xポスト\`
    *   `.\04_アウトプット\03_Note\`

2.  **中間ファイルの削除 (必須)**: 以下の中間ファイルを `04_アウトプット` 直下から**全て削除**する。
    *   **Command**: `Remove-Item` または `del` を使用。
    *   **Delete Targets** (削除対象):
        ```
        .\04_アウトプット\*_Structure.md
        .\04_アウトプット\Mail_Draft_*.md
        .\04_アウトプット\Mail_Refined.md
        .\04_アウトプット\X_Theme_*.md
        .\04_アウトプット\X_Post_*.md
        .\04_アウトプット\Note_Draft_*.md
        .\04_アウトプット\Note_Structure_*.md
        ```
    *   **Verify**: `04_アウトプット` 直下に `.md` ファイルが残っていないことを確認。

3.  **完了報告**: 「マルチユースワークフローが完了しました。最終成果物は各フォルダに保存されています。」と報告。

---
**使用方法**:
「/multi-use [ファイルパス]」
**AIへの指示**: 各ステップでツールを実行するたびに、必ず `task_boundary` を更新し、進捗を明示すること。勝手に文章を作成せず、必ず指定されたプロンプトファイルの内容に従うこと。