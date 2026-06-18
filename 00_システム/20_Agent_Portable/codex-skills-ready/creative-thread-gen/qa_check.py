#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
creative-thread-gen QA チェッカー
使い方: python3 qa_check.py <生成スレ.md> [--min 2500] [--max 3200]

生成した創作スレを文体パターン.mdの全基準で一括判定し、落ちた項目だけ
具体的なリカバリ指示を出す。これを毎回通すことで"毎回同じ品質"を仕組みで担保する。

対応フォーマット（自動判定）:
  1: 本文                       （プレーン）
  5: >>1 本文                   （安価付き）
  5 ID:Gy2ka0 >>1 本文          （ID＋安価・本物寄せ）
  2 ID:7gKw2a 本文
"""
import re, sys, argparse
from collections import Counter

POST_RE = re.compile(r'^(\d+)\s*:?\s*(?:ID:(\S+))?\s*(?:>>(\d+))?\s*(.*)$')

# 禁止語（全活用形・複合語含む）。死は「守」直後のみ除外。
BANNED_RE = re.compile(r'死(?!守)|殺|バカ|馬鹿|クソ|糞|[〇○●]')
# 蔑称・差別語（ヘイト機械ブロック）。保護対象属性への蔑称＝YouTube規約一発アウト。
# コーパス(学習素材)に混じってても生成には絶対出さない。検出したら必ずFAIL。
SLUR_RE = re.compile(
    r'チョン|チャンコロ|シナ人|支那|ジャップ|ジ.プ|露助|毛唐|鬼畜米英|鬼畜米|三国人|土人|'
    r'穢多|えた非人|非人(?!間)|きちがい|気違い|キチガイ|池沼|ガイジ|めくら|盲(?=ども|者ども)|'
    r'つんぼ|おしども|びっこ|片輪|かたわ|不具者|白痴|低能|劣等民族|未開人|ニガー')
# メタ自己言及締め（AIテンプレ＝全コーパスで出現0）
META_RE = re.compile(r'様式美|毎回.{0,5}モメ|結論出んのもいつも|アンチも結局.{0,4}詳し|いつもこうなる|語れる.{0,4}人気者の証拠')
URO_RE = re.compile(r'知らんけど|って聞いた|とかなんとか|どうなんやろ|やったはず|な気がする|やっけ|うろ覚え|とか聞いた')
HAKISUTE_RE = re.compile(r'^で？|信者|はい解散|見苦し|引くわ|^乙|盛りすぎて')
TEISEI_RE = re.compile(r'俗説|盛りすぎ|そうやったか|勘違い|あ、そうなん|違うわ|それ.{0,8}やで|間違|ちゃうで|嘘やろ|てへんわ|やなくて|混同|サンガツ')
FRICTION_RE = re.compile(r'^いや|やろ$|過大評価|過小評価|盛り|是々非々|限らん|矛盾|水掛け|^でも|^は？|^で？|認めへん|信者|アンチ')
# 属性ベース侮辱の疑い（蔑称"語"でない文脈差別）。WARN止まり→文脈確認/LLMゲートへ回す。
# 属性語。順方向(属性+侮蔑構文)は全属性、逆方向(蔑視語+属性)は"集団"語だけ(男/女/身分等は「○○な男」と人物描写で誤爆するため除外)。
ATTR_ALL = r'(朝鮮人|韓国人|中国人|在日|部落|百姓|農民|女|男|老人|障[がが]い|身分|出自|百済|新羅|高麗|渤海|アイヌ|蝦夷|異民族|外国人|民族)'
ATTR_GROUP = r'(朝鮮人|韓国人|中国人|在日|部落|百済|新羅|高麗|渤海|アイヌ|蝦夷|異民族|外国人|民族)'
_CONSTRUCT = r'(だから無能|だから駄目|だからアカン|のくせに|ごとき|風情|には無理|なんかに|とか笑|の分際)'  # 順方向の侮蔑構文
_DEROG = r'(野蛮|未開|格下|劣等|下等|低俗|信用ならん|劣っ)'  # 逆方向の蔑視語
# ①属性+侮蔑構文(順方向・全属性) ②集団語と蔑視語が近接(両方向・集団語のみ)。正当な史実もヒットしうる→必ずLLM文脈確認へ。
SLUR_CONTEXT_RE = re.compile(
    ATTR_ALL + r'.{0,8}' + _CONSTRUCT + r'|'
    + ATTR_GROUP + r'.{0,10}' + _DEROG + r'|'
    + _DEROG + r'.{0,10}' + ATTR_GROUP)

# 婉曲差別・非人間化（文脈差別の機械化・2026-06-17 残課題2）。蔑称"語"でない＝血統本質主義/非人間化/現代ゼノフォビア構文を拾う。
# 歴史chは身分・民族語が正当に頻出するため誤爆を抑える設計：1)非人間化が"集団語"に近接＝ほぼ確実にヘイト→FAIL／2)本質主義・帰れ・民度・優生＝WARN(必ずLLM確認へ)。
_DEHUMAN = r'(湧いて|湧く|沸いて|わいて|害虫|寄生虫|ゴキブリ|蛆|駆除|間引|根絶やし|処分しろ|処分すべき|消えろ|滅べ|絶滅さ)'
DEHUMANIZE_RE = re.compile(
    ATTR_GROUP + r'.{0,12}' + _DEHUMAN + r'|'
    + _DEHUMAN + r'.{0,12}' + ATTR_GROUP)
_ESSENCE = r'(の血(?:筋|統|が|を|は)|民族性|国民性|DNA|遺伝子レベル|生まれつき.{0,4}(?:劣|駄目|無能|犯罪)|血が穢|血が汚|血は争えん)'
_XENO    = r'(国へ?帰れ|祖国へ?帰れ|半島へ?帰れ|大陸へ?帰れ|出て行け|出ていけ)'
_EUGENIC = r'(優生|劣等遺伝|劣った血|生産性が(?:ない|低)|社会のお荷物|穀潰し|間引いた方)'
_MINDO   = r'民度(?:が)?(?:低|ない|の低)'
EUPHEMISM_RE = re.compile(
    ATTR_GROUP + r'.{0,10}' + _ESSENCE + r'|' + _ESSENCE + r'.{0,8}' + ATTR_GROUP + r'|'
    + ATTR_GROUP + r'.{0,12}' + _XENO + r'|'
    + ATTR_ALL + r'.{0,10}' + _EUGENIC + r'|' + _EUGENIC + r'|'
    + _MINDO)

# スレタイ品質（1レス目）。本物スレタイ188本実測＝とかいう4%/結論書ききりは0。AI臭の典型を機械検出。
TITLE_TOKAIU_RE = re.compile(r'とかいう')
# 結論書ききり・ブログ/AI臭（「実は〜だった」「〜という真実」「〜が判明」等）。※「→嘘でした」は本物の型なので除外。
TITLE_CONCL_RE = re.compile(r'という真実|が判明|ことが判明|実は.{0,12}(?:だった|でした|なんだ|なのだ|な件)|衝撃の事実|驚きの真実|ヤバすぎた真実')

# 時代タグ照合（人物の実在年代とトーン指示の時代タグを機械照合。立花宗茂[戦国]に"時代=飛鳥"が付く等の分類事故を防ぐ）
ERA_ORDER = ['縄文', '弥生', '古墳', '飛鳥', '奈良', '平安', '鎌倉', '室町', '戦国', '江戸', '幕末']
ERA_TABLE = {
    '縄文': ['縄文人'],
    '弥生': ['卑弥呼', '邪馬台'],
    '飛鳥': ['聖徳太子', '厩戸', '蘇我入鹿', '蘇我馬子', '蘇我蝦夷', '中大兄', '中臣鎌足', '天智天皇', '天武天皇', '推古'],
    '奈良': ['鑑真', '聖武天皇', '行基', '道鏡', '阿倍仲麻呂', '長屋王'],
    '平安': ['平清盛', '源義経', '源頼朝', '紫式部', '清少納言', '藤原道長', '菅原道真', '平将門', '安倍晴明', '源義仲', '源義家'],
    '鎌倉': ['北条政子', '北条時宗', '北条義時', '後醍醐', '楠木正成', '新田義貞'],
    '室町': ['足利尊氏', '足利義満', '足利義政', '日野富子'],
    '戦国': ['北条早雲', '斎藤道三', '今川義元', '武田信玄', '上杉謙信', '織田信長', '明智光秀', '豊臣秀吉', '徳川家康', '石田三成', '真田幸村', '真田信繁', '伊達政宗', '立花宗茂', '大谷吉継', '北条氏康', '毛利元就', '前田利家', '加藤清正', '福島正則', '島津義弘', '直江兼続', '黒田官兵衛', '長宗我部'],
    '江戸': ['徳川家光', '徳川綱吉', '徳川吉宗', '田沼意次', '松平定信', '大塩平八郎', '水戸黄門', '吉良', '赤穂'],
    '幕末': ['坂本龍馬', '西郷隆盛', '徳川慶喜', '勝海舟', '新選組', '新撰組', '土方歳三', '榎本武揚', '大久保利通', '吉田松陰'],
}


def infer_era(text):
    """テキスト(主にスレタイ)から登場人物を拾って実在年代を推定。返り値=(era, 人物) or (None, None)"""
    for era, names in ERA_TABLE.items():
        for nm in names:
            if nm in text:
                return era, nm
    return None, None


def era_index(era):
    """時代名→ERA_ORDER上のインデックス（未知ならNone）"""
    if not era:
        return None
    for i, x in enumerate(ERA_ORDER):
        if x in era or era in x:
            return i
    return None


def scan_people(text):
    """本文に出現する既知人物を {人物名: (時代, 出現回数)} で返す（時代混線の自動検出用）"""
    found = {}
    for era, names in ERA_TABLE.items():
        for nm in names:
            c = text.count(nm)
            if c > 0:
                found[nm] = (era, c)
    return found


def parse(path):
    posts = []
    for ln in open(path, encoding='utf-8'):
        m = POST_RE.match(ln.rstrip('\n'))
        if not m:
            continue
        num, pid, anc, body = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        posts.append({'n': int(num), 'id': pid, 'anc': int(anc) if anc else None, 'body': body})
    return posts


def mark(ok):
    return '✅' if ok == 'ok' else ('⚠️ ' if ok == 'warn' else '❌')


def check(path, mn=2500, mx=3200, era=None):
    posts = parse(path)
    if not posts:
        print('❌ パース失敗：レス行が見つからない')
        return 1
    bodies = [p['body'] for p in posts]
    text = ''.join(bodies)
    n = len(posts)
    nums = [p['n'] for p in posts]
    maxn = max(nums)
    has_id = any(p['id'] for p in posts)
    fails, warns, hints = [], [], []

    print(f'=== QA: {path.split("/")[-1]} ===')
    print(f'表示レス {n} / 最大番号 {maxn} / ID形式 {"あり" if has_id else "なし"}\n')

    # 1. 字数
    chars = sum(len(b) for b in bodies)
    if chars < mn:
        st = 'fail'; fails.append('字数')
        cur_long = sum(1 for b in bodies if len(b) >= 60)
        need_long = -(-(mn - chars) // 130)  # ceil: 不足字数÷130＝追加すべき長文本数
        hints.append(f'尺不足（あと{mn-chars}字／現在の長文60字+={cur_long}本）→ 知識ニキ長文(130〜150字)を約{need_long}本トピック別に追加（短レス追加では埋まらない＝1430→2500は短レスでは無理）。次回は「尺設計図→長文ファースト」で長文10本を先に書き切ってから短・中レスを挟むと初稿一発で乗る')
    elif chars > mx:
        st = 'warn'; warns.append('字数'); hints.append(f'長すぎ（{chars}字）→ 冗長な解説を削るか分割')
    else:
        st = 'ok'
    print(f'{mark(st)} 本文字数: {chars}（目標 {mn}〜{mx}）')

    # 2. 禁止語・伏字
    banned = BANNED_RE.findall(text)
    if banned:
        fails.append('禁止語')
        locs = [f"#{p['n']}「{p['body'][:18]}」" for p in posts if BANNED_RE.search(p['body'])]
        hints.append('禁止語/伏字あり → 言い換え（死→亡くなる/逝く・殺す→やる・バカ→アホ・糞→削除）。複合語注意（必死→懸命/必殺技→お家芸/脱糞→漏らす）：' + ' '.join(locs[:6]))
    print(f'{mark("fail" if banned else "ok")} 禁止語・伏字: {Counter(banned) if banned else "なし"}')

    # 2b. 蔑称・差別語（ヘイト＝YouTube規約一発アウト）
    slurs = SLUR_RE.findall(text)
    if slurs:
        fails.append('蔑称・ヘイト')
        slocs = [f"#{p['n']}「{p['body'][:18]}」" for p in posts if SLUR_RE.search(p['body'])]
        hints.append('⚠️蔑称・差別語あり＝YouTube規約一発アウト → 即削除/言い換え。煽りは属性でなく"人物の能力・評価"へ向ける。対外戦争/民族/出自/病気を蔑む方向にしない：' + ' '.join(slocs[:6]))
    print(f'{mark("fail" if slurs else "ok")} 蔑称・差別語(ヘイト): {Counter(slurs) if slurs else "なし"}')

    # 2c. 属性ベース侮辱の疑い（文脈差別・WARN→LLMゲートで要確認）
    attr_hits = [f"#{p['n']}「{p['body'][:22]}」" for p in posts if SLUR_CONTEXT_RE.search(p['body'])]
    if attr_hits:
        warns.append('属性侮辱疑い')
        hints.append('属性(民族/性別/身分等)ベースの侮辱の疑い→必ず文脈確認＆youtube-script-checker(LLM)へ。煽りは"人物の能力・評価"に向け直す：' + ' '.join(attr_hits[:5]))
    print(f'{mark("warn" if attr_hits else "ok")} 属性侮辱の疑い: {len(attr_hits)}件（要LLM文脈確認）')

    # 2d. 非人間化（集団語に近接＝ほぼ確実にヘイト→FAIL）
    dehum = [f"#{p['n']}「{p['body'][:24]}」" for p in posts if DEHUMANIZE_RE.search(p['body'])]
    if dehum:
        fails.append('非人間化ヘイト')
        hints.append('⚠️集団(民族/外国人等)の非人間化表現(湧く/害虫/駆除/根絶やし等)＝YouTube規約一発アウト → 即削除。煽りは"人物個人の能力・評価"へ向ける：' + ' '.join(dehum[:5]))
    print(f'{mark("fail" if dehum else "ok")} 非人間化ヘイト: {len(dehum)}件')

    # 2e. 婉曲差別の疑い（血統本質主義/帰れ系/民度/優生＝文脈差別・WARN→LLM）
    euph = [f"#{p['n']}「{p['body'][:26]}」" for p in posts if EUPHEMISM_RE.search(p['body'])]
    if euph:
        warns.append('婉曲差別疑い')
        hints.append('婉曲な差別の疑い(◯◯人の血/民族性/国民性・帰れ系・民度・優生)→必ず文脈確認＆youtube-script-checker(LLM)へ。属性でなく"人物の行動・実績"を論じる形に直す：' + ' '.join(euph[:5]))
    print(f'{mark("warn" if euph else "ok")} 婉曲差別の疑い: {len(euph)}件（要LLM文脈確認）')

    # 3. メタ自己言及締め
    meta_hits = [f"#{p['n']}「{p['body'][:20]}」" for p in posts if META_RE.search(p['body'])]
    if meta_hits:
        fails.append('メタ締め')
        hints.append('AIテンプレのメタ締めあり（全コーパスで出現0）→ 削除。脱線・生活雑事（飯/寝る/観光）でフッと終える：' + ' '.join(meta_hits))
    print(f'{mark("fail" if meta_hits else "ok")} メタ締めテンプレ: {len(meta_hits)}件')

    # 4. 安価率
    anc_posts = [p for p in posts if p['anc'] is not None]
    rate = len(anc_posts) * 100 // n
    bad_anc = [p['n'] for p in anc_posts if p['anc'] >= p['n']]  # 未来/自己参照
    if bad_anc:
        fails.append('安価整合'); hints.append(f'未来/自己参照アンカー → 後方のレスを指すよう修正: #{bad_anc[:8]}')
    if rate > 40:
        st = 'fail'; fails.append('安価過多'); hints.append(f'安価{rate}%は盛りすぎ（本物24%）→ 直前への当たり前の返信から>>を外す。残すのは「離れたレス/特定質問への回答/名指し反論」だけ')
    elif rate < 12:
        st = 'warn'; warns.append('安価少'); hints.append(f'安価{rate}%は薄い → 離れたレスへの返信・反論に>>を付ける（目標2〜3割）')
    else:
        st = 'ok'
    print(f'{mark(st)} 安価率: {rate}%（目標 18〜32%）/ 整合: {"NG"+str(bad_anc[:5]) if bad_anc else "OK"}')

    # 5. 欠番率＋不規則性（テキスト台本用。TTSは連番に戻す前提）
    miss_rate = (maxn - n) * 100 // maxn if maxn else 0
    gaps = [nums[i + 1] - nums[i] for i in range(len(nums) - 1)]  # 連続レス間の番号差(1=詰まり,2+=飛び)
    same = Counter(gaps).most_common(1)[0][1] if gaps else 0
    uniform = gaps and same / len(gaps) > 0.75  # 同じ差が75%超＝等間隔すぎ
    if miss_rate == 0:
        st = 'warn'; warns.append('欠番ゼロ'); hints.append('レス番号が完全連番＝最大のAI臭 → まとめ抜粋風に20〜30%欠番にする（音声化フローでは連番のまま）')
    elif miss_rate < 12 or miss_rate > 38:
        st = 'warn'
    elif uniform:
        st = 'warn'; warns.append('欠番が等間隔'); hints.append('欠番が等間隔(機械的)＝AI臭 → 連番が詰まる箇所(盛り上がり)と過疎(飛び)を混在させて不規則に')
    else:
        st = 'ok'
    print(f'{mark(st)} 欠番率: {miss_rate}%（目標20〜30%）/ 不規則性: {"等間隔⚠" if uniform else "OK"}（テキスト台本のみ）')

    # 6. 冷たい立ち上がり（最初の80字超レスの位置）
    first_long = next((i for i, b in enumerate(bodies) if len(b) >= 80), None)
    if first_long is None:
        st = 'warn'; warns.append('長文なし')
    elif first_long < 5:
        st = 'warn'; warns.append('立ち上がり'); hints.append(f'{first_long+1}レス目で即長文＝立ち上がりが熱い → 冒頭5〜9レスは短文に、知識ニキ長文は8〜10レス目以降へ')
    else:
        st = 'ok'
    print(f'{mark(st)} 冷たい立ち上がり: 最初の長文は{(first_long+1) if first_long is not None else "—"}レス目（目標 8以降）')

    # 7. 緩急（長文/短レス）
    longn = sum(1 for b in bodies if len(b) >= 60)
    shortn = sum(1 for b in bodies if len(b) <= 12)
    if longn < 6:
        warns.append('長文不足'); hints.append(f'知識ニキ長文が{longn}本 → 6〜10本に（尺と厚みの両取り）')
    print(f'{mark("ok" if longn>=6 else "warn")} 緩急: 長文(60字+){longn} / 短レス(12字-){shortn}')

    # 8. 摩擦の三分割
    t = n // 3 or 1
    seg = [sum(1 for p in posts[i*t:(i+1)*t if i < 2 else n] if FRICTION_RE.search(p['body'])) for i in range(3)]
    if min(seg) == 0:
        st = 'warn'; warns.append('摩擦偏り'); hints.append(f'摩擦が序{seg[0]}中{seg[1]}終{seg[2]} → 0の区間に賛否のぶつかりを足す（冒頭に固めない）')
    else:
        st = 'ok'
    print(f'{mark(st)} 摩擦の三分割: 序{seg[0]} 中{seg[1]} 終{seg[2]}（各1以上）')

    # 9. 本物寄せ要素（うろ覚え/吐き捨て/誤答訂正/全角ｗ）
    uro = sum(1 for b in bodies if URO_RE.search(b))
    haki = sum(1 for b in bodies if HAKISUTE_RE.search(b))
    teisei = sum(1 for b in bodies if TEISEI_RE.search(b))
    zenw = text.count('ｗ'); hanw = len(re.findall(r'(?<![A-Za-z])w+(?![A-Za-z])', text))  # 半角wも本物では優勢
    zw = zenw + hanw
    def soft(name, val, need):
        if val < need:
            warns.append(name);
        return 'ok' if val >= need else 'warn'
    print(f'{mark(soft("うろ覚え", uro, 2))} うろ覚え又聞き: {uro}本（目標2+）')
    print(f'{mark(soft("吐き捨て", haki, 2))} 吐き捨て口調: {haki}本（目標2+）')
    print(f'{mark(soft("誤答訂正", teisei, 1))} 誤答→訂正の気配: {teisei}本（目標1+）')
    print(f'{mark(soft("笑いw", zw, 3))} 笑いw: 全角ｗ{zenw}+半角w{hanw}={zw}個（目標3+・半角wは本物で優勢でOK）')

    # 9b. 接続「で、」のレス頭多用（2026-06-18 オーナー指摘＝同じ繋ぎの連発でAI臭。本物は接続詞を散らす）
    #   レス頭の「で、（＝それで）」だけ数える。コピュラ「〜で、(である)」やテ形「飛んで、」は文中で自然なので対象外。
    de_open = sum(1 for b in bodies if re.match(r'^(?:>>\d+\s*|↑\s*)?で、', b))
    if de_open >= 2:
        warns.append('で、多用')
        hints.append(f'レス頭の接続「で、」が{de_open}本＝同じ繋ぎの連発でAI臭（句読点改行すると単独行で余計目立つ）→ 0〜1本に削減。てか/ところで/そんで/ほんで/そして/つまり/削除 に散らす。コピュラ「〜で、」やテ形「飛んで、」はOK')
    print(f'{mark("warn" if de_open >= 2 else "ok")} 接続「で、」のレス頭: {de_open}本（0〜1が目標）')

    # 9c. 語尾の偏り（2026-06-18 オーナー指摘＝同じ語尾の多用がAI臭。本物コーパスは9割が体言止め/言い切り、なんJ語尾は各1%未満）
    #   各レスの末尾をなんJ語尾カテゴリに分類。flat(体言止め/言い切り/標準語)はNone。
    def _gtail(b):
        b = re.sub(r'^(?:>>\d+\s*|↑\s*)', '', b.strip())
        return re.sub(r'[。、！？\.\?!ｗwＷ〜～…\s（）()「」]+$', '', b)
    GOBI = [('わけや/わ', r'(わけや|わ)$'), ('やろ', r'やろ$'), ('やん', r'やん$'),
            ('やねん/ねん', r'(やねん|ねん)$'), ('とる系', r'(とる|とった|とん|どる)$'),
            ('んよ/んや', r'(んよ|んや|のよ)$'), ('やで', r'やで$'), ('な/なあ', r'(なあ|な)$'),
            ('や/だ', r'(や|だ)$'), ('ンゴ', r'ンゴ$')]
    def _gcat(t):
        for nm, pat in GOBI:
            if re.search(pat, t):
                return nm
        return None
    gt = [_gcat(_gtail(b)) for b in bodies if _gtail(b)]
    ng = len(gt) or 1
    nanj = [g for g in gt if g]
    nanj_share = len(nanj) * 100 // ng
    gc = Counter(nanj)
    # 説明おじさん語尾クラスタ（わけや/やねん/とる/んよ）＝本物コーパス全体で計≈5%なのに生成は3〜4倍に膨らむ最大の癖
    EXPL = ('わけや/わ', 'やねん/ねん', 'とる系', 'んよ/んや')
    expl_share = sum(v for k, v in gc.items() if k in EXPL) * 100 // ng
    top_name, top_cnt = gc.most_common(1)[0] if gc else ('—', 0)
    top_share = top_cnt * 100 // ng
    # 基準=コーパス6119レス実測（なんJ語尾≈32%/説明クラスタ≈5%/な・なあが主力13%）。WARNは明確オーバー側で。
    flat = nanj_share < 20
    gobi_warn = nanj_share > 50 or expl_share > 12 or flat
    if gobi_warn:
        warns.append('語尾の偏り')
        if flat:
            hints.append(f'なんJ語尾{nanj_share}%＝削りすぎでフラット化(本物≈32%)→ や/やで/やろ/な/わ を足してなんJ味を戻す（目標帯20〜32%。標準語締めすぎは解説臭）')
        else:
            hints.append(f'語尾＝なんJ調{nanj_share}%(本物≈32%)・説明クラスタ(わけや/やねん/とる/んよ){expl_share}%(本物≈5%)・最多「{top_name}」{top_share}%＝同じ語尾の多用でAI臭 → なんJ語尾は35%前後・説明クラスタ12%未満に。特に〜わけや/〜やねん/〜やん/〜んよ の連発をほどき体言止め・言い切りに散らす（同一語尾3連続禁止。「な/なあ」は本物主力なので減らさなくてよい）')
    print(f'{mark("warn" if gobi_warn else "ok")} 語尾の偏り: なんJ語尾{nanj_share}%(基準≈32%・20〜32帯){" ←フラット化" if flat else ""} / 説明クラスタ{expl_share}%(基準≈5%・12%未満) / 最多「{top_name}」{top_share}%')

    # === 9d〜9h: 多次元AI癖ゲート群（2026-06-18 ultracode多次元監査で確定。本物コーパス6119レス実測基準）===
    body_join = '\n'.join(bodies)
    nb = len(bodies) or 1
    def _head(b):
        return re.sub(r'^(?:>>\d+\s*|↑\s*)', '', b.strip())

    # 9d. 本物0件の作為クセ（即FAIL）＋ ナレ接着レス頭クラスタ（接続詞/定型句/構造の共通指摘）
    banned0 = [w for w in ('それがな', 'それがそう', 'これ豆な', 'ここ大事') if w in body_join]
    if banned0:
        fails.append('本物0件クセ')
        hints.append('本物コーパス0件の作為クセ ' + '/'.join(banned0) + ' → 全削除/別表現へ（ナレ講釈臭の主因・ゼロ強制）')
    print(f'{mark("fail" if banned0 else "ok")} 本物0件クセ(それがな/これ豆な/ここ大事等): {len(banned0)}種')
    NARRA = ('それがな', 'それが', 'そう、', 'そうなる', 'そっから', 'そんで', 'もはや', 'つまり', '結局')
    narra_pct = sum(1 for b in bodies if _head(b).startswith(NARRA)) * 100 // nb
    so_pct = sum(1 for b in bodies if _head(b).startswith('そ')) * 100 // nb
    nd_warn = narra_pct > 3 or so_pct > 9
    if nd_warn:
        warns.append('ナレ接着頭')
        hints.append(f'物語つなぎのレス頭(それがな/結局/そんで/もはや等){narra_pct}%・そ始まり{so_pct}%＝ナレ講釈臭（本物≈0.3%/4.5%）→ 主語始まり(将門は〜)や>>N受けに。同じ頭語を3レス以内に再使用しない')
    print(f'{mark("warn" if nd_warn else "ok")} ナレ接着レス頭: {narra_pct}%(基準≈0.3/閾3) / そ始まり{so_pct}%(基準4.5)')
    # 9d2. レス頭フィラー同語3連発（文中と区別＝レス頭のみ。本物は同語頭の連発が稀）
    HEADW = ('それがな','それが','結局','つまり','まあ','正直','そもそも','ちな','てか','そんで','もはや','で、','要は','ようは')
    head_hits = Counter()
    for b in bodies:
        h = _head(b)
        for w in HEADW:
            if h.startswith(w):
                head_hits[w] += 1
                break
    head_rep = [(w, c) for w, c in head_hits.items() if c >= 3]
    if head_rep:
        warns.append('レス頭同語連発')
        hints.append('同じフィラーがレス頭で3回以上: ' + '/'.join(f'{w}×{c}' for w, c in head_rep) + ' → レス頭は同語2回までに散らす(文中はOK・文頭/文中を区別)')
    print(f'{mark("warn" if head_rep else "ok")} レス頭同語連発: {("/".join(f"{w}×{c}" for w,c in head_rep)) if head_rep else "なし(各2回以内)"}')

    # 9e. 談話標識の本物比上限
    disc = []
    if body_join.count('結局') * 100 // nb > 4:
        disc.append('結局' + str(body_join.count('結局') * 100 // nb) + '%(本物0.7)')
    if (body_join.count('要は') + body_join.count('ようは')) * 100 // nb > 2:
        disc.append('要は系過多')
    if (body_join.count('ってこと') + body_join.count('っちゅう')) * 100 // nb > 4:
        disc.append('ってこと系過多')
    if disc:
        warns.append('談話標識過多')
        hints.append('談話標識 ' + '/'.join(disc) + '（本物比過剰）→ つまり/しょせん/そのまま/体言始まりに散らす。置換先で別のレア語過剰を作らない')
    print(f'{mark("warn" if disc else "ok")} 談話標識: {"/".join(disc) if disc else "OK"}')

    # 9f. 説明おじさんクラスタ密度（最終語尾だけでなく句末・節末／長文の途中節も数える）
    clause = re.findall(r'(わけや|やねん|んよ|んどる|っとる|とった|とる)(?=[。、！？\sｗwやでなねの]|$)', body_join)
    dens = len(clause) * 100 // nb
    if dens > 12:
        warns.append('説明クラスタ密度')
        hints.append(f'説明おじさん語尾(わけや/やねん/んよ/とる)が節末含め{dens}語/100res＝本物≈1.8の過剰 → 長文の途中節末も〜てる/〜んや/体言止めに散らす（1レス1回まで）')
    print(f'{mark("warn" if dens > 12 else "ok")} 説明クラスタ密度(節末含む): {dens}語/100res（基準≈1.8・12未満目標）')

    # 9g. 長文の解説お膳立て頭率 ＆ アンカー応答率（独り語り検出）※parse()がanc(>>N)を分離済みなのでpostsで判定
    long_posts = [p for p in posts if len(p['body']) >= 80]
    nl2 = len(long_posts) or 1
    EXPL_HEAD = ('それがな', 'それが', 'ちな', 'ちなみ', 'そもそも', 'しかも', 'ここ大事', 'もういっこ', 'ついでに', 'あと同じ', 'これ豆な')
    exhead = sum(1 for p in long_posts if p['body'].startswith(EXPL_HEAD)) * 100 // nl2
    lanc = sum(1 for p in long_posts if p['anc'] is not None) * 100 // nl2
    lg_warn = exhead > 8 or lanc < 25
    if lg_warn:
        warns.append('長文の独り語り')
        hints.append(f'長文の解説お膳立て頭{exhead}%(本物≈3%)/アンカー始まり{lanc}%(本物≈52%)＝独り語りで降る兆候 → 長文の1/4以上は直前の懐疑・質問へ>>N受けで開く（偽アンカー禁止）')
    print(f'{mark("warn" if lg_warn else "ok")} 長文({nl2}本)独り語り: お膳立て頭{exhead}%(基準≈3) / アンカー始まり{lanc}%(基準≈52・25以上目標)')

    # 9h. 記号ゲート（ASCII"は即FAIL・笑い記号率・カタカナ強調・オノマトペ・↑）
    ascii_dq = body_join.count('"') + body_join.count('“') + body_join.count('”') + body_join.count('＂')
    if ascii_dq:
        fails.append('ASCII"使用')
        hints.append(f'ASCIIダブルクオートが本文に{ascii_dq}箇所＝本物0件のNG → 引用・強調は「」のみ（入れ子も「」）')
    warai_rate = sum(1 for b in bodies if re.search(r'[ｗ草]|(?<![A-Za-z])w+(?![A-Za-z])', b)) * 100 // nb
    sym = []
    if warai_rate > 6:
        sym.append(f'笑い記号レス{warai_rate}%(本物2.3/目標3-4)')
    if len(re.findall(r'ド[真派]', body_join)) > 2:
        sym.append('ド+語強調過多')
    if len(re.findall(r'ポツン|ポンポン|ブチギレ|ゾッと|ブッキラ', body_join)) > 1:
        sym.append('オノマトペ過多')
    if '↑' in body_join:
        sym.append('↑参照(>>Nへ)')
    if len(re.findall(r'[!！][?？]', body_join)) > 1:
        sym.append('!?連結過多(本物0.14%)')
    if len(re.findall(r'エグ', body_join)) > 1:
        sym.append('現代スラング(エグ)連発')
    if sym:
        warns.append('記号の癖')
        hints.append('記号 ' + '/'.join(sym) + ' → 本物水準に。前レス参照は↑でなく>>N')
    print(f'{mark("fail" if ascii_dq else ("warn" if sym else "ok"))} 記号ゲート: ASCII\"={ascii_dq}(即FAIL) / {"/".join(sym) if sym else "他OK"}')

    # 10. ID（本物寄せ）＋知識役の一極集中（最大のAI臭・2026-06-16監査でHigh）
    if has_id:
        idc = Counter(p['id'] for p in posts if p['id'])
        recur = [i for i, c in idc.items() if c >= 3]
        if not recur:
            warns.append('ID再登場')
        print(f'{mark("ok" if recur else "warn")} ID: {len(idc)}種 / 3回以上再登場 {len(recur)}人（役の一貫性）')
        # 長文(60字+)が特定IDに集中＝講義臭。最多IDが長文の45%超ならWARN
        long_by_id = Counter(p['id'] for p in posts if p['id'] and len(p['body']) >= 60)
        if sum(long_by_id.values()) >= 4:
            top_id, top_cnt = long_by_id.most_common(1)[0]
            share = top_cnt / sum(long_by_id.values())
            if share > 0.45:
                warns.append('知識役の集中')
                hints.append(f'解説長文が ID:{top_id} に{int(share*100)}%集中＝講義臭（最大のAI臭）→ 解説を3人以上に分散。1スレ1回「住人が間違える→知識ニキ以外が訂正→本人が引き下がる」を作る')
            print(f'{mark("warn" if share>0.45 else "ok")} 知識役の分散: 最多ID {top_id} が長文の{int(share*100)}%（45%以下が目標）')

    # 11. スレタイ（1レス目）＝本物61本のauditで誤検知を抑えた判定。
    #   ・「」内/【】内の読点は構造的二節ではないので地の文(bare)で判定
    #   ・二段重ねは「主張、…？」(、が？より前)のみ。断定？＋列挙(、)は除外
    #   ・説明過多は ？無し・【】始まりでない・26字超 に限定／長いは45字超
    #   ・とかいうは型ラベルで示すだけ（単発は本物で許容・連発抑制はプロトコル側）
    title = bodies[0]
    bare = re.sub(r'【[^】]*】', '', re.sub(r'「[^」]*」', '', title))  # 「」内・【】内を除いた地の文
    cpos = bare.find('、')
    qpos = next((i for i, c in enumerate(bare) if c in '？?'), -1)
    t_fail = []
    if '"' in title or '"' in title or '＂' in title:
        t_fail.append('ASCII"使用')
    if cpos >= 0 and qpos >= 0 and cpos < qpos:
        t_fail.append('二段重ね疑い(主張、…？)')
    elif cpos >= 0 and qpos < 0 and len(title) > 26 and not title.startswith('【'):
        t_fail.append('説明過多疑い(、で二節)')
    if TITLE_CONCL_RE.search(title):
        t_fail.append('結論書ききり/ブログ臭')
    if len(title) > 45:
        t_fail.append(f'長い({len(title)}字)')
    # ←列挙の語の使い回し（2026-06-17ブラインドで判明＝同じ評を2回使うとAI臭。本物は各項バラける）
    arrow_vals = re.findall(r'←([^←　\s]+)', title)
    if len(arrow_vals) >= 2:
        dup = [w for w, c in Counter(arrow_vals).items() if c >= 2 and len(w) >= 2]
        if dup:
            t_fail.append('←列挙の使い回し(' + '/'.join(dup) + ')')
    # 型の自動判定（毎回違う型を引けてるか・偏り把握用）
    if '「' in title and '」' in title:
        ttype = 'セリフ寸劇'
    elif '←' in title:
        ttype = '←ツッコミ'
    elif re.search(r'【.+?】', title):
        ttype = '【ブラケット】'
    elif TITLE_TOKAIU_RE.search(title):
        ttype = 'とかいう'
    elif '→' in title:
        ttype = '→列挙/通説破壊'
    elif re.search(r'[ｗw]{2,}$|草$', title):
        ttype = '末尾ｗ草'
    elif title.endswith('？') or title.endswith('?'):
        ttype = '疑問'
    else:
        ttype = '断定/その他'
    if t_fail:
        warns.append('スレタイ'); hints.append('スレタイ → 型違いで複数案出して採点し直す/1フックで止める/「」のみ/結論を書ききらない（「実は〜だった」「という真実」はAI臭）: ' + '・'.join(t_fail))
    print(f'{mark("warn" if t_fail else "ok")} スレタイ[{ttype}]: 「{title[:30]}」{" ←"+",".join(t_fail) if t_fail else ""}')

    # 11c. 時代タグ照合（2026-06-17 残課題④で標準フローに配線＝--era無しでも自動で効く）
    #   ①--era指定時：トーン指示タグ vs スレタイ人物年代（ネタ分類の事故検出・2段以上でFAIL）
    #   ②常時(自動era)：スレタイ人物の時代を基準に、本文に出る"他の既知人物"の時代混線を検出
    #     （スレタイ人物と3段以上離れた人物が3回以上＝主役級に出たらWARN。1〜2回の比較・引き合いは許容）
    inf_era, inf_who = infer_era(bodies[0])
    ti = era_index(inf_era)
    if inf_era is None:
        print('🧭 時代タグ照合: スレタイから既知人物を検出できず（テーブル外）→ スキップ')
    else:
        # ① --era 明示照合（従来＝ネタ管理の時代タグの分類事故検出）
        if era:
            gj = era_index(era)
            if gj is None:
                print(f'🧭 時代タグ照合: 指定タグ「{era}」が未知（{inf_who}={inf_era}）→ 参考のみ')
            elif abs(ti - gj) >= 2:
                fails.append('時代タグ不一致')
                hints.append(f'時代タグ不一致＝{inf_who}は{inf_era}の人物やのに指示タグが「{era}」（{abs(ti-gj)}段ズレ）→ タグを{inf_era}に直す or テーマを{era}の人物に差し替える')
                print(f'❌ 時代タグ照合: {inf_who}＝{inf_era} vs 指示「{era}」＝{abs(ti-gj)}段ズレ（不一致）')
            else:
                print(f'✅ 時代タグ照合: {inf_who}＝{inf_era} ≒ 指示「{era}」（整合）')
        else:
            print(f'🧭 時代タグ（自動era）: スレタイ人物「{inf_who}」＝{inf_era} を基準に本文を自動照合（--eraでネタ分類タグも照合可）')

        # ② 本文の時代混線の自動検出（--eraの有無に関わらず常時。これが残課題④の配線の核）
        mixed = []
        for nm, (e, cnt) in scan_people(text).items():
            if nm == inf_who:
                continue
            ei = era_index(e)
            if ei is not None and ti is not None and abs(ei - ti) >= 3 and cnt >= 3:
                mixed.append(f'{nm}({e}・{cnt}回)')
        if mixed:
            warns.append('時代混線疑い')
            hints.append(f'時代混線の疑い＝スレタイは{inf_who}({inf_era})やのに、3段以上離れた時代の人物が主役級に頻出: {", ".join(mixed)} → 別時代の人物を主題にしてないか／時代を取り違えてないか確認（比較・引き合いの1〜2回はOK）')
        print(f'{mark("warn" if mixed else "ok")} 本文の時代混線: {("⚠️"+",".join(mixed)) if mixed else "なし（基準"+inf_era+"）"}')

    # 12. 締め（最終レス）
    print(f'   末尾: 「{bodies[-1][:30]}」')

    # 総合
    print('\n' + '=' * 50)
    if fails:
        print(f'❌ NEEDS-FIX: {len(fails)}件の必須項目が未達 → {", ".join(fails)}')
    elif warns:
        print(f'⚠️  PASS（要改善 {len(warns)}件: {", ".join(warns)}）')
    else:
        print('✅ PASS：全項目クリア')
    if hints:
        print('\n【リカバリ指示】')
        for h in hints:
            print(' ・' + h)
    return 1 if fails else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--min', type=int, default=2500)
    ap.add_argument('--max', type=int, default=3200)
    ap.add_argument('--era', default=None, help='トーン指示の時代タグ(例:戦国/飛鳥)。人物実在年代と機械照合')
    a = ap.parse_args()
    sys.exit(check(a.file, a.min, a.max, a.era))
