import re
import urllib.request
from pathlib import Path

RAW_SOURCE = (
    "https://raw.githubusercontent.com/jingjingge-art/youtube/main/全球直播电视监控iptvCAM-12-หาดตาแหวน.txt"
)

OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)

CATEGORY_FILES = {
    "国内": "国内.m3u",
    "国外": "国外.m3u",
    "新闻": "新闻.m3u",
    "电影": "电影.m3u",
    "综艺": "综艺.m3u",
    "体育": "体育.m3u",
    "少儿": "少儿.m3u",
    "纪录": "纪录.m3u",
    "监控": "监控.m3u",
    "其他": "其他.m3u",
}

DOMESTIC_KEYWORDS = [
    "cctv", "央视", "中国", "卫视", "北京", "上海", "广东", "深圳", "湖南",
    "江苏", "浙江", "山东", "重庆", "四川", "湖北", "安徽", "河南",
    "辽宁", "吉林", "黑龙江", "广西", "海南", "甘肃", "陕西", "云南",
    "贵州", "青海", "宁夏", "新疆", "内地", "港澳", "香港", "澳门", "台湾",
    "中国交通", "熊猫直播", "中央电视塔", "直播中国", "南京", "大湾区", "长江", "珠江"
]

FOREIGN_KEYWORDS = [
    "美国", "英国", "法国", "德国", "日本", "韩国", "加拿大", "澳大利亚",
    "国际", "world", "news", "bbc", "cnn", "fox", "nhk", "euronews",
    "sooplive", "印度", "泰国", "马来西亚", "越南", "捷克", "布拉格", "海外",
    "印尼", "菲律宾", "新加坡", "俄罗斯", "欧洲"
]

NEWS_KEYWORDS = [
    "新闻", "news", "时政", "直播", "综合", "资讯", "晚间", "今日", "民生",
    "广播", "社教", "都市", "政法", "财经", "第一财经", "教育"
]

MOVIE_KEYWORDS = [
    "电影", "movie", "film", "cinema", "影剧", "影院", "港剧", "电影频道",
    "华语影视", "美亚电影", "龙门飞甲", "让子弹飞", "寒战", "我不是药神",
    "电影八点档", "周星星", "高分动作", "功夫片"
]

VARIETY_KEYWORDS = [
    "综艺", "娱乐", "music", "音乐", "演唱会", "真人秀", "show", "谈话",
    "节目", "风采", "综艺节目", "音乐现场", "舞台"
]

SPORT_KEYWORDS = [
    "体育", "sport", "football", "篮球", "足球", "赛车", "电竞", "高尔夫",
    "纬来体育", "精品体育", "广东体育", "综艺体育", "冠军", "赛场"
]

CHILD_KEYWORDS = [
    "少儿", "卡通", "儿童", "kid", "kids", "动画", "七龙珠", "中华小当家",
    "EBS", "少儿频道", "儿童频道"
]

DOCUMENTARY_KEYWORDS = [
    "纪录", "documentary", "nature", "地理中国", "人与自然", "航拍",
    "飞碟", "自然传奇", "中国村庄", "地理"
]

SURVEILLANCE_KEYWORDS = [
    "监控", "cam", "camera", "摄像头", "安防", "摄像", "观光平台", "大桥",
    "海滩", "公园", "门口", "停车场", "监控直播", "NanjingNews", "南京",
    "上海1", "上海2", "上海3", "外滩", "北外滩", "陆家嘴", "魔都眼",
    "新街口", "鼓楼", "长江大桥", "南站", "小公园亭"
]

def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")

def split_urls(raw: str):
    urls = []
    for part in str(raw).split("#"):
        p = part.strip()
        if p.startswith("http://") or p.startswith("https://"):
            urls.append(p)
    return urls

def normalize_text(s: str) -> str:
    return (s or "").replace("\\r", "").replace("\\n", "").strip()

def parse_entries(text: str):
    entries = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") or line in {"#genre#", "#EXTM3U"}:
            continue

        if "," in line and not line.startswith(("http://", "https://")):
            name_part, url_part = line.split(",", 1)
            name = normalize_text(name_part)
            url_part = normalize_text(url_part)
            if not name or not url_part:
                continue
            urls = split_urls(url_part)
            if not urls:
                continue
            for url in urls:
                entries.append({"name": name, "url": url})
            continue
    return entries

def classify_name(name: str, url: str = "") -> str:
    text = f"{name} {url}".lower()

    if any(k.lower() in text for k in SURVEILLANCE_KEYWORDS):
        return "监控"
    if any(k.lower() in text for k in MOVIE_KEYWORDS):
        return "电影"
    if any(k.lower() in text for k in SPORT_KEYWORDS):
        return "体育"
    if any(k.lower() in text for k in CHILD_KEYWORDS):
        return "少儿"
    if any(k.lower() in text for k in DOCUMENTARY_KEYWORDS):
        return "纪录"
    if any(k.lower() in text for k in VARIETY_KEYWORDS):
        return "综艺"
    if any(k.lower() in text for k in NEWS_KEYWORDS):
        return "新闻"
    if any(k.lower() in text for k in FOREIGN_KEYWORDS):
        return "国外"
    if any(k.lower() in text for k in DOMESTIC_KEYWORDS):
        return "国内"
    return "其他"

def write_m3u(path: Path, items):
    lines = ["#EXTM3U"]
    seen = set()
    for item in items:
        name = normalize_text(item.get("name", ""))
        url = normalize_text(item.get("url", ""))
        if not name or not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        lines.append(f'#EXTINF:-1 tvg-name="{name}",{name}')
        lines.append(url)
    path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")

def main():
    try:
        source_text = fetch_text(RAW_SOURCE)
        print(f"Fetched source length: {len(source_text)}")
    except Exception as e:
        print(f"FETCH FAILED: {e}")
        raise

    entries = parse_entries(source_text)
    print(f"Parsed entries: {len(entries)}")

    buckets = {key: [] for key in CATEGORY_FILES}
    for entry in entries:
        name = normalize_text(entry.get("name", ""))
        url = normalize_text(entry.get("url", ""))
        category = classify_name(name, url)
        buckets.setdefault(category, []).append({"name": name, "url": url})

    for category, filename in CATEGORY_FILES.items():
        target = OUTPUT_DIR / filename
        write_m3u(target, buckets.get(category, []))
        print(f"{category}: {len(buckets.get(category, []))} 条 -> {target}")

    print("\\n已完成分类输出。")

if __name__ == "__main__":
    main()
