"""
email_sender.py
Gửi HTML email qua Gmail SMTP.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    html_content: str,
    school_count: int = 0,
) -> None:
    """
    Gửi email báo cáo qua Gmail SMTP (TLS port 587).
    
    Args:
        sender_email:    Gmail của bạn (ví dụ: yourname@gmail.com)
        app_password:    Gmail App Password (16 ký tự, không phải mật khẩu thường)
        recipient_email: Email nhận báo cáo
        html_content:    Nội dung HTML đã build sẵn
        school_count:    Số trường tìm được (để ghi vào subject)
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    if school_count == 0:
        subject = f"[School Finder] Không có trường mới tuần này — {today}"
    else:
        subject = f"[School Finder] {school_count} trường mới khởi công — {today} ⚽"
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"School Finder Bot <{sender_email}>"
    msg["To"]      = recipient_email
    
    # Plain text fallback
    plain_text = (
        f"Báo cáo trường học mới — {today}\n"
        f"Tìm được {school_count} trường mới trong 14 ngày qua.\n"
        "Mở email bằng HTML để xem bảng đầy đủ.\n"
    )
    
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    print(f"Đang gửi email tới {recipient_email}...")
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
    
    print(f"✓ Email đã gửi thành công: {subject}")
