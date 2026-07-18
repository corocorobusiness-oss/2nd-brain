# Hermes default legacy archive manifest

作成日: 2026-07-18
対象: Hermes Agent v0.18.2 default profile
状態: **HOLD（安全な最小アーカイブは合格。不採用exportの削除承認待ち）**

## 採用するアーカイブ

### `default-profile-minimal-sanitized.tar.gz`

- サイズ: 5,613 bytes
- SHA-256: `a9a1ecc7d20917fe95cb05ad960528436c180648455c34fcf9a2d577b7371db8`
- 内容:
  - `SOUL.md`
  - `config.yaml`
- 用途: 旧default Hermesの人格・非秘密設定を確認するための参考記録
- 注意: 認証や会話状態を含まないため、これ単独で旧実行状態を完全復元するものではない

抽出後の照合:

- `SOUL.md` source/extracted SHA-256:
  `d2a7b1d72d76ddada2bdc2756cfd31c4d2f68b4af21d379cd30522a7333db74f`
- `config.yaml` source/extracted SHA-256:
  `24be0e4696f968fff579806a4df352c0db1b4246f614d1be943b3060180c6eff`

### `AI_EMPLOYEE_OPERATING_RULES.md`

- 行数: 586
- サイズ: 23,350 bytes
- SHA-256: `f0908887401161ef08592424ee96dca84b5a31564e447805497e4dceb062bd81`
- 元ファイルとのSHA-256一致: PASS
- 用途: 旧default Hermesへ設定したAI社員運用ルールの参考記録

## 除外を確認したもの

採用アーカイブには次を含めていない。

- `auth.json`
- `.env`
- `state.db`, `state.db-shm`, `state.db-wal`
- `sessions/`
- `logs/`
- `cache/`
- OAuth情報
- 会話履歴

検証結果:

- tar内ファイル数: 2
- 禁止ファイル名・禁止ディレクトリ検出: 0
- 秘密鍵、代表的なAPIキー、Bearer token、Discord token形式の検出: 0
- `SOUL.md`と`config.yaml`のsource/extracted hash一致: PASS

## 不採用の公式export

### `REJECTED-official-export-contains-runtime-cache.tar.gz`

- サイズ: 9,900,678 bytes
- tar内エントリ数: 629
- SHA-256: `406f6ecb9678cfc2da31594de0bb610f3c402fbdc6a217906fcde0a0afd8a759`
- 判定: **REJECTED / 復元・移行に使用禁止**
- 理由:
  - `cron/executions.db`を含む
  - `skills/.hub/index-cache/`を含む
  - スキル利用状態など、今回不要なランタイム由来データを含む
- 認証情報、root `state.db`、会話本文は公式exportで除外されていたが、今回の「cacheをコピーしない」という承認条件を満たさない
- 削除は危険操作承認がないため実施していない

### Vault自動コミットの記録

- Vault既存の自動コミットが作業中に実行され、commit `7e5a264`へ不採用exportと最小アーカイブの初版が取り込まれた
- commit時点の最小アーカイブは5,606 bytes、SHA-256は`cef9c9744b541276baf5fe68766f9d134a10fce7666bbb8b13b2bd9bb4c01aef`。その後、同時進行で更新されていた`config.yaml`を再読込し、現行の採用版5,613 bytesへ作り直した
- 現在の採用版のサイズ・SHA-256は、このMANIFESTの「採用するアーカイブ」に記載した値を正とする
- Git履歴の削除・書換えは危険操作承認がないため実施していない
- 不採用exportは現在の作業ツリーだけでなくcommit `7e5a264`にも残る。履歴上の扱いは別判断とし、無承認では変更しない

## 独立検証

- 別エージェントによる読み取り限定の再検証: 実施済み
- 採用tarのgzip整合、2件の内容、禁止パス0件、サイズ、SHA-256: PASS
- 個別運用ルールの行数、サイズ、SHA-256: PASS
- 不採用exportの629エントリと`cron/executions.db`、`skills/.hub/index-cache/`の存在: 再確認済み
- 判定: 採用アーカイブ単体はPASS、作業全体はHOLD

## 運用上の扱い

- 採用対象は最小アーカイブと個別運用ルールだけ
- 不採用exportは開かず、復元に使わない
- このアーカイブから新しいAI Company COOプロフィールをcloneしない
- 新プロフィールは空の状態から作成し、AI Company OS正本から必要情報だけ配備する
- 現在の`/Users/kojinn/.hermes`は変更・削除・移動していない

## 完了を保留する条件

不採用exportが作業ツリーとGit履歴に残っているため、本作業全体はまだ完成扱いにしない。作業ツリーからの削除とGit履歴の書換えは別操作として扱い、それぞれ実施するには、対象・差分・影響・戻し方を明記した危険操作承認が必要。
