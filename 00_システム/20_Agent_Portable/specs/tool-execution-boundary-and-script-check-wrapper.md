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

- もっとも濃い原因は、Claude Code / Channels の構造化ツール呼び出し境界が崩れ、本来ツール呼び出しとして処理されるべきものが本文テキストとして出た事故。
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

この転送を作る場合は、`exec "$HOME/agent-skills/youtube-script-checker/bin/yt-script-scan" "$@"` だけの薄いshimにする。判定ロジック、辞書パス、出力整形は置かない。

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

### 終了コード契約

`scan_v4.py` 本体は `verdict` をJSONで返すだけで、WARN / FAIL を非0終了にしない可能性がある。wrapperは次の終了コードで機械判定を固定する。

| exit | 意味 | 扱い |
|---:|---|---|
| 0 | PASS | 出荷判定の第1段階OK |
| 10 | WARN / yellowあり | 自動処理では成功扱いにしない。文脈確認または人間判断へ |
| 20 | FAIL / redあり | 要修正。次工程へ進めない |
| 30 | CSV不正 / 入力ファイルなし | 実行失敗。出荷判定しない |
| 40 | data-dir不備 / 辞書0件疑い | 設定不備。偽PASS防止のため失敗 |
| 50 | `scan_v4.py` 非0終了 / JSON parse失敗 | 実行失敗。stdout / stderr を確認 |
| 60 | `<invoke` 等の実行タグ漏れ検知 | 未実行扱い。通常のshell/wrapper実行へ戻す |

自動化ジョブは exit 0 以外を成功扱いしない。特に exit 10 は「壊れてはいないが人間確認が必要」という扱いで、次工程へ自動進行させない。

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
2. 既存PASS台本は exit 0
3. yellowありfixtureは exit 10
4. redありfixtureは exit 20
5. 存在しないCSV、空CSV、台詞列なしCSVで分かるエラーになり exit 30
6. data-dirを壊したとき偽PASSにせず exit 40
7. `scan_v4.py` 非0終了やJSON parse失敗は exit 50
8. `<invoke` 漏れ検知は exit 60
9. read-only環境でも `PYTHONDONTWRITEBYTECODE=1` 付きで落ちない
10. `--json` が既存 `scan_v4.py` 互換を保つ
11. 日本語・空白入りパスで `rg` 文脈確認が動く
12. ネットワークなし、ファイル書き込みなしで完結する
13. Channels / `claude -p` / デスクトップの3経路で `<invoke` が成功扱いにならない

## 次にやる実装

優先順位:

1. `~/agent-skills/youtube-script-checker/bin/yt-script-scan` を作る
2. `youtube-script-checker/SKILL.md` の実行手順を wrapper 呼び出しへ置換する
3. Channels / Discord 側に `<invoke` 漏れ検知ガードを追加する
4. `claude -p` 直叩きを、無害系から `claude_run.sh` / `agent-run` に寄せる

注意:

- `~/agent-skills` と `~/agent-adapters` はSecond Brain外の別正本。編集時はそのrepo側でgit状態を確認する。
- 実装者と確認者の分離が必要な領域（お金、削除、外部投稿、自動化停止）にはこのwrapper設計を直接広げない。まず読み取り専用・台本チェックから始める。
