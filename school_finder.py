"""
school_finder.py
Crawl Google News RSS để tìm trường học mới khởi công, khánh thành tại Việt Nam.
"""

import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import feedparser
import requests
import trafilatura
import json
import re
import time
import random
import hashlib
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

# ── 1. Từ khoá tìm kiếm ────────────────────────────────────────────────────

KEYWORDS = [
    # Khởi công
    "khởi công xây dựng trường học 2025",
    "khởi công xây dựng trường 2026",
    "lễ khởi công trường học mới",
    "động thổ xây dựng trường học",
    # Kánh thành / bàn giao (vừa xây xong, sân có thể chưa có)
    "khánh thành trường học mới xây",
    "bàn giao trường học mới xây dựng",
    "đưa vào sử dụng trường học mới",
    # Đầu tư / quy mô lớn
    "đầu tư xây dựng trường học mới tỷ đồng",
    "UBND xây trường học mới tỷ đồng",
    "phê duyệt dự án xây dựng trường học",
    "trường học chuẩn quốc gia mới xây dựng",
    # Sân bóng / thể thao trường học (mục tiêu chính)
    "xây mới trường học sân thể thao",
    "sân bóng trường học mới xây",
    "sân thể thao trường học khởi công",
    "khu thể thao trường học xây mới",
    # Quảng cáo đấu thầu
    "gói thầu xây dựng trường học",
    "mời thầu xây dựng trường học",
    # Nội trú / liên cấp (quy mô lớn, nhiều có sân)
    "khởi công trường nội trú liên cấp",
    "xây dựng trường phổ thông nội trú",
    # Cơ sở vật chất
    "xây mới cơ sở vật chất trường học",
    "nâng cấp đầu tư trường học tỷ đồng 2025",
]

# ── 2. Danh sách 63 tỉnh/thành ────────────────────────────────────────────

PROVINCES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu",
    "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cao Bằng", "Đắk Lắk", "Đắk Nông",
    "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang",
    "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hậu Giang", "Hòa Bình",
    "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định",
    "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên",
    "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị",
    "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên",
    "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
    # Thành phố trực thuộc TW
    "Hà Nội", "TP HCM", "TP.HCM", "Thành phố Hồ Chí Minh",
    "Đà Nẵng", "Hải Phòng", "Cần Thơ",
]

# Từ khoá nhận diện bài có đề cập sân bóng/thể thao (ưu tiên cao nhất)
SPORTS_SIGNALS = [
    "sân bóng", "sân thể thao", "khu thể thao", "sân vận động",
    "nhà thi đấu", "sân tập", "thể dục thể thao", "công trình thể thao",
]

# Từ khoá nhận diện trường lớn (ưu tiên cao)
LARGE_SCHOOL_SIGNALS = [
    "nội trú", "liên cấp", "chuẩn quốc gia", "trọng điểm",
    "ký túc xá", "đa năng",
]

SEEN_URLS_FILE = "seen_urls.json"

# ── 4. Helpers ────────────────────────────────────────────────────────────

def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def load_seen_urls() -> set:
    if os.path.exists(SEEN_URLS_FILE):
        with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_urls(seen: set):
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


def detect_level(text: str) -> str:
    text_lower = text.lower()
    for level, kws in LEVEL_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            return level
    return "Không rõ"


def detect_province(text: str) -> str:
    """Tìm tỉnh/thành trong văn bản, ưu tiên khớp dài hơn."""
    text_lower = text.lower()
    found = []
    for province in PROVINCES:
        if province.lower() in text_lower:
            found.append(province)
    if not found:
        return "Không rõ"
    # Trả về tên dài nhất (tránh "Hà Nam" match khi có "Hà Nội")
    return max(found, key=len)


