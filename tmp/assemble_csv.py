# -*- coding: utf-8 -*-
# creative-thread-pipeline 組み立てエンジン（正本）
# 役割: LLMが §6.5/6.6 で判断した reply_map / inserts(after_seq) を受け取り、
#   話者ローテ・大/下・返信先(>>)・解説挿入・句読点改行を「規約どおり機械適用」して CSV を出す。
#   スレ本文は read-only（番号は振り直さない）。返信先の自動導出はしない（LLM判断＝§7.1）。
#
# 使い方:  python3 assemble_csv.py <manifest.json>
#   manifest の section "path" は manifest ファイルからの相対パスで解決する（CWD非依存）。
#   出力: <out_base>_台本.csv (utf-8-sig/句読点改行) ＋ <out_base>_台本.md (人間可読)。
#   ~/Desktop へのCSV複製は標準では作らない。必要な場合のみ manifest の copy_desktop=true で一時コピー。
#   §4.8 受入チェックを stdout に出力。未来/自己参照・大に>>・スレタイ不正があれば exit≠0（"完成"と言わせない）。
import json, csv, re, sys, os, shutil, subprocess

ROT = ["男性A", "女性B", "男性C", "女性D", "男性E"]
FAR_GAP = 5   # 離れた返信(seq-tgt>=FAR_GAP)は >> 番号は残すが話者の「下」を付けない（2026-06-22 池田さん指定）

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

def wrapped_line_count(s):
    return kuten(s).count("\n") + 1 if s else 0

if len(sys.argv) < 2:
    sys.exit("usage: python3 assemble_csv.py <manifest.json>")
man_path = os.path.abspath(sys.argv[1])
man_dir = os.path.dirname(man_path)
man = json.load(open(man_path, encoding="utf-8"))
kaisetsu_opening_style = str(man.get("kaisetsu_opening_style", "definition"))
require_definition_opening = kaisetsu_opening_style != "freeform"
copy_desktop = bool(man.get("copy_desktop", False))

def resolve(p):  # section path は manifest からの相対で解決（絶対パスはそのまま）
    return p if os.path.isabs(p) else os.path.join(man_dir, p)

def _str_lower(v):
    return str(v or "").strip().lower()

def _length_policy():
    policy = man.get("length_policy", {})
    return policy if isinstance(policy, dict) else {}

def _is_zatsugaku_mode():
    policy = _length_policy()
    return (
        _str_lower(man.get("content_mode")) == "zatsugaku"
        or _str_lower(policy.get("profile")) == "zatsugaku"
    )

def _thread_body_chars(path):
    return sum(len(clean(body)) for _, body in parse_thread(path))

def enforce_zatsugaku_length_gate():
    if not _is_zatsugaku_mode():
        return

    policy = _length_policy()
    min_front = int(policy.get("min_thread1_chars", 2500))
    min_back = int(policy.get("min_thread2_chars", 2500))
    min_total = int(policy.get("min_total_thread_chars", 5000))
    thread_secs = [sec for sec in man.get("sections", []) if sec.get("type") == "thread"]
    if len(thread_secs) < 2:
        sys.exit("[ERROR] zatsugaku_length_gate FAIL: 雑学モードはスレ①/スレ②の2本が必須")

    front_chars = _thread_body_chars(resolve(thread_secs[0]["path"]))
    back_chars = _thread_body_chars(resolve(thread_secs[1]["path"]))
    total_chars = front_chars + back_chars

    issues = []
    if front_chars < min_front:
        issues.append(f"スレ① {front_chars}字 < {min_front}字")
    if back_chars < min_back:
        issues.append(f"スレ② {back_chars}字 < {min_back}字")
    if total_chars < min_total:
        issues.append(f"スレ合計 {total_chars}字 < {min_total}字")

    if issues:
        sys.exit("[ERROR] zatsugaku_length_gate FAIL: " + " / ".join(issues))

    print(f"[zatsugaku_length_gate] PASS: スレ①={front_chars}字 / スレ②={back_chars}字 / 合計={total_chars}字")

