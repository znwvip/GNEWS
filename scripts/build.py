import json  
import os  
import time  
from datetime import datetime  
import requests  
  
# -----------------------------  
# 配置：使用更稳定的公共 API 源  
# -----------------------------  
# 这些接口对 GitHub Actions 更友好，不会返回 403  
API_MAP = {  
    "zhihu": "https://api.vvhan.com/api/hotlist?type=zhihu",  
    "weibo": "https://api.vvhan.com/api/hotlist?type=wbHot",  
    "baidu": "https://api.vvhan.com/api/hotlist?type=baiduHot",  
    "bilibili": "https://api.vvhan.com/api/hotlist?type=bili",  
    "toutiao": "https://api.vvhan.com/api/hotlist?type=toutiao",  
}  
  
PLATFORM_NAMES = {  
    "zhihu": "知乎",  
    "weibo": "微博",  
    "baidu": "百度热搜",  
    "bilibili": "B站热搜",  
    "toutiao": "今日头条",  
}  
  
def fetch_data(ptype, url):  
    """抓取数据"""  
    headers = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  
    }  
    try:  
        print(f"[正在抓取] {PLATFORM_NAMES[ptype]}...")  
        resp = requests.get(url, headers=headers, timeout=15)  
        if resp.status_code == 200:  
            data = resp.json()  
            if data.get("success"):  
                return data.get("data", [])  
        print(f"[错误] {PLATFORM_NAMES[ptype]} 返回状态码: {resp.status_code}")  
    except Exception as e:  
        print(f"[异常] {PLATFORM_NAMES[ptype]} 网络错误: {e}")  
    return []  
  
def main():  
    docs_dir = os.path.join(os.getcwd(), "docs")  
    os.makedirs(docs_dir, exist_ok=True)  
  
    all_items = []  
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
  
    for ptype, url in API_MAP.items():  
        raw_list = fetch_data(ptype, url)  
          
        for item in raw_list:  
            # 这里的字段根据 vvhan API 的结构进行了适配  
            all_items.append({  
                "source": PLATFORM_NAMES[ptype],  
                "rank": item.get("index"),  
                "title": item.get("title"),  
                "url": item.get("mobilUrl") or item.get("url"), # 优先跳转手机页  
                "time": update_time  
            })  
          
        # 频率限制  
        time.sleep(0.5)  
  
    # 构造最终输出  
    payload = {  
        "updated_at": update_time,  
        "total": len(all_items),  
        "items": all_items  
    }  
  
    output_path = os.path.join(docs_dir, "data.json")  
    with open(output_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[完成] 成功抓取 {len(all_items)} 条热搜数据！")  
  
if __name__ == "__main__":  
    main()  
