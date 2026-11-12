import argparse
import os
import sys

from serper import fetch_target_domains
from scanner import WPScanner
from exporter import save_site_plugins_csv, save_themes_summary_csv

# تنظیم انکودینگ UTF-8 برای ترمینال ویندوز
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

# بررسی وجود کتابخانه‌های اصلاح جهت متن فارسی در CMD سنتی ویندوز
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False

# تشخیص اینکه آیا ترمینال مدرن (مثل Windows Terminal یا VS Code) است یا CMD کلاسیک
IS_MODERN_TERMINAL = bool(os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") == "vscode")


def fa(text: str) -> str:
    """تنظیم هوشمند جهت و چسبندگی حروف فارسی برای کنسول ویندوز"""
    if HAS_BIDI and not IS_MODERN_TERMINAL:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    return text


def log(text: str):
    print(fa(text), flush=True)


def ask_prompt(prompt_text: str, default: str = "") -> str:
    suffix = f" (پیش‌فرض: {default}): " if default else ": "
    val = input(fa(prompt_text + suffix)).strip()
    # حذف کوتیشن‌های احتمالی در مسیرهای ویندوز
    val = val.strip('"').strip("'")
    return val if val else default


def parse_pages_input(pages_str: str) -> list[int]:
    """تبدیل ورودی صفحات (مثلاً '1-3' یا '1,3,5' یا '3') به لیست اعداد"""
    pages = set()
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                pages.update(range(min(start, end), max(start, end) + 1))
            except ValueError:
                pass
        else:
            try:
                pages.add(int(part))
            except ValueError:
                pass
    return sorted([p for p in pages if p > 0]) or [1]


def get_inputs():
    parser = argparse.ArgumentParser(description="WP-Recon: WordPress Theme & Plugin Recon Tool")
    parser.add_argument("-q", "--query", type=str, help="عبارت جستجو (فارسی یا انگلیسی)")
    parser.add_argument("-n", "--num-sites", type=int, help="حداکثر تعداد سایت برای بررسی")
    parser.add_argument("-p", "--pages", type=str, help="صفحات گوگل (مثال: 1-3 یا 1,2,5)")
    parser.add_argument("-o", "--output", type=str, help="مسیر پوشه ذخیره خروجی")

    args = parser.parse_args()

    print("=" * 65)
    log("  WP-Recon v1.1 | ابزار شناسایی قالب و افزونه‌های وردپرس")
    print("=" * 65)

    query = args.query or ask_prompt("1. موضوع یا عبارت جستجو را وارد کنید")
    while not query:
        query = ask_prompt("لطفاً یک عبارت معتبر وارد کنید")

    if args.num_sites:
        num_sites = args.num_sites
    else:
        num_raw = ask_prompt("2. حداکثر چند سایت بررسی شود؟", "5")
        num_sites = int(num_raw) if num_raw.isdigit() and int(num_raw) > 0 else 5

    pages_raw = args.pages or ask_prompt("3. کدام صفحات جستجو بررسی شوند؟ (مثال: 1-3 یا 3)", "1-2")
    output_dir = args.output or ask_prompt("4. مسیر ذخیره فایل‌های CSV", "./output")

    pages = parse_pages_input(pages_raw)
    return query, num_sites, pages, output_dir


def main():
    query, max_sites, pages, output_dir = get_inputs()

    print("\n" + "-" * 65)
    log("مرحله ۱: استخراج لینک‌ها از موتور جستجو")
    print("-" * 65)

    target_urls = fetch_target_domains(query, pages, max_sites, log)

    if not target_urls:
        log("\n[X] هیچ سایتی یافت نشد. لطفاً اتصال اینترنت خود را بررسی کنید.")
        return

    log(f"\n[OK] تعداد {len(target_urls)} دامنه یکتا برای اسکن آماده شد.")

    print("\n" + "-" * 65)
    log("مرحله ۲: اسکن فنی سایت‌ها و استعلام از مخزن وردپرس")
    print("-" * 65)

    scanner = WPScanner()
    wp_results = []
    total = len(target_urls)

    for idx, url in enumerate(target_urls, start=1):
        domain = url.replace("https://", "").replace("http://", "")
        log(f"[{idx}/{total}] در حال بررسی سایت: {domain} ...")

        scan_data = scanner.scan_site(url)

        if scan_data["is_wordpress"]:
            wp_results.append(scan_data)
            csv_path = save_site_plugins_csv(scan_data["domain"], scan_data["plugins"], output_dir)
            theme_name = scan_data["theme"].get("name", "نامشخص")
            p_count = len(scan_data["plugins"])
            log(f"   [+] وردپرس شناسایی شد! | قالب: {theme_name} | تعداد افزونه‌ها: {p_count}")
            log(f"   [+] فایل ذخیره شد: {os.path.basename(csv_path)}")
        else:
            log(f"   [-] غیر وردپرسی یا عدم دسترسی: {domain}")

    print("\n" + "=" * 65)
    log("مرحله ۳: گزارش نهایی پروژه")
    print("=" * 65)

    if wp_results:
        summary_path = save_themes_summary_csv(wp_results, output_dir)
        log(f"تعداد کل سایت‌های بررسی شده: {total}")
        log(f"تعداد سایت‌های وردپرسی کشف شده: {len(wp_results)}\n")

        for item in wp_results:
            t_name = item["theme"].get("name", "نامشخص")
            t_slug = item["theme"].get("slug", "")
            log(f" * سایت: {item['domain']} | قالب: {t_name} ({t_slug}) | افزونه‌ها: {len(item['plugins'])} عدد")

        print("-" * 65)
        log(f"مسیر ذخیره فایل‌های CSV افزونه‌ها:\n{os.path.abspath(output_dir)}")
        log(f"\nفایل گزارش کلی قالب‌ها:\n{os.path.abspath(summary_path)}")
    else:
        log("[!] هیچ سایت وردپرسی در میان دامنه‌های بررسی‌شده پیدا نشد.")
        log("پیشنهاد: تعداد سایت‌ها را بیشتر کنید (مثلاً 10 یا 15) یا صفحات 1-3 را انتخاب کنید.")


if __name__ == "__main__":
    main()