enforce_zatsugaku_length_gate()

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
    # 話者はスレ内seqに対して厳密に5人ローテ固定。
    # idsによる「同一投稿者の話者据え置き」は、YMM4上の同一話者連続やローテ飛びを生むため廃止。
    speakers = [ROT[j % len(ROT)] for j in range(nseq)]
    prev_dai = False
    for i, (num, body) in enumerate(posts):
        seq = i + 1
        c = clean(body)
        line_count = wrapped_line_count(c)
        base_dai = len(c) >= 88 or line_count >= 4  # 中央ルール: 88字以上または句読点改行後4行以上
        is_dai = override.get(seq, base_dai)        # ⑤ dai_overrideがあれば自動判定より優先
        if seq != 1 and 83 <= len(c) <= 92 and seq not in override:   # 境界±5字の未確認＝グレーゾーン
            A.setdefault("grey", []).append({
                "label": label,
                "seq": seq,
                "len": len(c),
                "lines": line_count,
                "判定": "大" if is_dai else "非大",
            })
        sp = speakers[i]
        if seq == 1:
            emit(sp, body, label, str(seq)); prev_dai = False
            A.setdefault("thread_titles", []).append(sp)   # スレタイ話者を記録（labelテキスト非依存の受入チェック用）
        else:
            tgt = rmap.get(seq)
            if tgt is not None: A["confirmed"] += 1
            is_reply = (tgt is not None) and (not prev_dai) and (not is_dai)
            is_far = is_reply and (seq - tgt) >= FAR_GAP   # 離れた返信＝>>は残すが「下」は付けない
            if tgt is not None and not is_reply:
                reason = "大" if is_dai else "大の直後"
                A["suppressed"].append({"label": label, "seq": seq, "tgt": tgt,
                                         "why": reason})
            if is_far:
                A.setdefault("far", []).append({"label": label, "seq": seq, "tgt": tgt, "gap": seq - tgt})
            suf = ("下" if (is_reply and not is_far) else "") + ("大" if is_dai else "")
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

# ~/Desktop へ CSV 複製（標準では作らない。manifest copy_desktop=true の場合のみ）
desk = os.path.expanduser("~/Desktop")
desk_csv = "(標準では作成しない)"
if copy_desktop and os.path.isdir(desk):
    desk_csv = os.path.join(desk, os.path.basename(csv_path))
    try:
        shutil.copyfile(csv_path, desk_csv)
    except Exception as e:
        desk_csv = f"(複製失敗: {e})"
elif copy_desktop:
    desk_csv = "(Desktopなし)"

# ===== §4.8 受入チェック =====
outarrow = sum(1 for r in rows if ">>" in str(r[3]))
future = [r[3] for r in rows if ">>" in str(r[3])
          and int(str(r[3]).split(">>")[1]) >= int(str(r[3]).split(">>")[0])]
title_speakers = A.get("thread_titles", [])   # labelテキスト非依存（列挙系ラベルでも誤NGにならない）
title_ok = len(title_speakers) > 0 and all(s == "男性A" for s in title_speakers)
ascii_dq = [r[3] for r in rows if '"' in r[1]]   # 出荷物にASCII"が残ってないか（qaのハードゲートと整合）
speaker_pat = re.compile(r"^(男性|女性)([A-E])(?:大|下)?$")
def speaker_base(sp):
    m = speaker_pat.match(sp or "")
    return "".join(m.group(1, 2)) if m else sp

