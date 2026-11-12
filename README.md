# 🔍 WP-Recon

A lightweight, browserless Python CLI tool to identify WordPress websites from Google search results and accurately extract active themes and plugins along with official metadata from the `wordpress.org` repository.

> **Passive & Frontend-Only:** This tool does not send intrusive requests to the target website's backend or server; it relies strictly on publicly accessible frontend data (HTML source, public asset paths, and exposed metadata).

## ✨ Features
- **Passive Frontend Analysis:** Extracts data solely from the public frontend layer without probing or straining the target server.
- **Bilingual Search Support:** Search Persian and English queries with custom page selection and maximum site limits.
- **Zero Browser Dependencies:** Purely HTTP-based without requiring Selenium, headless browsers, or external WebDrivers.
- **Multi-Layer Plugin Detection:** Identifies plugins across three confidence levels (`api`, `high`, `medium`).
- **Official Repository Metadata:** Automatically queries official plugin names, last update dates, and repository status from the `wordpress.org` API.
- **Structured CSV Exports:** Generates a dedicated CSV file per domain alongside an aggregated summary report of detected themes.

---

<div dir="rtl">

# 🔍 معرفی ابزار WP-Recon

ابزار خط فرمان (CLI) سبک و بدون نیاز به مرورگر به زبان پایتون برای شناسایی وب‌سایت‌های وردپرسی از نتایج موتور جستجوی گوگل و استخراج دقیق قالب (Theme) و افزونه‌ها (Plugins) به همراه متادیتای رسمی از مخزن `wordpress.org`.

> **تحلیل کاملاً غیرتهاجمی (Frontend-Only):** این ابزار هیچ درخواست اضافی یا سنگینی به سمت سرور و بک‌اند سایت ارسال نمی‌کند و تمام اطلاعات را صرفاً از داده‌های عمومی قابل مشاهده در بخش فرانت (سورس HTML و مسیرهای عمومی) استخراج می‌نماید.

## ✨ ویژگی‌ها
- **استخراج صرفاً از بخش فرانت:** بدون ارسال درخواست به سرور هدف و کاملاً متکی بر اطلاعات عمومی سمت کاربر (Frontend).
- **پشتیبانی از جستجوی فارسی و انگلیسی:** قابلیت تعیین صفحات دلخواه گوگل و تنظیم سقف تعداد سایت‌های مورد بررسی.
- **بدون وابستگی به مرورگر:** اجرای سریع و مستقیم بدون نیاز به مرورگر یا درایورهای خارجی (کاملاً مبتنی بر درخواست‌های HTTP).
- **تشخیص چندلایه افزونه‌ها:** شناسایی افزونه‌ها در سه سطح اطمینان (`api`، `high` و `medium`).
- **استعلام از مخزن رسمی وردپرس:** دریافت خودکار نام رسمی، تاریخ آخرین بروزرسانی و وضعیت انتشار افزونه از API مخزن `wordpress.org`.
- **خروجی استاندارد CSV:** تولید فایل اختصاصی CSV برای هر دامنه به همراه یک فایل گزارش تجمیعی از قالب‌های شناسایی‌شده.

</div>

## 🚀 نصب و راه‌اندازی

```bash
git clone [https://github.com/armankarmi94/WP-Recon.git](https://github.com/armankarmi94/WP-Recon.git)
cd WP-Recon
pip install -r requirements.txt