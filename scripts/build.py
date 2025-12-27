import json  
import os  
import time  
from datetime import datetime  
import requests  
  
# -----------------------------  
# 配置：多路备用 API 方案  
# -----------------------------  
# 方案 A: vvhan (最近有 DNS 问题，但通常最快)  
# 方案 B: 52vmy (备用，较稳定)  
API_CONFIG = {  
    "zhihu": [  
        "https://api.vvhan.com/api/hotlist?type=zhihu",  
        "https://api.52vmy.cn/api/wl/hot/zhihu"  
    ],  
    "weibo": [  
        "https://api.vvhan.com/api/hotlist?type=wbHot",  
        "https://api.52vmy.cn/api/wl/hot/weibo"  
    ],  
    "baidu": [  
        "https://api.vvhan.com/api/hotlist?type=baiduHot",  
        "https://api.52vmy.cn/api/wl/hot/baidu"  
    ],  
    "bilibili": [  
        "https://api.vvhan.com/api/hotlist?type=bili",  
        "https://api.52vmy.cn/api/wl/hot/bili"  
    ]  
}  
  
PLATFORM_NAMES = {  
    "zhihu": "知乎",  
    "weibo": "微博",  
    "baidu": "百度热搜",  
    "bilibili": "B站热搜"  
}  
  
def fetch_with_fallback(ptype):  
    """为一个平台尝试多个 API 地址"""  
    urls = API_CONFIG.get(ptype, [])  
    headers = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  
    }  
      
    for url in urls:  
        try:  
            print(f"  [尝试接口] {url}")  
            resp = requests.get(url, headers=headers, timeout=15)  
            if resp.status_code == 200:  
                data_json = resp.json()  
                # 统一解析逻辑  
                items = data_json.get("data", [])  
                if items and len(items) > 0:  
                    print(f"  [成功] 从该接口获取到 {len(items)} 条数据")  
                    return items  
            print(f"  [跳过] 状态码: {resp.status_code}")  
        except Exception as e:  
            print(f"  [跳过] 网络错误: {e}")  
        time.sleep(1) # 失败后稍微等一下  
      
    return []  
  
def main():  
    docs_dir = os.path.join(os.getcwd(), "docs")  
    os.makedirs(docs_dir, exist_ok=True)  
  
    all_items = []  
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
  
    for ptype, name in PLATFORM_NAMES.items():  
        print(f"\n[开始抓取] {name}...")  
        raw_list = fetch_with_fallback(ptype)  
          
        count = 0  
        for item in raw_list:  
            # 适配不同 API 的字段名 (title/word, url/link/mobilUrl)  
            title = item.get("title") or item.get("word") or item.get("name")  
            link = item.get("mobilUrl") or item.get("url") or item.get("link")  
              
            if title:  
                all_items.append({  
                    "source": name,  
                    "rank": item.get("index") or (count + 1),  
                    "title": str(title).strip(),  
                    "url": str(link).strip() if link else "",  
                    "time": update_time  
                })  
                count += 1  
          
        if count == 0:  
            print(f"[警告] {name} 所有接口均失效")  
  
    # 写入 JSON  
    payload = {  
        "updated_at": update_time,  
        "total": len(all_items),  
        "items": all_items  
    }  
  
    output_path = os.path.join(docs_dir, "data.json")  
    with open(output_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[任务结束] 汇总 {len(all_items)} 条数据，更新于 {update_time}")  
  
if __name__ == "__main__":  
    main()  
