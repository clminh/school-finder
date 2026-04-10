# ⚽ School Finder — Tìm Trường Học Mới Khởi Công

Bot tự động chạy mỗi **thứ Hai lúc 8:00 SA**, crawl 15 từ khoá trên Google News RSS,
tổng hợp thông tin trường học mới khởi công/khánh thành, và gửi báo cáo HTML về email.

**Không cần chạy tay. Không tốn VPS. Hoàn toàn miễn phí.**

---

## Cách hoạt động

```
Google News RSS (15 keyword) → Filter 14 ngày → Dedup → Fetch bài → Parse → Email đẹp
```

- **Không bị block**: Dùng RSS chính thức của Google, không scrape trực tiếp
- **Không trùng lặp**: Lưu URL đã báo cáo vào `seen_urls.json`, tuần sau không báo lại
- **Đánh giá tự động**: Phân loại RẤT CAO / CAO / TRUNG BÌNH / THẤP theo cấp trường + đầu tư

---

## Setup (10 phút)

### Bước 1: Tạo Gmail App Password

> Bắt buộc — Google không cho dùng mật khẩu thường qua SMTP từ năm 2022.

1. Vào [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Bật **2-Step Verification** (nếu chưa bật)
3. Vào [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Tạo App Password mới → chọn **Mail** + **Other (custom name)** → đặt tên `School Finder`
5. Copy 16 ký tự được tạo (dạng: `xxxx xxxx xxxx xxxx`)

### Bước 2: Tạo GitHub Repository mới

```bash
# Tại thư mục school-finder này
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Tạo repo mới trên github.com rồi push lên
git remote add origin https://github.com/TEN_BAN/school-finder.git
git push -u origin main
```

> Có thể để **Private repo** — miễn phí và an toàn hơn.

### Bước 3: Thêm GitHub Secrets

Vào repo GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Thêm 3 secrets sau:

| Tên secret | Giá trị |
|---|---|
| `GMAIL_USER` | Email Gmail của bạn (vd: `yourname@gmail.com`) |
| `GMAIL_PASSWORD` | 16 ký tự App Password ở bước 1 |
| `RECIPIENT_EMAIL` | Email nhận báo cáo (có thể khác Gmail gửi) |

### Bước 4: Chạy thử ngay

1. Vào tab **Actions** trên GitHub
2. Click vào workflow **Weekly School Finder Report**
3. Click **Run workflow** → **Run workflow** (màu xanh)
4. Chờ ~3-5 phút → Kiểm tra inbox

---

## Cấu trúc project

```
school-finder/
├── school_finder.py      # Core: crawl RSS, fetch bài, parse thông tin
├── report_builder.py     # Tạo email HTML đẹp
├── email_sender.py       # Gửi qua Gmail SMTP
├── run.py                # Entry point (đọc env vars, gọi pipeline)
├── requirements.txt      # Python dependencies
├── seen_urls.json        # Cache URL đã báo cáo (tự tạo sau lần đầu)
└── .github/
    └── workflows/
        └── weekly.yml    # GitHub Actions schedule
```

---

## Tuỳ chỉnh

### Thêm/bớt từ khoá
Sửa danh sách `KEYWORDS` trong `school_finder.py`.

### Đổi lịch chạy
Sửa dòng `cron` trong `.github/workflows/weekly.yml`:
```yaml
# Mỗi thứ Hai 8h sáng (UTC+7)
- cron: "0 1 * * 1"

# Mỗi thứ Hai và thứ Năm
- cron: "0 1 * * 1,4"
```

### Tăng số bài đọc
Sửa `max_fetch=25` trong `run.py` → `find_schools(max_fetch=40)`.

---

## Đọc kết quả email

| Badge | Ý nghĩa |
|---|---|
| ⚽ **RẤT CAO** | Bài báo đề cập sân bóng/thể thao — liên hệ **ngay** |
| 🟢 **CAO** | Trường THCS/THPT — tiếp cận sớm |
| 🟠 **TRUNG BÌNH** | Trường tiểu học — chào thầu sân mini |
| 🔴 **THẤP** | Trường mầm non — ít cơ hội |

---

## Chi phí

| Hạng mục | Chi phí |
|---|---|
| GitHub Actions | **Miễn phí** (2,000 phút/tháng, script chạy ~5 phút) |
| Google News RSS | **Miễn phí** |
| Gmail SMTP | **Miễn phí** |
| **Tổng** | **$0/tháng** |
