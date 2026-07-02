#!/bin/bash
# ============================================================
# Vault＋経費レシートのローカルスナップショット（Google喪失対策）
#   2nd-BrainはMacローカル正本、経費精算/売上証憑はGoogle Drive正本として
#   ~/claude-backups/ にtarで写し取る。
#   秘密情報は含まないが事業データなので chmod 600。
#
#   重要な制約（ツバキ検証 2026-06-12）:
#     launchd直起動のbashはGoogle Drive(CloudStorage)を「読めない」(TCC)。
#     書き込みは通る。claude経由ならFull Disk Accessで読める。
#   → launchdからは agent-run 経由で本スクリプトの direct モードを呼ぶ。
#      （com.claude.vault-snapshot → run_vault_snapshot.sh → agent-run(Claude固定) → ここ）
#
#   副次効果: tarで全ファイルを読む＝クラウドのみのプレースホルダを
#   ローカルに実体化（ダウンロード）させる。レシートの実体確保も兼ねる。
#
#   使い方: vault-snapshot.sh direct   … 実際にtarを作る（claude経由/手動用）
# ============================================================
set -uo pipefail

BACKUP_DIR="$HOME/claude-backups"
QUARANTINE="$BACKUP_DIR/_quarantine"
ARCHIVE_DIR="$BACKUP_DIR/_old"
KEEP=4   # 週次なので約1ヶ月分
STAMP="$(date '+%Y-%m-%d')"
OUT="$BACKUP_DIR/vault-snapshot-$STAMP.tar.gz"
TMP_OUT="$OUT.part"
BUILD_TMP=""
NOTIFY="$HOME/.claude/scripts/discord_notify.sh"
STATE="$HOME/.claude/scripts/vault-snapshot-state.json"
DRIVE_ROOT="$HOME/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ"
VAULT_SRC="$HOME/2nd-Brain-master"
VAULT_PARENT="${VAULT_SRC%/*}"
VAULT_BASENAME="${VAULT_SRC##*/}"
# 復元演習（柱③）用 manifest: 全ファイルのsha256をtar内に焼き込む。
# 月次のrestore-drill.shが/tmp展開してこれと照合し「中身の正しさ」を検査する。
MANIFEST_DIR="$BACKUP_DIR/.manifest"
MANIFEST_NAME="_BACKUP_MANIFEST.sha256"
MANIFEST="$MANIFEST_DIR/$MANIFEST_NAME"
# 会計の生命線: 二重計上防止の唯一の永続記憶（freee無料プランで30日超の取引はAPI不可視に
# なるため、この台帳が消えると過去明細を再登録＝二重計上する）。SPOF回避のため週次snapshotに
# 同梱して「Drive喪失対策tar → 自動でSSDオフサイト → restore-drill照合」の経路へ確実に載せる。
# 機密（鍵/トークン）は含まない取引ID台帳なので平文SSDコピーにも適合。追加のみ・既存対象は不変。
FREEE_LEDGER_DIR="$HOME/.claude/scripts"
FREEE_LEDGER_NAME="freee_registered_txns.json"
FREEE_LEDGER="$FREEE_LEDGER_DIR/$FREEE_LEDGER_NAME"

alarm() {
  echo "🔴 $1" >&2
  bash "$NOTIFY" "🔴【Vaultスナップショット異常】$1（機: $(hostname -s)）" || echo "（Discord通報も失敗）" >&2
}
quarantine_and_die() {
  mkdir -p "$QUARANTINE"
  [ -n "${BUILD_TMP:-}" ] && rm -rf "$BUILD_TMP"
  [ -f "$TMP_OUT" ] && mv "$TMP_OUT" "$QUARANTINE/$(basename "$OUT").$(date +%H%M%S).bad"
  alarm "$1 → 新スナップショットを隔離。前回良品は無傷。"
  exit 1
}
trap 'alarm "ジョブが予期せず異常終了（行 $LINENO）"' ERR

mkdir -p "$BACKUP_DIR" "$ARCHIVE_DIR"

# --- 読めるか先に確認（TCCブロックならここで即わかる）---
if [ ! -s "$VAULT_SRC/CLAUDE.md" ]; then
  alarm "ローカル2nd-Brain正本が読めない: $VAULT_SRC"
  exit 1
fi
if ! ls "$DRIVE_ROOT/経費精算" >/dev/null 2>&1; then
  alarm "Driveの経費精算が読めない（TCC）。agent-run経由で再実行が必要"
  exit 1
fi
if ! ls "$DRIVE_ROOT/売上証憑" >/dev/null 2>&1; then
  alarm "Driveの売上証憑が読めない（TCC）。agent-run経由で再実行が必要"
  exit 1
fi

PREV="$(ls -1t "$BACKUP_DIR"/vault-snapshot-*.tar.gz 2>/dev/null | grep -v "$STAMP" | head -1 || true)"