def detect_district(text: str) -> str:
    """Tìm quận/huyện trong văn bản."""
    patterns = [
        r'(?:huyện|quận|thị xã|thành phố)\s+([\w\s]+?)(?:\s*,|\s*tỉnh|\s*tp|$)',
        r'(?:xã|phường|thị trấn)\s+[\w\s]+,\s+(?:huyện|quận)\s+([\w\s]+?)(?:\s*,|$)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            district = m.group(1).strip()
            if len(district) < 30:  # Tránh match quá dài
                return district
    return ""


def extract_school_name(title: str, content: str) -> str:
    """Cố gắng trích xuất tên trường từ tiêu đề hoặc nội dung."""
    # Pattern: "Trường [cấp] [Tên]" hoặc "[Tên] Trường [cấp]"
    patterns = [
        r'trường\s+(?:tiểu học|thcs|thpt|mầm non|phổ thông|trung học)[\s]+([\w\s]+?)(?:\s*[,\-–]|\s*tại|\s*ở|$)',
        r'(?:xây dựng|khởi công|khánh thành)\s+trường\s+([\w\s]+?)(?:\s*[,\-–]|\s*tại|\s*ở|$)',
    ]
    for text in [title, content[:500]]:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                # Loại bỏ tên quá ngắn hoặc quá dài
                if 3 < len(name) < 60:
                    return name
    return ""


def extract_investment(text: str) -> str:
    """Trích xuất số tiền đầu tư từ nội dung bài."""
    # Xử lý nhiều format: "120 tỷ", "120,5 tỷ", "1.200 tỷ", "120 tỷ đồng"
    patterns = [
        r'(?:tổng mức đầu tư|tổng đầu tư|kinh phí|vốn đầu tư)[^\d]*(\d{1,4}(?:[,\.]\d{1,3})?)\s*tỷ',
        r'(\d{1,4}(?:[,\.]\d{1,3})?)\s*tỷ\s*đồng',
        r'(\d{1,4}(?:[,\.]\d{1,3})?)\s*tỷ',
    ]
    amounts = []
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for m in matches:
            try:
                val = float(m.replace(".", "").replace(",", "."))
                if 0.5 <= val <= 5000:  # Lọc giá trị hợp lý (0.5 - 5000 tỷ)
                    amounts.append(val)
            except ValueError:
                pass
        if amounts:
            break
    if amounts:
        best = max(amounts)  # Lấy giá trị lớn nhất = tổng đầu tư
        return f"{best:g} tỷ đồng"
    return "Chưa rõ"


def extract_classrooms(text: str) -> str:
    """Trích xuất số phòng học."""
    patterns = [
        r'(\d+)\s*phòng\s*học',
        r'(\d+)\s*phòng\s*(?:chức năng|học tập|bộ môn)',
        r'quy mô\s*(\d+)\s*lớp',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} phòng học"
    return ""


def extract_area(text: str) -> str:
    """Trích xuất diện tích."""
    m = re.search(r'(\d{3,6}(?:[,\.]\d+)?)\s*m[²2]', text)
    if m:
        return f"{m.group(1)} m²"
    return ""


def extract_completion_date(text: str) -> str:
    """Trích xuất thời gian dự kiến hoàn thành."""
    patterns = [
        r'(?:hoàn thành|hoàn công|bàn giao)(?:[^\d]*)(\d{1,2}/\d{4}|\d{4}|tháng\s*\d+\s*năm\s*\d{4})',
        r'dự kiến\s+(?:hoàn thành|đưa vào sử dụng)[^\d]*(\d{4})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def assess_potential(text: str, investment_str: str) -> tuple[str, str]:
    """
    Đánh giá tiềm năng chào thầu sân bóng — không phân cấp trường.
    Trả về (nhãn, màu hex).
    """
    text_lower = text.lower()
    
    # Cao nhất: bài đề cập trực tiếp sân thể thao/sân bóng
    if any(kw in text_lower for kw in SPORTS_SIGNALS):
        return "★ Có sân thể thao", "#1a7f3c"
    
    # Parse giá trị đầu tư
    inv = 0.0
    m = re.search(r"([\d,\.]+)\s*tỷ", investment_str)
    if m:
        try:
            inv = float(m.group(1).replace(".", "").replace(",", "."))
        except ValueError:
            pass
    
    # Cao: trường lớn (nội trú, liên cấp, chuẩn quốc gia) hoặc đầu tư >30 tỷ
    has_large = any(kw in text_lower for kw in LARGE_SCHOOL_SIGNALS)
    if has_large or inv >= 30:
        return "Tiềm năng cao", "#27ae60"
    
    # Mặc định: đáng tiếp cận (mọi trường mới xây đều có cơ hội)
    return "Tiếp cận", "#e67e22"


# ── 5. RSS fetch ──────────────────────────────────────────────────────────

def fetch_rss_entries(keyword: str, max_age_days: int = 14) -> list[dict]:
    """Lấy kết quả Google News RSS cho một từ khoá."""
    encoded = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=vi&gl=VN&ceid=VN:vi"
    
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SchoolFinderBot/1.0)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"  [RSS ERROR] {keyword}: {e}")
        return []
    
    entries = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    
    for entry in feed.entries:
        try:
            pub_date = parsedate_to_datetime(entry.get("published", ""))
            if pub_date < cutoff:
                continue
        except Exception:
            pub_date = datetime.now(timezone.utc)
        
        # Lấy cả summary từ RSS (thường có ~1-2 câu mô tả)
        summary_raw = entry.get("summary", "")
        summary = BeautifulSoup(summary_raw, "lxml").get_text(" ", strip=True) if summary_raw else ""
        
        entries.append({
            "title":    entry.get("title", ""),
            "url":      entry.get("link", ""),
            "published": pub_date.strftime("%d/%m/%Y"),
            "source":   entry.get("source", {}).get("title", ""),
            "summary":  summary,
        })
    
    return entries

