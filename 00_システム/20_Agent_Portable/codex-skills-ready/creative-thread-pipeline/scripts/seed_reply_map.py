# -*- coding: utf-8 -*-
# reply_map 骨格の半自動生成（⑦ STEP4の手起こし負荷を減らす）。
# 「決定的に分かる返信」だけ自動で seq:seq に起こす＝(a)本文が >>RAW で始まる明示アンカー（raw→seq変換つき）
#   (b)スレタイ反応バースト（seq2〜5の短レス→>>1の"候補"）。
# ⚠️ regexで全部は導出しない（実証で50%破綻）。暗黙の返信（短い相づち→直近の実体レス等）は
#    出さない＝そこは LLM が本文を読んで §6.5/6.6 で判断して足す。これは"叩き台"。
#
# 使い方:  python3 seed_reply_map.py <thread.md>
#   出力: ①seq付きの本文一覧（raw→seqの対応も表示＝手計算の誤りを排除）
#         ②自動シードした reply_map(JSON・明示>>のみ) ③スレタイ反応の候補
import re, sys, json

if len(sys.argv) < 2:
    sys.exit("usage: python3 seed_reply_map.py <thread.md>")

posts = []  # (raw, body)
for l in open(sys.argv[1], encoding="utf-8").read().split("\n"):
    m = re.match(r"^\s*(\d+):\s?(.*)$", l)
    if m:
        posts.append((int(m.group(1)), m.group(2)))

raw2seq = {raw: i + 1 for i, (raw, _) in enumerate(posts)}
seed = {}        # seq -> seq（明示アンカーのみ・高信頼）
burst = {}       # seq -> 1（スレタイ反応の候補・LLM確認用）
unresolved = []  # 本文>>が範囲外などで変換できなかったもの

print(f"=== {sys.argv[1]} : {len(posts)}レス（seq=位置番号） ===")
for i, (raw, body) in enumerate(posts):
    seq = i + 1
    m = re.match(r"^\s*>>(\d+)\s*", body)         # 明示アンカー
    tgt = ""
    if m:
        rawtgt = int(m.group(1))
        if rawtgt in raw2seq and raw2seq[rawtgt] < seq:
            seed[seq] = raw2seq[rawtgt]
            tgt = f"  ←明示>>{rawtgt}=seq{raw2seq[rawtgt]}"
        else:
            unresolved.append({"seq": seq, "raw_tgt": rawtgt})
            tgt = f"  ←⚠️>>{rawtgt}が変換不可(範囲外/未来)"
    elif 2 <= seq <= 5 and len(re.sub(r'^\s*>>\d+\s*', '', body)) <= 14:  # スレタイ反応バースト候補
        burst[seq] = 1
        tgt = "  ←(候補)スレタイ反応>>1?"
    raw_disp = f"raw{raw}" if raw != seq else "  ="
    print(f"seq{seq:<3}({raw_disp:>6}) {body[:42]}{tgt}")

print("\n--- ① 自動シード reply_map（明示>>のみ・そのまま信頼してよい） ---")
print(json.dumps({str(k): v for k, v in seed.items()}, ensure_ascii=False))
print("\n--- ② スレタイ反応の候補（LLMが本文確認して採否を決める・>>1） ---")
print(json.dumps({str(k): v for k, v in burst.items()}, ensure_ascii=False))
if unresolved:
    print("\n--- ⚠️ 変換不可（本文の>>が範囲外/未来＝要目視） ---")
    print(unresolved)
print("\n→ ①を土台に、②の採否＋【暗黙の返信（相づち/反論→直近の実体レス）】をLLMが §6.5/6.6 で足して完成。")
print("  暗黙分の判定は regex に任せない（50%破綻の実証あり）＝本文の意味で決める。")
