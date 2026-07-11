#!/usr/bin/env python3
import copy
import json
import re
import subprocess
from pathlib import Path


ROOT = Path("/Users/kojinn/2nd-Brain-master")
OUT = ROOT / "work/brief_generation_2026-07-12/normal_drafts"
PROJECT = Path("/Users/kojinn/Projects/youtube/創作スレ下書き")
PREDICT = Path("/Users/kojinn/.claude/skills/neta-research/scripts/predict_score.py")
SUFFIX = " 2ちゃんねるの歴史オタクたちの見解がおもしろい【ゆっくり解説】"


def score(title, flags=()):
    command = ["python3", str(PREDICT), *flags, title]
    raw = subprocess.check_output(command, text=True).strip()
    match = re.search(r"\[([A-Z])\]\s+pred=\s*([\d,]+)\s+p10k=([\d.]+)%", raw)
    if not match:
        raise RuntimeError(f"score parse failed: {raw}")
    return {
        "predicted_views": int(match.group(2).replace(",", "")),
        "over_10k_prob": round(float(match.group(3)) / 100, 4),
        "rank": match.group(1),
        "raw": raw,
    }


def titles(items, flags=()):
    result = []
    for index, (title, pattern) in enumerate(items):
        found = score(title, flags)
        result.append({
            "title": title,
            "pattern": pattern,
            "predicted_views": found["predicted_views"],
            "over_10k_prob": found["over_10k_prob"],
            "rank": found["rank"],
        })
    return result


def scoring(candidate, flags=()):
    found = score(candidate["title"], flags)
    return {
        "predicted_views": found["predicted_views"],
        "over_10k_prob": found["over_10k_prob"],
        "rank": found["rank"],
        "breakdown": {"engine": "predict_score.py", "raw": found["raw"]},
        "boost": [flag.lstrip("-") for flag in flags],
        "model_version": "median-2026-06-23",
        "recent_hit_rate": 0.673,
        "confidence": "mid",
    }


def fact(fid, claim, url, half, year, tier="公的"):
    return {
        "id": fid,
        "claim": claim,
        "source_url": url,
        "source_tier": tier,
        "year": year,
        "half": half,
    }


def theory(sid, claim, variants, hedge, half):
    return {
        "id": sid,
        "claim": claim,
        "variants": variants,
        "hedge_phrase": hedge,
        "usable_in": half,
    }


def glossary(terms, fact_ids, era):
    result = []
    for index, (term, reading, layer) in enumerate(terms):
        result.append({
            "term": term,
            "reading": reading,
            "era_check": era,
            "suggested_insert_after_cluster": f"{term}が初めて議論の焦点になるクラスタ直後",
            "background_facts": [{
                "fact_id": fact_ids[min(index, len(fact_ids) - 1)],
                "c2_type": "④出典史料" if index % 2 else "②背景構造",
                "intended_use": f"{term}の本筋外の制度・史料背景を短く補足する",
            }],
            "core_new_claim": f"{term}は本筋の結論とは分け、制度・史料上の位置づけを確認する必要がある。",
            "demand_type": "hybrid" if index < 2 else "meta_background",
            "core_answer_risk": "medium" if index < 2 else "low",
            "explainable_layer": layer,
            "thread_may_say": [f"{term}の名前や一点だけの事実", f"{term}への疑問や茶々"],
            "thread_should_not_say": [f"{term}の制度・出典・帰結を一レスで説明し切る"],
        })
    return result


def directives(must_terms, tone):
    return {
        "target_chars_per_thread": "2500-3000",
        "shaku_blueprint": {
            "long": {"n": 10, "chars": "88+"},
            "mid": {"n": 8, "chars": "50-87"},
            "short": {"chars": "0-49"},
            "recommended_long": {"chars": "120-150"},
        },
        "tone": tone,
        "must_surface_terms": must_terms,
        "buntai_doc_path": "03_知識ベース/YouTube・コンテンツ制作/2chスレ文体パターン.md",
        "gloss_handling": "gloss_targets語はスレ内で断片・疑問・一点うんちくに留め、定義→背景→帰結まで説明し切らない",
        "thread_terminal_cap": {
            "window": 8,
            "max_long_88": 0,
            "allowed": ["具体物", "茶々", "疑問", "未解決感", "次の問い"],
            "forbidden": ["総括", "教訓", "余韻回収", "評価保留", "closing claim再説明"],
        },
    }


def base_draft(subject, era, save_dir, title_items, split, confirmed, shosetsu,
               avoids, hard_dates, must_terms, gloss_terms, context, flags=(), tone="光と影"):
    candidates = titles(title_items, flags)
    return {
        "save_dir": f"Projects/youtube/創作スレ下書き/{save_dir}/",
        "status": "ready_for_pipeline",
        "block_reasons": [],
        "theme_subject": subject,
        "era": era,
        "working_title": candidates[0]["title"],
        "title_candidates": candidates,
        "split": split,
        "scoring": scoring(candidates[0], flags),
        "facts": {
            "confirmed": confirmed,
            "shosetsu": shosetsu,
            "avoid_assertions": avoids,
            "hard_dates": hard_dates,
        },
        "gen_directives": directives(must_terms, tone),
        "gloss": {"gloss_targets": glossary(gloss_terms, [x["id"] for x in confirmed], era), "narr_budget_pct": 25},
        "context": context,
    }


def strip_brief(source):
    data = json.loads(source.read_text(encoding="utf-8"))
    for key in ("schema_version", "brief_id", "created_at", "source_tool", "publish", "market", "trend"):
        data.pop(key, None)
    return data


