# -*- coding: utf-8 -*-
# Phase2 自動化グラデーションの成熟度トラッカー（提案専用・勝手にflipしない）。
# 各STEPの「そのまま承認(approved)／修正(modified)」の連続回数を記録し、
# K回連続承認で「自動化していい？」の"提案"対象にする。flip(auto化)はユーザー承認後にのみ実行。
# ⚠️ 鉄則：①勝手に自動化しない（提案だけ）②🔴/FAILのハードゲートは永久に自動承認しない
#        ③auto中に修正が入ったら即manualへ降格（自動が早すぎたサイン）。
#
# 使い方:
#   python3 maturity.py status                  … ダッシュボード表示（セッション開始時に必ず見る）
#   python3 maturity.py record <STEP> approved|modified [メモ]   … STEP完了時に結果を記録
#   python3 maturity.py propose                 … 自動化提案の対象STEP一覧
#   python3 maturity.py flip <STEP> auto|manual … モード変更（autoはユーザー承認後のみ）
import json, os, sys

STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "automation-state.json")
STATE = os.path.normpath(STATE)

DEFAULT = {
    "K": 3,
    "note": "K回連続approvedで自動化"+chr(39)+"提案"+chr(39)+"。flipはユーザー承認後のみ。hard_gate=trueは永久にauto不可。",
    "steps": {
        "STEP2":   {"label": "創作スレ生成(qa)",      "mode": "manual", "streak": 0, "automatable": True,  "hard_gate": False, "history": []},
        "STEP3":   {"label": "解説対象・挿入位置",     "mode": "manual", "streak": 0, "automatable": True,  "hard_gate": False, "history": []},
        "STEP4":   {"label": "アセンブル(§4.8)",       "mode": "manual", "streak": 0, "automatable": True,  "hard_gate": False, "history": []},
        "STEP4.5": {"label": "敵対監査",               "mode": "manual", "streak": 0, "automatable": True,  "hard_gate": False, "history": []},
        "STEP5":   {"label": "規約チェック",           "mode": "manual", "streak": 0, "automatable": False, "hard_gate": True,  "history": []},
        "STEP6":   {"label": "読み仮名dic",            "mode": "manual", "streak": 0, "automatable": True,  "hard_gate": False, "history": []},
    },
}

def load():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return json.loads(json.dumps(DEFAULT))

def save(d):
    json.dump(d, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def status(d):
    K = d["K"]
    print(f"=== 自動化グラデーション（K={K}・提案専用） ===")
    print(f"{'STEP':<8}{'label':<20}{'mode':<8}{'streak':<8}状態")
    for k, s in d["steps"].items():
        if s["hard_gate"]:
            state = "🔒ハードゲート(永久manual)"
        elif s["mode"] == "auto":
            state = "⚙️自動(修正入れば降格)"
        elif s["automatable"] and s["streak"] >= K:
            state = f"💡自動化を提案できる(連続{s['streak']}≥{K})"
        else:
            state = f"確認継続(あと{max(0,K-s['streak'])}回)"
        print(f"{k:<8}{s['label']:<20}{s['mode']:<8}{s['streak']:<8}{state}")
    print("\nauto=確認スキップ(ハードゲートは実行)／manual=提案→確認。詳細ルールは learning-log.md。")

def record(d, step, outcome, note=""):
    if step not in d["steps"]:
        sys.exit(f"未知のSTEP: {step}（{list(d['steps'])}）")
    if outcome not in ("approved", "modified"):
        sys.exit("outcome は approved か modified")
    s = d["steps"][step]
    entry = outcome + (f":{note}" if note else "")
    s["history"] = (s["history"] + [entry])[-12:]
    if outcome == "approved":
        s["streak"] += 1
    else:
        s["streak"] = 0
        if s["mode"] == "auto":            # 自動中に修正＝早すぎた→manualへ降格（安全側）
            s["mode"] = "manual"
            s["history"][-1] += "→auto降格"
            print(f"⚠️ {step} は自動結果を修正したため manual に降格した")
    save(d)
    K = d["K"]
    if s["mode"] == "manual" and s["automatable"] and s["streak"] >= K:
        print(f"💡 {step}（{s['label']}）が連続{s['streak']}回そのまま承認＝**自動化を提案できる**。"
              f"ユーザーに『このSTEP自動化していい？』と確認し、OKなら `flip {step} auto`。")
    else:
        print(f"記録: {step} {outcome} / streak={s['streak']} / mode={s['mode']}")

def propose(d):
    K = d["K"]
    cand = [k for k, s in d["steps"].items()
            if s["mode"] == "manual" and s["automatable"] and not s["hard_gate"] and s["streak"] >= K]
    if cand:
        print("自動化を提案できるSTEP（ユーザー承認で flip <STEP> auto）:")
        for k in cand:
            print(f"  - {k} {d['steps'][k]['label']}（連続{d['steps'][k]['streak']}回）")
    else:
        print("自動化提案できるSTEPは今のところ無し（K回連続承認に未到達）。")

def flip(d, step, mode):
    if step not in d["steps"]:
        sys.exit(f"未知のSTEP: {step}")
    if mode not in ("auto", "manual"):
        sys.exit("mode は auto か manual")
    s = d["steps"][step]
    if mode == "auto" and (s["hard_gate"] or not s["automatable"]):
        sys.exit(f"❌ {step} はハードゲート/自動化不可＝auto化できない（🔴/FAILは永久にユーザー確認）")
    if mode == "auto":
        print(f"⚠️ {step} を auto にする前に、ユーザーが『自動化していい』と承認済みか確認したか？（提案専用の鉄則）")
    s["mode"] = mode
    save(d)
    print(f"{step} → mode={mode}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: maturity.py status|record|propose|flip ...")
    d = load(); cmd = sys.argv[1]
    if cmd == "status":   status(d)
    elif cmd == "record": record(d, sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "propose": propose(d)
    elif cmd == "flip":   flip(d, sys.argv[2], sys.argv[3])
    else: sys.exit(f"未知のコマンド: {cmd}")
