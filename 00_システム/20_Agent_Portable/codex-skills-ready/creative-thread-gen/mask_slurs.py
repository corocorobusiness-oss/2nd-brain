#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mask_slurs.py - コーパス取り込み時の蔑称マスカー
使い方:
  python3 mask_slurs.py <in.md> [-o out.md]   # ファイル→ファイル(無指定はstdout)
  cat in.md | python3 mask_slurs.py            # stdin→stdout

スクレイプした実スレを学習コーパスに取り込む前に、保護対象属性への蔑称・差別語だけを
【NG】に置換する。判定の単一ソースは qa_check.py の SLUR_RE（二重管理を避けるためimport）。
※禁止語（死/殺/バカ/糞）は学習用に残す＝本物のリズム再現のため。生成側で言い換える方針なので
  コーパスにあってよい（蔑称＝ヘイトだけは原本から消す）。原本は _原本バックアップ/ に別途退避する運用。
"""
import io, sys, argparse, importlib.util, os

# qa_check.py から SLUR_RE を単一ソースとして読み込む
_QA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_check.py")
_spec = importlib.util.spec_from_file_location("qa_check_for_mask", _QA)
_qa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_qa)
SLUR_RE = _qa.SLUR_RE


def mask(text):
    """蔑称・差別語を【NG】に置換し、(置換後テキスト, 置換件数) を返す"""
    n = len(SLUR_RE.findall(text))
    return SLUR_RE.sub("【NG】", text), n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="入力ファイル（無指定はstdin）")
    ap.add_argument("-o", "--out", help="出力ファイル（無指定はstdout）")
    a = ap.parse_args()
    src = io.open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    masked, n = mask(src)
    if a.out:
        io.open(a.out, "w", encoding="utf-8").write(masked)
        sys.stderr.write(f"[mask] 蔑称 {n}件を【NG】化 → {a.out}\n")
    else:
        sys.stdout.write(masked)
        sys.stderr.write(f"[mask] 蔑称 {n}件を【NG】化\n")
