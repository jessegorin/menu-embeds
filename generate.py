#!/usr/bin/env python3
"""
COO Menu Embed Generator
Fetches a Chowly Online Ordering store page and emits a self-contained,
copy-paste <script> loader that renders a beautified, responsive menu
(items, images, descriptions, prices, and collapsible modifier options)
into a host page via Shadow DOM — fully isolated from the host site's CSS.

Reuses the data layer from the coo-menu-pdf skill (store info, ordering-API
menu fallback, Koala brand colors, hours parsing) and adds modifier
extraction. Images are referenced from the Koala CDN (not base64) to keep
the bundle small.

Usage:
    # Add / update one store and (re)generate its bundle:
    python3 generate.py "https://www.smashvillefl.com/store/21411"

    # Regenerate every store already registered in stores.json (cron mode):
    python3 generate.py --all

Output:
    docs/menu-<id>.js   the embeddable bundle
    stores.json         the registry the --all refresh iterates
"""

import argparse
import gzip
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timedelta, timezone
from html import escape as esc
from pathlib import Path

# Repo root = parent of this script's directory (script lives at <repo>/generate.py
# in the embeds repo, and at <skill>/scripts/generate.py in the skill — both resolve
# their output relative to the current working directory, which the skill sets to the
# repo clone).
REPO_ROOT = Path.cwd()
DOCS_DIR = REPO_ROOT / "docs"
REGISTRY = REPO_ROOT / "stores.json"

PAGES_BASE = "https://jessegorin.github.io/menu-embeds"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def _decompress(raw, enc):
    if enc == "gzip":
        return gzip.decompress(raw)
    if enc == "deflate":
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw


def fetch_bytes(url, extra_headers=None):
    hdr = dict(HEADERS)
    if extra_headers:
        hdr.update(extra_headers)
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return _decompress(r.read(), r.headers.get("Content-Encoding", ""))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None
    except Exception:
        return None


def fetch_text(url, extra_headers=None):
    raw = fetch_bytes(url, extra_headers)
    return raw.decode("utf-8", errors="replace") if raw is not None else None


def fetch_page_data(url):
    """Fetch and parse __NEXT_DATA__ JSON from a COO store page."""
    html = fetch_text(url)
    if not html:
        sys.exit(f"Error: could not fetch {url}")
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not m:
        sys.exit("Could not find __NEXT_DATA__ on the page. Is this a COO store URL?")
    return json.loads(m.group(1)), html


