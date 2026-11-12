import csv
import os

CSV_FIELDNAMES = ["slug", "name", "confidence", "active_installs", "last_updated", "on_wporg"]


def save_site_plugins_csv(domain: str, plugins: list[dict], output_dir: str) -> str:
    """ذخیره افزونه‌های سایت با فرمت کاملاً منطبق بر نمونه کاربر"""
    os.makedirs(output_dir, exist_ok=True)
    safe_domain = domain.replace(":", "_").replace("/", "")
    filepath = os.path.join(output_dir, f"{safe_domain}-plugins.csv")

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for plugin in plugins:
            writer.writerow(plugin)

    return filepath


def save_themes_summary_csv(results: list[dict], output_dir: str) -> str:
    """ذخیره گزارش کلی قالب‌ها و تعداد افزونه‌های هر سایت"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "_themes_and_sites_summary.csv")

    fields = ["domain", "url", "theme_slug", "theme_name", "theme_version", "plugins_count"]
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            theme = item.get("theme", {})
            writer.writerow({
                "domain": item.get("domain", ""),
                "url": item.get("url", ""),
                "theme_slug": theme.get("slug", ""),
                "theme_name": theme.get("name", ""),
                "theme_version": theme.get("version", ""),
                "plugins_count": len(item.get("plugins", []))
            })

    return filepath