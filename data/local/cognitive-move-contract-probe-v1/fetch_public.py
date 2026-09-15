"""按冻结清单读取公开页面；不重试、不登录，保存所有尝试。"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import requests

ROOT = Path(__file__).resolve().parent
UA = "DeAIodorantResearch/1.0 (bounded public article inspection)"

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def get_once(url, directory, name):
    directory.mkdir(parents=True, exist_ok=True)
    record_path = directory / (name + "-request.json")
    if record_path.exists():
        raise ValueError("拒绝覆盖或重试已有请求：" + str(record_path))
    record = {"url":url,"requested_at_utc":now(),"method":"GET","user_agent":UA,"timeout_seconds":20,"redirects_allowed":False}
    try:
        response = requests.get(url, headers={"User-Agent":UA}, timeout=20, allow_redirects=False)
        raw = response.content
        record.update({"status":response.status_code,"content_type":response.headers.get("Content-Type"),"location":response.headers.get("Location"),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"completed_at_utc":now()})
        (directory / (name + ".html")).write_bytes(raw)
        save(record_path, record)
        return response, record
    except requests.RequestException as exc:
        record.update({"error":type(exc).__name__,"message":str(exc),"completed_at_utc":now()})
        save(record_path, record)
        return None, record

def main():
    selected = json.loads((ROOT / "selections.json").read_text(encoding="utf-8"))["articles"]
    assert len(selected) <= 6
    robots = {}
    for article in selected:
        url = article["url"]
        host = urlsplit(url).netloc
        folder = ROOT / "documents" / article["id"]
        if host not in robots:
            robot_url = "https://" + host + "/robots.txt"
            response, record = get_once(robot_url, ROOT / "robots" / host, "robots")
            parser = RobotFileParser(robot_url)
            if response is not None and response.status_code == 200:
                parser.parse(response.text.splitlines())
                robots[host] = (parser, "available")
            elif response is not None and response.status_code == 404:
                robots[host] = (None, "not_found")
            else:
                robots[host] = (None, "unresolved_stop")
            print(json.dumps({"robots":host,"state":robots[host][1],"status":record.get("status")},ensure_ascii=False),flush=True)
        parser, state = robots[host]
        if state == "unresolved_stop" or (parser is not None and not parser.can_fetch(UA, url)):
            save(folder / "article-request.json", {"url":url,"requested_at_utc":now(),"article_get_sent":False,"status":"skipped_robots","robots_state":state})
            print(json.dumps({"id":article["id"],"status":"skipped_robots"}),flush=True)
            continue
        response, record = get_once(url, folder, "article")
        print(json.dumps({"id":article["id"],"status":record.get("status"),"bytes":record.get("bytes"),"error":record.get("error")},ensure_ascii=False),flush=True)

if __name__ == "__main__":
    main()
