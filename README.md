# menu-embeds

Copy-paste website embeds for Chowly Online Ordering (COO) menus.

Each registered store gets a self-contained loader served from GitHub Pages.
A customer pastes two lines onto their marketing site and a beautified,
responsive menu — item photos, descriptions, prices, and collapsible modifier
options — renders in the customer's brand colors, fully isolated from their
site's CSS via Shadow DOM.

```html
<div id="chowly-menu"></div>
<script src="https://jessegorin.github.io/menu-embeds/menu-<STORE_ID>.js"></script>
```

> Use a different container id with `data-target`:
> `<script src=".../menu-<id>.js" data-target="my-menu"></script>`

## How it works

- `generate.py` fetches a COO store page, extracts store info + menu (with the
  ordering-API fallback), brand colors from the Koala web-config API, the logo,
  and every item's modifier groups, then writes `docs/menu-<id>.js`.
- `stores.json` is the registry of embedded stores.
- `docs/index.html` is an auto-generated preview gallery.
- `.github/workflows/refresh.yml` runs `generate.py --all` **nightly** so every
  embedded menu stays current. No secrets required — a fresh token is pulled
  from each public store page on each run.

## Add or update a store

```bash
python3 generate.py "https://<domain>/store/<id>"
```

Writes/updates `docs/menu-<id>.js`, `stores.json`, and `docs/index.html`.
This is normally driven by the `coo-menu-embed` Claude Code skill, which opens
a PR with the change.

## Refresh everything now

```bash
python3 generate.py --all
```

Or trigger the **Refresh menu embeds** workflow from the Actions tab.

## Notes

- The bundle references item images by their Koala CDN URL (not base64), so the
  file stays small and images lazy-load.
- The menu is a snapshot refreshed nightly, not per-page-load-live. Truly live
  rendering would require a Chowly backend endpoint that proxies COO with auth +
  CORS (the COO API is auth-gated and its CORS preflight disallows the required
  headers, so a browser on a customer domain can't fetch it directly).
