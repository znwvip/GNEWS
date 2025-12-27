import json  
import os  
import time  
import random  
from datetime import datetime  
import requests  
  
# -----------------------------  
# 配置：根据你提供的参考代码进行精准适配  
# -----------------------------  
API_BASE_URL = "https://newsnow.busiyi.world/api/s"  
  
# 平台 ID 列表  
PLATFORMS = [  
    {"id": "zhihu", "name": "知乎"},  
    {"id": "weibo", "name": "微博"},  
    {"id": "baidu", "name": "百度热搜"},  
    {"id": "bilibili", "name": "B站热搜"},  
    {"id": "toutiao", "name": "今日头条"},  
]  
  
# 使用参考代码中的标准请求头  
DEFAULT_HEADERS = {  
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  
    "Accept": "application/json, text/plain, */*",  
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",  
    "Connection": "keep-alive",  
}  
  
def fetch_newsnow_data(platform_id, platform_name):  
    """  
    完全参照你提供的参考代码逻辑进行抓取  
    """  
    # 构造 URL: /api/s?id=xxx&latest  
    url = f"{API_BASE_URL}?id={platform_id}&latest"  
      
    try:  
        print(f"[正在抓取] {platform_name}...")  
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)  
          
        # 如果遇到 403，说明 GitHub IP 被封，我们需要打印出来以便确认  
        if response.status_code == 403:  
            print(f"  [警告] 403 Forbidden: GitHub IP 可能被该站点屏蔽")  
            return []  
              
        if response.status_code == 200:  
            data_json = response.json()  
              
            # 参照参考代码判断 status  
            status = data_json.get("status")  
            if status in ["success", "cache"]:  
                items = data_json.get("items", [])  
                print(f"  [成功] 获取到 {len(items)} 条数据 ({status})")  
                return items  
            else:  
                print(f"  [失败] 响应状态异常: {status}")  
        else:  
            print(f"  [失败] HTTP 状态码: {response.status_code}")  
              
    except Exception as e:  
        print(f"  [异常] 错误信息: {e}")  
      
    return []  
  
def main():  
    docs_dir = os.path.join(os.getcwd(), "docs")  
    os.makedirs(docs_dir, exist_ok=True)  
  
    all_results = []  
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
  
    for p in PLATFORMS:  
        raw_items = fetch_newsnow_data(p["id"], p["name"])  
          
        for idx, item in enumerate(raw_items):  
            title = item.get("title")  
            # 跳过无效标题  
            if title is None or not str(title).strip():  
                continue  
                  
            all_results.append({  
                "source": p["name"],  
                "rank": idx + 1,  
                "title": str(title).strip(),  
                "url": item.get("mobileUrl") or item.get("url") or "",  
                "time": update_time  
            })  
          
        # 按照参考代码，请求之间稍微停顿，模拟真实行为  
        time.sleep(random.uniform(1, 2))  
  
    # 汇总并保存  
    payload = {  
        "updated_at": update_time,  
        "total": len(all_results),  
        "items": all_results  
    }  
  
    output_path = os.path.join(docs_dir, "data.json")  
    with open(output_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[任务完成] 汇总条数: {len(all_results)}")  
    if len(all_results) == 0:  
        print("!!! 重要提示: 未能抓取到任何数据，请检查 Actions 日志中的状态码 !!!")  
  
if __name__ == "__main__":  
    main()  
