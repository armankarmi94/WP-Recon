import time
import random
import re
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
]
BLACKLIST_DOMAINS = {
    'google.com', 'www.google.com', 'bing.com', 'www.bing.com',
    'yahoo.com', 'search.yahoo.com', 'duckduckgo.com', 'html.duckduckgo.com',
    'youtube.com', 'www.youtube.com', 'aparat.com', 'www.aparat.com',
    'instagram.com', 'linkedin.com', 'wikipedia.org', 'fa.wikipedia.org',
    'pinterest.com', 'facebook.com', 'twitter.com', 'x.com', 't.me',
    'virgool.io', 'ninisite.com', 'torob.com', 'emalls.ir', 'digikala.com',
    'basalam.com', 'divar.ir', 'sheypoor.com', 'microsoft.com'
}


def is_valid_target(url: str) -> bool:
    if not url or not url.startswith(('http://', 'https://')):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        if not domain or '.' not in domain:
            return False
        for bad in BLACKLIST_DOMAINS:
            if domain == bad or domain.endswith('.' + bad):
                return False
        return True
    except Exception:
        return False


def decode_bing_url(url: str) -> str:
    """رمزگشایی لینک‌های ریدایرکت موتور جستجوی بینگ"""
    if "bing.com/ck/a" in url and "u=a1" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'u' in qs:
                encoded = qs['u'][0][2:]  # حذف پیشوند a1
                padding = 4 - (len(encoded) % 4)
                if padding != 4:
                    encoded += "=" * padding
                return base64.urlsafe_b64decode(encoded).decode('utf-8', errors='ignore')
        except Exception:
            pass
    return url


def search_google(query: str, page: int) -> list[str]:
    """۱. تلاش برای جستجوی مستقیم از گوگل"""
    start = (page - 1) * 10
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8"
    }
    params = {"q": query, "start": start, "hl": "fa", "num": 10}
    urls = []
    try:
        resp = requests.get("https://www.google.com/search", params=params, headers=headers, timeout=10)
        if resp.status_code == 200 and "detected unusual traffic" not in resp.text.lower():
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/url?q="):
                    href = urllib.parse.unquote(href.split("/url?q=")[1].split("&")[0])
                if is_valid_target(href):
                    urls.append(href)
    except Exception:
        pass
    return urls


def search_bing(query: str, page: int) -> list[str]:
    """۲. جستجو با پشتیبانی از شماره صفحه دقیق در Bing (بسیار پایدار در ایران و بدون کپچا)"""
    first = (page - 1) * 10 + 1
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8"
    }
    params = {"q": query, "first": first, "count": 10}
    urls = []
    try:
        resp = requests.get("https://www.bing.com/search", params=params, headers=headers, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("li.b_algo h2 a, h2 a[href]"):
                href = decode_bing_url(a.get("href", ""))
                if is_valid_target(href):
                    urls.append(href)
    except Exception:
        pass
    return urls


def search_yahoo(query: str, page: int) -> list[str]:
    """۳. جستجو با پشتیبانی از شماره صفحه در Yahoo Search"""
    b_param = (page - 1) * 10 + 1
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8"
    }
    params = {"p": query, "b": b_param}
    urls = []
    try:
        resp = requests.get("https://search.yahoo.com/search", params=params, headers=headers, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "RU=" in href:
                    try:
                        href = urllib.parse.unquote(href.split("RU=")[1].split("/RK=")[0])
                    except Exception:
                        pass
                if is_valid_target(href):
                    urls.append(href)
    except Exception:
        pass
    return urls


def search_ddg_get(query: str) -> list[str]:
    """۴. جستجوی مستقیم از طریق درخواست GET در DuckDuckGo"""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    urls = []
    try:
        resp = requests.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "uddg=" in href:
                    href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                if is_valid_target(href):
                    urls.append(href)
    except Exception:
        pass
    return urls


def fetch_target_domains(query: str, pages: list[int], max_sites: int, log_fn) -> list[str]:
    """جمع‌آوری دامنه‌های یکتا از صفحات انتخاب‌شده با مکانیزم ضد مسدودیت"""
    collected_urls = []
    seen_domains = set()

    # اضافه کردن کلیدواژه کمکی در صورت کوتاه بودن عبارت برای یافتن سایت‌های فروشگاهی/وردپرسی بیشتر
    queries_to_try = [query]
    if len(query.split()) == 1:
        queries_to_try.append(f"خرید {query}")

    for page in pages:
        if len(collected_urls) >= max_sites:
            break

        log_fn(f"[*] در حال کاوش صفحه {page} نتایج جستجو برای عبارت: {query}")

        page_urls = []
        for q in queries_to_try:
            # زنجیره موتورهای جستجو به ترتیب اولویت
            page_urls = search_google(q, page)
            if not page_urls:
                page_urls = search_bing(q, page)
            if not page_urls:
                page_urls = search_yahoo(q, page)
            if not page_urls:
                page_urls = search_ddg_get(q)

            if page_urls:
                break

        added_in_page = 0
        for url in page_urls:
            parsed = urllib.parse.urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            if domain not in seen_domains:
                seen_domains.add(domain)
                collected_urls.append(base_url)
                added_in_page += 1
                if len(collected_urls) >= max_sites:
                    break

        log_fn(f"    -> در این صفحه {added_in_page} دامنه جدید استخراج شد.")
        time.sleep(random.uniform(0.8, 1.5))

    return collected_urls