def write(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.draft.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


def main():
    info_title = "【2ch歴史】明智光秀「信長を討ったぞ！」→秀吉が偽情報で逆転した件www" + SUFFIX
    info_titles = [
        (info_title, "2ch会話フック"),
        ("【2ch歴史】秀吉「信長は生きてるぞ」←本能寺後の情報戦がえぐすぎる件www" + SUFFIX, "情報戦"),
        ("【2ch歴史】秀吉、本能寺直後に「信長は無事」と偽情報を流して味方を増やした件www" + SUFFIX, "意外な真実"),
        ("【2ch歴史】秀吉、明智光秀より先に偽情報で摂津の武将を固めた件www" + SUFFIX, "比較"),
    ]
    info_facts = [
        fact("c01", "天正10年6月2日、本能寺の変で織田信長と嫡男・信忠が倒れた。", "https://da.lib.kobe-u.ac.jp/da/sc/0100399107/", "前半", 1582, "大学"),
        fact("c02", "羽柴秀吉は6月5日付で摂津茨木城主・中川清秀へ書状を送った。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c03", "6月5日付書状には、信長・信忠が無事に脱出して膳所へ退いたという事実と異なる情報が記された。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c04", "神戸大学の中川家文書解題は、この偽情報を清秀が光秀方に付くことを牽制するためだったと説明している。", "https://da.lib.kobe-u.ac.jp/da/sc/0100399107/", "前半", 1582, "大学"),
        fact("c05", "当時の軍事通信では書状の往復が成立し、中川清秀から秀吉への返答も行われていた。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c06", "現存する6月10日付の羽柴秀吉書状写は、秀吉が明石を通過した後に中川清秀へ送ったものとされる。", "https://da.lib.kobe-u.ac.jp/da/sc/0100399107/", "後半", 1582, "大学"),
        fact("c07", "6月10日書状の文言から、清秀が秀吉支持と光秀の動向に関する情報を返信していたことが分かる。", "https://da.lib.kobe-u.ac.jp/da/sc/0100399107/", "後半", 1582, "大学"),
        fact("c08", "秀吉は清秀に出兵を求め、高山右近や丹羽長秀らとの連絡状況も知らせた。", "https://da.lib.kobe-u.ac.jp/da/sc/0100399107/", "後半", 1582, "大学"),
        fact("c09", "中川清秀は6月11日に秀吉軍へ合流し、山崎合戦で本隊の一翼を担った。", "https://da.lib.kobe-u.ac.jp/da/sc/0100399107/", "後半", 1582, "大学"),
    ]
    info = base_draft(
        "羽柴秀吉の偽情報戦―中川清秀宛書状", "戦国", "2026-07-15_秀吉_本能寺後の偽情報",
        info_titles,
        {
            "pattern_id": "③", "pattern_name": "前提を疑う型",
            "front": {"role": "タイトルネタ", "theme": "6月5日書状に記された『信長・信忠は無事』という事実と異なる情報と、その宛先・狙いを追う。", "hook_type": "情報戦・意外な真実", "fact_ids": ["c01", "c02", "c03", "c04", "c05"], "rationale": "一通の書状という具体物から入り、遺体や流血を前面に出さず秀吉の情報操作を可視化する。"},
            "back": {"role": "本筋", "theme": "6月10日の返書と11日の合流までを追い、偽情報が往復書状による陣営形成の一部だったことを検証する。", "fact_ids": ["c06", "c07", "c08", "c09"], "rationale": "派手な嘘話から、返信・出兵要請・合流という実証へ深める。"},
            "thread_core_question": {"front": "秀吉は中川清秀へ何を伝え、なぜ事実と異なる情報を送ったのか？", "back": "その情報は清秀の判断と秀吉陣営の形成にどう関わったのか？"},
            "transition_B": "ここまでは、秀吉が中川清秀へ送った事実と異なる情報を見てきたが、『書状を一通送っただけで本当に武将が動くのか？』という疑問も出てきた。では返書と実際の合流はどうつながるのか。引き続き議論を見ていこう。",
            "gap_rationale": "前半の一通の嘘から、後半の往復通信・連絡網・軍勢合流へ移る。",
        },
        info_facts,
        [
            theory("s01", "秀吉が最初から虚偽を創作したのか、不確かな風評も混じったのかは断定できない。", ["意図的な情報操作", "不確かな情報の利用"], "情報操作とみられるが、書状内容が事実と異なることを中心に扱う", "前半"),
            theory("s02", "中川清秀の参陣を偽情報だけの効果と断定できない。", ["重要な判断材料", "既存関係や戦況も作用"], "判断材料の一つになったとみられる", "後半"),
        ],
        ["一通の書状だけで山崎の勝敗が決まったと断定しない", "摂津の全武将が偽情報を信じたと断定しない", "清秀が元々光秀方だったと断定しない", "タイトル内の発言を史料の逐語引用として扱わない", "遺体をタイトルやサムネの中心語にしない", "中国大返しの距離・速度・兵站を再説明しない"],
        [{"event": "本能寺の変", "year": 1582}, {"event": "秀吉の中川清秀宛書状", "year": 1582}, {"event": "中川清秀の合流", "year": 1582}],
        ["中川清秀", "膳所", "梅林寺文書", "茨木城"],
        [("中川清秀", "なかがわきよひで", "人物関係"), ("膳所", "ぜぜ", "地名"), ("梅林寺文書", "ばいりんじもんじょ", "出典史料"), ("茨木城", "いばらきじょう", "地理背景")],
        {"taiga_linked": True, "recent_overlap_urls": ["/Users/kojinn/Projects/youtube/創作スレ下書き/2026-07-03_中国大返し/2026-07-03_中国大返し_台本.md", "/Users/kojinn/Projects/youtube/創作スレ下書き/2026-07-10_明智光秀_本能寺の変理由リメイク/2026-07-10_明智光秀_本能寺の変理由リメイク_台本.md"]},
        ("--taiga", "--trend"), "情報戦を史料で解く",
    )
    write("2026-07-15_秀吉_本能寺後の偽情報", info)

    mori_titles = [
        ("【2ch歴史】毛利軍、本能寺の変を知ったのに秀吉を追撃しなかったの謎すぎる件www" + SUFFIX, "なぜ・疑問"),
        ("【2ch歴史】秀吉、毛利に背中を見せて撤退したのに追撃されなかった件www" + SUFFIX, "意外な真実"),
        ("【2ch歴史】毛利軍、秀吉が京へ撤退した時にはもう追う気がなかった件www" + SUFFIX, "前提反転"),
        ("【2ch歴史】本能寺の変を知った毛利軍、秀吉より先に撤退していた件www" + SUFFIX, "前提反転"),
    ]
    mori_facts = [
        fact("c01", "備中高松城攻めは天正10年5月上旬から進み、毛利側は周辺城を相次いで失っていた。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c02", "毛利輝元は猿掛城まで、吉川元春と小早川隆景は高松城近くまで出陣していた。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c03", "毛利勢は高松城近くまで来たが、秀吉の包囲を破って城を救援できなかった。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c04", "6月4日に清水宗治らの切腹が行われ、停戦と和議が進んだ。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c05", "6月6日付の毛利方書状が残り、遅くとも同日までに毛利側は信長死去の情報を得ていた。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "前半", 1582, "学術"),
        fact("c06", "毛利輝元の6月6日書状には、和平成立後に羽柴軍と毛利側がそれぞれ引き退いた状況が記される。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "後半", 1582, "学術"),
        fact("c07", "6月8日付の輝元書状にも、双方が和平に同意して引き退いた後に信長父子の死を聞いたとある。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "後半", 1582, "学術"),
        fact("c08", "小早川隆景は6月6日の段階で、高松近辺から西方の幸山・河辺方面へすでに移動していた。", "https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1516170/hattori_2015_6.pdf", "後半", 1582, "学術"),
    ]
    mori = base_draft(
        "本能寺の変後、毛利軍が秀吉を追撃しなかった理由", "戦国", "2026-07-17_毛利軍_秀吉を追撃しなかった理由", mori_titles,
        {
            "pattern_id": "③", "pattern_name": "前提を疑う型",
            "front": {"role": "タイトルネタ", "theme": "毛利は変を知らず秀吉を逃がしたという一般像に対し、6月6日までに変報を把握していた同時代書状を提示する。", "hook_type": "なぜ・前提反転", "fact_ids": ["c01", "c02", "c03", "c04", "c05"], "rationale": "『知らなかったから追わなかった』という単純説明を史料でひっくり返す。"},
            "back": {"role": "本筋", "theme": "毛利側はすでに和議と撤退を進めていた。元春追撃論・隆景制止の有名場面と同時代書状を切り分け、複合要因を検証する。", "fact_ids": ["c06", "c07", "c08", "s01", "s02", "s03"], "rationale": "武士の美談から、撤退位置・戦況・和議という戦略判断へ移す。"},
            "thread_core_question": {"front": "毛利はいつ本能寺の変を知ったのか？", "back": "知った後でも追撃しなかったのは何が重なった結果なのか？"},
            "transition_B": "ここまでは、毛利側が変報を把握していた時期を見てきたが、『では元春が追撃を叫び、隆景が誓紙を理由に止めたという名場面は同時代史料にもあるのか？』という疑問も出てきた。引き続き議論を見ていこう。",
            "gap_rationale": "知らなかった説の反転から、後世の人物劇と同時代書状の比較へ進む。",
        }, mori_facts,
        [
            theory("s01", "元春が追撃を主張し、隆景が誓紙の義理を理由に止めたという有名場面は後世の軍記に基づく。", ["川角太閤記の物語", "同時代書状では会話不明"], "有名な逸話として紹介し、逐語会話とは扱わない", "後半"),
            theory("s02", "追撃を見送った理由は損耗、撤退開始、和議、失敗時の危険などの複合要因と考えられる。", ["戦力・位置関係", "和議の拘束", "毛利家の安全"], "単一理由に固定せず複合要因として扱う", "後半"),
            theory("s03", "毛利が追撃すれば秀吉を倒せたかは反実仮想である。", ["成功可能性あり", "追撃側にも大きな危険"], "もし追っていたら、という仮説に留める", "後半"),
        ],
        ["毛利は本能寺の変を知るのが遅すぎたと断定しない", "隆景の武士の義理だけを唯一の理由にしない", "毛利が追えば秀吉軍を確実に全滅させられたと断定しない", "毛利が何も知らず完全に騙されたとしない", "元春と隆景の会話を逐語史実として描かない", "中国大返しの距離・速度・兵站を再説明しない", "7月15日の中川清秀宛偽情報を再使用しない"],
        [{"event": "備中高松城攻め", "year": 1582}, {"event": "本能寺の変", "year": 1582}, {"event": "毛利方6月6日書状", "year": 1582}],
        ["毛利輝元", "吉川元春", "小早川隆景", "幸山城"],
        [("毛利輝元", "もうりてるもと", "人物関係"), ("吉川元春", "きっかわもとはる", "人物関係"), ("小早川隆景", "こばやかわたかかげ", "人物関係"), ("幸山城", "こうざんじょう", "地理背景")],
        {"taiga_linked": True, "recent_overlap_urls": ["/Users/kojinn/Projects/youtube/創作スレ下書き/2026-07-03_中国大返し/2026-07-03_中国大返し_台本.md"]}, ("--taiga",), "外交と撤退判断",
    )
    write("2026-07-17_毛利軍_秀吉を追撃しなかった理由", mori)

    # Existing brief transformations
    takasugi = strip_brief(PROJECT / "2026-07-24_高杉晋作__差し替え保留/brief.json")
    takasugi["save_dir"] = "Projects/youtube/創作スレ下書き/2026-07-18_高杉晋作/"
    takasugi_items = [
        ("【2ch歴史】高杉晋作、約80人の挙兵から長州藩の流れを変えた件www" + SUFFIX, "人物・意外な真実"),
        ("【2ch歴史】高杉晋作、わずか80人ほどで長州藩の流れを変えた件www" + SUFFIX, "人物・誇張抑制"),
        ("【2ch歴史】功山寺挙兵、80人ほどで始めたの無謀すぎる件www" + SUFFIX, "事件フック"),
        ("【2ch歴史】高杉晋作、わずかな仲間で長州藩を倒幕へ動かした件www" + SUFFIX, "人物再評価"),
    ]
    takasugi["title_candidates"] = titles(takasugi_items)
    takasugi["working_title"] = takasugi["title_candidates"][0]["title"]
    takasugi["scoring"] = scoring(takasugi["title_candidates"][0])
    keep_confirmed = {"c01", "c02", "c03", "c04", "c05", "c06", "c09", "c10"}
    takasugi["facts"]["confirmed"] = [x for x in takasugi["facts"]["confirmed"] if x["id"] in keep_confirmed]
    for item in takasugi["facts"]["confirmed"]:
        if item["id"] == "c04": item["half"] = "前半"
    takasugi["facts"]["confirmed"].append(fact("c11", "元治元年12月、高杉晋作は力士隊や遊撃隊など約80人を率いて功山寺で挙兵したと山口県公式観光資料は紹介している。", "https://yamaguchi-tourism.jp/feature/shinsaku", "前半", 1864, "公的"))
    takasugi["facts"]["shosetsu"] = [x for x in takasugi["facts"]["shosetsu"] if x["id"] in {"s03", "s04"}]
    for item in takasugi["facts"]["shosetsu"]:
        if item["id"] == "s03": item["usable_in"] = "前半"
    takasugi["facts"]["avoid_assertions"] = ["功山寺挙兵の人数を80人と確定せず『約80人』『80人ほど』とする", "高杉晋作一人で長州藩を倒幕へ導いたと断定せず、諸隊・正義派全体の動きを示す", "第二次長州征討の戦果を英雄譚どおりに誇張しない", "死因や辞世を見せ場にしない"]
    takasugi["split"] = {
        "pattern_id": "①", "pattern_name": "人物深掘り型",
        "front": {"role": "タイトルネタ", "theme": "功山寺で約80人から始めた無謀な挙兵と、会所襲撃までの切迫感。", "hook_type": "少数決起・意外な真実", "fact_ids": ["c01", "c04", "c11", "s03"], "rationale": "人数は約と留保しつつ、行動の異常な速さを入口にする。"},
        "back": {"role": "本筋", "theme": "上海視察、奇兵隊、四国艦隊講和、諸隊の合流、大田・絵堂、第二次長州征討へつながる長州藩内の流れ。", "fact_ids": ["c02", "c03", "c05", "c06", "c09", "c10", "s04"], "rationale": "一人の英雄譚ではなく、諸隊と正義派の運動へ広げる。"},
        "thread_core_question": {"front": "高杉晋作はなぜ約80人で藩政府へ反旗を翻せたのか？", "back": "その小さな決起はなぜ長州藩全体の流れを変えるまで拡大したのか？"},
        "transition_B": "ここまでは約80人で始まった功山寺挙兵を見てきたが、『少人数の決起だけで藩全体が動くわけないだろ』という疑問も出てきた。では諸隊や正義派はどう続いたのか。引き続き議論を見ていこう。",
        "gap_rationale": "少人数の一点突破から、諸隊・政治・戦争を含む集団運動へ広げる。",
    }
    takasugi["gen_directives"] = directives(["高杉晋作", "功山寺挙兵", "俗論派", "正義派", "大田・絵堂の戦い", "奇兵隊", "諸隊", "長州藩"], "無謀な決起から集団運動へ")
    takasugi["gloss"] = {"gloss_targets": glossary([("高杉晋作", "たかすぎしんさく", "人物背景"), ("功山寺挙兵", "こうざんじきょへい", "事件背景"), ("俗論派", "ぞくろんは", "藩内政治"), ("正義派", "せいぎは", "藩内政治"), ("大田・絵堂の戦い", "おおだ・えどうのたたかい", "戦局背景"), ("奇兵隊", "きへいたい", "軍事制度"), ("諸隊", "しょたい", "軍事制度"), ("長州藩", "ちょうしゅうはん", "藩政背景")], ["c01", "c04", "c11", "c11", "c05", "c03", "c05", "c06"], "幕末"), "narr_budget_pct": 25}
    write("2026-07-18_高杉晋作", takasugi)

    katsu = strip_brief(PROJECT / "2026-07-17_勝海舟__差し替え保留/brief.json")
    katsu["save_dir"] = "Projects/youtube/創作スレ下書き/2026-07-22_勝海舟/"
    katsu_items = [
        (katsu["working_title"], "何をした人・再評価"),
        ("【2ch歴史】勝海舟って結局何した人？調べたら幕末屈指の交渉人だった件www" + SUFFIX, "人物再評価"),
        ("【2ch歴史】勝海舟、戦わずに江戸を守った交渉人だった件www" + SUFFIX, "実績フック"),
        ("【2ch歴史】咸臨丸と江戸無血開城だけでも勝海舟が有能すぎる件www" + SUFFIX, "実績列挙"),
    ]
    katsu["title_candidates"] = titles(katsu_items)
    katsu["working_title"] = katsu["title_candidates"][0]["title"]
    katsu["scoring"] = scoring(katsu["title_candidates"][0])
    katsu["facts"]["confirmed"] = [x for x in katsu["facts"]["confirmed"] if x["id"] not in {"c09", "c10"}]
    katsu["facts"]["confirmed"].append(fact("c11", "江戸城総攻撃回避の交渉には、高橋泥舟の提案、山岡鉄舟の事前交渉、勝海舟と西郷隆盛の会談という複数段階があった。", "https://www.ndl.go.jp/zoshoin/collection/07.html", "後半", 1868, "公的"))
    katsu["split"]["front"]["fact_ids"] = ["c01", "c05", "c08", "s04", "s05"]
    katsu["split"]["back"]["fact_ids"] = ["c02", "c03", "c04", "c06", "c07", "c11", "s01", "s03"]
    katsu["split"]["back"]["theme"] = "咸臨丸渡航、神戸海軍操練所、山岡鉄舟らの事前交渉を経た江戸無血開城という、交渉と先見で時代を動かした実績を掘る。"
    katsu["split"]["back"]["rationale"] = "咸臨丸は米海軍ブルックらの支援を受けた事実を明示し、江戸無血開城も海舟一人の英雄譚にしない。"
    katsu["split"]["thread_core_question"] = {"front": "勝海舟はなぜ名前の割に何をした人か説明しづらいのか？", "back": "複数の交渉と海軍構想の中で、勝海舟が実際に担った役割は何だったのか？"}
    katsu["gen_directives"] = directives(["勝海舟", "咸臨丸", "江戸無血開城", "西郷隆盛", "神戸海軍操練所", "山岡鉄舟", "高橋泥舟", "痩我慢の説"], "低評価から実績再評価へ")
    katsu["gloss"] = {"gloss_targets": glossary([("勝海舟", "かつかいしゅう", "人物背景"), ("咸臨丸", "かんりんまる", "航海史"), ("江戸無血開城", "えどむけつかいじょう", "交渉過程"), ("西郷隆盛", "さいごうたかもり", "人物関係"), ("神戸海軍操練所", "こうべかいぐんそうれんじょ", "海軍制度"), ("山岡鉄舟", "やまおかてっしゅう", "事前交渉"), ("高橋泥舟", "たかはしでいしゅう", "事前交渉"), ("痩我慢の説", "やせがまんのせつ", "後世評価")], ["c01", "c02", "c04", "c04", "c03", "c11", "c11", "c05"], "幕末"), "narr_budget_pct": 25}
    write("2026-07-22_勝海舟", katsu)

    yama_titles = [
        ("【2ch歴史】秀吉vs光秀、山崎の戦いの勝敗を分けたのは天王山じゃなかった件www" + SUFFIX, "通説反転"),
        ("【2ch歴史】「天下分け目の天王山」←実は勝負が決まったのは淀川沿いだった件www" + SUFFIX, "意外な真実"),
        ("【2ch歴史】山崎の戦い、天王山争奪戦で決まったという通説が後世の脚色だった件www" + SUFFIX, "史料検証"),
        ("【2ch歴史】明智光秀、天王山ではなく川沿いの側面突破で崩された件www" + SUFFIX, "戦術"),
    ]
    yama_facts = [
        fact("c01", "6月12日までに羽柴・明智両軍はほぼ布陣を終え、天王山側で小規模な衝突があった。", "https://www2.ntj.jac.go.jp/dglib/contents/learn/edc18/ehon/yomoyama/y3/a.html", "前半", 1582, "公的"),
        fact("c02", "山崎の戦いの全面戦闘は翌6月13日に起きた。", "https://www2.ntj.jac.go.jp/dglib/contents/learn/edc18/ehon/yomoyama/y3/a.html", "前半", 1582, "公的"),
        fact("c03", "堀尾吉晴と松田太郎左衛門による山頂争奪の物語は、小瀬甫庵『太閤記』で流布したと考えられている。", "https://www2.ntj.jac.go.jp/dglib/contents/learn/edc18/ehon/yomoyama/y3/a.html", "前半", 1625, "公的"),
        fact("c04", "日本芸術文化振興会の解説は、後世に語られる天王山争奪が勝敗を決めたわけではないとしている。", "https://www2.ntj.jac.go.jp/dglib/contents/learn/edc18/ehon/yomoyama/y3/a.html", "前半", 1582, "公的"),
        fact("c05", "実際の主戦場は天王山東側の湿地帯で、天王山と淀川に挟まれた狭い地形だった。", "https://www.town.oyamazaki.kyoto.jp/kanko/kankospot/2523.html", "後半", 1582, "公的"),
        fact("c06", "明智方は狭隘部から出る羽柴方を各個撃破する意図で天王山東側に展開した。", "https://www.town.oyamazaki.kyoto.jp/kanko/kankospot/2523.html", "後半", 1582, "公的"),
        fact("c07", "中川清秀・高山右近らの先手に斎藤利三らが攻めかかったが、湿地に制約されて崩し切れなかった。", "https://www.town.oyamazaki.kyoto.jp/kanko/kankospot/2523.html", "後半", 1582, "公的"),
        fact("c08", "その間に池田恒興・加藤光泰・木村隼人らが淀川沿いを進み、円明寺川東側へ展開した。", "https://www.town.oyamazaki.kyoto.jp/kanko/kankospot/2523.html", "後半", 1582, "公的"),
        fact("c09", "川沿いの明智方は比較的手薄で、同方面の部隊が苦戦したことが全軍の崩れにつながった。", "https://www.town.oyamazaki.kyoto.jp/kanko/kankospot/2523.html", "後半", 1582, "公的"),
        fact("c10", "戦闘は約3時間で終わり、光秀は勝龍寺城へ退いた。", "https://www.town.oyamazaki.kyoto.jp/kanko/kankospot/2523.html", "後半", 1582, "公的"),
    ]
    yama = base_draft(
        "山崎の戦い―天王山争奪神話と淀川沿いの実戦", "戦国", "2026-07-24_山崎の戦い", yama_titles,
        {
            "pattern_id": "③", "pattern_name": "前提を疑う型",
            "front": {"role": "タイトルネタ", "theme": "山頂を取った側が勝ったという天王山争奪物語と、その物語が『太閤記』で広まった経緯。", "hook_type": "通説反転", "fact_ids": ["c01", "c02", "c03", "c04"], "rationale": "誰もが知る慣用句を史料形成から問い直す。"},
            "back": {"role": "本筋", "theme": "主戦場だった天王山東側の湿地、円明寺川、淀川沿いでどの部隊が戦線を崩したのかを地形ベースで追う。", "fact_ids": ["c05", "c06", "c07", "c08", "c09", "c10"], "rationale": "山頂の英雄譚から川沿いの部隊運動へ視点を下ろす。"},
            "thread_core_question": {"front": "天王山山頂の争奪が本当に山崎の勝敗を決めたのか？", "back": "実際の戦線ではどこが突破され、明智方はどう崩れたのか？"},
            "transition_B": "ここまでは天王山争奪の有名な物語を見てきたが、『それが後世に広まった話なら、6月13日の本戦で実際に明智軍を崩したのは何だったのか？』という疑問も出てきた。引き続き議論を見ていこう。",
            "gap_rationale": "有名な山頂の物語から、湿地と川沿いの戦闘推移へ切り替える。",
        }, yama_facts,
        [theory("s01", "両軍の正確な兵数は史料により幅がある。", ["羽柴方3万数千", "明智方1万数千"], "兵数は推定値として幅を持たせる", "後半"), theory("s02", "旗立松や秀吉の山頂行動は伝承を含む。", ["後世の天王山物語", "現地伝承"], "伝承として扱う", "前半")],
        ["天王山はまったく無意味だったと断定しない", "山崎で山上の戦闘が一切なかったとしない", "池田恒興個人が一撃で勝敗を決めたとしない", "中国大返し・味方不参加・三日天下を主要敗因として繰り返さない", "光秀の最期を見せ場にしない", "既存台本の天王山3レスを文言ごと再利用しない"],
        [{"event": "山崎の戦い前日の布陣", "year": 1582}, {"event": "山崎の戦い", "year": 1582}, {"event": "小瀬甫庵『太閤記』刊行", "year": 1625}],
        ["天王山", "円明寺川", "小瀬甫庵", "勝龍寺城"],
        [("天王山", "てんのうざん", "地形と通説"), ("円明寺川", "えんみょうじがわ", "主戦場"), ("小瀬甫庵", "おぜほあん", "後世史料"), ("勝龍寺城", "しょうりゅうじじょう", "退却先")],
        {"taiga_linked": True, "recent_overlap_urls": ["/Users/kojinn/Projects/youtube/創作スレ下書き/2026-07-03_中国大返し/2026-07-03_中国大返し_台本.md", "/Users/kojinn/Projects/youtube/創作スレ下書き/2026-07-10_山崎の戦い__差し替え保留/brief.json"]}, ("--taiga", "--trend"), "通説から地形戦へ",
    )
    write("2026-07-24_山崎の戦い", yama)

    saigo = strip_brief(PROJECT / "2026-07-18_西郷隆盛__差し替え保留/brief.json")
    saigo["save_dir"] = "Projects/youtube/創作スレ下書き/2026-07-26_西郷隆盛/"
    saigo_items = [
        ("【2ch歴史】西郷隆盛、維新の功労者から賊軍になった理由www" + SUFFIX, "なぜ・理由"),
        ("【2ch歴史】明治政府の功労者・西郷隆盛、なぜ賊軍になったのかwww" + SUFFIX, "なぜ・理由"),
        ("【2ch歴史】維新三傑・西郷隆盛がわずか10年後に賊軍になった理由www" + SUFFIX, "時間ギャップ"),
        ("【2ch歴史】西郷隆盛はなぜ自分が作った明治政府と戦うことになったのかwww" + SUFFIX, "なぜ・理由"),
    ]
    saigo["title_candidates"] = titles(saigo_items)
    saigo["working_title"] = saigo["title_candidates"][0]["title"]
    saigo["scoring"] = scoring(saigo["title_candidates"][0])
    saigo["facts"]["confirmed"] = [x for x in saigo["facts"]["confirmed"] if x["id"] not in {"c09", "c10", "c12"}]
    saigo["facts"]["confirmed"].append(fact("c13", "西南戦争は1877年2月に始まり、私学校生徒による火薬庫襲撃が直接の引き金の一つとなった。", "https://www.pref.kagoshima.jp/ab23/pr/gaiyou/rekishi/bakumatu/seinan.html", "後半", 1877, "公的"))
    saigo["facts"]["confirmed"].append(fact("c14", "西郷隆盛は死後の1889年に大赦を受け、正三位を追贈された。", "https://kokkai.ndl.go.jp/simple/detail?minId=107204889X03219740521&spkNum=41", "後半", 1889, "一次"))
    saigo["facts"]["shosetsu"] = [x for x in saigo["facts"]["shosetsu"] if x["id"] in {"s01", "s06"}]
    saigo["facts"]["avoid_assertions"] += ["西郷が自ら西南戦争を始めたと断定しない", "賊軍を道徳的な悪人評価として扱わない", "明治政府に殺されたという単純図式にしない", "死傷場面をタイトルや見せ場にしない"]
    saigo["split"] = {
        "pattern_id": "②", "pattern_name": "逆視点型",
        "front": {"role": "タイトルネタ", "theme": "島津斉彬による登用、王政復古、戊辰戦争、江戸無血開城、維新三傑という功労者の側。", "hook_type": "英雄からの反転", "fact_ids": ["c01", "c02", "c03", "c04", "c11"], "rationale": "明治政府を作った側だった事実を明確にする。"},
        "back": {"role": "本筋", "theme": "明治六年政変、下野、私学校、火薬庫襲撃、西南戦争、官位剥奪と後の大赦まで、功労者が賊軍とされた因果を追う。", "fact_ids": ["c05", "c06", "c07", "c08", "c13", "c14", "s01", "s06"], "rationale": "最期のドラマではなく、政治対立と集団の暴発、後世の名誉回復までを本筋にする。"},
        "thread_core_question": {"front": "西郷隆盛は明治維新でどんな役割を担ったのか？", "back": "その功労者がなぜ新政府と戦い、賊軍と位置づけられたのか？"},
        "transition_B": "ここまでは維新の功労者としての西郷を見てきたが、『その本人がなぜわずか十年ほどで新政府と戦う側になったのか？』という疑問も出てきた。政変から私学校、西南戦争までを見ていこう。",
        "gap_rationale": "国家を作った側から、その国家に反する側へ置かれた政治過程へ反転する。",
    }
    saigo["gen_directives"] = directives(["西郷隆盛", "明治六年政変", "征韓論", "私学校", "西南戦争", "官位褫奪", "大赦", "正三位"], "英雄像から政治的因果へ")
    saigo["gloss"] = {"gloss_targets": glossary([("西郷隆盛", "さいごうたかもり", "人物背景"), ("明治六年政変", "めいじろくねんせいへん", "政治対立"), ("征韓論", "せいかんろん", "諸説整理"), ("私学校", "しがっこう", "組織背景"), ("西南戦争", "せいなんせんそう", "戦争背景"), ("官位褫奪", "かんいちだつ", "法制度"), ("大赦", "たいしゃ", "後世評価"), ("正三位", "しょうさんみ", "位階制度")], ["c01", "c05", "c05", "c06", "c13", "c08", "c14", "c14"], "幕末"), "narr_budget_pct": 25}
    write("2026-07-26_西郷隆盛", saigo)

    yoshimitsu = strip_brief(PROJECT / "2026-07-26_足利義満__差し替え保留/brief.json")
    yoshimitsu["save_dir"] = "Projects/youtube/創作スレ下書き/2026-07-29_足利義満/"
    yoshimitsu_items = [
        ("【2ch歴史】足利義満って結局何をした人なん？調べたら天皇以上の権力を目指した説まであった件www" + SUFFIX, "何をした人・前提疑問"),
        ("【2ch歴史】足利義満って何をした人？調べたら室町幕府を最盛期にした将軍だった件www" + SUFFIX, "人物再評価"),
        ("【2ch歴史】足利義満、金閣だけじゃなく南北朝まで終わらせてた件www" + SUFFIX, "実績フック"),
        ("【2ch歴史】足利義満、本当に天皇以上の権力を目指したのか問題www" + SUFFIX, "前提を疑う"),
    ]
    yoshimitsu["title_candidates"] = titles(yoshimitsu_items)
    yoshimitsu["working_title"] = yoshimitsu["title_candidates"][0]["title"]
    yoshimitsu["scoring"] = scoring(yoshimitsu["title_candidates"][0])
    yoshimitsu["facts"]["confirmed"] = [x for x in yoshimitsu["facts"]["confirmed"] if x["id"] not in {"c09", "c10"}]
    yoshimitsu["facts"]["shosetsu"] = [x for x in yoshimitsu["facts"]["shosetsu"] if x["id"] not in {"s03"}]
    yoshimitsu["facts"]["avoid_assertions"] += ["『天皇以上の権力を目指した』は必ず説・疑惑として扱う", "陰謀や不審死をクリック要素として足さない"]
    yoshimitsu["split"] = {
        "pattern_id": "③", "pattern_name": "前提を疑う型",
        "front": {"role": "タイトルネタ", "theme": "南北朝合一、有力守護の抑制、日明貿易、北山文化、太政大臣という確定した実績から『結局何をした人か』を整理する。", "hook_type": "何をした人・実績再評価", "fact_ids": ["c01", "c02", "c03", "c04", "c05", "c06", "c07", "c08", "c11", "c12"], "rationale": "まず確定実績で人物像を立て、金閣だけの人から幕府最盛期の統治者へ再評価する。"},
        "back": {"role": "本筋", "theme": "義満の権威上昇から後世に皇位簒奪説が出た根拠を検証し、直接史料の不足と近年の否定的研究を整理する。", "fact_ids": ["c01", "c03", "c05", "c06", "c08", "c11", "s01", "s02", "s04"], "rationale": "タイトルの強い説を確定史実にせず、出典と近年研究で前提を問い直す。"},
        "thread_core_question": {"front": "足利義満は金閣以外に何を成し遂げた将軍なのか？", "back": "天皇以上の権力を目指したという説は何を根拠にし、どこまで確かか？"},
        "transition_B": "ここまでは義満の確定した実績を見てきたが、『これほど公武の頂点に立ったから皇位簒奪説まで出たのか？その計画は本当に史料で確認できるのか？』という疑問も出てきた。引き続き議論を見ていこう。",
        "gap_rationale": "確定実績の人物紹介から、強いが未確定の簒奪説を史料検証する後半へ移る。",
    }
    yoshimitsu["gen_directives"] = directives(["足利義満", "南北朝合一", "明徳の乱", "応永の乱", "太政大臣", "日本国王", "勘合貿易", "北山殿", "義嗣", "皇位簒奪説"], "実績の光から説の検証へ")
    yoshimitsu["gloss"] = {"gloss_targets": glossary([("足利義満", "あしかがよしみつ", "人物背景"), ("南北朝合一", "なんぼくちょうごういつ", "政治制度"), ("明徳の乱", "めいとくのらん", "守護統制"), ("応永の乱", "おうえいのらん", "守護統制"), ("太政大臣", "だじょうだいじん", "官職制度"), ("日本国王", "にほんこくおう", "対外称号"), ("勘合貿易", "かんごうぼうえき", "対外交易"), ("北山殿", "きたやまどの", "文化史"), ("義嗣", "よしつぐ", "人物関係"), ("皇位簒奪説", "こういさんだつせつ", "研究史")], ["c01", "c03", "c02", "c04", "c05", "c06", "c06", "c07", "c08", "c08"], "室町"), "narr_budget_pct": 25}
    write("2026-07-29_足利義満", yoshimitsu)

    kiyosu_titles = [
        ("【2ch歴史】清須会議、秀吉vs勝家の後継者バトルではなかった件www" + SUFFIX, "前提反転"),
        ("【2ch歴史】清須会議「秀吉が三法師を抱いて勝家を黙らせた」←後世の創作だった説www" + SUFFIX, "通説反転"),
        ("【2ch歴史】信長の後継者を決めた清須会議、実は議題が違った件www" + SUFFIX, "前提を疑う"),
        ("【2ch歴史】秀吉、清須会議で柴田勝家を出し抜いて天下取りを始めた件www" + SUFFIX, "会議・対立"),
    ]
    kiyosu_facts = [
        fact("c01", "本能寺の変は6月2日、山崎の戦いは6月13日、清須での談合は6月27日で、山崎から14日後だった。", "https://bunkyo.repo.nii.ac.jp/record/2002562/files/BKK0004700.pdf", "前半", 1582, "学術"),
        fact("c02", "清須で談合した中心人物は羽柴秀吉・丹羽長秀・池田恒興・柴田勝家の4人だった。", "https://bunkyo.repo.nii.ac.jp/record/2002562/files/BKK0004700.pdf", "前半", 1582, "学術"),
        fact("c03", "近年の研究は、談合の直接の課題を織田家家督を継ぐ三法師の後見・御名代を定めることと整理している。", "https://ndlsearch.ndl.go.jp/books/R000000004-I034617220", "前半", 1582, "学術"),
        fact("c04", "秀吉書状では三法師が会議で突然候補になったのではなく、信忠の遺児として家督に立てる前提で記される。", "https://bunkyo.repo.nii.ac.jp/record/2002562/files/BKK0004700.pdf", "後半", 1582, "学術"),
        fact("c05", "問題になっていたのは、信雄と信孝のどちらが三法師の御名代になるかだった。", "https://bunkyo.repo.nii.ac.jp/record/2002562/files/BKK0004700.pdf", "後半", 1582, "学術"),
        fact("c06", "談合後に単独の御名代は確定せず、三法師はいったん信孝に預けられて清須から岐阜へ移されたと秀吉書状にある。", "https://bunkyo.repo.nii.ac.jp/record/2002562/files/BKK0004700.pdf", "後半", 1582, "学術"),
        fact("c07", "6月27日付の蒲生氏郷宛安堵状などには4人が連署し、4宿老による談合を裏づける。", "https://bunkyo.repo.nii.ac.jp/record/2002562/files/BKK0004700.pdf", "後半", 1582, "学術"),
        fact("c08", "遺領配分では秀吉旧領の長浜が柴田勝家側へ渡され、会議時点で秀吉だけが一方的に総取りしたわけではない。", "https://crd.ndl.go.jp/reference/entry/index.php?id=1000250921&page=ref_view", "後半", 1582, "公的"),
        fact("c09", "会議後、織田信雄が清須城主となって城を改修した。", "https://www.city.kiyosu.aichi.jp/shisetsu_annai/kanko_shisetsu_sonota/kiyosujo.html", "後半", 1582, "公的"),
        fact("c10", "秀吉と勝家の軍事的決着は翌1583年の賤ヶ岳合戦まで持ち越された。", "https://history-museum.city.fukui.lg.jp/tenji/tenran/katsuie.html", "後半", 1583, "博物館"),
        fact("c11", "清須市は歴史的な城と会議を清須と表記しており、今回の動画では大河の回名に合わせて清須会議と統一する。", "https://www.city.kiyosu.aichi.jp/shisetsu_annai/kanko_shisetsu_sonota/kiyosujo.html", "前半", 1582, "公的"),
    ]
    kiyosu = base_draft(
        "清須会議―三法師の後見体制と秀吉対勝家通説", "戦国", "2026-07-31_清須会議", kiyosu_titles,
        {
            "pattern_id": "③", "pattern_name": "前提を疑う型",
            "front": {"role": "タイトルネタ", "theme": "山崎勝利後の秀吉が清須で主導権を広げ、後の天下取りの起点となった流れ。", "hook_type": "会議・権力逆転", "fact_ids": ["c01", "c02", "c03", "c11", "s01"], "rationale": "大河の回名と一致させつつ、有名な秀吉対勝家の構図を入口にする。"},
            "back": {"role": "本筋", "theme": "同日文書の4宿老連署、三法師の御名代問題、遺領配分を追い、秀吉の一方的勝利という通説を問い直す。", "fact_ids": ["c04", "c05", "c06", "c07", "c08", "c09", "c10", "s01", "s02"], "rationale": "映画的な一騎打ちから集団統治と後見問題へ反転する。"},
            "thread_core_question": {"front": "6月27日の清須会議で実際に決められたことは何か？", "back": "秀吉が三法師を抱いて勝家を屈服させたという有名場面はどこまで史実なのか？"},
            "transition_B": "ここまでは秀吉対勝家という有名な清須会議像を見てきたが、『同日付の文書には勝家を含む4人の署名がある。勝家は本当にその場で完全敗北したのか？』という疑問も出てきた。引き続き議論を見ていこう。",
            "gap_rationale": "秀吉の一発逆転物語から、4宿老連署と御名代問題の史料検証へ移る。",
        }, kiyosu_facts,
        [theory("s01", "勝家が信孝、秀吉が三法師を推し、秀吉が三法師を抱いて一同を平伏させたという劇的な通説がある。", ["後世の軍記・絵画由来", "会議の象徴的物語"], "有名な通説として扱い、確定史実にはしない", "both"), theory("s02", "清須会議を天下取りの開始点と呼ぶのは、後世から結果を見た評価である。", ["政治的起点", "会議で天下は未確定"], "後世から見た起点という意味に限定する", "後半")],
        ["清須会議だけで秀吉が天下を取ったとしない", "勝家が会議で完全に権力を失ったとしない", "秀吉が三法師を突然後継候補として発案したとしない", "三法師を抱いて一同を平伏させた逸話を確定史実にしない", "出席者が不確かな人物を断定しない", "勝家・お市・信孝・三法師の末路を先取りしない", "清洲会議と清須会議を説明なく混在させない"],
        [{"event": "本能寺の変", "year": 1582}, {"event": "山崎の戦い", "year": 1582}, {"event": "清須での談合", "year": 1582}, {"event": "賤ヶ岳合戦", "year": 1583}],
        ["清須会議", "三法師", "柴田勝家", "丹羽長秀"],
        [("清須会議", "きよすかいぎ", "会議の史料"), ("三法師", "さんぼうし", "後継関係"), ("柴田勝家", "しばたかついえ", "宿老関係"), ("丹羽長秀", "にわながひで", "連署体制")],
        {"taiga_linked": True, "recent_overlap_urls": ["/Users/kojinn/Projects/youtube/創作スレ下書き/2026-07-11_清洲会議/brief.json"]}, ("--taiga",), "通説の権力劇から文書検証へ",
    )
    write("2026-07-31_清須会議", kiyosu)


if __name__ == "__main__":
    main()
