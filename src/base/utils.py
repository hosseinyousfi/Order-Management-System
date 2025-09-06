from django.http import HttpResponse
import csv
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import CMYKColor
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from django.http import HttpResponse
from django.conf import settings
from django.utils.html import format_html
from django.contrib import messages
from django.contrib import messages
from django.shortcuts import redirect
# Import for Farsi/Arabic RTL support
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display
from num2fawords import words
from collections import defaultdict
from jdatetime import datetime
from base.models import Factor



# Export CSV Action
def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    response.write(u'\ufeff'.encode('utf8')) # BOM for UTF-8 in Excel

    writer = csv.writer(response)
    
    # Persian Headers
    writer.writerow([
        'عنوان سفارش',
        'توضیحات',
        'نام مشتری',
        'نام شرکت',
        'قیمت واحد',
        'قیمت کل',
        'مبلغ پرداختی',
        'پرداخت باقی‌مانده',
        'وضعیت سفارش',
        'تاریخ ایجاد'
    ])

    for order in queryset:
        customer_info = order.company_name.name if order.company_name else order.customer_name
        writer.writerow([
            order.title,
            order.description,
            order.customer_name,
            customer_info,
            order.unit_cost,
            order.total_cost,
            order.payment,
            order.remaining_payment,
            'تکمیل شده' if order.order_status else 'در حال انتظار',
            order.order_date.strftime('%Y/%m/%d %H:%M:%S') # Format Jalali date for CSV
        ])
    return response

export_orders_csv.short_description = "خروجی CSV از سفارشات انتخاب شده"

# --- Farsi Font & Reshaper Configuration ---
# مسیر دقیق فایل فونت TTF شما.
# مطمئن شوید که IRANSansX-Black.ttf در پوشه static/fonts/ پروژه شما وجود دارد.
FONT_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'IRANSansX-Medium.ttf')

global_reshaper = None
global_font_registered = False

try:
    if not os.path.isfile(FONT_PATH):
        raise FileNotFoundError(f"فایل فونت در مسیر {FONT_PATH} یافت نشد.")

    if 'IranSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('IranSans', FONT_PATH))
        global_font_registered = True
        print(f"فونت 'IranSans' با موفقیت از مسیر {FONT_PATH} ثبت شد.")
    else:
        print("فونت 'IranSans' قبلاً ثبت شده بود.")

    reshaper_config = {
        'delete_harakat': False,
        'support_ligatures': True,
        'supported_ligatures': { 'LAM_ALEF': True },
        'shift_harakat_position': True
    }
    global_reshaper = ArabicReshaper(reshaper_config)

except FileNotFoundError as e:
    print(f"خطا در بارگذاری فونت: {e}")
    global_font_registered = False
    messages.error(None, format_html(f"خطا در بارگذاری فونت برای PDF: <b>{e}</b> لطفاً مطمئن شوید فایل فونت در مسیر صحیح قرار دارد."))
except Exception as e:
    print(f"خطای ناشناخته در ثبت فونت یا تنظیم ریشیپر: {e}")
    global_font_registered = False
    messages.error(None, format_html(f"خطای ناشناخته در آماده‌سازی PDF: <b>{e}</b>"))


def generate_safe_filename(factor_ids):
    date_str = datetime.now().strftime('%Y-%m-%d')
    id_str = "_".join(str(fid) for fid in factor_ids)
    return f"factor_{id_str}_{date_str}.pdf"


def get_farsi_text(text):
    if not global_font_registered or global_reshaper is None:
        return str(text) if text is not None else ''

    if text is None:
        return ''
    
    text = str(text)
    if not text.strip():
        return ''

    text = convert_to_farsi_numbers(text)

    reshaped_text = global_reshaper.reshape(text)
    return get_display(reshaped_text)


def convert_to_farsi_numbers(text):
    en_to_fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return text.translate(en_to_fa)


# --- Helper to draw CMYK circles ---
def draw_cmyk_circles(canvas_obj, x, y, radius):
    colors_cmyk = [
        CMYKColor(1, 0, 0, 0),   # Cyan
        CMYKColor(0, 1, 0, 0),   # Magenta
        CMYKColor(0, 0, 1, 0),   # Yellow
        CMYKColor(0, 0, 0, 1)    # Black
    ]
    spacing = radius * 2.2 # فاصله بین دایره‌ها

    for i, cmyk_color in enumerate(colors_cmyk):
        canvas_obj.setFillColor(cmyk_color)
        canvas_obj.circle(x + i * spacing, y, radius, fill=1) # fill=1 یعنی پر کردن دایره


# --- Django Admin Action ---

