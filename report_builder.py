"""
report_builder.py
Tạo HTML email báo cáo đẹp, tương thích Gmail/Outlook.
"""

from datetime import datetime


def _badge(text: str, color: str) -> str:
    return (
        f'<span style="'
        f'background:{color};color:#fff;padding:3px 10px;'
        f'border-radius:12px;font-size:12px;font-weight:700;'
        f'white-space:nowrap;">{text}</span>'
    )


def build_html_report(schools: list[dict]) -> str:
    """Tạo HTML email hoàn chỉnh từ danh sách trường."""
    
    today = datetime.now().strftime("%d/%m/%Y")
    total = len(schools)
    
    # Thống kê nhanh
    counts = {"★ Có sân thể thao": 0, "Tiềm năng cao": 0, "Tiếp cận": 0}
    for s in schools:
        key = s.get("potential", "Tiếp cận")
        counts[key] = counts.get(key, 0) + 1
    
    # ── Rows bảng ────────────────────────────────────────────────────────────
    rows_html = ""
    for i, s in enumerate(schools):
        bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        
        # Snippet — hiển thị nội dung bài
        snippet = s.get("snippet", "")
        snippet_html = ""
        if snippet:
            snippet_html = f'<div style="font-size:12px;color:#555;margin-top:6px;line-height:1.5;border-top:1px solid #f0f0f0;padding-top:6px;">{snippet}</div>'
        
        # Chất lượng nội dung
        content_len = s.get("content_length", 0)
        quality = "✅" if content_len > 300 else ("⚠️" if content_len > 50 else "❌")
        
        # Tên trường (nếu có)
        school_name = s.get("school_name", "")
        name_html = f'<div style="font-size:11px;color:#27ae60;font-weight:600;margin-top:2px;">🏫 {school_name}</div>' if school_name else ""
        
        title_link = (
            f'<a href="{s["url"]}" target="_blank" '
            f'style="color:#1a73e8;text-decoration:none;font-weight:600;font-size:13px;">'
            f'{s["title"]}</a>'
        )
        
        # Địa chỉ: Tỉnh + Huyện
        loc_parts = [s.get("province", "Không rõ")]
        district = s.get("district", "")
        if district and district not in loc_parts[0]:
            loc_parts.append(f'<span style="font-size:11px;color:#888;">{district}</span>')
        location_html = "<br>".join(loc_parts)
        
        # Quy mô: phòng học + diện tích
        qm_parts = []
        if s.get("classrooms"): qm_parts.append(s["classrooms"])
        if s.get("area"): qm_parts.append(s["area"])
        qm_html = "<br>".join(qm_parts) if qm_parts else '<span style="color:#ccc">—</span>'
        
        # Hoàn thành
        completion = s.get("completion", "") or '<span style="color:#ccc">—</span>'
        
        # Đầu tư
        inv = s.get("investment", "Chưa rõ")
        inv_color = "#27ae60" if inv != "Chưa rõ" else "#bbb"
        inv_html = f'<span style="color:{inv_color};font-weight:600;">{inv}</span>'
        
        rows_html += f"""
        <tr style="background:{bg};">
            <td style="padding:12px 10px;border-bottom:1px solid #eee;vertical-align:top;">
                {title_link}
                {name_html}
                {snippet_html}
                <div style="font-size:10px;color:#aaa;margin-top:4px;">Nội dung {quality} ({content_len} ký tự) • {s.get("source","")}</div>
            </td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;white-space:nowrap;color:#333;font-size:13px;">{s.get("level","?")}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;font-size:12px;">{location_html}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;font-size:13px;">{inv_html}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;font-size:12px;color:#555;">{qm_html}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;font-size:12px;color:#555;">{completion}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;white-space:nowrap;color:#555;font-size:12px;">{s.get("published","?")}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;">{_badge(s["potential"], s["potential_color"])}</td>
        </tr>"""
    
    if not rows_html:
        rows_html = """
        <tr><td colspan="8" style="padding:30px;text-align:center;color:#888;font-size:14px;">
            Không tìm thấy trường học mới trong tuần này.
        </td></tr>"""
    
    # ── Stat cards ───────────────────────────────────────────────────────────
    stat_cards = f"""
    <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:24px;">
      <tr>
        <td style="padding:4px;">
          <div style="background:#1a7f3c;border-radius:10px;padding:16px 20px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#fff;">{counts.get("★ Có sân thể thao",0)}</div>
            <div style="font-size:11px;color:#b7f1cc;margin-top:2px;">CÓ SÂN THỂ THAO ★</div>
          </div>
        </td>
        <td style="padding:4px;">
          <div style="background:#27ae60;border-radius:10px;padding:16px 20px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#fff;">{counts.get("Tiềm năng cao",0)}</div>
            <div style="font-size:11px;color:#c8f7d6;margin-top:2px;">TIỀM NĂNG CAO</div>
          </div>
        </td>
        <td style="padding:4px;">
          <div style="background:#e67e22;border-radius:10px;padding:16px 20px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#fff;">{counts.get("Tiếp cận",0)}</div>
            <div style="font-size:11px;color:#fde8c8;margin-top:2px;">TIẾp CẬN</div>
          </div>
        </td>
        <td style="padding:4px;">
          <div style="background:#2c3e50;border-radius:10px;padding:16px 20px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#fff;">{total}</div>
            <div style="font-size:11px;color:#bdc3c7;margin-top:2px;">TỔNG Kử</div>
          </div>
        </td>
      </tr>
    </table>"""
    
    # ── Potent advisory text ─────────────────────────────────────────────────
    advisory = (
        "⚽ <b>RẤT CAO</b>: Bài báo đề cập sân thể thao/sân bóng — liên hệ ngay.<br>"
        "🟢 <b>CAO</b>: Trường THCS/THPT — tiếp cận sớm để giới thiệu sân bóng.<br>"
        "🟠 <b>TRUNG BÌNH</b>: Trường tiểu học — có thể chào thầu sân mini.<br>"
        "🔴 <b>THẤP</b>: Trường mầm non — ít khả năng cần sân bóng."
    )
    
    # ── Full HTML ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Báo cáo trường học mới — {today}</title>
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,Helvetica,sans-serif;">
  <table cellpadding="0" cellspacing="0" width="100%" style="background:#f0f2f5;padding:20px 0;">
    <tr>
      <td align="center">
        <table cellpadding="0" cellspacing="0" width="900" style="max-width:900px;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10);">
          
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a3c6e 0%,#2980b9 100%);padding:32px 40px;">
              <div style="font-size:26px;font-weight:800;color:#fff;">⚽ Báo Cáo Trường Học Mới Khởi Công</div>
              <div style="font-size:14px;color:#aad4f5;margin-top:6px;">Tự động cập nhật — Tuần ngày {today}</div>
              <div style="font-size:13px;color:#aad4f5;margin-top:2px;">Tìm cơ hội chào thầu xây dựng sân bóng, sân thể thao cho trường học</div>
            </td>
          </tr>
          
          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              
              <!-- Stat cards -->
              {stat_cards}
              
              <!-- Legend -->
              <div style="background:#f8f9fa;border-left:4px solid #2980b9;border-radius:4px;padding:12px 16px;margin-bottom:24px;font-size:13px;color:#555;line-height:1.8;">
                {advisory}
              </div>
              
              <!-- Table -->
              <div style="overflow-x:auto;">
              <table cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;font-size:14px;">
                <thead>
                  <tr style="background:#2c3e50;color:#fff;">
                    <th style="padding:12px 10px;text-align:left;font-weight:700;width:35%;">Tiêu đề / Trích dẫn</th>
                    <th style="padding:12px 10px;text-align:center;font-weight:700;">Địa điểm</th>
                    <th style="padding:12px 10px;text-align:center;font-weight:700;">Đầu tư</th>
                    <th style="padding:12px 10px;text-align:center;font-weight:700;">Quy mô</th>
                    <th style="padding:12px 10px;text-align:center;font-weight:700;">Hoàn thành</th>
                    <th style="padding:12px 10px;text-align:center;font-weight:700;">Ngày đăng</th>
                    <th style="padding:12px 10px;text-align:center;font-weight:700;">Tiềm năng sân bóng</th>
                  </tr>
                </thead>
                <tbody>
                  {rows_html}
                </tbody>
              </table>
              </div>
              
              <!-- Footer note -->
              <div style="margin-top:24px;font-size:12px;color:#999;text-align:center;">
                Báo cáo được tạo tự động bởi School Finder Bot • Chạy mỗi thứ Tư lúc 10:00 SA<br>
                Nguồn: Google News RSS ({len(schools)} kết quả mới trong 14 ngày qua)
              </div>
            </td>
          </tr>
          
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    
    return html
