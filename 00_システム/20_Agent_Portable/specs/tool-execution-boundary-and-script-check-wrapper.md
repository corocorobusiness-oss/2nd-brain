# Tool Execution Boundary and Script Check Wrapper Design

作成日: 2026-06-29
状態: 設計案（実装は次ステップ）
対象: Claude Code / Claude Channels / Codex / YouTube台本チェック

## 結論

今回の `願人坊主` / `狸親父` 確認で起きた問題は、単なる権限不足ではない。

`<invoke name="Bash">` のようなツール呼び出し風テキストが本文に出ても、それは実行ではない。実ツール結果、終了コード、出力、差分、API応答などの証拠がないものは未実行として扱う。

根本対応は2層に分ける。

1. 共通契約: 実行証拠がないものを完了扱いしない
2. 実務設計: 台本チェックなどの定型処理は、AIに長いコマンドを書かせず、決定論的な薄いwrapperへ寄せる

## 複数エージェント合意

独立レビュー3件の結論はほぼ一致。

- もっとも濃い原因は、Claude Codeが本来構造化ツール呼び出しとして出すべきものを本文テキストとして漏らす境界事故。
- `--allowedTools` を増やしても、本文に出た `<invoke ...>` は実行されない。
- Channels / Discord は受付・通知・軽い定型処理に寄せ、Bashを伴う重い作業はデスクトップClaude CodeかCodexへ渡す。
- `agent-run` はAI本体を呼ぶ入口であり、ローカル検査ツールまで背負わせない。
- YouTube台本チェッカーは `~/agent-skills/youtube-script-checker/` に薄い実行wrapperを置くのが一番壊れにくい。

## 実行境界ルール

次のどれかが確認できるまで、実行済みとして扱わない。

- ツール実行結果
- 終了コード
- stdout / stderr
- ファイル差分
- API応答
- スクリーンショットやレンダリング結果
- wrapperが出した機械判定

次は実行証拠ではない。

- 本文に出た `<invoke name="Bash">...`
- 本文に出た `Bashツールで実行します`
- 実行予定のコマンド説明だけ
- 空出力
- JSON parse不能な結果
- 権限エラーを握りつぶした出力

## YouTube台本チェック wrapper 設計

正本候補:

```text
~/agent-skills/youtube-script-checker/bin/yt-script-scan
```

任意の薄い転送:

```text
~/agent-adapters/bin/yt-script-scan
```

`agent-run` には載せない。`agent-run` は Claude / Codex などAI実行入口の差し替え点であり、`scan_v4.py` のようなローカル決定論ツールはスキル側のbinに置く。

### 標準コマンド

```bash
PYTHONDONTWRITEBYTECODE=1 python3 "$HOME/agent-skills/youtube-script-checker/scripts-v2/scan_v4.py" "$CSV" --data-dir "$HOME/agent-skills/youtube-script-checker/refs/data"
```

理由:

- `PYTHONDONTWRITEBYTECODE=1` で read-only / sandbox 環境の `.pyc` 書き込み失敗を避ける
- `--data-dir` を明示して、辞書未読込による偽PASSを防ぐ
- `~/agent-skills` を正本にして、Claude / Codex で同じ辞書とスクリプトを読む

文脈確認の標準形:

```bash
rg -n -C 2 --fixed-strings -e "願人坊主" -e "狸親父" "$SCRIPT_DIR"
```

### wrapper 仕様

```text
yt-script-scan <台本.csv> [--json] [--debug]
```

通常出力:

```text
規約8層: PASS red=0 yellow=0
辞書: OK
次: 文脈チェックへ
```

`--json`:

- `scan_v4.py` 互換のJSONを返す
- 既存の自動処理を壊さない

`--debug`:

- 実行したPythonパス
- data-dir
- exit code
- stdout / stderr先頭
- CSV行数
- 辞書ファイル検出状況

### エラー設計

wrapperは、以下を短い診断に変換する。

| 状況 | 扱い |
|---|---|
| JSON parse失敗 | スキャン結果がJSONではない。stdout / stderr / exit code を表示し、出荷判定しない |
| 権限不足 | `PYTHONDONTWRITEBYTECODE=1` 付き再実行、または読める場所への移動を促す |
| CSV不正 | 台詞列または有効な台詞データがないとして失敗 |
| 辞書0件 | data-dir違いの疑いとして失敗。偽PASSにしない |
| `<invoke` 漏れ | 実行タグが本文に漏れているとして未実行扱い |

## Claude / Channels 側の運用

短期:

- Channelsで `<invoke` / `<parameter` / `tool call was malformed` が本文に出たら、続行せず未実行扱いにする。
- 無害な読み取りコマンド以外は自動再試行しない。freee、削除、外部投稿、自動化停止は二重実行リスクがある。
- 重いBash作業は「受付だけしてCodex/デスクトップClaude Codeへ渡す」。

中期:

- `claude -p` 直叩きを `claude_run.sh` / `agent-run` へ順次寄せる。
- Channels出力ガードを追加し、本文に `<invoke` が出たら成功扱いにしない。
- 台本チェック、タスク管理、売上集計などの定型処理は、AIにコマンドを作文させず決定論CLIへ寄せる。

長期:

- Channels / Discord をInbox化し、実作業はキューからClaude Code / Codexが処理する。
- Claude Code SDKまたは構造化出力前提の実行ハーネスで、malformed検知から安全な再生成まで機械化する。
- 失敗事例をSecond Brainへ残すだけでなく、wrapper・hook・テストへ昇格する。

## 検証

最低限の検証:

1. 既存PASS台本で `PASS red=0 yellow=0` が出る
2. 🔴入りfixtureで `FAIL` とヒット要約が出る
3. 存在しないCSV、空CSV、台詞列なしCSVで分かるエラーになる
4. data-dirを壊したとき偽PASSにしない
5. read-only環境でも `PYTHONDONTWRITEBYTECODE=1` 付きで落ちない
6. `--json` が既存 `scan_v4.py` 互換を保つ
7. 日本語・空白入りパスで `rg` 文脈確認が動く
8. ネットワークなし、ファイル書き込みなしで完結する
9. Channels / `claude -p` / デスクトップの3経路で `<invoke` が成功扱いにならない

## 次にやる実装

優先順位:

1. `~/agent-skills/youtube-script-checker/bin/yt-script-scan` を作る
2. `youtube-script-checker/SKILL.md` の実行手順を wrapper 呼び出しへ置換する
3. Channels / Discord 側に `<invoke` 漏れ検知ガードを追加する
4. `claude -p` 直叩きを、無害系から `claude_run.sh` / `agent-run` に寄せる

注意:

- `~/agent-skills` と `~/agent-adapters` はSecond Brain外の別正本。編集時はそのrepo側でgit状態を確認する。
- 実装者と確認者の分離が必要な領域（お金、削除、外部投稿、自動化停止）にはこのwrapper設計を直接広げない。まず読み取り専用・台本チェックから始める。
