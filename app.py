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
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PSD Hunter — Web Scraper",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
#  CUSTOM CSS — Clean Modern Dashboard
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── App background ── */
.stApp {
    background: #F7F8FC;
}

/* ── Main container tweak ── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}

/* ── Header ── */
.psd-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    color: white;
    position: relative;
    overflow: hidden;
}
.psd-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: rgba(94, 234, 212, 0.08);
}
.psd-header::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 40%;
    width: 160px; height: 160px;
    border-radius: 50%;
    background: rgba(99, 102, 241, 0.10);
}
.psd-header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0 0 0.3rem;
    letter-spacing: -0.5px;
    color: white !important;
}
.psd-header p {
    color: rgba(255,255,255,0.65);
    font-size: 1rem;
    margin: 0;
    font-weight: 300;
}
.psd-badge {
    display: inline-block;
    background: rgba(94,234,212,0.15);
    border: 1px solid rgba(94,234,212,0.3);
    color: #5eead4;
    border-radius: 50px;
    padding: 3px 14px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}

/* ── Stat cards ── */
.stat-row { display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }
.stat-card {
    background: white;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    flex: 1;
    min-width: 140px;
    border: 1px solid #EAECF0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.stat-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-bottom: 0.4rem;
}
.stat-value {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
    line-height: 1;
}
.stat-value.accent { color: #6366F1; }
.stat-value.green  { color: #10B981; }
.stat-value.amber  { color: #F59E0B; }
.stat-value.red    { color: #EF4444; }

/* ── Cards ── */
.card {
    background: white;
    border-radius: 16px;
    padding: 1.8rem;
    border: 1px solid #EAECF0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 1.2rem;
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.2rem;
}
.card-sub {
    font-size: 0.82rem;
    color: #6B7280;
    margin-bottom: 1.2rem;
}

/* ── File row ── */
.file-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.85rem 1rem;
    border-radius: 10px;
    border: 1px solid #F3F4F6;
    margin-bottom: 0.5rem;
    background: #FAFAFA;
    transition: background 0.15s;
}
.file-row:hover { background: #F0F1FF; border-color: #C7D2FE; }
.file-icon {
    width: 36px; height: 36px;
    border-radius: 8px;
    background: linear-gradient(135deg,#6366F1,#8B5CF6);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.file-name { font-weight: 600; font-size: 0.88rem; color: #111827; }
.file-url  { font-size: 0.75rem; color: #9CA3AF; word-break: break-all; }
.file-size { font-size: 0.78rem; color: #6366F1; font-weight: 600; white-space: nowrap; }

/* ── Status pills ── */
.pill {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 50px;
    font-size: 0.73rem; font-weight: 600;
}
.pill-ok  { background: #D1FAE5; color: #065F46; }
.pill-err { background: #FEE2E2; color: #991B1B; }
.pill-warn{ background: #FEF3C7; color: #92400E; }
.pill-info{ background: #E0E7FF; color: #3730A3; }

/* ── Log box ── */
.log-box {
    background: #0D1117;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #7EE8A2;
    max-height: 280px;
    overflow-y: auto;
    border: 1px solid #21262D;
    line-height: 1.7;
}
.log-ts   { color: #484F58; }
.log-ok   { color: #7EE8A2; }
.log-warn { color: #FFB86C; }
.log-err  { color: #FF5555; }
.log-info { color: #8BE9FD; }

/* ── Sidebar tweaks ── */
section[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    border-right: none;
}
section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stCheckbox label {
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.82rem !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.6rem !important;
    border: none !important;
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    color: white !important;
    transition: opacity 0.2s !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Input ── */
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #E5E7EB !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 1rem !important;
    background: white !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Dataframe ── */
.dataframe { font-size: 0.83rem !important; }

/* ── Progress ── */
.stProgress > div > div { background: linear-gradient(90deg,#6366F1,#8B5CF6) !important; border-radius: 10px !important; }

/* ── Divider ── */
hr { border-color: #F3F4F6 !important; margin: 1.5rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def log(msg, level="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    icon = {"ok": "✓", "warn": "⚠", "err": "✗", "info": "›"}.get(level, "›")
    st.session_state.logs.append(
        f'<span class="log-ts">[{ts}]</span> '
        f'<span class="log-{level}">{icon} {msg}</span>'
    )

def check_robots(base_url):
    try:
        rp = urllib.robotparser.RobotFileParser()
        robots_url = urljoin(base_url, "/robots.txt")
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(HEADERS["User-Agent"], base_url)
        return allowed, rp
    except Exception:
        return True, None

def get_page(url, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except Exception as e:
        return None

def extract_page_meta(soup, url):
    title = ""
    description = ""
    author = ""
    license_info = ""
    tags = []

    if soup.title:
        title = soup.title.string or ""

    for m in soup.find_all("meta"):
        name = (m.get("name") or m.get("property") or "").lower()
        content = m.get("content", "")
        if "description" in name:
            description = content
        if "author" in name:
            author = content
        if "keywords" in name:
            tags = [t.strip() for t in content.split(",") if t.strip()][:8]

    # license hints
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").lower()
        text = a.get_text().lower()
        if "license" in href or "creative commons" in text or "cc by" in text:
            license_info = a.get_text(strip=True)[:60]
            break

    return {
        "page_title": title.strip(),
        "description": description[:200],
        "author": author[:100],
        "tags": ", ".join(tags),
        "license": license_info or "Not specified",
        "page_url": url,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def find_psd_links(soup, base_url):
    psd_links = []
    seen = set()

    # 1. Direct .psd href links
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        full = urljoin(base_url, href)
        low = full.lower()
        if low.endswith(".psd") and full not in seen:
            seen.add(full)
            psd_links.append({
                "filename": os.path.basename(urlparse(full).path) or "unknown.psd",
                "url": full,
                "anchor_text": a.get_text(strip=True)[:80],
                "source": "direct_link",
            })

    # 2. data-* attributes that point to .psd
    for tag in soup.find_all(True):
        for attr, val in tag.attrs.items():
            if isinstance(val, str) and ".psd" in val.lower():
                full = urljoin(base_url, val)
                if full not in seen and full.lower().endswith(".psd"):
                    seen.add(full)
                    psd_links.append({
                        "filename": os.path.basename(urlparse(full).path) or "file.psd",
                        "url": full,
                        "anchor_text": f"[data-attr: {attr}]",
                        "source": "data_attribute",
                    })

    # 3. Script/JSON embedded URLs
    scripts = soup.find_all("script")
    for s in scripts:
        text = s.string or ""
        matches = re.findall(r'https?://[^\s\'"<>]+\.psd', text, re.IGNORECASE)
        for m in matches:
            if m not in seen:
                seen.add(m)
                psd_links.append({
                    "filename": os.path.basename(urlparse(m).path) or "file.psd",
                    "url": m,
                    "anchor_text": "[embedded in script]",
                    "source": "script_tag",
                })

    # 4. CDN / download button patterns (common on freebies sites)
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()
        full = urljoin(base_url, href)
        if full in seen:
            continue
        if ("download" in text or "free download" in text) and (
            "psd" in text or "psd" in href.lower()
        ):
            seen.add(full)
            psd_links.append({
                "filename": os.path.basename(urlparse(full).path) or "download.psd",
                "url": full,
                "anchor_text": a.get_text(strip=True)[:80],
                "source": "download_button",
            })

    return psd_links

def get_file_size(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        cl = r.headers.get("Content-Length")
        if cl:
            size = int(cl)
            if size < 1024:
                return f"{size} B"
            elif size < 1024**2:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/1024**2:.1f} MB"
        return "Unknown"
    except Exception:
        return "Unknown"

def download_file(url, delay=1.0):
    time.sleep(delay)
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        return r.content, None
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
for key, val in {
    "logs": [],
    "results": [],
    "meta": {},
    "scraped": False,
    "selected": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1.5rem 0 1rem;'>
        <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;
                    color:white;letter-spacing:-0.5px;'>PSD Hunter</div>
        <div style='font-size:0.75rem;color:rgba(255,255,255,0.4);margin-top:2px;'>
            Web Scraper v1.0
        </div>
    </div>
    <hr style='border-color:rgba(255,255,255,0.08)!important;margin:0 0 1.5rem!important;'/>
    """, unsafe_allow_html=True)

    st.markdown("**⚙️ Scraper Settings**")
    delay = st.slider("Rate limit delay (sec)", 0.5, 3.0, 1.0, 0.5,
                      help="Pause between requests. Higher = more polite.")
    max_depth = st.selectbox("Crawl depth", [1, 2, 3], index=0,
                             help="1 = only the given URL; 2 = follow internal links one level deep")
    respect_robots = st.checkbox("Respect robots.txt", value=True)
    check_file_size = st.checkbox("Prefetch file sizes", value=True,
                                  help="Makes HEAD requests to get file sizes (slower but informative)")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08)!important;margin:1rem 0!important;'/>",
                unsafe_allow_html=True)

    st.markdown("**📂 Export Settings**")
    export_format = st.selectbox("Report format", ["CSV + JSON", "CSV only", "JSON only"])
    zip_downloads = st.checkbox("Bundle downloads as ZIP", value=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08)!important;margin:1rem 0!important;'/>",
                unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.72rem;color:rgba(255,255,255,0.3);line-height:1.6;'>
        ⚠️ Only scrapes publicly accessible content.<br>
        Always respect site terms of service.<br>
        PSD Hunter does not bypass paywalls.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="psd-header">
    <div class="psd-badge">🎨 PSD Scraper</div>
    <h1>PSD Hunter</h1>
    <p>Discover, catalogue and download PSD files from any public webpage — with metadata, licensing info &amp; export reports.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  INPUT
# ─────────────────────────────────────────
col_in, col_btn = st.columns([4, 1])
with col_in:
    url_input = st.text_input(
        "Target URL",
        placeholder="https://www.freepik.com/free-psds  or  https://example.com/resources",
        label_visibility="collapsed",
    )
with col_btn:
    scan_clicked = st.button("🔍 Scan", use_container_width=True)

# ─────────────────────────────────────────
#  SCRAPE LOGIC
# ─────────────────────────────────────────
if scan_clicked and url_input:
    st.session_state.logs = []
    st.session_state.results = []
    st.session_state.meta = {}
    st.session_state.scraped = False

    url = url_input.strip()
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    log(f"Starting scan → {url}", "info")

    # robots.txt
    if respect_robots:
        allowed, rp = check_robots(base_url)
        if not allowed:
            log("robots.txt disallows scraping this URL. Aborting.", "err")
            st.error("🚫 robots.txt disallows access to this URL. Enable 'Ignore robots.txt' to override (at your own risk).")
            st.stop()
        else:
            log("robots.txt check passed ✓", "ok")

    # Fetch page
    log(f"Fetching page…", "info")
    with st.spinner("Fetching page…"):
        resp = get_page(url)

    if resp is None:
        log("Failed to fetch page. Check URL or network.", "err")
        st.error("❌ Could not fetch the URL. It may be behind a login, down, or blocking scrapers.")
        st.stop()

    log(f"Page fetched — HTTP {resp.status_code} — {len(resp.content)//1024} KB", "ok")

    soup = BeautifulSoup(resp.text, "html.parser")
    meta = extract_page_meta(soup, url)
    st.session_state.meta = meta
    log(f"Page title: {meta['page_title'] or '(none)'}", "info")

    # Find PSDs on main page
    all_urls_to_scan = [(url, soup)]

    # Crawl deeper if needed
    if max_depth >= 2:
        log("Crawling internal links (depth 2)…", "info")
        internal_links = set()
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if href.startswith(base_url) and href != url:
                internal_links.add(href)
        internal_links = list(internal_links)[:20]  # cap at 20 sub-pages
        log(f"Found {len(internal_links)} internal links to check", "info")
        time.sleep(delay)
        for link in internal_links:
            r2 = get_page(link)
            if r2:
                s2 = BeautifulSoup(r2.text, "html.parser")
                all_urls_to_scan.append((link, s2))
                time.sleep(delay)

    # Collect all PSDs
    all_psds = []
    seen_psd_urls = set()
    for pg_url, pg_soup in all_urls_to_scan:
        found = find_psd_links(pg_soup, pg_url)
        for f in found:
            if f["url"] not in seen_psd_urls:
                seen_psd_urls.add(f["url"])
                all_psds.append(f)

    log(f"Found {len(all_psds)} PSD file(s)", "ok" if all_psds else "warn")

    # File sizes
    if check_file_size and all_psds:
        log("Prefetching file sizes…", "info")
        for psd in all_psds:
            psd["file_size"] = get_file_size(psd["url"])
            time.sleep(delay * 0.3)
    else:
        for psd in all_psds:
            psd["file_size"] = "—"

    # Enrich with page meta
    for psd in all_psds:
        psd.update({
            "page_title": meta["page_title"],
            "page_url": meta["page_url"],
            "author": meta["author"],
            "license": meta["license"],
            "tags": meta["tags"],
            "scraped_at": meta["scraped_at"],
        })

    st.session_state.results = all_psds
    st.session_state.selected = [p["url"] for p in all_psds]
    st.session_state.scraped = True
    log("Scan complete.", "ok")

# ─────────────────────────────────────────
#  RESULTS DASHBOARD
# ─────────────────────────────────────────
if st.session_state.scraped:
    results = st.session_state.results
    meta = st.session_state.meta
    n = len(results)

    sources = {}
    for r in results:
        s = r.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1

    # ── Stat cards ──
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">PSDs Found</div>
            <div class="stat-value accent">{n}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Direct Links</div>
            <div class="stat-value">{sources.get('direct_link', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Script Embeds</div>
            <div class="stat-value">{sources.get('script_tag', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Data Attrs</div>
            <div class="stat-value">{sources.get('data_attribute', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Download Btns</div>
            <div class="stat-value">{sources.get('download_button', 0)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Page Info card ──
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📄 Page Information</div>
        <div class="card-sub">{meta.get('page_url','')}</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.8rem;">
            <div><span style="font-size:0.72rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;">Title</span>
                 <div style="font-size:0.88rem;color:#111827;font-weight:500;margin-top:2px;">{meta.get('page_title','—') or '—'}</div></div>
            <div><span style="font-size:0.72rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;">Author</span>
                 <div style="font-size:0.88rem;color:#111827;font-weight:500;margin-top:2px;">{meta.get('author','—') or '—'}</div></div>
            <div><span style="font-size:0.72rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;">License</span>
                 <div style="font-size:0.88rem;color:#111827;font-weight:500;margin-top:2px;">{meta.get('license','—') or '—'}</div></div>
            <div><span style="font-size:0.72rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;">Tags</span>
                 <div style="font-size:0.88rem;color:#111827;font-weight:500;margin-top:2px;">{meta.get('tags','—') or '—'}</div></div>
            <div><span style="font-size:0.72rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;">Scanned At</span>
                 <div style="font-size:0.88rem;color:#111827;font-weight:500;margin-top:2px;">{meta.get('scraped_at','—')}</div></div>
            <div><span style="font-size:0.72rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;">Description</span>
                 <div style="font-size:0.82rem;color:#6B7280;margin-top:2px;">{meta.get('description','—')[:120] or '—'}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if n == 0:
        st.markdown("""
        <div class="card" style="text-align:center;padding:3rem;">
            <div style="font-size:3rem;margin-bottom:0.8rem;">🔍</div>
            <div class="card-title">No PSD files found</div>
            <div class="card-sub">
                This page may require login, use JavaScript rendering, or simply has no public PSD links.<br>
                Try increasing crawl depth or checking a different URL.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── File list ──
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📦 Found PSD Files</div>
            <div class="card-sub">{n} file(s) discovered — select below to include in download</div>
        """, unsafe_allow_html=True)

        for r in results:
            src_map = {
                "direct_link": ("🔗", "Direct Link", "pill-ok"),
                "script_tag": ("⚙️", "Script Embed", "pill-warn"),
                "data_attribute": ("🏷️", "Data Attr", "pill-info"),
                "download_button": ("⬇️", "Download Btn", "pill-ok"),
            }
            ico, lbl, pill_cls = src_map.get(r["source"], ("📄", "Unknown", "pill-info"))
            st.markdown(f"""
            <div class="file-row">
                <div class="file-icon">🖼</div>
                <div style="flex:1;min-width:0;">
                    <div class="file-name">{r['filename']}</div>
                    <div class="file-url">{r['url']}</div>
                    <div style="margin-top:4px;">
                        <span class="pill {pill_cls}">{ico} {lbl}</span>
                        {"&nbsp;<span class='pill pill-info'>Anchor: " + r['anchor_text'][:40] + "…</span>" if r['anchor_text'] and not r['anchor_text'].startswith('[') else ""}
                    </div>
                </div>
                <div class="file-size">{r['file_size']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # ── DataFrame preview ──
        st.markdown('<div class="card"><div class="card-title">🗃️ Data Table</div><div class="card-sub">Full structured view of all discovered files</div>', unsafe_allow_html=True)
        df = pd.DataFrame(results)
        display_cols = ["filename", "file_size", "source", "anchor_text", "license", "author", "url"]
        display_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Export Reports ──
        st.markdown('<div class="card"><div class="card-title">📊 Export Reports</div><div class="card-sub">Download structured metadata reports</div>', unsafe_allow_html=True)
        ec1, ec2 = st.columns(2)

        if export_format in ["CSV + JSON", "CSV only"]:
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            with ec1:
                st.download_button(
                    "⬇️ Download CSV Report",
                    data=csv_buf.getvalue(),
                    file_name=f"psd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        if export_format in ["CSV + JSON", "JSON only"]:
            json_data = json.dumps(results, indent=2, ensure_ascii=False)
            with ec2:
                st.download_button(
                    "⬇️ Download JSON Report",
                    data=json_data,
                    file_name=f"psd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Download PSD files ──
        st.markdown('<div class="card"><div class="card-title">⬇️ Download PSD Files</div><div class="card-sub">Fetch all found PSDs and bundle as a ZIP archive</div>', unsafe_allow_html=True)

        dl_col1, dl_col2 = st.columns([3, 1])
        with dl_col2:
            download_all = st.button("📦 Download All PSDs", use_container_width=True)

        if download_all:
            prog = st.progress(0)
            status_txt = st.empty()
            zip_buf = io.BytesIO()
            success, failed = 0, 0

            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, psd in enumerate(results):
                    status_txt.markdown(
                        f"<small>Downloading **{psd['filename']}** ({i+1}/{n})…</small>",
                        unsafe_allow_html=True,
                    )
                    content, err = download_file(psd["url"], delay=delay)
                    if content:
                        zf.writestr(psd["filename"], content)
                        log(f"Downloaded: {psd['filename']}", "ok")
                        success += 1
                    else:
                        log(f"Failed: {psd['filename']} — {err}", "err")
                        failed += 1
                    prog.progress((i + 1) / n)

                # Add JSON manifest inside zip
                manifest = json.dumps(results, indent=2)
                zf.writestr("_manifest.json", manifest)

            status_txt.empty()
            prog.empty()
            zip_buf.seek(0)

            st.download_button(
                f"💾 Save ZIP ({success} files, {failed} failed)",
                data=zip_buf.getvalue(),
                file_name=f"psd_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True,
            )
            log(f"ZIP ready — {success} downloaded, {failed} failed", "ok" if failed == 0 else "warn")

        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  ACTIVITY LOG
# ─────────────────────────────────────────
if st.session_state.logs:
    st.markdown('<div class="card"><div class="card-title">🖥️ Activity Log</div>', unsafe_allow_html=True)
    log_html = "<br>".join(st.session_state.logs)
    st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────
if not st.session_state.scraped and not st.session_state.logs:
    st.markdown("""
    <div class="card" style="text-align:center;padding:4rem 2rem;">
        <div style="font-size:4rem;margin-bottom:1rem;">🎨</div>
        <div class="card-title" style="font-size:1.3rem;margin-bottom:0.5rem;">Ready to Hunt PSDs</div>
        <div class="card-sub" style="max-width:480px;margin:0 auto;">
            Paste any public URL above — design resource sites, freebie pages, portfolios, or any page 
            hosting PSD files. PSD Hunter will discover, catalogue and let you download them all.
        </div>
        <div style="margin-top:2rem;display:flex;gap:0.8rem;justify-content:center;flex-wrap:wrap;">
            <span class="pill pill-ok">✓ Respects robots.txt</span>
            <span class="pill pill-info">⚡ Multi-source detection</span>
            <span class="pill pill-warn">📦 ZIP export</span>
            <span class="pill pill-info">📊 CSV + JSON reports</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
