from school_finder import fetch_rss_entries

keyword = "khởi công xây dựng trường học 2025"
entries = fetch_rss_entries(keyword, max_age_days=60)
print(f"Tìm được {len(entries)} kết quả cho: {keyword}")
for e in entries[:8]:
    pub = e['published']
    title = e['title'][:80]
    source = e['source']
    print(f"  [{pub}] {title} ({source})")