# --- 事前実体化: 全ファイルを先に読み、Driveのdatalessファイルを実体化 ---
#   bsdtarはdatalessファイルでEDEADLK死するため、先に全ファイルをreadして
#   FileProviderに実体化させる。checksum manifestはtarへ実際に入った中身から後段で生成する。
#   読めた件数=n / 読めなかった件数=fail。failは「バックアップから漏れる」ので警告。
mkdir -p "$MANIFEST_DIR"
MATERIALIZED=$(python3 - "$VAULT_SRC" "$DRIVE_ROOT/経費精算" "$DRIVE_ROOT/売上証憑" <<'PY'
import os, sys, ctypes
# datalessファイルはそのまま読むとEDEADLKになる環境があるため、
# 実体化ポリシーを明示ON（IOPOL_TYPE_VFS_MATERIALIZE_DATALESS_FILES=3, PROCESS=0, ON=2）
ctypes.CDLL("/usr/lib/libSystem.dylib").setiopolicy_np(3, 0, 2)
n = fail = 0
for top in sys.argv[1:]:
    for root, dirs, fs in os.walk(top):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in fs:
            if f == ".git":
                continue
            p = os.path.join(root, f)
            try:
                with open(p, "rb") as fh:
                    for _ in iter(lambda: fh.read(1 << 20), b""):
                        pass
                n += 1
            except OSError:
                fail += 1
print(f"{n} {fail}")
PY
)
MAT_OK="${MATERIALIZED% *}"; MAT_FAIL="${MATERIALIZED#* }"
[ "$MAT_OK" != "0" ] && echo "📥 materialize: ${MAT_OK}件を読み取り（Drive実体化チェック）"
[ "$MAT_FAIL" != "0" ] && alarm "読めず事前実体化できなかったファイルが${MAT_FAIL}件ある（読めない＝バックアップから漏れる）"

# --- 会計の生命線（freee台帳）を同梱の準備: 存在すれば tar 引数に追記する ---
#   tar は -C で基点を切り替えながら追加できる。台帳が無い時は黙って同梱しない
#   （月次claude-backupにも入る二重経路なので、ここはあくまで頻度を上げる週次の上乗せ）。
LEDGER_ARGS=()
LEDGER_INCLUDED="no"
if [ -f "$FREEE_LEDGER" ]; then
  LEDGER_ARGS=( -C "$FREEE_LEDGER_DIR" "$FREEE_LEDGER_NAME" )
  LEDGER_INCLUDED="yes"
else
  log_ledger_missing="yes"
fi

# --- tar作成 ---
#   1) payload tarを作る
#   2) payload tarを一時展開する
#   3) 展開された「実際にtarへ入った中身」からmanifestを生成する
#   4) manifest込みで最終tarを作る
# これにより、実行時刻だけが変わるstateファイルがmanifest作成後に更新されても照合が壊れない。
BUILD_TMP="$(mktemp -d)"
PAYLOAD_TAR="$BUILD_TMP/payload.tar.gz"
SNAPSHOT_ROOT="$BUILD_TMP/root"
mkdir -p "$SNAPSHOT_ROOT"

tar -czf "$PAYLOAD_TAR" \
  --exclude='.git' \
  -s ",^${VAULT_BASENAME}$,2nd-Brain," \
  -s ",^${VAULT_BASENAME}/,2nd-Brain/," \
  -C "$VAULT_PARENT" \
  "$VAULT_BASENAME" \
  -C "$DRIVE_ROOT" \
  "経費精算" \
  "売上証憑" \
  ${LEDGER_ARGS[@]+"${LEDGER_ARGS[@]}"} || quarantine_and_die "tar作成失敗（exit $?）"

tar -xzf "$PAYLOAD_TAR" -C "$SNAPSHOT_ROOT" || quarantine_and_die "manifest生成用のpayload展開に失敗"

