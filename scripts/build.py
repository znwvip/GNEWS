import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


# 你可以在 Actions 里用环境变量覆盖这个地址
NEWSNOW_BASE_URL = os.getenv("NEWSNOW_BASE_URL", "https://newsnow.busiyi.world")

# 先用最常见的“聚合列表”端点写法占位。
# 如果你的 API 实际端点不同，只需要改这里（见脚本底部的报错提示）
API_URL = os.getenv("NEWSNOW_API_URL", f"{NEWSNOW_BASE_URL}/api/news")


PLATFORMS_DEFAULT = [
    {"id": "zhihu", "name": "知乎"},
    {"id": "weibo", "name": "微博"},
    {"id": "baidu", "name": "百度热搜"},
    {"id": "bilibili-hot-search", "name": "bilibili 热搜"},
    {"id": "toutiao", "name": "今日头条"},
]


def now_beijing_str() -> str:
    # 北京时间 = UTC+8
    return datetime.now(timezone.utc).astimezone(
        timezone.utc.replace(tzinfo=timezone.utc)
    ).strftime("%Y-%m-%d %H:%M:%S")


def safe_get(d: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def fetch_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def normalize_items(raw: Any) -> List[Dict[str, Any]]:
    """
    把 newsnow 返回的数据尽量“宽松地”归一化成：
    {source, rank, title, url, time}
    """
    items: List[Dict[str, Any]] = []

    # 允许 raw 是 dict 或 list；尽量找一个“列表型字段”
    candidate_list = None
    if isinstance(raw, list):
        candidate_list = raw
    elif isinstance(raw, dict):
        # 常见可能：data/items/list/result 等
        for path in (["data"], ["items"], ["list"], ["result"], ["data", "items"], ["data", "list"]):
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
        url = it.get("url") or it.get("link") or ""
        rank = it.get("rank") or it.get("index") or it.get("position")
        source = it.get("source") or it.get("platform") or it.get("from") or it.get("source_name") or ""

        # 时间字段可能很乱，先原样放
        time_str = it.get("time") or it.get("timestamp") or it.get("date") or ""

        if not title:
            continue

        items.append(
            {
                "source": str(source) if source else "Unknown",
                "rank": rank if isinstance(rank, int) else rank,
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

    # 这里先用一个“聚合接口”假设：GET /api/news?platform=xxx
    all_items: List[Dict[str, Any]] = []
    ok = 0
    fail = 0

    for p in platforms:
        pid = p["id"]
        pname = p["name"]
        try:
            raw = fetch_json(API_URL, params={"platform": pid})
            part = normalize_items(raw)

            # 如果 source 为空，补上平台名
            for x in part:
                if x.get("source") in ("", "Unknown"):
                    x["source"] = pname

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
            "api_url": API_URL,
            "platform_ok": ok,
            "platform_fail": fail,
            "note": "如果 items 为空或平台全失败，请检查 NEWSNOW_API_URL 是否正确（newsnow 的 API 路径可能不同）。",
        },
    }

    out_path = os.path.join(docs_dir, "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote {out_path} items={len(all_items)} ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
