#!/usr/bin/env python3
"""
thread_scraper.py - 2chまとめサイトスレッドスクレイパー
Usage:
    python thread_scraper.py <URL> [<URL2> ...]
    python thread_scraper.py --file urls.txt
    python thread_scraper.py <URL1> <URL2> -o output.md

Output: 構造化Markdown（レス番号・本文）を stdout または -o 指定ファイルに出力
"""

import argparse
import re
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Comment

# ============================================================
# 共通設定
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2  # サーバー負荷軽減
MAX_RETRIES = 3             # HTML取得リトライ回数
RETRY_DELAY = 5             # リトライ間隔（秒）
MIN_RES_COUNT = 5           # これ以下ならWARN判定


# ============================================================
# サイト判定
# ============================================================

def detect_site(url: str) -> str:
    """URLからサイトタイプを判定"""
    domain = urlparse(url).netloc.lower()

    # livedoor Blog 系 (多くのまとめサイトが利用)
    livedoor_domains = [
        "absurd.blogo.jp",           # 非常識＠なんJ
        "gabareki.blog.jp",          # ガバガバ歴史速報
        "tihourekisimatome.blog.jp", # 遅報歴史まとめ
        "namekkutake.livedoor.blog", # まとメメちゃん
        "niwareki.doorblog.jp",      # ニワカ歴史オタ
    ]

    # livedoor/blog.jp系
    if any(d in domain for d in livedoor_domains):
        return "livedoor"
    if domain.endswith(".blog.jp") or domain.endswith(".doorblog.jp"):
        return "livedoor"
    if "livedoor" in domain or "blogo.jp" in domain:
        return "livedoor"

    # 2chblog系 (livedoorベースだがクラス名が異なる場合あり)
    if "2chblog.jp" in domain:
        return "livedoor_2chblog"

    # 大河ドラマ2ch
    if "2chtaiga.com" in domain:
        return "livedoor"

    # nanjgod
    if "nanjgod.com" in domain:
        return "nanjgod"

    # れふかん
    if "merit-information.com" in domain:
        return "merit_info"

    # まめ速
    if "mamesoku.com" in domain:
        return "livedoor"

    # FC2系
    if "fc2.com" in domain or "fc2" in domain:
        return "fc2"

    # WordPressっぽいもの
    if "love-knowledge.com" in domain:
        return "wordpress"

    # その他
    return "generic"


# ============================================================
# HTML取得
# ============================================================

def fetch_html(url: str) -> str:
    """URLからHTMLを取得（リトライ付き）"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            # エンコーディング自動検出の改善
            if resp.encoding and resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding
            if resp.text and len(resp.text) > 500:
                return resp.text
            # HTMLが極端に短い → リトライ
            print(f"⚠ HTML短すぎ ({len(resp.text)}文字), リトライ {attempt}/{MAX_RETRIES}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"⚠ 取得失敗 (試行{attempt}/{MAX_RETRIES}): {url}\n  Error: {e}", file=sys.stderr)
        if attempt < MAX_RETRIES:
            print(f"⏳ {RETRY_DELAY}秒後にリトライ...", file=sys.stderr)
            time.sleep(RETRY_DELAY)
    print(f"❌ {MAX_RETRIES}回試行後も取得失敗: {url}", file=sys.stderr)
    return ""


# ============================================================
# パーサー: livedoor Blog 系
# ============================================================

def parse_livedoor(html: str, url: str) -> dict:
    """livedoor Blog系まとめサイトのパーサー"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"title": "", "body_lines": [], "url": url}

    # タイトル取得
    title_el = soup.select_one("h1.article-title a, h2.article-title a, h1 a, .article-title")
    if title_el:
        result["title"] = title_el.get_text(strip=True)
    else:
        title_tag = soup.find("title")
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)

    # 記事本文 (スレまとめ部分 = 元2chスレのレスのみ)
    article = soup.select_one("div.article-body-inner, div.article-body, div.entry-content, .article-body-more")
    if not article:
        article = soup.select_one("article, main, .main-content")

    if article:
        result["body_lines"] = _extract_res_blocks(article)

    # まとめサイトの読者コメントは取得しない
    return result


