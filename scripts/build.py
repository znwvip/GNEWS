import json  
import os  
import time  
from datetime import datetime  
import requests  
  
# -----------------------------  
# 配置：换成备用的稳定 API 源 (api.oick.cn)  
# -----------------------------  
API_MAP = {  
    "zhihu": "https://api.oick.cn/hot/api.php?source=zhihu",  
    "weibo": "https://api.oick.cn/hot/api.php?source=weibo",  
    "baidu": "https://api.oick.cn/hot/api.php?source=baidu",  
    "bilibili": "https://api.oick.cn/hot/api.php?source=bilibili",  
}  
  
PLATFORM_NAMES = {  
    "zhihu": "知乎",  
    "weibo": "微博",  
    "baidu": "百度热搜",  
    "bilibili": "B站热搜",  
}  
  
def fetch_data(ptype, url):  
    headers = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  
    }  
    try:  
        print(f"[正在抓取] {PLATFORM_NAMES[ptype]}...")  
        # 增加 verify=False 防止 SSL 证书解析问题导致的 DNS 错误  
        resp = requests.get(url, headers=headers, timeout=20)  
        if resp.status_code == 200:  
            data_json = resp.json()  
            # api.oick.cn 返回的是 {"data": [...]} 或者直接是列表  
            if isinstance(data_json, dict) and "data" in data_json:  
                return data_json["data"]  
            if isinstance(data_json, list):  
                return data_json  
        print(f"[错误] {PLATFORM_NAMES[ptype]} 状态码: {resp.status_code}")  
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
          
        # 记录抓取数量  
        count = 0  
        for item in raw_list:  
            # 兼容不同 API 的字段名  
            title = item.get("title") or item.get("word") or item.get("name")  
            link = item.get("link") or item.get("url")  
              
            if title:  
                all_items.append({  
                    "source": PLATFORM_NAMES[ptype],  
                    "rank": count + 1,  
                    "title": str(title).strip(),  
                    "url": str(link).strip() if link else "",  
                    "time": update_time  
                })  
                count += 1  
        print(f"[完成] {PLATFORM_NAMES[ptype]} 成功获取 {count} 条数据")  
        time.sleep(1)  
  
    payload = {  
        "updated_at": update_time,  
        "total": len(all_items),  
        "items": all_items  
    }  
  
    output_path = os.path.join(docs_dir, "data.json")  
    with open(output_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[结果] 最终汇总 {len(all_items)} 条数据至 {output_path}")  
  
if __name__ == "__main__":  
    main()  
