"""
run.py
Entry point — chạy toàn bộ pipeline và gửi email.
"""

import os
import sys

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from school_finder import find_schools
from report_builder import build_html_report
from email_sender import send_email


def main():
    # ── Đọc config từ biến môi trường (GitHub Secrets) ──────────────────────
    gmail_user      = os.environ.get("GMAIL_USER")
    gmail_password  = os.environ.get("GMAIL_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    
    # Kiểm tra biến môi trường bắt buộc
    missing = [k for k, v in {
        "GMAIL_USER": gmail_user,
        "GMAIL_PASSWORD": gmail_password,
        "RECIPIENT_EMAIL": recipient_email,
    }.items() if not v]
    
    if missing:
        print(f"[ERROR] Thiếu biến môi trường: {', '.join(missing)}")
        print("Hãy thêm các biến này vào GitHub Secrets hoặc file .env")
        sys.exit(1)
    
    print("=" * 60)
    print(" SCHOOL FINDER — Tìm trường học mới khởi công")
    print("=" * 60)
    
    # ── Bước 1: Tìm trường ───────────────────────────────────────────────────
    schools = find_schools(max_fetch=25)
    
    # ── Bước 2: Tạo báo cáo HTML ─────────────────────────────────────────────
    html = build_html_report(schools)
    
    # Lưu file HTML để debug (tuỳ chọn, sẽ thấy trong GitHub Actions artifact)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✓ Đã lưu report.html")
    
    # ── Bước 3: Gửi email ────────────────────────────────────────────────────
    send_email(
        sender_email=gmail_user,
        app_password=gmail_password,
        recipient_email=recipient_email,
        html_content=html,
        school_count=len(schools),
    )
    
    print("=" * 60)
    print(f" HOÀN THÀNH — Tìm được {len(schools)} trường mới")
    print("=" * 60)


if __name__ == "__main__":
    main()
