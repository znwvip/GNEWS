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
          
        # 打印响应状态和内容类型  
        print(f"  [状态] HTTP {resp.status_code}, Content-Type: {resp.headers.get('content-type', 'unknown')}")  
          
        if resp.status_code == 200:  
            # 尝试解析JSON  
            try:  
                res_json = resp.json()  
            except json.JSONDecodeError:  
                print(f"  [错误] 响应不是有效的JSON格式")  
                print(f"  [调试] 响应内容前200字符: {resp.text[:200]}")  
                return []  
                  
            if res_json.get("status") in ["success", "cache"]:  
                items = res_json.get("items", [])  
                if not items:  
                    print(f"  [警告] API返回了空的数据列表")  
                else:  
                    print(f"  [成功] 拿到 {len(items)} 条")  
                    return items  
            else:  
                print(f"  [失败] API返回状态: {res_json.get('status')}")  
                # 打印API返回的错误信息  
                if 'error' in res_json:  
                    print(f"  [错误详情] {res_json['error']}")  
        else:  
            print(f"  [失败] HTTP状态码: {resp.status_code}")  
            # 打印错误响应内容  
            print(f"  [调试] 错误响应: {resp.text[:200]}")  
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
    print(f"[调试] 备份目录创建成功: {backup_dir}")  
  
    all_results = []  
    update_time = get_beijing_time()  
    print(f"[调试] 当前北京时间: {update_time}")  
  
    for p in PLATFORMS:  
        raw_items = fetch_data(p["id"], p["name"])  
        if not raw_items:  
            print(f"  [跳过] {p['name']} 没有数据，跳过处理")  
            continue  
              
        for idx, item in enumerate(raw_items):  
            # 多种可能的标题字段  
            title = item.get("title") or item.get("word") or item.get("name") or item.get("text")  
            if not title or not str(title).strip():  
                print(f"  [跳过] 第{idx+1}条标题为空")  
                continue  
                  
            # 多种可能的URL字段  
            url = item.get("mobileUrl") or item.get("url") or item.get("link") or item.get("href") or ""  
              
            all_results.append({  
                "source": p["name"],  
                "rank": idx + 1,  
                "title": str(title).strip(),  
                "url": str(url).strip(),  
                "time": update_time  
            })  
            print(f"  [添加] {p['name']} 第{idx+1}条: {title[:30]}...")  
              
        time.sleep(random.uniform(0.5, 1.2))  
  
    if not all_results:  
        print(f"[错误] 没有抓取到任何数据，创建空文件")  
        payload = {  
            "updated_at": update_time,  
            "total": 0,  
            "items": [],  
            "error": "No data fetched"  
        }  
    else:  
        payload = {  
            "updated_at": update_time,  
            "total": len(all_results),  
            "items": all_results  
        }  
  
    # 保存到docs/data.json（主文件）  
    output_path = os.path.join(docs_dir, "data.json")  
    with open(output_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
    print(f"[调试] 主文件已保存: {output_path}")  
  
    # 备份功能  
    beijing_time = datetime.now(timezone(timedelta(hours=8)))  
    date_dir = beijing_time.strftime("%Y-%m-%d")  
    backup_date_dir = os.path.join(backup_dir, date_dir)  
    os.makedirs(backup_date_dir, exist_ok=True)  
    print(f"[调试] 按日期创建备份目录: {backup_date_dir}")  
      
    # 文件名格式：年-月-日_时-分-秒.json  
    backup_filename = f"{date_dir}_{beijing_time.strftime('%H-%M-%S')}.json"  
    backup_path = os.path.join(backup_date_dir, backup_filename)  
      
    with open(backup_path, "w", encoding="utf-8") as f:  
        json.dump(payload, f, ensure_ascii=False, indent=2)  
  
    print(f"\n[任务结束] 汇总 {len(all_results)} 条数据。北京时间: {update_time}")  
    print(f"[备份完成] 备份至: {backup_path}")  
    print(f"[调试] 备份文件大小: {os.path.getsize(backup_path)} 字节")  
  
if __name__ == "__main__":  
    main()  