MANIFEST_COUNT=$(python3 - "$SNAPSHOT_ROOT" "$MANIFEST" <<'PY'
import os, sys, hashlib
root, manifest_path = sys.argv[1], sys.argv[2]
n = 0
with open(manifest_path, "w", encoding="utf-8") as mf:
    for cur, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in fs:
            if f in {".git", "_BACKUP_MANIFEST.sha256"}:
                continue
            p = os.path.join(cur, f)
            try:
                h = hashlib.sha256()
                with open(p, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                rel = os.path.relpath(p, root).replace(os.sep, "/")
                # shasum -c はパスに改行があると壊れる。該当ファイルはmanifestから外す（存在チェックは鍵リストが受ける）
                if "\n" in rel:
                    continue
                mf.write(f"{h.hexdigest()}  {rel}\n")
                n += 1
            except OSError:
                pass
print(n)
PY
)
[ "$MANIFEST_COUNT" != "0" ] && echo "🔏 manifest: ${MANIFEST_COUNT}件をtar展開物からsha256記録（柱③復元演習の照合台帳）"
[ -s "$MANIFEST" ] || quarantine_and_die "manifest生成に失敗（空）"

FINAL_ENTRIES=( "2nd-Brain" "経費精算" "売上証憑" )
[ "$LEDGER_INCLUDED" = "yes" ] && FINAL_ENTRIES+=( "$FREEE_LEDGER_NAME" )
tar -czf "$TMP_OUT" \
  -C "$SNAPSHOT_ROOT" \
  "${FINAL_ENTRIES[@]}" \
  -C "$MANIFEST_DIR" \
  "$MANIFEST_NAME" || quarantine_and_die "manifest込みtar作成失敗（exit $?）"
chmod 600 "$TMP_OUT"
# manifestがtarに確実に入ったか（入ってないと復元演習が照合できない）
tar -tzf "$TMP_OUT" | grep -qx "$MANIFEST_NAME" || quarantine_and_die "manifestがtarに焼かれていない"
# 会計の生命線がtarに確実に入ったか（存在するのに入っていなければ隔離して大声で気づく）
if [ "$LEDGER_INCLUDED" = "yes" ]; then
  tar -tzf "$TMP_OUT" | grep -qx "$FREEE_LEDGER_NAME" || quarantine_and_die "freee台帳（$FREEE_LEDGER_NAME）がtarに焼かれていない"
fi

# --- 検査: 整合性・ファイル数・容量・テスト復旧 ---
gzip -t "$TMP_OUT" 2>/dev/null || quarantine_and_die "gzip整合性チェック失敗"
NEW_COUNT=$(tar -tzf "$TMP_OUT" | grep -cv '/$')
NEW_SIZE=$(stat -f%z "$TMP_OUT")
if [ -n "$PREV" ]; then
  PREV_COUNT=$(tar -tzf "$PREV" | grep -cv '/$')
  PREV_SIZE=$(stat -f%z "$PREV")
  [ "$NEW_COUNT" -lt $((PREV_COUNT / 2)) ] && quarantine_and_die "ファイル数半減: $NEW_COUNT < 前回${PREV_COUNT}の半分（大量削除/同期破壊の疑い）"
  [ "$NEW_SIZE" -lt $((PREV_SIZE / 2)) ] && quarantine_and_die "容量半減: $((NEW_SIZE/1024))KB < 前回$((PREV_SIZE/1024))KBの半分"
fi
RESTORE_TMP="$(mktemp -d)"
tar -xzf "$TMP_OUT" -C "$RESTORE_TMP" "2nd-Brain/CLAUDE.md" 2>/dev/null
[ -s "$RESTORE_TMP/2nd-Brain/CLAUDE.md" ] || { rm -rf "$RESTORE_TMP"; quarantine_and_die "テスト復旧: 2nd-Brain/CLAUDE.md が読めない"; }
rm -rf "$RESTORE_TMP"
rm -rf "$BUILD_TMP"
BUILD_TMP=""

# --- 残存プレースホルダの数（tar後もdatalessなら同期不調のサイン）---
DATALESS=$(python3 - "$DRIVE_ROOT/経費精算" <<'PY'
import os, sys
n = 0
for root, dirs, fs in os.walk(sys.argv[1]):
    for f in fs:
        try: st = os.stat(os.path.join(root, f))
        except OSError: continue
        if st.st_size > 4096 and st.st_blocks == 0: n += 1
print(n)
PY
)

# --- 合格 → 採用・ローテーション（削除しない=風神さん流）---
mv "$TMP_OUT" "$OUT"
ls -1t "$BACKUP_DIR"/vault-snapshot-*.tar.gz 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r old; do
  mv "$old" "$ARCHIVE_DIR/"
done

python3 - "$OUT" "$NEW_SIZE" "$NEW_COUNT" "$STATE" <<'PY'
import json, sys, datetime
open(sys.argv[4], "w").write(json.dumps({
  "last_success": datetime.datetime.now().isoformat(timespec="seconds"),
  "file": sys.argv[1], "size_bytes": int(sys.argv[2]), "files": int(sys.argv[3])}, ensure_ascii=False, indent=1))
PY

NOTE=""
[ "$DATALESS" -gt 0 ] && NOTE="⚠️レシート${DATALESS}件がまだクラウドのみ（要確認）"
[ "${log_ledger_missing:-}" = "yes" ] && NOTE="${NOTE}⚠️freee台帳が見つからず同梱できなかった（要確認）"
echo "✅ Vaultスナップショット完了: ${OUT}（${NEW_COUNT}ファイル・$((NEW_SIZE/1024/1024))MB）${NOTE}"
# 週次の成功は静かに（失敗時だけ大声）。ただし残存プレースホルダは通報
[ "$DATALESS" -gt 0 ] && bash "$NOTIFY" "⚠️【Vaultスナップショット】完了したが、経費精算にクラウドのみのレシートが${DATALESS}件残ってる（Drive同期の確認を）" || true
# 会計の生命線が消えている可能性＝二重計上の温床なので、欠落時は黙らず通報する
[ "${log_ledger_missing:-}" = "yes" ] && bash "$NOTIFY" "⚠️【Vaultスナップショット】freee台帳（freee_registered_txns.json）が見つからずsnapshotに同梱できなかった。二重計上防止の生命線なので存在を確認して" || true

# --- SSDが挿さっていればオフサイトコピーも更新（無ければ静かにスキップ）---
bash "$HOME/.claude/scripts/ssd-backup.sh" || true
exit 0