def fetch_menu_api(token, org_id, location_id, operating_hours=None):
    """Fetch the menu from the ordering API when __NEXT_DATA__ carries no products.

    The ordering API only returns products for times the store is open, so we
    aim wanted-at inside the next upcoming open window.
    """
    now_utc = datetime.now(timezone.utc)
    wanted = None
    if operating_hours:
        future = []
        for h in operating_hours:
            try:
                start_dt = datetime.fromisoformat(h.get("start", "").replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(h.get("end", "").replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                if end_dt > now_utc:
                    future.append((start_dt, end_dt))
            except Exception:
                pass
        if future:
            future.sort(key=lambda x: x[0])
            start_dt, end_dt = future[0]
            mid = start_dt + (end_dt - start_dt) / 2
            target = max(start_dt + timedelta(minutes=30), min(mid, end_dt - timedelta(minutes=5)))
            wanted = target.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    if not wanted:
        wanted = (now_utc + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    api_url = (
        f"https://prod-coo-api.chowly.io/v1/ordering/store-locations/{location_id}/menu"
        f"?wanted-at={urllib.parse.quote(wanted)}"
    )
    raw = fetch_bytes(api_url, {
        "Authorization": f"Bearer {token}",
        "x-organization-id": str(org_id),
        "Accept": "application/json",
    })
    if raw is None:
        return []
    try:
        return json.loads(raw.decode()).get("data", {}).get("categories", [])
    except Exception:
        return []


def fetch_brand_colors(token, org_id):
    """Fetch brand colors from the Koala web-config API (with safe fallback)."""
    fallback = {
        "accent": "#111111",
        "body_bg": "#ffffff",
        "text_dark": "#1a1a1a",
        "section_bg": "#f6f6f6",
    }
    raw = fetch_bytes(
        "https://prod-coo-api.chowly.io/configurations/schema/v1/config/label/web-config",
        {"Authorization": f"Bearer {token}", "x-organization-id": str(org_id),
         "Accept": "application/json"},
    )
    if raw is None:
        return fallback
    try:
        cfg = json.loads(raw.decode())["data"]["data"]
        g = cfg.get("global", {})
        txt = cfg.get("text", {})
        return {
            "accent": g.get("primary_active_color") or fallback["accent"],
            "body_bg": g.get("body_color") or fallback["body_bg"],
            "text_dark": txt.get("primary_text_color") or fallback["text_dark"],
            "section_bg": "#f6f6f6",
        }
    except Exception:
        return fallback


def parse_hours(operating_hours, utc_offset=-4):
    """Convert operating_hours to readable, grouped day->time strings."""
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = {}
    tz = timezone(timedelta(hours=utc_offset))
    for h in operating_hours:
        day = h.get("day_of_week", "")
        start_str = h.get("start", "")
        end_str = h.get("end", "")
        if not day or not start_str:
            continue
        try:
            start_local = datetime.fromisoformat(start_str.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).astimezone(tz)
            end_local = datetime.fromisoformat(end_str.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).astimezone(tz)
            by_day[day] = f"{start_local.strftime('%-I:%M %p')} – {end_local.strftime('%-I:%M %p')}"
        except Exception:
            by_day[day] = "See website"
    if not by_day:
        return []
    days_seen = [(d, by_day[d]) for d in day_order if d in by_day]
    groups = []
    start_day, current, end_day = days_seen[0][0], days_seen[0][1], days_seen[0][0]
    for day, hours in days_seen[1:]:
        if hours == current:
            end_day = day
        else:
            groups.append((start_day, end_day, current))
            start_day, current, end_day = day, hours, day
    groups.append((start_day, end_day, current))
    out = []
    for start, end, hours in groups:
        out.append(f"{start}: {hours}" if start == end else f"{start[:3]}–{end[:3]}: {hours}")
    return out


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def format_price(cents):
    if cents is None:
        return ""
    return f"${cents / 100:.2f}"


def format_upcharge(cents):
    if not cents:
        return ""
    return f"+${cents / 100:.2f}"


def readable_on(hex_color):
    """Return black or white — whichever is readable on the given hex color."""
    try:
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        # relative luminance (sRGB, simple linearization)
        def lin(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
        return "#1a1a1a" if lum > 0.5 else "#ffffff"
    except Exception:
        return "#ffffff"


def extract_modifiers(product):
    """Flatten a product's option_groups into display-ready modifier groups."""
    groups = []
    for g in product.get("option_groups", []) or []:
        if g.get("is_hidden"):
            continue
        choices = []
        for o in g.get("options", []) or []:
            if o.get("is_available") is False or o.get("is_hidden"):
                continue
            name = o.get("name") or o.get("description")
            if not name:
                continue
            choices.append({"name": name, "up": format_upcharge(o.get("cost"))})
        if not choices:
            continue
        mn = g.get("min_selections")
        mx = g.get("max_selections")
        if mn and mn > 0:
            rule = "Required" + (f" · choose {mx}" if mx and mx > 1 else "")
        elif mx and mx > 0:
            rule = f"Optional · up to {mx}"
        else:
            rule = "Optional"
        groups.append({
            "label": g.get("description") or "Options",
            "rule": rule,
            "choices": choices,
        })
    return groups


def extract_menu(data):
    """Pull menu sections from __NEXT_DATA__, falling back to the ordering API."""
    app = data["props"]["pageProps"]["initialState"]["app"]
    org = app["organization"].get("organization", {})
    loc = app["locations"]["detail"]
    token = app.get("global", {}).get("token", {}).get("access_token", "")

    queries = data["props"]["pageProps"]["initialProps"]["props"]["serverState"]["queries"]
    sections = []
    for q in queries:
        if q["queryKey"][0] == "menu":
            raw = q["state"]["data"]
            sections = raw[0] if isinstance(raw, list) and raw else raw
            break

    total = sum(len(s.get("products", [])) for s in sections)
    if total == 0 and sections is not None:
        sections = fetch_menu_api(
            token, org.get("id", ""), loc.get("id", ""),
            operating_hours=loc.get("operating_hours", []),
        ) or sections
    return sections or [], app, org, loc, token


def extract_store(app, org, loc):
    name = loc.get("label") or org.get("label", "Restaurant")
    slug = org.get("slug", "menu")
    cached = loc.get("cached_data", {})

    phone_raw = loc.get("phone_number") or cached.get("phone_number", "")
    phone = (f"({phone_raw[:3]}) {phone_raw[3:6]}-{phone_raw[6:]}"
             if phone_raw and len(phone_raw) == 10 else phone_raw)

    street = loc.get("street_address") or cached.get("street_address", "")
    city = loc.get("city") or cached.get("city", "")
    state = ""
    for k in ("state", "state_id"):
        v = loc.get(k) or cached.get(k)
        if isinstance(v, str) and len(v) <= 3:
            state = v
            break
    zip_code = loc.get("zip_code") or cached.get("zip", "")
    address = ", ".join(filter(None, [street, city, state, zip_code]))

    utc_offset = cached.get("utc_offset", -4)
    hours = parse_hours(loc.get("operating_hours", []), utc_offset=utc_offset)
    return {"name": name, "slug": slug, "address": address, "phone": phone, "hours": hours}


def extract_logo(html):
    m = re.search(r'nav-logo[^>]+href="[^"]*"[^>]*>\s*<img[^>]+src="([^"]+)"', html)
    if not m:
        return None
    raw_logo = m.group(1)
    source_m = re.search(r"source=([^&\"]+)", raw_logo)
    if source_m:
        return urllib.parse.unquote(source_m.group(1))
    return raw_logo


def item_image(product):
    imgs = product.get("images") or {}
    return (imgs.get("image_url_1_by_1") or imgs.get("image_url_2_by_3")
            or imgs.get("image_url_3_by_2") or product.get("image") or "")


def build_data(store, sections, colors, logo_url, store_url):
    out_sections = []
    for section in sections:
        items = []
        for p in section.get("products", []):
            if p.get("is_disabled"):
                continue
            items.append({
                "name": p.get("name", "").strip(),
                "desc": (p.get("description") or "").strip(),
                "price": format_price(p.get("cost")),
                "img": item_image(p),
                "mods": extract_modifiers(p),
            })
        if items:
            out_sections.append({"name": section.get("name", ""), "items": items})
    colors = {**colors, "on_accent": readable_on(colors.get("accent", "#111"))}
    return {
        "store": {
            "name": store["name"], "address": store["address"],
            "phone": store["phone"], "hours": store["hours"], "url": store_url,
        },
        "colors": colors,
        "logo": logo_url or "",
        "sections": out_sections,
    }


# ---------------------------------------------------------------------------
# Bundle (the embeddable JS)
# ---------------------------------------------------------------------------

# The runtime renderer, injected verbatim into every bundle. It builds the menu
# inside a Shadow DOM so nothing on the host page can leak in or out.
RENDERER = r"""
function chowlyRenderMenu(DATA, mountId) {
  var host = document.getElementById(mountId);
  if (!host) { console.warn("[chowly-menu] container #" + mountId + " not found"); return; }
  var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;

  var c = DATA.colors || {};
  var accent = c.accent || "#111";
  var onAccent = c.on_accent || "#fff";
  var textDark = c.text_dark || "#1a1a1a";
  var sectionBg = c.section_bg || "#f6f6f6";

  var css = "\n" +
    ":host { display:block; width:100%; }\n" +
    ":host, * { box-sizing: border-box; }\n" +
    ".cm { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;" +
      " color:" + textDark + "; --accent:" + accent + "; --on-accent:" + onAccent + "; --sec:" + sectionBg + ";" +
      " width:100%; line-height:1.5; }\n" +
    ".cm-head { text-align:center; padding:8px 12px 16px; }\n" +
    ".cm-logo { max-width:180px; max-height:80px; object-fit:contain; margin:0 auto 10px; display:block; }\n" +
    ".cm-name { font-size:1.7rem; font-weight:800; letter-spacing:-.01em; margin:0 0 4px; color:var(--accent); }\n" +
    ".cm-meta { font-size:.82rem; color:#6b6b6b; display:flex; gap:6px 18px; flex-wrap:wrap; justify-content:center; }\n" +
    ".cm-hours { font-size:.78rem; color:#7a7a7a; margin-top:6px; }\n" +
    /* horizontal scrolling category nav */
    ".cm-nav { display:flex; gap:8px; overflow-x:auto; overflow-y:hidden; padding:10px 2px;" +
      " position:sticky; top:0; z-index:5; background:rgba(255,255,255,.96);" +
      " backdrop-filter:saturate(160%) blur(6px); -webkit-backdrop-filter:saturate(160%) blur(6px);" +
      " border-bottom:1px solid rgba(0,0,0,.08); scroll-behavior:smooth; -webkit-overflow-scrolling:touch; }\n" +
    ".cm-nav::-webkit-scrollbar { height:6px; }\n" +
    ".cm-nav::-webkit-scrollbar-thumb { background:rgba(0,0,0,.18); border-radius:3px; }\n" +
    ".cm-nav { scrollbar-width:thin; }\n" +
    ".cm-tab { flex:0 0 auto; white-space:nowrap; padding:8px 16px; border-radius:999px;" +
      " border:1px solid rgba(0,0,0,.15); background:#fff; font:inherit; font-size:.82rem; font-weight:700;" +
      " color:#555; cursor:pointer; transition:background .15s,color .15s,border-color .15s; }\n" +
    ".cm-tab:hover { border-color:var(--accent); color:var(--accent); }\n" +
    ".cm-tab.cm-active { background:var(--accent); color:var(--on-accent); border-color:var(--accent); }\n" +
    ".cm-panel { display:none; padding-top:20px; }\n" +
    ".cm-panel.cm-active { display:block; }\n" +
    ".cm-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; }\n" +
    ".cm-item { background:#fff; border:1px solid rgba(0,0,0,.08); border-radius:12px; overflow:hidden;" +
      " display:flex; flex-direction:column; transition:box-shadow .15s ease,transform .15s ease; }\n" +
    ".cm-item:hover { box-shadow:0 6px 22px rgba(0,0,0,.09); transform:translateY(-1px); }\n" +
    ".cm-img { width:100%; aspect-ratio:16/10; object-fit:cover; background:var(--sec); }\n" +
    ".cm-body { padding:12px 14px 14px; display:flex; flex-direction:column; flex:1; }\n" +
    ".cm-row { display:flex; justify-content:space-between; align-items:baseline; gap:10px; }\n" +
    ".cm-iname { font-size:.98rem; font-weight:700; margin:0; }\n" +
    ".cm-price { font-size:.95rem; font-weight:800; color:var(--accent); white-space:nowrap;" +
      " font-variant-numeric:tabular-nums; }\n" +
    ".cm-desc { font-size:.83rem; color:#6b6b6b; margin:5px 0 0; }\n" +
    ".cm-optbtn { margin-top:10px; align-self:flex-start; background:none; border:none; padding:4px 0;" +
      " font:inherit; font-size:.78rem; font-weight:700; color:var(--accent); cursor:pointer;" +
      " display:inline-flex; align-items:center; gap:5px; }\n" +
    ".cm-optbtn .cm-caret { transition:transform .18s ease; display:inline-block; }\n" +
    ".cm-optbtn[aria-expanded='true'] .cm-caret { transform:rotate(90deg); }\n" +
    ".cm-opts { display:none; margin-top:8px; border-top:1px dashed rgba(0,0,0,.12); padding-top:10px; }\n" +
    ".cm-opts.cm-open { display:block; }\n" +
    ".cm-grp { margin-bottom:10px; }\n" +
    ".cm-grp:last-child { margin-bottom:0; }\n" +
    ".cm-glabel { font-size:.74rem; font-weight:800; letter-spacing:.02em; }\n" +
    ".cm-grule { font-size:.66rem; font-weight:600; color:#9a9a9a; text-transform:uppercase;" +
      " letter-spacing:.06em; margin-left:6px; }\n" +
    ".cm-choices { list-style:none; margin:5px 0 0; padding:0; }\n" +
    ".cm-choice { display:flex; justify-content:space-between; font-size:.8rem; color:#555;" +
      " padding:2px 0; gap:10px; }\n" +
    ".cm-up { color:var(--accent); font-weight:700; font-variant-numeric:tabular-nums; }\n" +
    ".cm-footer { text-align:center; font-size:.72rem; color:#aaa; margin:28px 0 6px; }\n" +
    ".cm-footer a { color:inherit; }\n" +
    "@media (max-width:520px){ .cm-grid{ grid-template-columns:1fr; } .cm-name{ font-size:1.4rem; } }\n";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  function itemCard(it) {
    var h = "<article class='cm-item'>";
    if (it.img) h += "<img class='cm-img' loading='lazy' src='" + esc(it.img) + "' alt='" + esc(it.name) + "'>";
    h += "<div class='cm-body'><div class='cm-row'><h3 class='cm-iname'>" + esc(it.name) + "</h3>";
    if (it.price) h += "<span class='cm-price'>" + esc(it.price) + "</span>";
    h += "</div>";
    if (it.desc) h += "<p class='cm-desc'>" + esc(it.desc) + "</p>";
    if (it.mods && it.mods.length) {
      h += "<button class='cm-optbtn' type='button' aria-expanded='false'>" +
        "<span class='cm-caret'>&#9656;</span>Options</button><div class='cm-opts'>";
      it.mods.forEach(function (g) {
        h += "<div class='cm-grp'><span class='cm-glabel'>" + esc(g.label) + "</span>" +
          "<span class='cm-grule'>" + esc(g.rule) + "</span><ul class='cm-choices'>";
        g.choices.forEach(function (ch) {
          h += "<li class='cm-choice'><span>" + esc(ch.name) + "</span>" +
            (ch.up ? "<span class='cm-up'>" + esc(ch.up) + "</span>" : "") + "</li>";
        });
        h += "</ul></div>";
      });
      h += "</div>";
    }
    return h + "</div></article>";
  }

  var html = "<style>" + css + "</style><div class='cm'>";

  // Header
  html += "<div class='cm-head'>";
  if (DATA.logo) html += "<img class='cm-logo' src='" + esc(DATA.logo) + "' alt='" + esc(DATA.store.name) + " logo'>";
  html += "<h2 class='cm-name'>" + esc(DATA.store.name) + "</h2><div class='cm-meta'>";
  if (DATA.store.address) html += "<span>" + esc(DATA.store.address) + "</span>";
  if (DATA.store.phone) html += "<span>" + esc(DATA.store.phone) + "</span>";
  html += "</div>";
  if (DATA.store.hours && DATA.store.hours.length)
    html += "<div class='cm-hours'>" + DATA.store.hours.map(esc).join(" &nbsp;·&nbsp; ") + "</div>";
  html += "</div>";

  // Category nav (horizontal scroll) — one tab per section
  html += "<nav class='cm-nav' role='tablist' aria-label='Menu categories'>";
  DATA.sections.forEach(function (sec, i) {
    html += "<button class='cm-tab" + (i === 0 ? " cm-active" : "") + "' role='tab' type='button'" +
      " data-i='" + i + "' aria-selected='" + (i === 0) + "'>" + esc(sec.name) + "</button>";
  });
  html += "</nav>";

  // One panel per section; only the active one is shown
  DATA.sections.forEach(function (sec, i) {
    html += "<section class='cm-panel" + (i === 0 ? " cm-active" : "") + "' role='tabpanel' data-i='" + i + "'>" +
      "<div class='cm-grid'>";
    sec.items.forEach(function (it) { html += itemCard(it); });
    html += "</div></section>";
  });

  html += "<div class='cm-footer'>Menu powered by Chowly";
  if (DATA.store.url) html += " · <a href='" + esc(DATA.store.url) + "' target='_blank' rel='noopener'>Order online</a>";
  html += "</div></div>";

  root.innerHTML = html;

  var nav = root.querySelector(".cm-nav");
  function selectCategory(i) {
    root.querySelectorAll(".cm-tab").forEach(function (t) {
      var on = t.getAttribute("data-i") === String(i);
      t.classList.toggle("cm-active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
    root.querySelectorAll(".cm-panel").forEach(function (p) {
      p.classList.toggle("cm-active", p.getAttribute("data-i") === String(i));
    });
  }

  root.addEventListener("click", function (e) {
    var tab = e.target.closest && e.target.closest(".cm-tab");
    if (tab) {
      selectCategory(tab.getAttribute("data-i"));
      // keep the chosen tab visible in the horizontal bar
      if (tab.scrollIntoView) tab.scrollIntoView({ inline: "center", block: "nearest" });
      return;
    }
    var btn = e.target.closest && e.target.closest(".cm-optbtn");
    if (btn) {
      var opts = btn.parentNode.querySelector(".cm-opts");
      var open = opts.classList.toggle("cm-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    }
  });
}
"""


def build_bundle(data, store_id):
    """Wrap DATA + renderer in an IIFE that self-mounts."""
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""/*! Chowly menu embed — store {store_id} — generated {generated}
 * Paste onto any site:
 *   <div id="chowly-menu"></div>
 *   <script src="{PAGES_BASE}/menu-{store_id}.js"></script>
 * Optional custom container:
 *   <div id="my-menu"></div>
 *   <script src="{PAGES_BASE}/menu-{store_id}.js" data-target="my-menu"></script>
 */
(function () {{
  var DATA = {data_json};
{RENDERER}
  var mount = "chowly-menu";
  var cs = document.currentScript;
  if (cs && cs.dataset && cs.dataset.target) mount = cs.dataset.target;
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", function () {{ chowlyRenderMenu(DATA, mount); }});
  }} else {{
    chowlyRenderMenu(DATA, mount);
  }}
}})();
"""


# ---------------------------------------------------------------------------
# Registry + index
# ---------------------------------------------------------------------------

def load_registry():
    if REGISTRY.exists():
        try:
            return json.loads(REGISTRY.read_text())
        except Exception:
            return []
    return []


def save_registry(reg):
    reg_sorted = sorted(reg, key=lambda s: s["id"])
    REGISTRY.write_text(json.dumps(reg_sorted, indent=2) + "\n")


def store_id_from_url(url):
    m = re.search(r"/store/(\d+)", url)
    return m.group(1) if m else re.sub(r"\W+", "", url)[-8:]


# Shared page chrome. Plain (non-f) strings so CSS/JS braces stay literal.
SHELL_CSS = """
  *, *::before, *::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }

  :root {
    --navy: #001f52;
    --brand-blue: #1B51A4;
    --accent-blue: #3B82F6;
    --sky: #38bdf8;
    --heading-navy: #0a2540;
    --text-body: #3b4563;
    --text-muted: #6b7a99;
    --text-subtle: #8b95ad;
    --surface: #ffffff;
    --surface-raised: #f8f9fc;
    --border: #e2e8f0;
    --border-subtle: #eef2f7;
    --font-head: Lato, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    --font-body: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;
    color-scheme: light;
  }

  body {
    font-family: var(--font-body);
    background: linear-gradient(180deg, #ffffff 0%, #f8f9fc 38%, #f0f3fa 100%);
    color: var(--text-body);
    line-height: 1.6;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }

  h1, h2 { font-family: var(--font-head); margin: 0; text-wrap: balance; }

  .wrap { max-width: 860px; margin: 0 auto; padding-inline: 24px; }

  .masthead {
    background: linear-gradient(150deg, #020817 0%, #001131 38%, #001f52 72%, #0c2d6b 100%);
    padding: 26px 0 46px;
    color: #fff;
  }
  .crumbs { margin-bottom: 26px; }
  .crumbs a {
    color: rgba(255,255,255,.72); text-decoration: none;
    font-size: 13px; font-weight: 600;
  }
  .crumbs a:hover { color: #fff; }
  .crumbs a:focus-visible { outline: 2px solid #fff; outline-offset: 3px; border-radius: 3px; }

  .eyebrow {
    margin: 0 0 12px; font-size: 11px; font-weight: 800;
    letter-spacing: 1.6px; text-transform: uppercase; color: var(--sky);
  }
  .masthead h1 {
    font-size: 2.1rem; font-weight: 900; line-height: 1.1;
    letter-spacing: -0.02em; color: #fff;
  }
  .lede { margin: 12px 0 0; color: rgba(255,255,255,.68); font-size: 14.5px; }

  main { padding-bottom: 60px; }

  /* ---------- index list ---------- */
  .list { list-style: none; padding: 0; margin: -26px 0 0; display: flex; flex-direction: column; gap: 12px; }
  a.row {
    display: flex; align-items: center; justify-content: space-between; gap: 18px;
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    padding: 20px 22px; text-decoration: none;
    box-shadow: 0 6px 20px rgba(0,0,0,.06);
    transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
  }
  a.row:hover { transform: translateY(-2px); border-color: var(--brand-blue); box-shadow: 0 14px 38px rgba(0,0,0,.10); }
  a.row:focus-visible { outline: 3px solid var(--brand-blue); outline-offset: 3px; }
  .row .name { display: block; font-family: var(--font-head); font-weight: 700; font-size: 1.05rem; color: var(--heading-navy); }
  .row .file { display: block; font-size: 12.5px; color: var(--text-subtle); margin-top: 3px; }
  .row .go { flex: 0 0 auto; font-size: 13.5px; font-weight: 600; color: var(--brand-blue); white-space: nowrap; }
  .empty { margin-top: -26px; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }

  /* ---------- store page ---------- */
  .panel {
    margin-top: 20px; background: var(--surface); border: 1px solid var(--border);
    border-radius: 18px; padding: 26px 26px 28px;
  }
  .panel:first-of-type { margin-top: -26px; box-shadow: 0 6px 20px rgba(0,0,0,.06); }
  .panel h2 { font-size: 1.15rem; font-weight: 700; color: var(--heading-navy); margin-bottom: 6px; }
  .hint { font-size: 13.5px; color: var(--text-muted); margin: 0 0 14px; }
  .hint code { background: var(--surface-raised); border: 1px solid var(--border-subtle); padding: 1px 6px; border-radius: 5px; font-size: 12.5px; }

  .snip { position: relative; margin-bottom: 18px; }
  .snip pre {
    margin: 0; background: #0a1428; color: #e6ecf7; padding: 16px 84px 16px 16px;
    border-radius: 12px; overflow-x: auto; font-size: 12.5px; line-height: 1.65;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  .copy {
    position: absolute; top: 10px; right: 10px;
    background: rgba(255,255,255,.1); color: #fff; border: 1px solid rgba(255,255,255,.2);
    border-radius: 8px; padding: 5px 12px; font: 600 12px var(--font-body);
    cursor: pointer; transition: background 150ms ease;
  }
  .copy:hover { background: rgba(255,255,255,.18); }
  .copy:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
  .copy.done { background: #2e7d32; border-color: #2e7d32; }

  .preview-frame { border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; }
  .srcline { margin: 22px 0 0; font-size: 13px; color: var(--text-muted); }
  .srcline a { color: var(--brand-blue); font-weight: 600; text-decoration: none; }
  .srcline a:hover { text-decoration: underline; }

  @media (max-width: 560px) {
    .masthead h1 { font-size: 1.7rem; }
    a.row { flex-direction: column; align-items: flex-start; gap: 10px; }
    .panel { padding: 20px; }
  }

  @media (prefers-reduced-motion: reduce) {
    a.row { transition: none; }
    a.row:hover { transform: none; }
  }
"""

COPY_JS = """
document.querySelectorAll('.copy').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var pre = document.getElementById(btn.getAttribute('data-copy'));
    if (!pre) return;
    var done = function () {
      var prev = btn.textContent;
      btn.textContent = 'Copied';
      btn.classList.add('done');
      setTimeout(function () { btn.textContent = prev; btn.classList.remove('done'); }, 1600);
    };
    var fallback = function () {
      var range = document.createRange();
      range.selectNodeContents(pre);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(pre.innerText).then(done, fallback);
    } else {
      fallback();
    }
  });
});
"""


def _document(title, body, extra_script=""):
    """Standard document shell shared by the index and every store page."""
    tail = f"\n<script>{extra_script}</script>" if extra_script else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title}</title>
<style>{SHELL_CSS}</style>
</head>
<body>
{body}{tail}
</body>
</html>
"""


def _snippet(sid, target=None):
    """The escaped copy-paste snippet for a store, as it should render in a <pre>."""
    div_id = target or "chowly-menu"
    attr = f' data-target="{esc(target)}"' if target else ""
    return (f'&lt;div id="{esc(div_id)}"&gt;&lt;/div&gt;\n'
            f'&lt;script src="{PAGES_BASE}/menu-{sid}.js"{attr}&gt;&lt;/script&gt;')


def write_store_page(s, generated):
    """Write docs/<id>/index.html — one loader, its snippet, and a live preview."""
    sid = s["id"]
    name = esc(s.get("name", sid))
    store_url = s.get("url", "")
    out_dir = DOCS_DIR / sid
    out_dir.mkdir(parents=True, exist_ok=True)

    source_link = (f'<a href="{esc(store_url)}" rel="noreferrer">Source store &#8599;</a> &middot; '
                   if store_url else "")

    body = f"""<header class="masthead">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">&larr; All menu embeds</a></nav>
    <p class="eyebrow">Menu embed</p>
    <h1>{name}</h1>
    <p class="lede">Store {sid} &middot; rebuilt nightly &middot; last built {generated}</p>
  </div>
</header>

<main class="wrap">

  <section class="panel">
    <h2>Paste this into the site</h2>
    <p class="hint">The menu renders wherever the div sits. Nothing else to install.</p>
    <div class="snip">
      <button class="copy" type="button" data-copy="snip-default">Copy</button>
      <pre id="snip-default">{_snippet(sid)}</pre>
    </div>
    <p class="hint">To mount it somewhere else on the page, point <code>data-target</code> at your own element:</p>
    <div class="snip">
      <button class="copy" type="button" data-copy="snip-target">Copy</button>
      <pre id="snip-target">{_snippet(sid, target="my-menu")}</pre>
    </div>
    <p class="srcline">{source_link}<a href="../menu-{sid}.js">View the loader &#8599;</a></p>
  </section>

  <section class="panel">
    <h2>Live preview</h2>
    <p class="hint">Exactly what the snippet renders. Refreshes with tonight's rebuild.</p>
    <div class="preview-frame">
      <div id="chowly-menu"></div>
      <script src="../menu-{sid}.js"></script>
    </div>
  </section>

</main>"""

    (out_dir / "index.html").write_text(
        _document(f"{name} — menu embed", body, extra_script=COPY_JS),
        encoding="utf-8",
    )


def prune_orphan_pages(live_ids):
    """Delete store-page directories for stores no longer in the registry.

    Drop a store from stores.json and its page must stop being served — a
    churned customer's menu should not sit at a public URL indefinitely.

    Deliberately narrow: only removes a directory whose name is all digits
    (a store id) and whose sole contents are the index.html we generate.
    Anything else is left alone rather than guessed at. Bundles
    (docs/menu-<id>.js) are NOT touched — sites may still be loading them,
    and pulling one would blank a live customer's menu without warning.
    """
    if not DOCS_DIR.exists():
        return
    for child in sorted(DOCS_DIR.iterdir()):
        if not child.is_dir() or not child.name.isdigit() or child.name in live_ids:
            continue
        contents = {p.name for p in child.iterdir()}
        if contents and contents != {"index.html"}:
            print(f"[prune] SKIPPED {child} — unexpected contents: {sorted(contents)}")
            continue
        for p in child.iterdir():
            p.unlink()
        child.rmdir()
        print(f"[prune] removed stale store page {child}")


def rebuild_index(reg):
    """Write docs/index.html plus one page per registered loader.

    Each store gets its own page so its preview actually renders — every bundle
    mounts into #chowly-menu, so the old single-page gallery could only ever
    show the first store's menu.
    """
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stores = sorted(reg, key=lambda x: x.get("name", x["id"]).lower())

    rows = []
    for s in stores:
        sid = s["id"]
        rows.append(f"""    <li><a class="row" href="./{sid}/">
      <span>
        <span class="name">{esc(s.get('name', sid))}</span>
        <span class="file">menu-{sid}.js &middot; store {sid}</span>
      </span>
      <span class="go">Get the snippet &rarr;</span>
    </a></li>""")
        write_store_page(s, generated)

    prune_orphan_pages({s["id"] for s in stores})

    count = len(stores)
    listing = ("  <ul class=\"list\">\n" + "\n".join(rows) + "\n  </ul>") if rows else \
              '  <p class="empty">No stores registered yet. Run <code>generate.py &lt;store-url&gt;</code> to add one.</p>'

    body = f"""<header class="masthead">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="https://jessegorin.github.io/">&larr; All work</a></nav>
    <p class="eyebrow">Chowly Online Ordering</p>
    <h1>Menu embeds</h1>
    <p class="lede">Copy-paste loaders that render a live menu into any website.
      {count} loader{'' if count == 1 else 's'} &middot; rebuilt nightly &middot; last built {generated}</p>
  </div>
</header>

<main class="wrap">
{listing}
</main>"""

    (DOCS_DIR / "index.html").write_text(
        _document("Chowly menu embeds", body), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Core generate
# ---------------------------------------------------------------------------

def generate_one(url):
    url = url.rstrip("/")
    store_id = store_id_from_url(url)
    print(f"[{store_id}] fetching {url}")
    data, html = fetch_page_data(url)
    sections, app, org, loc, token = extract_menu(data)
    store = extract_store(app, org, loc)
    colors = fetch_brand_colors(token, org.get("id", ""))
    logo_url = extract_logo(html)

    total = sum(len(s.get("products", [])) for s in sections)
    print(f"[{store_id}] {store['name']} — {len(sections)} sections, {total} items, accent {colors['accent']}")
    if total == 0:
        print(f"[{store_id}] WARNING: no menu items found (store may be closed / no upcoming window)")

    bundle_data = build_data(store, sections, colors, logo_url, url)
    n_items = sum(len(s["items"]) for s in bundle_data["sections"])
    n_mods = sum(len(it["mods"]) for s in bundle_data["sections"] for it in s["items"])
    print(f"[{store_id}] rendered {n_items} items, {n_mods} modifier groups")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out = DOCS_DIR / f"menu-{store_id}.js"
    out.write_text(build_bundle(bundle_data, store_id), encoding="utf-8")
    print(f"[{store_id}] wrote {out} ({out.stat().st_size // 1024} KB)")

    return {"id": store_id, "url": url, "name": store["name"], "slug": store["slug"]}


def main():
    ap = argparse.ArgumentParser(description="Generate embeddable COO menu loaders")
    ap.add_argument("url", nargs="?", help="COO store URL (omit with --all)")
    ap.add_argument("--all", action="store_true", help="Regenerate every store in stores.json")
    args = ap.parse_args()

    reg = load_registry()

    if args.all:
        if not reg:
            sys.exit("stores.json is empty — nothing to refresh.")
        by_id = {}
        for s in reg:
            try:
                by_id[s["id"]] = generate_one(s["url"])
            except SystemExit as e:
                print(f"[{s['id']}] SKIPPED: {e}")
                by_id[s["id"]] = s  # keep existing entry
        rebuild_index(list(by_id.values()))
        save_registry(list(by_id.values()))
        print(f"\nRefreshed {len(by_id)} store(s).")
        return

    if not args.url:
        ap.error("provide a store URL, or use --all")

    entry = generate_one(args.url)
    reg = [s for s in reg if s["id"] != entry["id"]] + [entry]
    save_registry(reg)
    rebuild_index(reg)

    print(f"\nDone. Embed snippet:\n"
          f'  <div id="chowly-menu"></div>\n'
          f'  <script src="{PAGES_BASE}/menu-{entry["id"]}.js"></script>')


if __name__ == "__main__":
    main()
