# -*- coding: utf-8 -*-
# creative-thread-pipeline 組み立てエンジン（正本）
# 役割: LLMが §6.5/6.6 で判断した reply_map / inserts(after_seq) を受け取り、
#   話者ローテ・大/下・返信先(>>)・解説挿入・句読点改行を「規約どおり機械適用」して CSV を出す。
#   スレ本文は read-only（番号は振り直さない）。返信先の自動導出はしない（LLM判断＝§7.1）。
#
# 使い方:  python3 assemble_csv.py <manifest.json>
#   manifest の section "path" は manifest ファイルからの相対パスで解決する（CWD非依存）。
#   出力: <out_base>_台本.csv (utf-8-sig/句読点改行) ＋ <out_base>_台本.md (人間可読) ＋ ~/Desktop へ CSV 複製。
#   §4.8 受入チェックを stdout に出力。未来/自己参照・大に>>・スレタイ不正があれば exit≠0（"完成"と言わせない）。
import json, csv, re, sys, os, shutil

ROT = ["男性A", "女性B", "男性C", "女性D", "男性E"]

def read_blocks(path):
    text = open(path, encoding="utf-8").read().strip("\n")
    return [b.strip("\n") for b in re.split(r"\n\s*\n", text) if b.strip()]

def parse_thread(path):
    posts = []
    for l in open(path, encoding="utf-8").read().split("\n"):
        m = re.match(r"^\s*(\d+):\s?(.*)$", l)
        if m:
            posts.append((int(m.group(1)), m.group(2)))
    return posts

def clean(b):
    b = re.sub(r'^\s*>>\d+\s*', '', b)
    b = re.sub(r'^\s*↑\s*', '', b)
    return b

def kuten(s):  # TTS用：。、！？で改行（既存改行は一旦解除してから付与）
    return re.sub(r'([。、！？])', r'\1\n', s.replace("\n", "")).rstrip("\n")

if len(sys.argv) < 2:
    sys.exit("usage: python3 assemble_csv.py <manifest.json>")
man_path = os.path.abspath(sys.argv[1])
man_dir = os.path.dirname(man_path)
man = json.load(open(man_path, encoding="utf-8"))

def resolve(p):  # section path は manifest からの相対で解決（絶対パスはそのまま）
    return p if os.path.isabs(p) else os.path.join(man_dir, p)

rows = []
counter = {}
A = {"confirmed": 0, "suppressed": [], "inserts_fired": [], "inserts_expected": 0, "badmap": []}

def emit(sp, serif, label, numstr=None):
    counter[label] = counter.get(label, 0) + 1
    rows.append([sp, serif, label, numstr if numstr is not None else str(counter[label])])

for sec in man["sections"]:
    if sec["type"] == "narr":
        for b in read_blocks(resolve(sec["path"])):
            emit("解説者", b, sec["label"])
        continue
    # thread
    label = sec["label"]
    A.setdefault("thread_labels", []).append(label)
    rmap = {int(k): int(v) for k, v in sec.get("reply_map", {}).items()}
    override = {int(k): bool(v) for k, v in sec.get("dai_override", {}).items()}  # ⑤グレーゾーン手動確定
    raw_inserts = sec.get("inserts", [])
    inserts = {}
    for d in raw_inserts:                      # 同一after_seq重複→即エラー（片方の無言消失を禁止）
        a = int(d["after_seq"])
        if a in inserts:
            sys.exit(f"[ERROR] {label}: after_seq={a} に解説が重複指定（片方が無言消失するため禁止）")
        inserts[a] = d
    A["inserts_expected"] += len(raw_inserts)   # 元配列長で数える（dedupで期待値が下がる自己無効化を防ぐ）
    posts = parse_thread(resolve(sec["path"]))
    nseq = len(posts)
    thread_seqs = set(range(1, nseq + 1))
    for asq in inserts:                       # H2: after_seq実在チェック（無言消失を禁止）
        if asq not in thread_seqs:
            sys.exit(f"[ERROR] {label}: insert after_seq={asq} がスレ({nseq}レス)に存在しない")
    for s, m in rmap.items():                 # reply_map レンジ＆未来参照チェック
        if s < 1 or s > nseq or m < 1 or m > nseq:
            A["badmap"].append({"label": label, "seq": s, "tgt": m, "why": "範囲外"})
        elif m >= s:
            A["badmap"].append({"label": label, "seq": s, "tgt": m, "why": "未来/自己参照"})
    prev_dai = False
    for i, (num, body) in enumerate(posts):
        seq = i + 1
        c = clean(body); base_dai = len(c) >= 88   # 字数は句読点改行を付与する前の生本文で数える
        is_dai = override.get(seq, base_dai)        # ⑤ dai_overrideがあれば88字判定より優先
        if seq != 1 and 83 <= len(c) <= 92 and seq not in override:   # 境界±5字の未確認＝グレーゾーン
            A.setdefault("grey", []).append({"label": label, "seq": seq, "len": len(c), "判定": "大" if is_dai else "非大"})
        sp = ROT[i % 5]
        if seq == 1:
            emit(sp, body, label, str(seq)); prev_dai = False
            A.setdefault("thread_titles", []).append(sp)   # スレタイ話者を記録（labelテキスト非依存の受入チェック用）
        else:
            tgt = rmap.get(seq)
            if tgt is not None: A["confirmed"] += 1
            is_reply = (tgt is not None) and (not prev_dai) and (not is_dai)   # 優先: is_dai>prev_dai>map
            if tgt is not None and not is_reply:
                A["suppressed"].append({"label": label, "seq": seq, "tgt": tgt,
                                         "why": "大" if is_dai else "大の直後"})
            suf = "大" if is_dai else ("下" if is_reply else "")
            numstr = f"{seq}>>{tgt}" if is_reply else str(seq)
            emit(sp + suf, c, label, numstr); prev_dai = is_dai
        if seq in inserts:                    # 解説挿入＝after_seq直後
            d = inserts[seq]; A["inserts_fired"].append(seq)
            for b in read_blocks(resolve(d["path"])):
                emit("解説者", b, d["label"])

