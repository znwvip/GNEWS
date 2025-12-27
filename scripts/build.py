# scripts/build.py
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# -----------------------------
# Config
# -----------------------------
NEWSNOW_BASE_URL = os.getenv("NEWSNOW_BASE_URL", "https://newsnow.busiyi.world").rstrip("/")

# 你也可以在 workflow 里显式设置 NEWSNOW_API_URL，绕过自动探测
NEWSNOW_API_URL = os.getenv("NEWSNOW_API_URL", "").strip()

PLATFORMS_DEFAULT = [
    {"id": "zhihu", "name": "知乎"},
    {"id": "weibo", "name": "微博"},
    {"id": "baidu", "name": "百度热搜"},
    {"id": "bilibili-hot-search", "name": "bilibili 热搜"},
    {"id": "toutiao", "name": "今日头条"},
]

# 一些常见“可能是 JSON API 的路径”候选。我们会逐个试探。
API_CANDIDATES = [
    "/api/news",
    "/api/news.json",
    "/api/v1/news",
    "/api/v1/news.json",
    "/news",
    "/news.json",
    "/v1/news",
    "/v1/news.json",
    "/api/sources",
    "/api/v1/sources",
]


def fetch_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """请求 JSON；如果返回不是 JSON，会打印 debug 头部帮助定位。"""
    headers = {"Accept": "application/json"}
    r = requests.get(url, params=params, timeout=30, headers=headers)
    ct = (r.headers.get("content-type") or "").lower()

    if "json" not in ct:
        # 返回 HTML / 文本时，打印前 200 字符，帮助你定位真实 API
        print(f"[DEBUG] url={r.url} status={r.status_code} content-type={ct}")
        print(f"[DEBUG] body_head={r.text[:200]!r}")

    r.raise_for_status()
    return r.json()


def pick_working_api(base_url: str) -> str:
    """从候选路径里选一个真正返回 JSON 的 API 端点。"""
    headers = {"Accept": "application/json"}
    for path in API_CANDIDATES:
        url = base_url + path
        try:
            r = requests.get(url, timeout=15, headers=headers)
            ct = (r.headers.get("content-type") or "").lower()
            if r.status_code == 200 and "json" in ct:
                print(f"[OK] picked JSON API: {url} (content-type={ct})")
                return url
            else:
                print(f"[DEBUG] candidate={url} status={r.status_code} content-type={ct}")
        except Exception as e:
            print(f"[DEBUG] candidate={url} error={e}")

    raise RuntimeError(
        "No JSON API endpoint found.\n"
        "Please set NEWSNOW_API_URL explicitly in GitHub Actions env.\n"
        "Example:\n"
        "  NEWSNOW_API_URL: \"https://<your-endpoint>/api/xxx\""
    )


def safe_get(d: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def normalize_items(raw: Any, fallback_source: str) -> List[Dict[str, Any]]:
    """
    把 API 返回尽量归一化为：
    {source, rank, title, url, time}

    注意：newsnow 的实际字段结构可能不同。
    这里做“宽松解析”，先让 MVP 跑通。
    """
    items: List[Dict[str, Any]] = []

    candidate_list: Optional[List[Any]] = None
    if isinstance(raw, list):
        candidate_list = raw
    elif isinstance(raw, dict):
        for path in (
            ["data"],
            ["items"],
            ["list"],
            ["result"],
            ["data", "items"],
            ["data", "list"],
            ["data", "result"],
        ):
            v = safe_get(raw, path)
            if isinstance(v, list):
                candidate_list = v
                break

    if not isinstance(candidate_list, list):
        return items

    for it in candidate_list:
        if not isinstance(it, dict):
            continue

        title = it.get("title") or it.get("name") or it.get("text") or ""
        url = it.get("url") or it.get("link") or it.get("href") or ""
        rank = it.get("rank") or it.get("index") or it.get("position")
        time_str = it.get("time") or it.get("timestamp") or it.get("date") or ""

        source = (
            it.get("source")
            or it.get("platform")
            or it.get("from")
            or it.get("source_name")
            or fallback_source
        )

        if not title:
            continue

        # rank 有时是字符串，这里不强制转换，前端会按原样展示
        items.append(
            {
                "source": str(source),
                "rank": rank,
                "title": str(title),
                "url": str(url),
                "time": str(time_str),
            }
        )

    return items


def main() -> None:
    docs_dir = os.path.join(os.getcwd(), "docs")
    os.makedirs(docs_dir, exist_ok=True)

    platforms = PLATFORMS_DEFAULT

    api_url = NEWSNOW_API_URL or pick_working_api(NEWSNOW_BASE_URL)
    print(f"[INFO] Using API URL: {api_url}")

    all_items: List[Dict[str, Any]] = []
    ok = 0
    fail = 0

    # MVP：假设 API 支持 ?platform=xxx
    # 如果不支持，会在 debug 输出里看到返回结构/错误，我们再调整请求方式。
    for p in platforms:
        pid = p["id"]
        pname = p["name"]
        try:
            raw = fetch_json(api_url, params={"platform": pid})
            part = normalize_items(raw, fallback_source=pname)
            all_items.extend(part)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"[WARN] platform={pid} failed: {e}")

    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platforms": [p["name"] for p in platforms],
        "items": all_items,
        "meta": {
            "source": "newsnow",
            "newsnow_base_url": NEWSNOW_BASE_URL,
            "api_url": api_url,
            "platform_ok": ok,
            "platform_fail": fail,
            "note": (
                "如果 items=0 或 fail 很高，说明：\n"
                "1) API 端点不对（请在 workflow 里设置 NEWSNOW_API_URL），或\n"
                "2) API 不支持 ?platform= 参数（需要换成按 source 拉取的方式）。\n"
                "查看 Actions 日志中的 [DEBUG] 输出即可定位。"
            ),
        },
    }

    out_path = os.path.join(docs_dir, "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote {out_path} items={len(all_items)} ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
