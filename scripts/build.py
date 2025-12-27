import json  
import os  
import time  
from datetime import datetime  
import requests  
  
# -----------------------------  
# 配置  
# -----------------------------  
# 从环境变量读取 API 地址，如果读取不到则用默认值  
API_URL = os.getenv("NEWSNOW_API_URL", "https://newsnow.busiyi.world/api")  
  
# 需要抓取的平台 ID  
PLATFORMS = [  
    {"id": "zhihu", "name": "知乎"},  
    {"id": "weibo", "name": "微博"},  
    {"id": "baidu", "name": "百度热搜"},  
    {"id": "bilibili", "name": "B站热搜"},  
    {"id": "toutiao", "name": "今日头条"},  
]  
  
def fetch_platform_data(pid: str, pname: str):  
    """  
    抓取单个平台的数据  
    """  
    headers = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  
        "Referer": "https://newsnow.busiyi.world/",  
        "Accept": "application/json"  
    }  
      
    # 关键：NewsNow 系统的参数名是 type  
    params = {"type": pid}  
      
    try:  
        print(f"[正在抓取] {pname} ({pid})...")  
        response = requests.get(API_URL, params=params, headers=headers, timeout=20)  
          
        if response.status_code == 200:  
            res_json = response.json()  
            # NewsNow 返回格式通常是 {"success": true, "data": [...]}  
            if isinstance(res_json, dict) and "data" in res_json:  
                return res_json["data"]  
            elif isinstance(res_json, list):  
                return res_json  
        else:  
            print(f"[错误] {pname} 返回状态码: {response.status_code}")  
              
    except Exception as e:  
        print(f"[异常] {pname} 抓取失败: {e}")  
      
    return []  
  
def main():  
    # 确保 docs 目录存在  
    docs_dir = os.path.join(os.getcwd(), "docs")  
    if not os.path.exists(docs_dir):  
        os.makedirs(docs_dir)  
  
    all_results = []  
  
    for p in PLATFORMS:  
        data = fetch_platform_data(p["id"], p["name"])  
          
        if data:  
            for idx, item in enumerate(data):  
                all_results.append({  
                    "source": p["name"],  
                    "rank": item.get("rank") or (idx + 1),  
                    "title": item.get("title") or item.get("word") or "无标题",  
                    "url": item.get("url") or item.get("link") or "",  
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                })  
            print(f"[成功] {p['name']} 抓取到 {len(data)} 条数据")  
        else:  
            print(f"[失败] {p['name']} 未获取到数据")  
          
        # 停顿 1 秒，避免请求太快被封  
        time.sleep(1)  
  
    # 最终汇总 JSON  
    payload = {  
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  
        "total": len(all_results),  
        "items": all_results  
    }  
  
    # 写入文件  
    output_file = os.path.join(docs_dir, "data.json")  
    with open(output_file, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[完成] 所有数据已保存至 {output_file}, 共 {len(all_results)} 条")  
  
if __name__ == "__main__":  
    main()  