base = man["out_base"]
csv_path = base + "_台本.csv"
md_path = base + "_台本.md"
out = [[r[0], kuten(r[1]), r[2], r[3]] for r in rows]
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["登場人物", "セリフ", "備考", "番号"]); w.writerows(out)

# 人間可読 .md（構成見出し付き・句読点改行は畳む）
mlines = [f"# {os.path.basename(base)} 台本（組み立て結果）\n"]
prev_label = None
for sp, serif, label, numstr in rows:
    if label != prev_label:
        mlines.append(f"\n## {label}\n"); prev_label = label
    flat = serif.replace("\n", "")
    if sp == "解説者":
        mlines.append(f"> {flat}")
    else:
        mlines.append(f"`{numstr}` **{sp}**：{flat}")
open(md_path, "w", encoding="utf-8").write("\n".join(mlines) + "\n")

# ~/Desktop へ CSV 複製（YMM4 へドラッグ用）
desk = os.path.expanduser("~/Desktop")
desk_csv = None
if os.path.isdir(desk):
    desk_csv = os.path.join(desk, os.path.basename(csv_path))
    try:
        shutil.copyfile(csv_path, desk_csv)
    except Exception as e:
        desk_csv = f"(複製失敗: {e})"

# ===== §4.8 受入チェック =====
outarrow = sum(1 for r in rows if ">>" in str(r[3]))
dai_arrow = [r[3] for r in rows if r[0].endswith("大") and ">>" in str(r[3])]
future = [r[3] for r in rows if ">>" in str(r[3])
          and int(str(r[3]).split(">>")[1]) >= int(str(r[3]).split(">>")[0])]
title_speakers = A.get("thread_titles", [])   # labelテキスト非依存（列挙系ラベルでも誤NGにならない）
title_ok = len(title_speakers) > 0 and all(s == "男性A" for s in title_speakers)
ascii_dq = [r[3] for r in rows if '"' in r[1]]   # 出荷物にASCII"が残ってないか（qaのハードゲートと整合）

print("=== 組み立て結果 ===")
for r in rows:
    tag = r[2][:6]
    print(f"{str(r[3]):<7} {r[0]:<6} [{tag}] {r[1].splitlines()[0][:30]}")

print("\n=== §4.8 受入チェック ===")
checks = []
突合 = (A['confirmed'] - len(A['suppressed']) == outarrow)
checks.append(("返信マップ突合 (承認−抑制=出力>>)", 突合,
               f"{A['confirmed']}−{len(A['suppressed'])}={A['confirmed']-len(A['suppressed'])} / 出力{outarrow}"))
checks.append(("解説 本数発火 (期待=発火)", A['inserts_expected'] == len(A['inserts_fired']),
               f"期待{A['inserts_expected']} / 発火{len(A['inserts_fired'])}@seq{A['inserts_fired']}"))
checks.append(("大に>>なし", not dai_arrow, dai_arrow or "なし"))
checks.append(("未来/自己参照なし", not future and not A['badmap'], (future + A['badmap']) or "なし"))
checks.append(("スレタイ=男性A・各スレ先頭", title_ok, f"{len(title_speakers)}スレ"))
checks.append(("出荷物にASCII\"なし", not ascii_dq, ascii_dq or "なし"))
for name, ok, detail in checks:
    print(f"  [{'OK' if ok else 'NG'}] {name}: {detail}")
print("※§4.8は構造整合の検査。返信先が会話として噛み合うかの意味検査はしない＝STEP4.5の敵対監査(LLM)の責務。")
print(f"\n抑制で消えた返信リンク(可視化): {A['suppressed'] or 'なし'}")
# ⑥ 出荷物(組み立て後CSV)の安価率を可視化＝WARN・exitには影響しない。
#    ★帯域は生スレqaの18〜32%とは別物：CSVの>>は動画の返信表示を駆動するので密度が高く、
#      本パイプラインの確立実績は≈44〜46%（平将門 本番=45/44%）。グロスな外れ値(盛り/薄すぎ)だけ拾う。
for tl in A.get("thread_labels", []):
    trows = [r for r in rows if r[2] == tl]
    if not trows:
        continue
    ar = sum(1 for r in trows if ">>" in str(r[3]))
    rate = round(100 * ar / len(trows))
    flag = "" if 30 <= rate <= 55 else "  ⚠️帯域外(組立CSV目安30〜55%・実績≈45%)"
    print(f"安価率 {tl}: {rate}% ({ar}/{len(trows)}){flag}")
# ⑤ 大判定グレーゾーン（83〜92字でoverride未指定＝要確認。dai_overrideで確定可）
if A.get("grey"):
    print(f"大グレーゾーン(83〜92字・未確認{len(A['grey'])}件): {A['grey']}")
    print('  → 必要なら manifestの該当threadに "dai_override": {"<seq>": true/false} を足して確定')
print(f"総行数: {len(rows)}")
print(f"出力CSV : {csv_path}")
print(f"出力MD  : {md_path}")
print(f"Desktop : {desk_csv or '(Desktopなし)'}")

allok = all(ok for _, ok, _ in checks)
print("\n判定:", "全PASS（出荷可）" if allok else "NGあり→完成と言わず修正")
sys.exit(0 if allok else 2)
