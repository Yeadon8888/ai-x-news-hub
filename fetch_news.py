#!/usr/bin/env python3
import json
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
OUT = DATA_DIR / "news.json"
REPORT_MD = DATA_DIR / "hotspots.md"

# 可扩展：直接添加你关心的 X 账号
X_ACCOUNTS = [
    "OpenAI", "sama", "xai", "AnthropicAI", "GoogleDeepMind",
    "NVIDIA", "TechCrunch", "verge", "WIRED", "arstechnica"
]

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.projectsegfau.lt",
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"


def fetch_url(url: str, timeout=20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def extract_image(desc_html: str):
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_html, re.IGNORECASE)
    return m.group(1) if m else None


def parse_rss(content: bytes, account: str):
    root = ET.fromstring(content)
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc_html = (item.findtext("description") or "").strip()
        summary = strip_html(desc_html)
        image = extract_image(desc_html)

        # 有些 RSS 会带 enclosure 图片
        enclosure = item.find("enclosure")
        if enclosure is not None and enclosure.get("type", "").startswith("image/"):
            image = enclosure.get("url") or image

        if title and link:
            items.append({
                "title": html.unescape(title),
                "url": link,
                "summary": summary,
                "image": image,
                "published": pub,
                "source": f"X/@{account}"
            })
    return items


def write_markdown_report(payload: dict):
    lines = []
    lines.append(f"# X 热点简报\n")
    lines.append(f"更新时间：{payload['updated_at']}  ")
    lines.append(f"总条数：{payload['count']}  ")
    lines.append("")

    for idx, it in enumerate(payload["items"][:40], 1):
        lines.append(f"## {idx}. {it['title']}")
        lines.append(f"- 内容摘要：{it.get('summary','')[:220]}")
        if it.get("image"):
            lines.append(f"- 图片：![]({it['image']})")
        else:
            lines.append(f"- 图片：无")
        lines.append(f"- 链接：{it['url']}")
        lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_items = []
    used_instance = None

    for inst in NITTER_INSTANCES:
        got_any = False
        temp = []
        for account in X_ACCOUNTS:
            rss_url = f"{inst}/{account}/rss"
            try:
                b = fetch_url(rss_url)
                if not b:
                    continue
                items = parse_rss(b, account)
                if items:
                    temp.extend(items)
                    got_any = True
            except Exception:
                continue

        if got_any:
            all_items = temp
            used_instance = inst
            break

    # 去重
    dedup = {}
    for it in all_items:
        dedup[it["url"]] = it
    items = list(dedup.values())

    # 按发布时间字符串逆序
    items.sort(key=lambda x: x.get("published", ""), reverse=True)
    items = items[:200]

    payload = {
        "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "count": len(items),
        "source_instance": used_instance,
        "accounts": X_ACCOUNTS,
        "items": items,
        "note": "数据来自 X 公开镜像 RSS（Nitter），可用性受镜像状态影响。"
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(payload)
    print(f"Wrote {len(items)} items -> {OUT}")
    print(f"Wrote markdown report -> {REPORT_MD}")


if __name__ == "__main__":
    main()
