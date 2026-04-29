"""
Web Hunter v2 — Universal Website Crawler & File Downloader
Crawls any public website (static or SPA-structured) and extracts:
  - All downloadable files (configurable extensions)
  - All external/internal links
  - All JS data files
  - Page metadata, headings, structured content
  - Full export: CSV, JSON, ZIP
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import json
import os
import time
import zipfile
import io
from datetime import datetime
import re
import urllib.robotparser
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Web Hunter — Site Crawler",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Syne:wght@600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #F4F6FB; }
.block-container { padding-top: 1.8rem !important; max-width: 1280px; }

/* ── Header ── */
.hero {
    background: linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#0f3460 100%);
    border-radius: 18px; padding: 2.2rem 2.8rem; margin-bottom: 1.6rem;
    position: relative; overflow: hidden; color: white;
}
.hero::before {
    content:''; position:absolute; top:-80px; right:-80px;
    width:280px; height:280px; border-radius:50%;
    background: radial-gradient(circle, rgba(99,102,241,.15) 0%, transparent 70%);
}
.hero h1 {
    font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800;
    margin:0 0 .3rem; letter-spacing:-.5px; color:white !important;
}
.hero p { color:rgba(255,255,255,.6); font-size:.95rem; margin:0; font-weight:300; }
.badge {
    display:inline-block; background:rgba(94,234,212,.15);
    border:1px solid rgba(94,234,212,.3); color:#5eead4;
    border-radius:50px; padding:2px 12px; font-size:.7rem; font-weight:600;
    letter-spacing:1px; text-transform:uppercase; margin-bottom:.7rem;
}

/* ── Stat cards ── */
.stat-row { display:flex; gap:.9rem; margin-bottom:1.6rem; flex-wrap:wrap; }
.stat-card {
    background:white; border-radius:13px; padding:1.2rem 1.4rem;
    flex:1; min-width:120px; border:1px solid #E5E7EB;
    box-shadow:0 1px 3px rgba(0,0,0,.04); transition:box-shadow .2s;
}
.stat-card:hover { box-shadow:0 4px 14px rgba(0,0,0,.08); }
.stat-label { font-size:.68rem; font-weight:600; letter-spacing:.8px;
    text-transform:uppercase; color:#9CA3AF; margin-bottom:.3rem; }
.stat-value { font-family:'Syne',sans-serif; font-size:1.85rem; font-weight:700;
    color:#111827; line-height:1; }
.stat-value.indigo { color:#6366F1; }
.stat-value.green  { color:#10B981; }
.stat-value.amber  { color:#F59E0B; }
.stat-value.red    { color:#EF4444; }
.stat-value.blue   { color:#3B82F6; }

/* ── Cards ── */
.card {
    background:white; border-radius:15px; padding:1.6rem;
    border:1px solid #E5E7EB; box-shadow:0 1px 3px rgba(0,0,0,.04);
    margin-bottom:1.1rem;
}
.card-title { font-family:'Syne',sans-serif; font-size:.95rem; font-weight:700;
    color:#111827; margin-bottom:.15rem; }
.card-sub { font-size:.8rem; color:#6B7280; margin-bottom:1rem; }

/* ── File rows ── */
.file-row {
    display:flex; align-items:flex-start; gap:.9rem; padding:.8rem .95rem;
    border-radius:10px; border:1px solid #F3F4F6; margin-bottom:.4rem;
    background:#FAFAFA; transition:background .15s;
}
.file-row:hover { background:#F0F1FF; border-color:#C7D2FE; }
.file-icon {
    width:34px; height:34px; border-radius:8px; flex-shrink:0;
    display:flex; align-items:center; justify-content:center; font-size:.95rem;
}
.fi-psd    { background:linear-gradient(135deg,#6366F1,#8B5CF6); }
.fi-pdf    { background:linear-gradient(135deg,#EF4444,#F97316); }
.fi-zip    { background:linear-gradient(135deg,#F59E0B,#EAB308); }
.fi-js     { background:linear-gradient(135deg,#10B981,#059669); }
.fi-img    { background:linear-gradient(135deg,#3B82F6,#6366F1); }
.fi-doc    { background:linear-gradient(135deg,#2563EB,#1D4ED8); }
.fi-link   { background:linear-gradient(135deg,#6B7280,#4B5563); }
.fi-other  { background:linear-gradient(135deg,#9CA3AF,#6B7280); }
.file-name { font-weight:600; font-size:.85rem; color:#111827; }
.file-url  { font-size:.72rem; color:#9CA3AF; word-break:break-all; margin-top:1px; }
.file-meta { font-size:.72rem; color:#6366F1; font-weight:600; white-space:nowrap; }

/* ── Pills ── */
.pill {
    display:inline-flex; align-items:center; gap:4px;
    padding:2px 9px; border-radius:50px; font-size:.7rem; font-weight:600;
}
.p-ok   { background:#D1FAE5; color:#065F46; }
.p-err  { background:#FEE2E2; color:#991B1B; }
.p-warn { background:#FEF3C7; color:#92400E; }
.p-info { background:#E0E7FF; color:#3730A3; }
.p-blue { background:#DBEAFE; color:#1E40AF; }
.p-gray { background:#F3F4F6; color:#374151; }

/* ── Section tabs ── */
.tab-row { display:flex; gap:.5rem; margin-bottom:1rem; flex-wrap:wrap; }
.tab-btn {
    padding:.4rem .9rem; border-radius:8px; font-size:.8rem; font-weight:600;
    cursor:pointer; border:1.5px solid #E5E7EB; background:white; color:#6B7280;
    transition:all .15s;
}
.tab-btn.active { background:#6366F1; color:white; border-color:#6366F1; }

/* ── Log box ── */
.log-box {
    background:#0D1117; border-radius:11px; padding:1rem 1.3rem;
    font-family:'Courier New',monospace; font-size:.76rem; color:#7EE8A2;
    max-height:260px; overflow-y:auto; border:1px solid #21262D; line-height:1.75;
}
.lt { color:#484F58; } .lok { color:#7EE8A2; }
.lwarn { color:#FFB86C; } .lerr { color:#FF5555; } .linfo { color:#8BE9FD; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#0f172a 0%,#1e293b 100%) !important;
}
section[data-testid="stSidebar"] * { color:rgba(255,255,255,.82) !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius:9px !important; font-family:'DM Sans',sans-serif !important;
    font-weight:600 !important; font-size:.87rem !important;
    padding:.5rem 1.4rem !important; border:none !important;
    background:linear-gradient(135deg,#6366F1,#8B5CF6) !important;
    color:white !important; box-shadow:0 2px 7px rgba(99,102,241,.3) !important;
}
.stButton > button:hover { opacity:.87 !important; }

/* ── Input ── */
.stTextInput > div > div > input {
    border-radius:9px !important; border:1.5px solid #E5E7EB !important;
    font-size:.88rem !important; padding:.6rem .95rem !important;
}
.stTextInput > div > div > input:focus {
    border-color:#6366F1 !important;
    box-shadow:0 0 0 3px rgba(99,102,241,.15) !important;
}

/* ── Progress ── */
.stProgress > div > div {
    background:linear-gradient(90deg,#6366F1,#8B5CF6) !important;
    border-radius:10px !important;
}
hr { border-color:#F3F4F6 !important; margin:1.2rem 0 !important; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7",
}

# Default downloadable extensions to hunt for
DEFAULT_EXTS = [".psd", ".pdf", ".zip", ".rar", ".7z", ".ai", ".eps",
                ".sketch", ".fig", ".xd", ".png", ".jpg", ".svg",
                ".docx", ".xlsx", ".pptx", ".mp4", ".mp3"]

FILE_ICONS = {
    ".psd": ("🖼️", "fi-psd"), ".ai": ("🎨", "fi-psd"), ".eps": ("🎨", "fi-psd"),
    ".sketch": ("💎", "fi-psd"), ".fig": ("💎", "fi-psd"), ".xd": ("💎", "fi-psd"),
    ".pdf": ("📄", "fi-pdf"),
    ".zip": ("🗜️", "fi-zip"), ".rar": ("🗜️", "fi-zip"), ".7z": ("🗜️", "fi-zip"),
    ".png": ("🖼️", "fi-img"), ".jpg": ("🖼️", "fi-img"), ".jpeg": ("🖼️", "fi-img"),
    ".svg": ("🖼️", "fi-img"), ".gif": ("🖼️", "fi-img"),
    ".docx": ("📝", "fi-doc"), ".xlsx": ("📊", "fi-doc"), ".pptx": ("📊", "fi-doc"),
    ".mp4": ("🎬", "fi-other"), ".mp3": ("🎵", "fi-other"),
    ".js": ("⚙️", "fi-js"), ".json": ("⚙️", "fi-js"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def add_log(msg, level="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"ok": "✓", "warn": "⚠", "err": "✗", "info": "›"}
    icon = icons.get(level, "›")
    st.session_state.logs.append(
        f'<span class="lt">[{ts}]</span> <span class="l{level}">{icon} {msg}</span>'
    )

def check_robots(base_url):
    try:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(urljoin(base_url, "/robots.txt"))
        rp.read()
        return rp.can_fetch(HEADERS["User-Agent"], base_url), rp
    except Exception:
        return True, None

def get_page(url, timeout=18):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception:
        return None

def get_file_size(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=7, allow_redirects=True)
        cl = r.headers.get("Content-Length")
        if cl:
            s = int(cl)
            if s < 1024: return f"{s} B"
            elif s < 1024**2: return f"{s/1024:.1f} KB"
            else: return f"{s/1024**2:.1f} MB"
        return "—"
    except Exception:
        return "—"

def ext_of(url):
    path = urlparse(url).path
    _, e = os.path.splitext(path)
    return e.lower()

def filename_of(url):
    name = os.path.basename(urlparse(url).path)
    return name if name else url.split("/")[-1] or "file"

# ─────────────────────────────────────────────────────────────────────────────
#  CORE CRAWL
# ─────────────────────────────────────────────────────────────────────────────

def crawl_page(url, soup, target_exts, base_domain):
    """
    Extract EVERYTHING from a parsed page:
      - downloadable files by extension (href, data-*, script embeds)
      - all <a> href links (internal + external)
      - all <script src="…"> JS/data files
      - all <link href="…"> resources
      - inline JS URL pattern scanning (handles SPAs)
    """
    files = []
    links_internal = []
    links_external = []
    js_files = []
    seen = set()

    def record_file(u, anchor="", source="href"):
        if u in seen:
            return
        seen.add(u)
        e = ext_of(u)
        if e in target_exts:
            ico, cls = FILE_ICONS.get(e, ("📁", "fi-other"))
            files.append({
                "filename": filename_of(u),
                "url": u,
                "ext": e,
                "anchor_text": anchor[:80],
                "source": source,
                "icon": ico,
                "icon_cls": cls,
                "file_size": "—",
            })

    # 1. All <a href>
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        full = urljoin(url, href)
        p = urlparse(full)
        if p.scheme not in ("http", "https"):
            continue
        anchor = a.get_text(strip=True)
        record_file(full, anchor, "direct_link")
        if p.netloc == base_domain:
            if full not in seen or ext_of(full) not in target_exts:
                links_internal.append({"url": full, "text": anchor[:80]})
        else:
            links_external.append({"url": full, "text": anchor[:80]})

    # 2. All data-* attributes
    for tag in soup.find_all(True):
        for attr, val in tag.attrs.items():
            if not isinstance(val, str):
                continue
            if val.startswith("http") or (val.startswith("/") and len(val) > 1):
                full = urljoin(url, val)
                record_file(full, f"[{attr}]", "data_attribute")

    # 3. All <script src>
    for s in soup.find_all("script", src=True):
        src = s["src"].strip()
        full = urljoin(url, src)
        if full not in seen:
            seen.add(full)
            js_files.append({"url": full, "filename": filename_of(full)})
        record_file(full, "[script src]", "script_src")

    # 4. Inline JS — scan for any URL-like strings matching target extensions
    for s in soup.find_all("script"):
        text = s.string or ""
        if len(text) < 10:
            continue
        # URLs in quotes
        raw_urls = re.findall(r'["\x27](https?://[^"\x27\s<>]{6,})["\x27]', text)
        for u in raw_urls:
            record_file(u, "[inline JS]", "inline_js")
        # Relative paths in quotes ending in known extensions
        for ext in target_exts:
            relative = re.findall(r'["\x27](/[^"\x27\s<>]+\\' + re.escape(ext) + r')["\x27]', text, re.IGNORECASE)
            for r in relative:
                full = urljoin(url, r)
                record_file(full, "[inline JS rel]", "inline_js")
        # Also scan inline JS for any .js data file references
        js_refs = re.findall(r'["\x27]((?:\.\.?/)?[^"\x27\s<>]+\.js)["\x27]', text)
        for jr in js_refs:
            full = urljoin(url, jr)
            if full not in seen:
                seen.add(full)
                js_files.append({"url": full, "filename": filename_of(full)})

    # 5. Download-button pattern heuristic
    download_keywords = {"download", "free download", "get free", "télécharger", "baixar"}
    for a in soup.find_all("a", href=True):
        text_low = a.get_text(strip=True).lower()
        href = a.get("href", "")
        full = urljoin(url, href)
        if full in seen:
            continue
        if any(kw in text_low for kw in download_keywords):
            record_file(full, a.get_text(strip=True)[:80], "download_button")

    # Deduplicate links
    seen_links = set()
    int_deduped = []
    for li in links_internal:
        if li["url"] not in seen_links:
            seen_links.add(li["url"])
            int_deduped.append(li)

    return files, int_deduped, links_external, js_files


def crawl_js_file(js_url, target_exts):
    """
    Download a .js / data file and scan its contents for file URLs.
    This is the KEY fix for SPAs like aml-hub.netlify.app where all content
    lives in external JS data files rather than in the HTML.
    """
    found_files = []
    r = get_page(js_url, timeout=15)
    if not r:
        return found_files, {}

    text = r.text
    size = len(r.content)

    # Extract metadata about this JS file
    js_meta = {
        "url": js_url,
        "filename": filename_of(js_url),
        "size_bytes": size,
        "size_human": f"{size/1024:.1f} KB" if size >= 1024 else f"{size} B",
        "char_count": len(text),
    }

    seen = set()
    for ext in target_exts:
        # https:// URLs with this extension
        urls = re.findall(r'(https?://[^\s"\x27<>]+' + re.escape(ext) + r')', text, re.IGNORECASE)
        for u in urls:
            u = u.strip("\"'.,;)")
            if u not in seen:
                seen.add(u)
                ico, cls = FILE_ICONS.get(ext, ("📁", "fi-other"))
                found_files.append({
                    "filename": filename_of(u),
                    "url": u,
                    "ext": ext,
                    "anchor_text": f"[in {filename_of(js_url)}]",
                    "source": "js_data_file",
                    "icon": ico,
                    "icon_cls": cls,
                    "file_size": "—",
                })

    return found_files, js_meta


def extract_page_info(soup, url, resp):
    """Extract rich page metadata."""
    info = {
        "url": url,
        "status_code": resp.status_code,
        "content_size": f"{len(resp.content)//1024} KB",
        "title": "",
        "description": "",
        "author": "",
        "keywords": "",
        "h1": "",
        "h2_list": [],
        "og_title": "",
        "og_description": "",
        "canonical": "",
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if soup.title:
        info["title"] = (soup.title.string or "").strip()

    for m in soup.find_all("meta"):
        name = (m.get("name") or m.get("property") or "").lower()
        content = m.get("content", "")
        if "description" in name and not info["description"]:
            info["description"] = content[:300]
        if "author" in name:
            info["author"] = content[:100]
        if "keyword" in name:
            info["keywords"] = content[:200]
        if name == "og:title":
            info["og_title"] = content[:200]
        if name == "og:description":
            info["og_description"] = content[:300]

    canonical = soup.find("link", rel="canonical")
    if canonical:
        info["canonical"] = canonical.get("href", "")

    h1 = soup.find("h1")
    if h1:
        info["h1"] = h1.get_text(strip=True)[:200]

    info["h2_list"] = [h.get_text(strip=True)[:100] for h in soup.find_all("h2")][:10]

    return info


# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "logs": [],
    "files": [],
    "links_int": [],
    "links_ext": [],
    "js_files_meta": [],
    "page_info": {},
    "js_content_files": [],
    "scraped": False,
    "active_tab": "files",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1.3rem 0 .9rem'>
        <div style='font-family:Syne,sans-serif;font-size:1.35rem;font-weight:800;color:white;'>
            🕸️ Web Hunter
        </div>
        <div style='font-size:.72rem;color:rgba(255,255,255,.35);margin-top:2px;'>Universal Crawler v2.0</div>
    </div>
    <hr style='border-color:rgba(255,255,255,.08)!important;margin:0 0 1.2rem!important'/>
    """, unsafe_allow_html=True)

    st.markdown("**⚙️ Crawl Settings**")

    depth = st.selectbox(
        "Crawl depth",
        options=[1, 2, 3],
        index=1,
        help="1 = only the given URL | 2 = follow internal links 1 level | 3 = 2 levels deep"
    )

    crawl_js = st.checkbox(
        "Scan JS / data files",
        value=True,
        help="Fetch all <script src=…> JS files and scan them for downloadable content. ESSENTIAL for SPAs."
    )

    respect_robots = st.checkbox("Respect robots.txt", value=True)

    delay = st.slider("Request delay (sec)", 0.3, 3.0, 0.7, 0.1)

    max_internal = st.slider("Max internal pages to crawl", 5, 100, 30)

    st.markdown("<hr style='border-color:rgba(255,255,255,.08)!important;margin:.9rem 0!important'/>",
                unsafe_allow_html=True)

    st.markdown("**🎯 File Types to Find**")

    all_ext_options = [
        ".psd", ".pdf", ".zip", ".rar", ".7z",
        ".ai", ".eps", ".sketch", ".fig", ".xd",
        ".png", ".jpg", ".jpeg", ".svg", ".gif",
        ".docx", ".xlsx", ".pptx",
        ".mp4", ".mp3", ".wav",
        ".js", ".json", ".xml", ".csv"
    ]
    selected_exts = st.multiselect(
        "Extensions to detect",
        options=all_ext_options,
        default=[".psd", ".pdf", ".zip", ".ai", ".eps", ".sketch", ".fig"],
        label_visibility="collapsed"
    )
    if not selected_exts:
        selected_exts = DEFAULT_EXTS

    prefetch_sizes = st.checkbox("Prefetch file sizes (slower)", value=False)

    st.markdown("<hr style='border-color:rgba(255,255,255,.08)!important;margin:.9rem 0!important'/>",
                unsafe_allow_html=True)

    st.markdown("**📤 Export**")
    export_format = st.selectbox("Report format", ["CSV + JSON", "CSV only", "JSON only"])

    st.markdown("""
    <div style='font-size:.7rem;color:rgba(255,255,255,.28);line-height:1.65;margin-top:.8rem;'>
        ⚠️ Only fetches publicly accessible content.<br>
        Respects rate limits. Does not bypass logins.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="badge">🕸️ Website Crawler</div>
    <h1>Web Hunter</h1>
    <p>Crawls any public website — static pages, SPAs, JS-heavy sites — and discovers all downloadable files,
       links, data resources, and page metadata. Exports full CSV + JSON reports.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  INPUT
# ─────────────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5, 1])
with c1:
    url_input = st.text_input(
        "URL",
        placeholder="https://aml-hub.netlify.app/  or  https://freepik.com/free-psds",
        label_visibility="collapsed",
    )
with c2:
    scan_clicked = st.button("🔍 Crawl", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CRAWL ENGINE
# ─────────────────────────────────────────────────────────────────────────────
if scan_clicked and url_input:
    # Reset state
    for k, v in defaults.items():
        st.session_state[k] = v if isinstance(v, (bool, str, int)) else type(v)()

    url = url_input.strip()
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    base_domain = parsed.netloc
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    add_log(f"Starting crawl → {url}", "info")
    add_log(f"Target extensions: {', '.join(selected_exts)}", "info")
    add_log(f"Crawl depth: {depth} | JS scan: {crawl_js}", "info")

    # ── robots.txt ──
    if respect_robots:
        allowed, _ = check_robots(base_url)
        if not allowed:
            add_log("robots.txt disallows. Aborting.", "err")
            st.error("🚫 robots.txt disallows this URL.")
            st.stop()
        else:
            add_log("robots.txt ✓ allowed", "ok")

    # ── Fetch root page ──
    add_log("Fetching root page…", "info")
    progress_bar = st.progress(0, text="Fetching root page…")

    resp = get_page(url)
    if not resp:
        add_log("Could not fetch page.", "err")
        st.error("❌ Could not fetch the URL. It may be down, require login, or block bots.")
        st.stop()

    add_log(f"Root page: HTTP {resp.status_code} — {len(resp.content)//1024} KB", "ok")
    soup = BeautifulSoup(resp.text, "html.parser")

    page_info = extract_page_info(soup, url, resp)
    st.session_state.page_info = page_info
    add_log(f"Title: {page_info['title'] or '(none)'}", "info")

    # ── Crawl pages ──
    pages_to_crawl = [(url, soup)]
    crawled_urls = {url}
    all_files = []
    all_links_int = []
    all_links_ext = []
    all_js_files = []
    all_js_files_seen = set()

    def process_page(pg_url, pg_soup, _files, _links_int, _links_ext, _js_files, _js_seen, label=""):
        """Mutates the passed-in lists directly — avoids nonlocal scoping issue."""
        add_log(f"Processing: {pg_url[:70]}…" if len(pg_url) > 70 else f"Processing: {pg_url}", "info")
        files, lints, lexts, jsf = crawl_page(pg_url, pg_soup, selected_exts, base_domain)

        # Merge files (dedup by URL)
        existing_urls = {f["url"] for f in _files}
        for f in files:
            if f["url"] not in existing_urls:
                _files.append(f)
                existing_urls.add(f["url"])

        _links_int.extend(lints)
        _links_ext.extend(lexts)

        for j in jsf:
            if j["url"] not in _js_seen:
                _js_seen.add(j["url"])
                _js_files.append(j)

        add_log(f"  Found {len(files)} file(s), {len(lints)} internal links, {len(jsf)} JS refs", "ok")

    # Process root
    process_page(url, soup, all_files, all_links_int, all_links_ext, all_js_files, all_js_files_seen, "root")
    progress_bar.progress(0.1, text="Root page processed…")

    # Depth 2+: follow internal links
    if depth >= 2:
        int_candidates = [li["url"] for li in all_links_int if li["url"] not in crawled_urls]
        int_candidates = int_candidates[:max_internal]
        add_log(f"Crawling {len(int_candidates)} internal pages (depth 2)…", "info")

        for i, link in enumerate(int_candidates):
            if link in crawled_urls:
                continue
            crawled_urls.add(link)
            time.sleep(delay)
            r2 = get_page(link)
            if r2:
                s2 = BeautifulSoup(r2.text, "html.parser")
                process_page(link, s2, all_files, all_links_int, all_links_ext, all_js_files, all_js_files_seen)

                # Depth 3
                if depth >= 3:
                    _, sub_lints, _, _ = crawl_page(link, s2, selected_exts, base_domain)
                    for sl in sub_lints[:10]:
                        if sl["url"] not in crawled_urls:
                            int_candidates.append(sl["url"])

            pct = 0.1 + 0.4 * (i + 1) / max(len(int_candidates), 1)
            progress_bar.progress(pct, text=f"Crawling internal page {i+1}/{len(int_candidates)}…")

    # ── Scan JS / data files ──
    js_content_files = []
    js_files_meta = []

    if crawl_js and all_js_files:
        add_log(f"Scanning {len(all_js_files)} JS/data file(s) for embedded content…", "info")
        for i, jsf in enumerate(all_js_files):
            time.sleep(delay * 0.5)
            found, meta = crawl_js_file(jsf["url"], selected_exts)
            if meta:
                js_files_meta.append(meta)
            existing_urls = {f["url"] for f in all_files}
            for f in found:
                if f["url"] not in existing_urls:
                    js_content_files.append(f)
                    existing_urls.add(f["url"])
            if found:
                add_log(f"  {jsf['filename']}: {len(found)} file ref(s) found", "ok")
            else:
                add_log(f"  {jsf['filename']}: no file refs", "info")
            pct = 0.5 + 0.4 * (i + 1) / max(len(all_js_files), 1)
            progress_bar.progress(pct, text=f"Scanning JS: {jsf['filename']}…")

    # ── Prefetch sizes ──
    all_discovered = all_files + js_content_files
    if prefetch_sizes and all_discovered:
        add_log(f"Prefetching sizes for {len(all_discovered)} files…", "info")
        for i, f in enumerate(all_discovered):
            f["file_size"] = get_file_size(f["url"])
            time.sleep(delay * 0.2)
        add_log("Size prefetch complete", "ok")

    # Save to session state
    st.session_state.files = all_files
    st.session_state.js_content_files = js_content_files
    st.session_state.links_int = all_links_int
    st.session_state.links_ext = all_links_ext
    st.session_state.js_files_meta = js_files_meta
    st.session_state.scraped = True

    progress_bar.progress(1.0, text="Crawl complete ✓")
    time.sleep(0.4)
    progress_bar.empty()

    total = len(all_files) + len(js_content_files)
    add_log(
        f"Crawl complete — {total} file(s) found | "
        f"{len(crawled_urls)} pages crawled | "
        f"{len(all_js_files)} JS files scanned",
        "ok"
    )

# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.scraped:
    all_files = st.session_state.files
    js_content_files = st.session_state.js_content_files
    all_discovered = all_files + js_content_files
    links_int = st.session_state.links_int
    links_ext = st.session_state.links_ext
    js_meta = st.session_state.js_files_meta
    page_info = st.session_state.page_info

    # Group by extension
    by_ext = defaultdict(list)
    for f in all_discovered:
        by_ext[f["ext"]].append(f)

    # ── Stat cards ──
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">Files Found</div>
            <div class="stat-value indigo">{len(all_discovered)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">In HTML</div>
            <div class="stat-value">{len(all_files)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">In JS Files</div>
            <div class="stat-value green">{len(js_content_files)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">JS Files Scanned</div>
            <div class="stat-value blue">{len(js_meta)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Internal Links</div>
            <div class="stat-value">{len(links_int)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">External Links</div>
            <div class="stat-value amber">{len(links_ext)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Page Info ──
    pi = page_info
    h2s = ", ".join(pi.get("h2_list", [])[:5]) or "—"
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📋 Page Information</div>
        <div class="card-sub">{pi.get('url','')}</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.75rem">
            <div><div class="stat-label">Title</div><div style="font-size:.85rem;font-weight:500;color:#111">{pi.get('title','—') or '—'}</div></div>
            <div><div class="stat-label">H1</div><div style="font-size:.85rem;font-weight:500;color:#111">{pi.get('h1','—') or '—'}</div></div>
            <div><div class="stat-label">Author</div><div style="font-size:.85rem;color:#374151">{pi.get('author','—') or '—'}</div></div>
            <div><div class="stat-label">H2 headings</div><div style="font-size:.8rem;color:#6B7280">{h2s[:120]}</div></div>
            <div><div class="stat-label">Page size</div><div style="font-size:.85rem;color:#374151">{pi.get('content_size','—')}</div></div>
            <div><div class="stat-label">Scraped at</div><div style="font-size:.85rem;color:#374151">{pi.get('scraped_at','—')}</div></div>
        </div>
        {"<div style='margin-top:.8rem'><div class='stat-label'>Description</div><div style='font-size:.82rem;color:#6B7280'>"+pi.get('description','')[:200]+"</div></div>" if pi.get('description') else ""}
    </div>
    """, unsafe_allow_html=True)

    # ── JS Files scanned ──
    if js_meta:
        items = "".join(
            f'<div class="file-row">'
            f'<div class="file-icon fi-js">⚙️</div>'
            f'<div style="flex:1;min-width:0">'
            f'<div class="file-name">{j["filename"]}</div>'
            f'<div class="file-url">{j["url"]}</div>'
            f'</div>'
            f'<div class="file-meta">{j["size_human"]}</div>'
            f'</div>'
            for j in js_meta
        )
        st.markdown(f"""
        <div class="card">
            <div class="card-title">⚙️ JS / Data Files Scanned</div>
            <div class="card-sub">{len(js_meta)} script file(s) fetched and scanned for embedded content (critical for SPAs)</div>
            {items}
        </div>
        """, unsafe_allow_html=True)

    # ── Tabs ──
    tabs = [
        ("files", f"📦 Found Files ({len(all_discovered)})"),
        ("internal", f"🔗 Internal Links ({len(links_int)})"),
        ("external", f"🌐 External Links ({len(links_ext)})"),
    ]
    tab_html = '<div class="tab-row">' + "".join(
        f'<div class="tab-btn {"active" if st.session_state.active_tab == tid else ""}" '
        f'onclick="window.location.reload()">{label}</div>'
        for tid, label in tabs
    ) + "</div>"

    tcols = st.columns(len(tabs))
    active_tab = st.session_state.active_tab
    for i, (tid, label) in enumerate(tabs):
        with tcols[i]:
            if st.button(label, key=f"tab_{tid}", use_container_width=True):
                st.session_state.active_tab = tid
                active_tab = tid

    # ── Files tab ──
    if active_tab == "files":
        if not all_discovered:
            st.markdown("""
            <div class="card" style="text-align:center;padding:3rem">
                <div style="font-size:3rem;margin-bottom:.8rem">🔍</div>
                <div class="card-title">No downloadable files found</div>
                <div class="card-sub">
                    Try enabling "Scan JS / data files", increasing crawl depth, or adding more file extensions.<br>
                    Note: sites that load content dynamically via JavaScript after page load
                    require a headless browser (Selenium/Playwright) — this tool handles
                    static HTML + JS data files only.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Filter by extension
            ext_choices = sorted(set(f["ext"] for f in all_discovered))
            sel_filter = st.multiselect(
                "Filter by extension",
                ext_choices,
                default=ext_choices,
                key="ext_filter",
            )
            filtered = [f for f in all_discovered if f["ext"] in sel_filter]

            st.markdown(f"""
            <div class="card">
                <div class="card-title">📦 Discovered Files</div>
                <div class="card-sub">{len(filtered)} file(s) — {len(all_files)} from HTML, {len(js_content_files)} from JS data files</div>
            """, unsafe_allow_html=True)

            source_labels = {
                "direct_link": ("🔗", "Direct Link", "p-ok"),
                "data_attribute": ("🏷️", "Data Attr", "p-info"),
                "inline_js": ("⚙️", "Inline JS", "p-warn"),
                "script_src": ("📜", "Script Src", "p-blue"),
                "js_data_file": ("📂", "JS Data File", "p-info"),
                "download_button": ("⬇️", "DL Button", "p-ok"),
            }

            for f in filtered:
                ico = f.get("icon", "📁")
                cls = f.get("icon_cls", "fi-other")
                src_ico, src_label, src_pill = source_labels.get(
                    f["source"], ("📄", f["source"], "p-gray")
                )
                anchor_html = ""
                if f["anchor_text"] and not f["anchor_text"].startswith("["):
                    anchor_html = f'&nbsp;<span class="pill p-gray">{f["anchor_text"][:45]}</span>'

                st.markdown(f"""
                <div class="file-row">
                    <div class="file-icon {cls}">{ico}</div>
                    <div style="flex:1;min-width:0">
                        <div class="file-name">{f['filename']}</div>
                        <div class="file-url">{f['url']}</div>
                        <div style="margin-top:3px">
                            <span class="pill p-gray">{f['ext']}</span>&nbsp;
                            <span class="pill {src_pill}">{src_ico} {src_label}</span>
                            {anchor_html}
                        </div>
                    </div>
                    <div class="file-meta">{f['file_size']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # DataFrame
            st.markdown('<div class="card"><div class="card-title">🗃️ Data Table</div><div class="card-sub">Full structured view</div>', unsafe_allow_html=True)
            df = pd.DataFrame(filtered)
            show_cols = [c for c in ["filename", "ext", "file_size", "source", "anchor_text", "url"] if c in df.columns]
            st.dataframe(df[show_cols], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Export
            st.markdown('<div class="card"><div class="card-title">📊 Export Reports</div><div class="card-sub">Download structured metadata</div>', unsafe_allow_html=True)
            ec1, ec2 = st.columns(2)

            all_data = {
                "page_info": page_info,
                "files": all_discovered,
                "js_files_scanned": js_meta,
                "internal_links": links_int,
                "external_links": links_ext,
            }

            if export_format in ["CSV + JSON", "CSV only"]:
                csv_buf = io.StringIO()
                df_full = pd.DataFrame(all_discovered)
                df_full.drop(columns=["icon", "icon_cls"], errors="ignore", inplace=True)
                df_full.to_csv(csv_buf, index=False)
                with ec1:
                    st.download_button(
                        "⬇️ Download CSV",
                        data=csv_buf.getvalue(),
                        file_name=f"webhunter_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            if export_format in ["CSV + JSON", "JSON only"]:
                clean_data = json.loads(
                    json.dumps(all_data, default=str)
                )
                with ec2:
                    st.download_button(
                        "⬇️ Download JSON",
                        data=json.dumps(clean_data, indent=2, ensure_ascii=False),
                        file_name=f"webhunter_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

            # Download files
            st.markdown('<div class="card"><div class="card-title">⬇️ Download All Files</div><div class="card-sub">Bundle everything as a ZIP archive</div>', unsafe_allow_html=True)
            _, dl_col = st.columns([3, 1])
            with dl_col:
                do_dl = st.button("📦 Build ZIP", use_container_width=True)

            if do_dl:
                prog2 = st.progress(0)
                status2 = st.empty()
                zb = io.BytesIO()
                ok_count, fail_count = 0, 0
                n = len(filtered)

                with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, f in enumerate(filtered):
                        status2.markdown(f"<small>Downloading **{f['filename']}** ({i+1}/{n})…</small>", unsafe_allow_html=True)
                        try:
                            r = requests.get(f["url"], headers=HEADERS, timeout=30, stream=True)
                            r.raise_for_status()
                            zf.writestr(f["filename"], r.content)
                            ok_count += 1
                            add_log(f"Downloaded: {f['filename']}", "ok")
                        except Exception as e:
                            fail_count += 1
                            add_log(f"Failed: {f['filename']} — {e}", "err")
                        prog2.progress((i + 1) / n)
                        time.sleep(delay)

                    # manifest
                    zf.writestr("_manifest.json", json.dumps(all_data, indent=2, default=str))

                status2.empty()
                prog2.empty()
                zb.seek(0)
                st.download_button(
                    f"💾 Save ZIP ({ok_count} ok, {fail_count} failed)",
                    data=zb.getvalue(),
                    file_name=f"webhunter_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Internal links tab ──
    elif active_tab == "internal":
        st.markdown(f'<div class="card"><div class="card-title">🔗 Internal Links ({len(links_int)})</div><div class="card-sub">All links pointing within the same domain</div>', unsafe_allow_html=True)
        if links_int:
            df_int = pd.DataFrame(links_int).drop_duplicates("url").head(200)
            st.dataframe(df_int, use_container_width=True, hide_index=True)
        else:
            st.info("No internal links found.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── External links tab ──
    elif active_tab == "external":
        st.markdown(f'<div class="card"><div class="card-title">🌐 External Links ({len(links_ext)})</div><div class="card-sub">All links pointing to other domains</div>', unsafe_allow_html=True)
        if links_ext:
            df_ext = pd.DataFrame(links_ext).drop_duplicates("url").head(200)
            st.dataframe(df_ext, use_container_width=True, hide_index=True)
        else:
            st.info("No external links found.")
        st.markdown("</div>", unsafe_allow_html=True)

# ── Activity Log ──
if st.session_state.logs:
    st.markdown('<div class="card"><div class="card-title">🖥️ Activity Log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="log-box">' + "<br>".join(st.session_state.logs) + '</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ── Empty state ──
if not st.session_state.scraped and not st.session_state.logs:
    st.markdown("""
    <div class="card" style="text-align:center;padding:4rem 2rem">
        <div style="font-size:4rem;margin-bottom:1rem">🕸️</div>
        <div class="card-title" style="font-size:1.25rem;margin-bottom:.4rem">Ready to Crawl</div>
        <div class="card-sub" style="max-width:520px;margin:0 auto">
            Paste any public URL — static sites, SPAs, design resource pages, or documentation sites.
            Web Hunter crawls the page, follows internal links, and scans JS/data files for
            downloadable content invisible to simple HTML scrapers.
        </div>
        <div style="margin-top:1.8rem;display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap">
            <span class="pill p-ok">✓ Crawls SPAs via JS scanning</span>
            <span class="pill p-info">⚡ Configurable depth</span>
            <span class="pill p-blue">📂 Any file type</span>
            <span class="pill p-warn">📊 CSV + JSON export</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