def parse_livedoor_2chblog(html: str, url: str) -> dict:
    """なんJ歴史部等の2chblog系"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"title": "", "body_lines": [], "url": url}

    title_el = soup.select_one("h1 a, h2 a, .article-title a, title")
    if title_el:
        result["title"] = title_el.get_text(strip=True)

    article = soup.select_one("div.article-body-inner, div.article-body, .entry-content")
    if article:
        result["body_lines"] = _extract_res_blocks(article)

    return result


# ============================================================
# パーサー: nanjgod
# ============================================================

def parse_nanjgod(html: str, url: str) -> dict:
    """nanjgod.com のパーサー"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"title": "", "body_lines": [], "url": url}

    title_el = soup.select_one("h1.entry-title, h1 a, title")
    if title_el:
        result["title"] = title_el.get_text(strip=True)

    article = soup.select_one(".entry-content, .article-body, article")
    if article:
        result["body_lines"] = _extract_res_blocks(article)

    return result


# ============================================================
# パーサー: れふかん (merit-information.com)
# ============================================================

def parse_merit_info(html: str, url: str) -> dict:
    """merit-information.com のパーサー"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"title": "", "body_lines": [], "url": url}

    title_el = soup.select_one("h1.entry-title, h1, title")
    if title_el:
        result["title"] = title_el.get_text(strip=True)

    article = soup.select_one(".entry-content, .post-content, article .content")
    if article:
        result["body_lines"] = _extract_res_blocks(article)

    return result


# ============================================================
# パーサー: WordPress 汎用
# ============================================================

def parse_wordpress(html: str, url: str) -> dict:
    """WordPress系汎用パーサー"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"title": "", "body_lines": [], "url": url}

    title_el = soup.select_one("h1.entry-title, h1.post-title, h1, title")
    if title_el:
        result["title"] = title_el.get_text(strip=True)

    article = soup.select_one(".entry-content, .post-content, article")
    if article:
        result["body_lines"] = _extract_res_blocks(article)

    return result


# ============================================================
# パーサー: 汎用 (フォールバック)
# ============================================================