same_base_runs = []
after_narr_reply_starts = []
speaker_rotation_breaks = []
explain_opening_issues = []
combined_label_issues = []
dai_reply_issues = []
seen_explain_labels = set()
prev = None
prev_was_narr = False
for idx, r in enumerate(rows, 1):
    sp, label, numstr = r[0], r[2], r[3]
    if sp == "解説者":
        if require_definition_opening and str(label).startswith("解説") and label not in seen_explain_labels:
            seen_explain_labels.add(label)
            first_line = r[1].replace("\n", "")
            if "とは" not in first_line[:40]:
                explain_opening_issues.append({
                    "label": label,
                    "num": numstr,
                    "text": first_line[:60],
                })
        prev = None
        prev_was_narr = True
        continue
    if prev_was_narr and ("下" in sp or ">>" in str(numstr)):
        after_narr_reply_starts.append({
            "label": label,
            "num": numstr,
            "sp": sp,
        })
    if "下大" in sp:
        combined_label_issues.append({
            "label": label,
            "num": numstr,
            "sp": sp,
        })
    if "大" in sp and ">>" in str(numstr):
        dai_reply_issues.append({
            "label": label,
            "num": numstr,
            "sp": sp,
        })
    prev_was_narr = False
    b = speaker_base(sp)
    try:
        seq = int(str(numstr).split(">>", 1)[0])
        expected_base = ROT[(seq - 1) % len(ROT)]
        if b != expected_base:
            speaker_rotation_breaks.append({
                "label": label,
                "num": numstr,
                "sp": sp,
                "expected": expected_base,
            })
    except Exception:
        pass
    if prev and label == prev["label"] and b == prev["base"]:
        same_base_runs.append({
            "label": label,
            "prev": prev["numstr"],
            "curr": numstr,
            "prev_sp": prev["sp"],
            "curr_sp": sp,
        })
    prev = {"label": label, "numstr": numstr, "sp": sp, "base": b}

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
checks.append(("未来/自己参照なし", not future and not A['badmap'], (future + A['badmap']) or "なし"))
checks.append(("スレタイ=男性A・各スレ先頭", title_ok, f"{len(title_speakers)}スレ"))
checks.append(("出荷物にASCII\"なし", not ascii_dq, ascii_dq or "なし"))
checks.append(("話者5人ローテ順の崩れなし", not speaker_rotation_breaks, speaker_rotation_breaks or "なし"))
checks.append(("同一ベース話者の連続なし", not same_base_runs, same_base_runs or "なし"))
checks.append(("解説直後の下スタートなし", not after_narr_reply_starts, after_narr_reply_starts or "なし"))
checks.append(("大行に>>なし", not dai_reply_issues, dai_reply_issues or "なし"))
checks.append(("下大ラベルなし", not combined_label_issues, combined_label_issues or "なし"))
checks.append(("解説パート先頭=「とは」型", (not require_definition_opening) or (not explain_opening_issues),
               "freeform指定のためskip" if not require_definition_opening else (explain_opening_issues or "なし")))
for name, ok, detail in checks:
    print(f"  [{'OK' if ok else 'NG'}] {name}: {detail}")
print("※§4.8は構造整合の検査。返信先が会話として噛み合うかの意味検査はしない＝STEP4.5の敵対監査(LLM)の責務。")
print(f"\n抑制で消えた返信リンク(可視化): {A['suppressed'] or 'なし'}")
print(f"離れた返信(>>残し・「下」なし / FAR_GAP={FAR_GAP}): {A.get('far') or 'なし'}")
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
print(f"Desktop : {desk_csv}")

allok = all(ok for _, ok, _ in checks)
if allok:
    mirror_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror_to_ssd.py")
    if os.path.exists(mirror_script):
        mr = subprocess.run(
            [sys.executable, mirror_script, os.path.dirname(os.path.abspath(csv_path))],
            text=True,
            capture_output=True,
        )
        if mr.stdout.strip():
            print(mr.stdout.strip())
        if mr.returncode != 0:
            print(f"⚠️ SSD mirror skipped/failed (non-blocking): {mr.stderr.strip() or mr.returncode}")
print("\n判定:", "全PASS（出荷可）" if allok else "NGあり→完成と言わず修正")
sys.exit(0 if allok else 2)