def generate_factor_pdf(modeladmin, request, queryset):
    if not global_font_registered:
        messages.error(request, "تولید PDF ناموفق: فونت فارسی به درستی بارگذاری نشده است. لطفاً گزارشات سرور را بررسی کنید.")
        return HttpResponse("خطا: فونت فارسی بارگذاری نشده است.", status=500)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    grouped_orders = defaultdict(list)
    
    # استایل‌های ReportLab Platypus
    styles = getSampleStyleSheet()
    # استایل برای پاراگراف‌های فارسی (به ویژه در جدول و توضیحات فوتر)
    farsi_paragraph_style_table = ParagraphStyle(name='FarsiParagraphTable',
                                                fontName='IranSans',
                                                fontSize=9, # کمی کوچکتر برای جدول
                                                alignment=TA_CENTER,
                                                leading=11)


    for order in queryset:
        key = order.company_name or order.customer_name or 'نامشخص'
        grouped_orders[key].append(order)

    # بررسی تعداد سفارش‌ها برای هر مشتری

    for key, orders in grouped_orders.items():
        if len(orders) > 16:
            messages.error(request, f"مشتری '{key}' بیش از ۱۶ سفارش دارد و نمی‌توان فاکتور ساخت.")
            return redirect(request.get_full_path())
        
    n = 0
    factor_ids = []
    for customer, orders in grouped_orders.items():
        
        if n != 0:
            p.showPage()
        n += 1
        
        # تنظیم فونت اصلی صفحه
        p.setFont("IranSans", 10)

        # --- ناحیه هدر ---
        header_y_start = height - 20*mm
        # فاکتور غیرقابل تغییر
        p.setFont("IranSans", 10)

        # کانون تبلیغاتی... (عنوان اصلی)
        p.setFont("IranSans", 16)
        main_title_text = get_farsi_text("کانون تبلیغاتی فرهنگی هنری")
        text_width = p.stringWidth(main_title_text, "IranSans", 16)
        p.drawString((width - text_width) / 2, header_y_start, main_title_text)

        # دایره‌های CMYK (جایگذاری تقریبی)
        draw_cmyk_circles(p, (width - text_width) / 2 - 25*mm, header_y_start + 5*mm, 3*mm)


        # --- اطلاعات عمومی فاکتور  ---
        p.setFont("IranSans", 10)
        line_spacing = 7 * mm
        info_y_start = header_y_start - 20 * mm

        info_x_right = width - 20 * mm  # سمت راست
        info_x_left = 20 * mm          # سمت چپ

        customer_display_name = customer.name if hasattr(customer, 'name') else customer
        phone_number = getattr(customer, 'phone_number', '-') if hasattr(customer, 'phone_number') else '-'
        if phone_number is None:
            phone_number = "_"        
        # ردیف اول: مشتری - شماره فاکتور
        # factor obj
        total_sum = 0
        total_payment = 0
        total_remaining = 0
        factor = Factor.objects.create(
            total_remaining=total_remaining,
            total_cost=total_sum,
            total_payment=total_payment,
            customer=order.customer_name,
            company=order.company_name
        )
        factor_ids.append(factor.id)

        p.drawRightString(info_x_right, info_y_start, get_farsi_text(f"مشتری: {customer_display_name}"))
        p.drawString(info_x_left, info_y_start, get_farsi_text(f"شماره: {factor.id}"))

        # ردیف دوم: شماره تلفن - تاریخ
        p.drawRightString(info_x_right, info_y_start - line_spacing, get_farsi_text(f"شماره تلفن: {phone_number}"))
        p.drawString(info_x_left, info_y_start - line_spacing, get_farsi_text("تاریخ: __/__/__14"))

        # --- خطوط افقی جداکننده هدر ---
        p.line(15 * mm, header_y_start - 10 * mm, width - 15 * mm, header_y_start - 10 * mm)  # خط زیر عنوان اصلی
        p.line(15 * mm, info_y_start - 2.5 * line_spacing, width - 15 * mm, info_y_start - 2.5 * line_spacing)  # خط زیر اطلاعات عمومی

        # --- جدول اصلی فاکتور ---
        table_y_start = info_y_start - 2.5 * line_spacing - 5*mm # شروع جدول
        table_col_widths = list(reversed([
            10 * mm,   # ردیف
            45 * mm,   # عنوان
            25 * mm,   # ابعاد
            15 * mm,   # تعداد
            28 * mm,   # مبلغ واحد
            28 * mm,   # مبلغ کل
            28 * mm,   # پرداختی
            28 * mm,   # باقیمانده
        ]))

        table_row_height = 8*mm # ارتفاع هر ردیف

        # سربرگ جدول
        table_header = list(reversed([
            Paragraph(get_farsi_text("ردیف"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("عنوان"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("ابعاد"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("تعداد"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("مبلغ واحد به ریال"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("مبلغ کل به ریال"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("مبلغ پرداختی به ریال"), farsi_paragraph_style_table),
            Paragraph(get_farsi_text("مبلغ باقیمانده به ریال"), farsi_paragraph_style_table)
        ]))

        table_data = [table_header]
        for i, order in enumerate(orders, start=1):
            dimensions = f"{order.width} * {order.height}"
            amount_text = get_farsi_text(str(order.amount))
            unit_cost_text = get_farsi_text(f'{order.unit_cost:,.0f}')
            total_cost_text = get_farsi_text(f'{order.total_cost:,.0f}')
            payment_text = get_farsi_text(f'{order.payment:,.0f}')
            remaining_text = get_farsi_text(f'{order.remaining_payment:,.0f}')
            
            row = list(reversed([
                Paragraph(get_farsi_text(str(i)), farsi_paragraph_style_table),
                Paragraph(get_farsi_text(order.title or ''), farsi_paragraph_style_table),
                Paragraph(get_farsi_text(dimensions), farsi_paragraph_style_table),
                Paragraph(amount_text, farsi_paragraph_style_table),
                Paragraph(unit_cost_text, farsi_paragraph_style_table),
                Paragraph(total_cost_text, farsi_paragraph_style_table),
                Paragraph(payment_text, farsi_paragraph_style_table),
                Paragraph(remaining_text, farsi_paragraph_style_table)
            ]))

            table_data.append(row)

            total_sum += order.total_cost
            total_remaining += order.remaining_payment
            total_payment += order.payment

        factor.total_cost = total_sum
        factor.total_payment = total_payment
        factor.total_remaining = total_remaining
        factor.save()
                    
        # تعریف استایل جدول
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'IranSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (3, -1), 'CENTER'),
        ])


        # ساخت جدول Platypus
        table = Table(table_data, colWidths=table_col_widths, rowHeights=table_row_height)
        table.setStyle(table_style)

        table_width, table_height = table.wrapOn(p, width, height)
        table_x = (width - table_width) / 2
        p.saveState() # برای اطمینان از اینکه تغییرات در حالت canvas فقط برای این بخش اعمال شود
        table.drawOn(p, table_x, table_y_start - table_height)
        p.restoreState()

        # تنظیم فونت
        p.setFont("IranSans", 10)

        # موقعیت راست صفحه
        total_x_right = width - 10 * mm

        # شروع از زیر جدول
        line_height = 7 * mm
        block_spacing = 2 * mm
        footer_y = table_y_start - table_height - 10 * mm

        # --- جمع کل ---
        p.drawRightString(total_x_right, footer_y, get_farsi_text(f"جمع کل: {total_sum:,.0f} ریال"))
        p.drawRightString(total_x_right, footer_y - line_height, get_farsi_text(f"مبلغ به حروف: {words(total_sum)} ریال"))

        # --- پرداختی ---
        footer_y -= 2 * line_height + block_spacing
        p.drawRightString(total_x_right, footer_y, get_farsi_text(f"جمع کل پرداختی: {total_payment:,.0f} ریال"))
        p.drawRightString(total_x_right, footer_y - line_height, get_farsi_text(f"مبلغ به حروف: {words(total_payment)} ریال"))

        # --- باقیمانده ---
        footer_y -= 2 * line_height + block_spacing
        p.drawRightString(total_x_right, footer_y, get_farsi_text(f"جمع کل بدهی باقیمانده: {total_remaining:,.0f} ریال"))
        p.drawRightString(total_x_right, footer_y - line_height, get_farsi_text(f"مبلغ به حروف: {words(total_remaining)} ریال"))


        # فاصله‌ای برای جدا شدن فوتر از اطلاعات مالی بالا
        footer_y_start = footer_y - 15 * mm
        footer_line_spacing = 6 * mm

        p.setFont("IranSans", 9)

        # اطلاعات تماس
        p.drawString(20 * mm, footer_y_start, get_farsi_text("تلفن: 061111111"))
        p.drawString(20 * mm, footer_y_start - footer_line_spacing,
                    get_farsi_text("شماره شبا: IR00000000000000000000"))

        card_number = convert_to_farsi_numbers("0000-0000-0000-0000")
        p.drawString(20 * mm, footer_y_start - 2 * footer_line_spacing,
                    get_farsi_text(f"شماره کارت: {card_number}"))
        p.drawString(20 * mm, footer_y_start - 3 * footer_line_spacing,
                    get_farsi_text("بنام: شرکت ایده نو"))

        # نوار مشکی پایین صفحه
        p.setStrokeColor(colors.black)
        p.setFillColor(colors.black)
        p.rect(15 * mm, 15 * mm, width - 30 * mm, 0.2 * mm, fill=1)


    p.save() # ذخیره نهایی PDF

    file_name = generate_safe_filename(factor_ids)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'
    return response

# نام قابل نمایش برای اکشن در پنل ادمین
generate_factor_pdf.short_description = "تولید فاکتور"
