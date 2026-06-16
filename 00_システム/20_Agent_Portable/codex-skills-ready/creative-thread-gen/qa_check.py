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
ATTR_RE = r'(朝鮮人|韓国人|中国人|在日|部落|百姓|農民|女|男|老人|障[がが]い|身分|出自|宗教|百済|新羅|高麗|渤海|アイヌ|蝦夷|異民族|外国人|民族|連中)'
_CONSTRUCT = r'(だから|のくせに|ごとき|風情|には無理|なんかに|とか笑|の分際|所詮|野蛮|未開|格下|劣等|劣[っる]|下等|低俗|信用なら|信用でき)'
# 属性語と侮蔑構文/蔑視語が近接（双方向）したらWARN。正当な史実説明もヒットしうる→必ずLLM文脈確認へ。
SLUR_CONTEXT_RE = re.compile(ATTR_RE + r'.{0,8}' + _CONSTRUCT + r'|' + _CONSTRUCT + r'.{0,8}' + ATTR_RE)


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


def check(path, mn=2500, mx=3200):
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
        st = 'fail'; fails.append('字数'); hints.append(f'尺不足（あと{mn-chars}字）→ 知識ニキの長文(100〜140字)をトピック別に追加。短レス追加では埋まらない')
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
    zw = text.count('ｗ')
    def soft(name, val, need):
        if val < need:
            warns.append(name);
        return 'ok' if val >= need else 'warn'
    print(f'{mark(soft("うろ覚え", uro, 2))} うろ覚え又聞き: {uro}本（目標2+）')
    print(f'{mark(soft("吐き捨て", haki, 2))} 吐き捨て口調: {haki}本（目標2+）')
    print(f'{mark(soft("誤答訂正", teisei, 1))} 誤答→訂正の気配: {teisei}本（目標1+）')
    print(f'{mark(soft("全角ｗ", zw, 3))} 全角ｗ: {zw}個（目標3+）')

    # 10. ID（本物寄せ）
    if has_id:
        idc = Counter(p['id'] for p in posts if p['id'])
        recur = [i for i, c in idc.items() if c >= 3]
        st = 'ok' if recur else 'warn'
        if not recur:
            warns.append('ID再登場')
        print(f'{mark(st)} ID: {len(idc)}種 / 3回以上再登場 {len(recur)}人（役の一貫性）')

    # 11. スレタイ（1レス目）
    title = bodies[0]
    t_fail = []
    if '"' in title or '"' in title:
        t_fail.append('ASCII"使用')
    if '、' in title and ('？' in title or '?' in title):
        t_fail.append('二段重ね疑い')
    if len(title) > 42:
        t_fail.append(f'長い({len(title)}字)')
    if t_fail:
        warns.append('スレタイ'); hints.append('スレタイ → 1フックで止める/「」のみ/結論を書ききらない: ' + '・'.join(t_fail))
    print(f'{mark("warn" if t_fail else "ok")} スレタイ: 「{title[:30]}」{" ←"+",".join(t_fail) if t_fail else ""}')

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
    a = ap.parse_args()
    sys.exit(check(a.file, a.min, a.max))