# ── 6. Article fetch & parse ──────────────────────────────────────────────

def resolve_google_news_url(url: str) -> str:
    """Resolve Google News redirect URL về URL bài báo gốc."""
    if "news.google.com" not in url:
        return url
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        # Google News thường redirect qua 1-2 bước
        resp = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        if resp.url != url:
            return resp.url
        # Thử GET nếu HEAD không redirect
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        return resp.url
    except Exception:
        return url


def fetch_article_content(url: str, rss_summary: str = "") -> tuple[str, str]:
    """
    Tải và trích xuất nội dung văn bản từ bài báo.
    Trả về (nội_dung, url_thực_tế).
    Thứ tự ưu tiên: trafilatura → BeautifulSoup → RSS summary.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    real_url = url
    raw_html = ""
    
    try:
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        real_url = resp.url
        raw_html = resp.text
    except Exception as e:
        print(f"    [HTTP ERROR] {e}")
        return rss_summary, url
    
    # Thử trafilatura trước (tốt nhất)
    content = trafilatura.extract(
        raw_html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        favor_recall=True,  # Ưu tiên lấy nhiều nội dung hơn là chuẩn xác
    )
    if content and len(content) > 100:
        return content, real_url
    
    # Fallback: BeautifulSoup lấy paragraphs
    try:
        soup = BeautifulSoup(raw_html, "lxml")
        # Xoá script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        paragraphs = soup.find_all("p")
        bs_text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
        if bs_text and len(bs_text) > 100:
            return bs_text, real_url
    except Exception:
        pass
    
    # Fallback cuối: RSS summary
    if rss_summary:
        return rss_summary, real_url
    
    return "", real_url

# ── 7. Main function ──────────────────────────────────────────────────────

def find_schools(max_fetch: int = 40) -> list[dict]:
    """
    Chạy toàn bộ pipeline: RSS → dedup → fetch → parse.
    Trả về list các trường học tìm được (mới, chưa báo cáo trước đó).
    """
    seen_urls = load_seen_urls()
    new_seen: set = set()
    
    # Bước 1: Thu thập entries từ tất cả keyword
    all_entries: dict[str, dict] = {}  # url_hash -> entry
    
    for i, keyword in enumerate(KEYWORDS):
        print(f"[{i+1}/{len(KEYWORDS)}] Searching: {keyword}")
        entries = fetch_rss_entries(keyword)
        for e in entries:
            h = url_hash(e["url"])
            if h not in all_entries:
                all_entries[h] = e
        time.sleep(random.uniform(0.5, 1.5))
    
    print(f"\nTổng entries unique: {len(all_entries)}")
    
    # Bước 2: Lọc đã báo cáo tuần trước
    new_entries = [
        (h, e) for h, e in all_entries.items()
        if h not in seen_urls
    ]
    
    print(f"Entries mới (chưa báo cáo): {len(new_entries)}")
    
    if not new_entries:
        return []
    
    # Bước 3: Fetch nội dung bài và parse (giới hạn max_fetch)
    schools: list[dict] = []
    fetch_count = 0
    
    for h, entry in new_entries:
        if fetch_count >= max_fetch:
            break
        
        new_seen.add(h)
        title = entry["title"]
        url = entry["url"]
        rss_summary = entry.get("summary", "")
        
        # Lọc nhanh theo title — chỉ bỏ qua bài rõ ràng không liên quan
        title_lower = title.lower()
        # Giữ lại mọi bài có nhắc đến trường hoặc xây dựng
        skip_terms = ["video", "kết quả", "xếp loại", "tuyển sinh", "học bạ", "thi cử"]
        if any(t in title_lower for t in skip_terms):
            continue
        relevant_terms = ["trường", "khởi công", "khánh thành", "bàn giao", "xây dựng",
                          "giáo dục", "học sinh", "phòng học", "công trình", "sân"]
        if not any(t in title_lower for t in relevant_terms):
            continue
        
        print(f"  Fetching: {title[:70]}...")
        content, real_url = fetch_article_content(url, rss_summary)
        fetch_count += 1
        
        # Fallback cuối: dùng title làm content
        if not content:
            content = title
        
        combined_text = title + " " + content
        
        province   = detect_province(combined_text)
        district   = detect_district(combined_text)
        investment = extract_investment(combined_text)
        classrooms = extract_classrooms(combined_text)
        area       = extract_area(combined_text)
        completion = extract_completion_date(combined_text)
        school_name = extract_school_name(title, content)
        potential, potential_color = assess_potential(combined_text, investment)
        
        # Tuyệt đối bỏ qua bài không liên quan gì đến cơ hội sân bóng
        # (gữ hết sau khi đã filter nhẹ trước)
        
        # Tạo snippet gọn — ưu tiên đoạn đầu bài có thông tin
        snippet = ""
        if content and len(content) > 50:
            # Lấy 2 câu đầu có ý nghĩa
            sentences = [s.strip() for s in re.split(r'[.!?]', content) if len(s.strip()) > 30]
            snippet = ". ".join(sentences[:2])
            if len(snippet) > 280:
                snippet = snippet[:280] + "…"
        
        schools.append({
            "title":          title,
            "school_name":    school_name,
            "url":            real_url or url,
            "published":      entry["published"],
            "source":         entry["source"],
            "province":       province,
            "district":       district,
            "investment":     investment,
            "classrooms":     classrooms,
            "area":           area,
            "completion":     completion,
            "potential":      potential,
            "potential_color":potential_color,
            "snippet":        snippet,
            "content_length": len(content),
        })
        
        time.sleep(random.uniform(1.0, 2.0))
    
    # Bước 4: Lưu seen URLs (cộng dồn)
    updated_seen = seen_urls | new_seen
    save_seen_urls(updated_seen)
    
    # Sắp xếp: có sân thể thao lên trước, rồi đến tiềm năng cao, cuối là tiếp cận
    priority = {"★ Có sân thể thao": 0, "Tiềm năng cao": 1, "Tiếp cận": 2}
    schools.sort(key=lambda s: priority.get(s["potential"], 9))
    
    print(f"\n✓ Tìm được {len(schools)} trường mới.")
    return schools
