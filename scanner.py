import html
import re
import urllib.parse
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# نگاشت Namespaceهای معروف REST API به اسلاگ دقیق افزونه
NAMESPACE_MAP = {
    "elementor": "elementor",
    "wc": "woocommerce",
    "woocommerce": "woocommerce",
    "jetpack": "jetpack",
    "yoast": "wordpress-seo",
    "rankmath": "seo-by-rank-math",
    "contact-form-7": "contact-form-7",
    "wpforms": "wpforms-lite",
    "pll": "polylang",
    "polylang": "polylang",
    "litespeed": "litespeed-cache",
    "wpml": "sitepress-multilingual-cms",
    "acf": "advanced-custom-fields",
    "wordfence": "wordfence",
    " monsterinsights": "google-analytics-for-wordpress",
    "redirection": "redirection",
    "updraftplus": "updraftplus",
    "mailchimp-for-wp": "mailchimp-for-wp",
    "yith": "yith-woocommerce-wishlist"
}

# الگوهای تشخیص غیرمستقیم (سطح اطمینان medium)
INDIRECT_SIGNATURES = {
    "polylang": [r"pll_", r"polylang"],
    "wordpress-seo": [r"yoast seo plugin", r"yoast-schema-graph"],
    "seo-by-rank-math": [r"rank-math-schema", r"rank math seo"],
    "wp-rocket": [r"wp-rocket", r"rocket-lazyload"],
    "litespeed-cache": [r"litespeed-cache", r"data-lazyloaded"],
    "autoptimize": [r"autoptimize_"],
    "w3-total-cache": [r"w3 total cache"],
    "wp-super-cache": [r"wp-super-cache"]
}


class WPScanner:
    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        self.wporg_cache = {}

    def query_wporg_plugin(self, slug: str) -> dict:
        """استعلام اطلاعات دقیق افزونه از مخزن رسمی wordpress.org"""
        if slug in self.wporg_cache:
            return self.wporg_cache[slug]

        api_url = f"https://api.wordpress.org/plugins/info/1.0/{slug}.json"
        result = {
            "name": "",
            "active_installs": "",
            "last_updated": "",
            "on_wporg": "unknown"
        }

        try:
            resp = self.session.get(api_url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "slug" in data and not data.get("error"):
                    raw_name = data.get("name", "")
                    clean_name = re.sub(r"<[^>]+>", "", html.unescape(raw_name)).strip()
                    result["name"] = clean_name
                    result["last_updated"] = data.get("last_updated", "")
                    # مطابق فایل نمونه شما، ستون active_installs در صورت نیاز خالی یا مقداردهی می‌شود
                    result["active_installs"] = ""
                    result["on_wporg"] = "yes"
        except Exception:
            pass

        self.wporg_cache[slug] = result
        return result

    def extract_theme_info(self, base_url: str, html_text: str) -> dict:
        """استخراج اسلاگ و نام دقیق قالب فعال سایت"""
        theme_matches = re.findall(r"/wp-content/themes/([a-zA-Z0-9_-]+)/", html_text)
        if not theme_matches:
            return {"slug": "نامشخص", "name": "نامشخص", "version": ""}

        theme_slug = theme_matches[0]
        theme_info = {"slug": theme_slug, "name": theme_slug, "version": ""}

        # تلاش برای خواندن هدر فایل style.css قالب جهت دریافت نام رسمی
        style_url = urllib.parse.urljoin(base_url, f"/wp-content/themes/{theme_slug}/style.css")
        try:
            resp = self.session.get(style_url, timeout=6, verify=False, headers={"Range": "bytes=0-2048"})
            if resp.status_code in (200, 206):
                name_match = re.search(r"Theme Name\s*:\s*(.+)", resp.text, re.IGNORECASE)
                ver_match = re.search(r"Version\s*:\s*(.+)", resp.text, re.IGNORECASE)
                if name_match:
                    theme_info["name"] = name_match.group(1).strip()
                if ver_match:
                    theme_info["version"] = ver_match.group(1).strip()
        except Exception:
            pass

        return theme_info

    def scan_site(self, url: str) -> dict:
        """اسکن کامل یک وب‌سایت برای تشخیص وردپرس، قالب و افزونه‌ها"""
        report = {
            "url": url,
            "domain": urllib.parse.urlparse(url).netloc.replace("www.", ""),
            "is_wordpress": False,
            "theme": {},
            "plugins": []
        }

        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False)
            if resp.status_code >= 400:
                return report
            html_text = resp.text
        except Exception:
            return report

        # دیکشنری ذخیره افزونه‌ها: slug -> confidence
        detected_plugins = {}

        # ۱. بررسی از طریق REST API (/wp-json/) -> سطح اطمینان: api
        wp_json_ok = False
        try:
            json_url = urllib.parse.urljoin(url, "/wp-json/")
            json_resp = self.session.get(json_url, timeout=8, verify=False)
            if json_resp.status_code == 200 and "namespaces" in json_resp.text:
                wp_json_ok = True
                json_data = json_resp.json()
                namespaces = json_data.get("namespaces", [])
                for ns in namespaces:
                    prefix = ns.split("/")[0].lower()
                    if prefix in ("wp", "oembed"):
                        continue
                    mapped_slug = NAMESPACE_MAP.get(prefix, prefix)
                    detected_plugins[mapped_slug] = "api"
        except Exception:
            pass

        # ۲. بررسی مستقیم مسیرهای فایل در HTML -> سطح اطمینان: high
        direct_slugs = set(re.findall(r"/wp-content/plugins/([a-zA-Z0-9_-]+)/", html_text))
        for slug in direct_slugs:
            slug_lower = slug.lower()
            if slug_lower not in detected_plugins:
                detected_plugins[slug_lower] = "high"

        # ۳. بررسی نشانه‌های غیرمستقیم در HTML -> سطح اطمینان: medium
        html_lower = html_text.lower()
        for slug, patterns in INDIRECT_SIGNATURES.items():
            if slug not in detected_plugins:
                for pat in patterns:
                    if re.search(pat, html_lower):
                        detected_plugins[slug] = "medium"
                        break

        # تصمیم‌گیری نهایی درباره وردپرسی بودن سایت
        has_wp_markers = (
            "/wp-content/" in html_text
            or "/wp-includes/" in html_text
            or 'name="generator" content="WordPress' in html_text
            or wp_json_ok
            or len(detected_plugins) > 0
        )

        if not has_wp_markers:
            return report

        report["is_wordpress"] = True
        report["theme"] = self.extract_theme_info(url, html_text)

        # تکمیل اطلاعات هر افزونه از مخزن وردپرس و مرتب‌سازی الفبایی بر اساس اسلاگ
        final_plugins = []
        for slug in sorted(detected_plugins.keys()):
            confidence = detected_plugins[slug]
            wporg_meta = self.query_wporg_plugin(slug)

            # اگر اسلاگ از طریق Namespace حدس زده شده ولی در مخزن نبود و در HTML هم نبود، حذف شود
            if confidence == "api" and wporg_meta["on_wporg"] == "unknown" and slug not in NAMESPACE_MAP.values():
                continue

            final_plugins.append({
                "slug": slug,
                "name": wporg_meta["name"],
                "confidence": confidence,
                "active_installs": wporg_meta["active_installs"],
                "last_updated": wporg_meta["last_updated"],
                "on_wporg": wporg_meta["on_wporg"]
            })

        report["plugins"] = final_plugins
        return report