def parse_generic(html: str, url: str) -> dict:
    """汎用フォールバックパーサー"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"title": "", "body_lines": [], "url": url}

    title_tag = soup.find("title")
    if title_tag:
        result["title"] = title_tag.get_text(strip=True)

    # 一番大きなテキストブロックを探す
    candidates = soup.select("article, .entry-content, .article-body, .post-content, .main-content, main")
    if not candidates:
        candidates = [soup.body] if soup.body else [soup]

    for candidate in candidates:
        lines = _extract_res_blocks(candidate)
        if len(lines) > len(result["body_lines"]):
            result["body_lines"] = lines

    return result


# ============================================================
# レス抽出ヘルパー
# ============================================================

def _extract_res_blocks(container) -> list:
    """
    まとめサイトの記事本文からレス（発言）ブロックを抽出する。
    各レスを {num, name, text} の辞書で返す。
    """
    results = []

    # -- 方式1: dt/dd ペア (livedoor系で多い) --
    dts = container.select("dt")
    dds = container.select("dd")
    if dts and dds and len(dts) == len(dds):
        for dt, dd in zip(dts, dds):
            num_match = re.search(r"(\d+)", dt.get_text())
            num = int(num_match.group(1)) if num_match else 0
            name = dt.get_text(strip=True)
            text = dd.get_text("\n", strip=True)
            if text:
                results.append({"num": num, "name": name, "text": text})
        if results:
            return results

    # -- 方式2: div.res / .response 等 (クラスベース) --
    res_divs = container.select(
        "div.res, div.response, div.t_b, div.comment, "
        "div[class*='res'], blockquote"
    )
    if res_divs:
        for i, div in enumerate(res_divs, 1):
            text = div.get_text("\n", strip=True)
            if text and len(text) > 2:
                num_match = re.search(r"^(\d+)", text)
                num = int(num_match.group(1)) if num_match else i
                results.append({"num": num, "name": "", "text": text})
        if results:
            return results

    # -- 方式3: <p>タグ群 / テキストノード (WordPress/独自CMS) --
    paragraphs = container.select("p, li")
    for i, p in enumerate(paragraphs, 1):
        text = p.get_text(strip=True)
        # 広告やナビ系テキストを除外
        if text and len(text) > 5 and not _is_noise(text):
            num_match = re.search(r"^(\d+)", text)
            num = int(num_match.group(1)) if num_match else i
            results.append({"num": num, "name": "", "text": text})

    # -- 方式4: 最終フォールバック - 全テキスト抽出 --
    if not results:
        full_text = container.get_text("\n", strip=True)
        lines = [l.strip() for l in full_text.split("\n") if l.strip() and len(l.strip()) > 3]
        for i, line in enumerate(lines, 1):
            if not _is_noise(line):
                results.append({"num": i, "name": "", "text": line})

    return results


def _is_noise(text: str) -> bool:
    """広告・ナビ等のノイズテキストかどうか"""
    noise_patterns = [
        r"^(スポンサー|広告|PR|AD|Sponsored)",
        r"^(トップ|ホーム|カテゴリ|タグ|アーカイブ|人気記事|関連記事|おすすめ)",
        r"^(コメント|トラックバック|コメントする|コメントを書く)",
        r"(RSS|フィード|購読)",
        r"^(前の記事|次の記事|← →)",
        r"(引用元|ソース|source|元スレ).*https?://",
        r"^https?://",
        r"^\d+$",
        r"^(Copyright|©)",
        r"(シェア|ツイート|いいね|LINEで送る|はてブ)",
    ]
    for pat in noise_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


# ============================================================
# 出力フォーマッター
# ============================================================

def verify_completeness(parsed: dict) -> dict:
    """取得漏れを検証する"""
    body = parsed["body_lines"]
    result = {"status": "OK", "issues": [], "res_count": len(body), "total_chars": 0}

    if not body:
        result["status"] = "FAIL"
        result["issues"].append("レスが1件も取得できませんでした")
        return result

    result["total_chars"] = sum(len(r["text"]) for r in body)

    # レス番号の欠番チェック
    nums = sorted(set(r["num"] for r in body if r["num"] > 0))
    if nums and nums[0] > 0:
        expected = list(range(nums[0], nums[-1] + 1))
        missing = set(expected) - set(nums)
        if missing and len(missing) <= 20:
            result["issues"].append(f"欠番あり: {sorted(missing)[:10]}{'...' if len(missing)>10 else ''} ({len(missing)}件)")
        elif missing:
            result["issues"].append(f"欠番多数: {len(missing)}件（レス{nums[0]}〜{nums[-1]}の範囲）")

    # 取得件数の判定
    if len(body) < MIN_RES_COUNT:
        result["status"] = "FAIL"
        result["issues"].append(f"取得レス数が極端に少ない（{len(body)}件 < 最低{MIN_RES_COUNT}件）")
    elif len(body) < 10:
        if result["status"] == "OK":
            result["status"] = "WARN"
        result["issues"].append(f"取得レス数がやや少ない（{len(body)}件）")

    # 文字数チェック
    if result["total_chars"] < 200:
        if result["status"] == "OK":
            result["status"] = "WARN"
        result["issues"].append(f"総文字数が少ない（{result['total_chars']}文字）")

    if not result["issues"]:
        result["issues"].append("問題なし")

    return result


def format_output(parsed: dict) -> str:
    """パース結果を構造化Markdownに変換"""
    lines = []
    verification = verify_completeness(parsed)

    lines.append(f"# {parsed['title']}")
    lines.append(f"URL: {parsed['url']}")
    lines.append(f"取得レス数: {verification['res_count']}件")
    lines.append(f"本文総文字数: 約{verification['total_chars']:,}文字")
    lines.append("")

    # 検証結果
    status_icon = {"OK": "✅", "WARN": "⚠", "FAIL": "❌"}.get(verification["status"], "?")
    lines.append(f"### 取得検証: {status_icon} {verification['status']}")
    for issue in verification["issues"]:
        lines.append(f"- {issue}")
    lines.append("")

    if verification["status"] == "FAIL":
        lines.append("❌ **取得失敗**: このURLは手動コピペが必要です。")
        lines.append("")

    lines.append("---")
    lines.append("## 記事本文（スレまとめ）")
    lines.append("")

    for res in parsed["body_lines"]:
        num = res["num"]
        name = res.get("name", "")
        text = res["text"]

        if name:
            lines.append(f"**{num}**: {name}")
            lines.append(text)
        else:
            lines.append(f"**{num}**: {text}")
        lines.append("")

    # まとめサイトの読者コメントは出力しない（元スレのレスのみ）

    return "\n".join(lines)


# ============================================================
# メインディスパッチ
# ============================================================

PARSERS = {
    "livedoor": parse_livedoor,
    "livedoor_2chblog": parse_livedoor_2chblog,
    "nanjgod": parse_nanjgod,
    "merit_info": parse_merit_info,
    "wordpress": parse_wordpress,
    "fc2": parse_generic,
    "generic": parse_generic,
}


def scrape_thread(url: str) -> tuple:
    """
    1つのURLをスクレイプして (構造化Markdown, 検証結果dict) を返す。
    FAIL判定の場合は自動リトライ（別パーサーも試行）する。
    """
    site_type = detect_site(url)
    print(f"🔍 サイト判定: {site_type} ({url})", file=sys.stderr)

    html = fetch_html(url)
    if not html:
        fail_msg = f"# 取得失敗\nURL: {url}\n\n❌ HTMLの取得に失敗しました（{MAX_RETRIES}回リトライ済み）。手動コピペが必要です。\n"
        return fail_msg, {"status": "FAIL", "res_count": 0, "total_chars": 0, "issues": ["HTML取得失敗"]}

    # 1回目: 本来のパーサーで試行
    parser = PARSERS.get(site_type, parse_generic)
    parsed = parser(html, url)
    verification = verify_completeness(parsed)

    if verification["status"] != "FAIL":
        return format_output(parsed), verification

    # FAIL → 別パーサーでリトライ
    print(f"⚠ {site_type}パーサーでFAIL。別パーサーで再試行...", file=sys.stderr)
    fallback_order = ["livedoor", "livedoor_2chblog", "wordpress", "generic"]
    for fb_type in fallback_order:
        if fb_type == site_type:
            continue
        fb_parser = PARSERS.get(fb_type, parse_generic)
        fb_parsed = fb_parser(html, url)
        fb_verify = verify_completeness(fb_parsed)
        if fb_verify["res_count"] > verification["res_count"]:
            print(f"  → {fb_type}パーサーで改善: {fb_verify['res_count']}件", file=sys.stderr)
            parsed = fb_parsed
            verification = fb_verify
            if verification["status"] != "FAIL":
                break

    # それでもFAILなら再取得を1回試行
    if verification["status"] == "FAIL":
        print(f"⚠ 全パーサーでFAIL。HTMLを再取得して最終試行...", file=sys.stderr)
        time.sleep(RETRY_DELAY)
        html2 = fetch_html(url)
        if html2 and html2 != html:
            parsed2 = parser(html2, url)
            v2 = verify_completeness(parsed2)
            if v2["res_count"] > verification["res_count"]:
                parsed = parsed2
                verification = v2

    return format_output(parsed), verification


def main():
    parser = argparse.ArgumentParser(
        description="2chまとめサイトスレッドスクレイパー"
    )
    parser.add_argument("urls", nargs="*", help="スクレイプするURL")
    parser.add_argument("--file", "-f", help="URLリストファイル（1行1URL）")
    parser.add_argument("--output", "-o", help="出力ファイル（省略時はstdout）")

    args = parser.parse_args()

    urls = list(args.urls) if args.urls else []

    if args.file:
        try:
            with open(args.file) as f:
                urls.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))
        except FileNotFoundError:
            print(f"⚠ ファイルが見つかりません: {args.file}", file=sys.stderr)
            sys.exit(1)

    if not urls:
        print("⚠ URLを指定してください。", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)

    all_output = []
    summary = []  # (url, status, res_count, total_chars, issues)

    for i, url in enumerate(urls):
        if i > 0:
            print(f"⏳ {DELAY_BETWEEN_REQUESTS}秒待機中...", file=sys.stderr)
            time.sleep(DELAY_BETWEEN_REQUESTS)

        output, verification = scrape_thread(url)
        all_output.append(output)
        all_output.append("\n" + "=" * 60 + "\n")
        summary.append((url, verification))

    # ===== 取得サマリーレポート =====
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("# 取得サマリーレポート")
    summary_lines.append(f"取得URL数: {len(urls)}")
    summary_lines.append("")

    ok_count = sum(1 for _, v in summary if v["status"] == "OK")
    warn_count = sum(1 for _, v in summary if v["status"] == "WARN")
    fail_count = sum(1 for _, v in summary if v["status"] == "FAIL")
    total_res = sum(v["res_count"] for _, v in summary)
    total_chars = sum(v["total_chars"] for _, v in summary)

    summary_lines.append(f"| # | URL | 判定 | レス数 | 文字数 | 問題 |")
    summary_lines.append(f"|---|-----|------|--------|--------|------|")
    for i, (url, v) in enumerate(summary, 1):
        icon = {"OK": "✅", "WARN": "⚠", "FAIL": "❌"}.get(v["status"], "?")
        short_url = url[:50] + "..." if len(url) > 50 else url
        issues = "; ".join(v["issues"])
        summary_lines.append(f"| {i} | {short_url} | {icon} {v['status']} | {v['res_count']} | {v['total_chars']:,} | {issues} |")

    summary_lines.append("")
    summary_lines.append(f"**合計**: ✅{ok_count} / ⚠{warn_count} / ❌{fail_count}  |  レス合計: {total_res}件  |  文字合計: 約{total_chars:,}文字")
    summary_lines.append("")

    if fail_count > 0:
        summary_lines.append("### ❌ 手動コピペが必要なURL:")
        for url, v in summary:
            if v["status"] == "FAIL":
                summary_lines.append(f"- {url}")
        summary_lines.append("")
        summary_lines.append("**重要**: 上記URLは自動取得に失敗しました。ブラウザで開いてコメント欄を全選択コピペしてください。")
        summary_lines.append("**構成は変更しないでください。** 選定済みスレの差し替えは行わず、手動取得で対応してください。")
    elif warn_count > 0:
        summary_lines.append("### ⚠ 注意:")
        summary_lines.append("一部レス数が少ないURLがあります。内容を確認し、不足があれば手動で補完してください。")
    else:
        summary_lines.append("### ✅ 全URL取得成功")
        summary_lines.append("全スレッドの取得が正常に完了しました。")

    summary_lines.append("=" * 60)

    # サマリーを先頭に配置
    final = "\n".join(summary_lines) + "\n\n" + "\n".join(all_output)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final)
        print(f"✅ 出力完了: {args.output}", file=sys.stderr)
        # サマリーだけstderrにも出力（呼び出し側が確認できるよう）
        print("\n".join(summary_lines), file=sys.stderr)
    else:
        print(final)


if __name__ == "__main__":
    main()
