# 🎨 PSD Hunter — Web Scraper

A clean, modern Streamlit app to discover, catalogue and download PSD files from any public webpage.

## Features

- **Multi-source detection** — finds PSDs via direct links, `data-*` attributes, embedded scripts, and download buttons
- **Page metadata extraction** — title, description, author, tags, license hints
- **robots.txt compliance** — respects crawling rules by default
- **Configurable crawl depth** — scan just the page, or follow internal links 1–2 levels deep
- **File size prefetching** — HEAD requests to show sizes before download
- **Export reports** — CSV and/or JSON with all metadata
- **ZIP download** — bundles all found PSDs + a JSON manifest
- **Rate limiting** — configurable delay between requests

## Setup

```bash
cd psd_scraper
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. Paste any public URL into the input box
2. Adjust settings in the sidebar (rate limit, depth, export format)
3. Click **Scan**
4. Review found PSDs, page metadata, and activity log
5. Download CSV/JSON report and/or ZIP of all PSD files

## Ethical Notes

- Only scrapes **publicly accessible** pages (no login bypass)
- Respects `robots.txt` by default
- Does not circumvent paywalls or DRM
- Rate-limited to avoid server overload
- Always check a site's Terms of Service before bulk downloading

## Deploy to Streamlit Cloud

1. Push this folder to a GitHub repo
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Set `app.py` as the entry point
4. No secrets needed
