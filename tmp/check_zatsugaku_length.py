# -*- coding: utf-8 -*-
"""雑学モード専用のスレ本文尺ゲート。

通常の創作スレには影響させないため、manifest に
content_mode: "zatsugaku" または length_policy.profile: "zatsugaku"
がある場合だけチェックする。
"""
import argparse
import json
import os
import re
import sys


def parse_thread(path):
    posts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*(\d+):\s?(.*)$", line.rstrip("\n"))
            if m:
                posts.append((int(m.group(1)), clean(m.group(2))))
    return posts


def clean(text):
    text = re.sub(r"^\s*>>\d+\s*", "", text)
    text = re.sub(r"^\s*↑\s*", "", text)
    return text


def lower(value):
    return str(value or "").strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--force", action="store_true", help="content_mode がなくても雑学基準で検査する")
    args = ap.parse_args()

    manifest_path = os.path.abspath(args.manifest)
    manifest_dir = os.path.dirname(manifest_path)
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    policy = manifest.get("length_policy", {})
    if not isinstance(policy, dict):
        policy = {}

    active = (
        args.force
        or lower(manifest.get("content_mode")) == "zatsugaku"
        or lower(policy.get("profile")) == "zatsugaku"
    )
    if not active:
        print(json.dumps({
            "verdict": "SKIP",
            "reason": "content_mode/length_policy is not zatsugaku",
        }, ensure_ascii=False, indent=2))
        return 0

    thread_sections = [s for s in manifest.get("sections", []) if s.get("type") == "thread"]
    if len(thread_sections) < 2:
        print(json.dumps({
            "verdict": "FAIL",
            "issues": ["雑学モードはスレ①/スレ②の2本が必須"],
        }, ensure_ascii=False, indent=2))
        return 2

    def resolve(path):
        return path if os.path.isabs(path) else os.path.join(manifest_dir, path)

    min_front = int(policy.get("min_thread1_chars", 2500))
    min_back = int(policy.get("min_thread2_chars", 2500))
    min_total = int(policy.get("min_total_thread_chars", 5000))

    front = thread_sections[0]
    back = thread_sections[1]
    front_chars = sum(len(body) for _, body in parse_thread(resolve(front["path"])))
    back_chars = sum(len(body) for _, body in parse_thread(resolve(back["path"])))
    total_chars = front_chars + back_chars

    issues = []
    if front_chars < min_front:
        issues.append(f"{front.get('label', 'スレ①')} {front_chars}字 < {min_front}字")
    if back_chars < min_back:
        issues.append(f"{back.get('label', 'スレ②')} {back_chars}字 < {min_back}字")
    if total_chars < min_total:
        issues.append(f"スレ合計 {total_chars}字 < {min_total}字")

    result = {
        "verdict": "FAIL" if issues else "PASS",
        "profile": "zatsugaku",
        "scope": "thread_body_only",
        "thresholds": {
            "min_thread1_chars": min_front,
            "min_thread2_chars": min_back,
            "min_total_thread_chars": min_total,
        },
        "actual": {
            front.get("label", "スレ①"): front_chars,
            back.get("label", "スレ②"): back_chars,
            "total_thread_chars": total_chars,
        },
        "issues": issues,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
