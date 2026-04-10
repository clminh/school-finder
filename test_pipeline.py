"""Test chạy pipeline đầy đủ, không gửi email — chỉ lưu report.html"""
import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from school_finder import find_schools
from report_builder import build_html_report

# Chỉ fetch 5 bài để test nhanh
schools = find_schools(max_fetch=5)

print(f"\n{'='*50}")
print(f"KẾT QUẢ: {len(schools)} trường")
print('='*50)
for s in schools:
    print(f"[{s['potential']}] {s['title'][:60]}")
    print(f"   Tỉnh: {s['province']} | Đầu tư: {s['investment']}")

html = build_html_report(schools)
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n✓ Saved report.html — mở file này trong browser để xem email preview")
