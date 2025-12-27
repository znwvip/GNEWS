import json  
import os  
import time  
import random  
from datetime import datetime, timedelta, timezone  
import requests  
  
# -----------------------------  
# 配置  
# -----------------------------  
API_BASE_URL = "https://newsnow.busiyi.world/api/s"  
  
# 平台列表  
PLATFORMS = [  
    {"id": "zhihu", "name": "知乎"},  
    {"id": "weibo", "name": "微博"},  
    {"id": "baidu", "name": "百度热搜"},  
    {"id": "bilibili", "name": "B站热搜"},  
    {"id": "douyin", "name": "抖音热搜"},  
    {"id": "toutiao", "name": "今日头条"},  
    {"id": "tieba", "name": "贴吧"},  
    {"id": "wallstreetcn", "name": "华尔街见闻"},  
    {"id": "cls", "name": "财联社"},  
    {"id": "thepaper", "name": "澎湃新闻"},  
    {"id": "ifeng", "name": "凤凰网"},  
]  
  
DEFAULT_HEADERS = {  
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  
    "Accept": "application/json, text/plain, */*",  
}  
  
def get_beijing_time():  
    """获取北京时间字符串"""  
    tz = timezone(timedelta(hours=8))  
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")  
  
def fetch_data(pid, pname):  
    url = f"{API_BASE_URL}?id={pid}&latest"  
    try:  
        print(f"[正在抓取] {pname}...")  
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)  
        if resp.status_code == 200:  
            res_json = resp.json()  
            if res_json.get("status") in ["success", "cache"]:  
                items = res_json.get("items", [])  
                print(f"  [成功] 拿到 {len(items)} 条")  
                return items  
        print(f"  [失败] 状态码: {resp.status_code}")  
    except Exception as e:  
        print(f"  [异常] {e}")  
    return []  
  
def main():  
    # 创建docs目录（如果不存在）  
    docs_dir = os.path.join(os.getcwd(), "docs")  
    os.makedirs(docs_dir, exist_ok=True)  
  
    # 创建备份目录结构  
    backup_dir = os.path.join(os.getcwd(), "backup")  
    os.makedirs(backup_dir, exist_ok=True)  
  
    all_results = []  
    update_time = get_beijing_time()  
  
    for p in PLATFORMS:  
        raw_items = fetch_data(p["id"], p["name"])  
        for idx, item in enumerate(raw_items):  
            title = item.get("title")  
            if not title or not str(title).strip():  
                continue  
                  
            all_results.append({  
                "source": p["name"],  
                "rank": idx + 1,  
                "title": str(title).strip(),  
                "url": item.get("mobileUrl") or item.get("url") or "",  
                "time": update_time  
            })  
        time.sleep(random.uniform(0.5, 1.2))  
  
    payload = {  
        "updated_at": update_time,  
        "total": len(all_results),  
        "items": all_results  
    }  
  
    # 保存到docs/data.json（主文件）  
    output_path = os.path.join(docs_dir, "data.json")  
    with open(output_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    # 备份功能  
    beijing_time = datetime.now(timezone(timedelta(hours=8)))  
    date_dir = beijing_time.strftime("%Y-%m-%d")  
    backup_date_dir = os.path.join(backup_dir, date_dir)  
    os.makedirs(backup_date_dir, exist_ok=True)  
      
    # 文件名格式：年-月-日_时-分-秒.json  
    backup_filename = f"{date_dir}_{beijing_time.strftime('%H-%M-%S')}.json"  
    backup_path = os.path.join(backup_date_dir, backup_filename)  
      
    with open(backup_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[任务结束] 汇总 {len(all_results)} 条数据。北京时间: {update_time}")  
    print(f"[备份完成] 备份至: {backup_path}")  
  
if __name__ == "__main__":  
    main()  
