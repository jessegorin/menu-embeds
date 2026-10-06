/*! Chowly menu embed — store 23067 — generated 2026-10-06
 * Paste onto any site:
 *   <div id="chowly-menu"></div>
 *   <script src="https://jessegorin.github.io/menu-embeds/menu-23067.js"></script>
 * Optional custom container:
 *   <div id="my-menu"></div>
 *   <script src="https://jessegorin.github.io/menu-embeds/menu-23067.js" data-target="my-menu"></script>
 */
(function () {
  var DATA = {"store":{"name":"Mofongos","address":"5757 Lankershim Blvd, North Hollywood, CA, 91601","phone":"(818) 754-1051","hours":["Mon–Tue: 1:00 AM – 12:59 AM","Wed–Sat: 12:00 AM – 11:59 PM","Sunday: 12:00 AM – 12:59 AM"],"url":"https://www.mofongosrestaurant.com/store/23067"},"colors":{"accent":"#ee4a23","body_bg":"#ffffff","text_dark":"#000000","section_bg":"#f6f6f6","on_accent":"#ffffff"},"logo":"https://chowly-coo-configuration-assets.nyc3.digitaloceanspaces.com/chowly-coo-prod-configuration-assets/public/assets/New-Logo-13-009efb14-8f39-431c-ba4b-30efd90b6741.png","sections":[{"name":"ALCOHOLIC BEVERAGES","items":[{"name":"Medalla Light","desc":"Puerto Rico's iconic light beer.","price":"$9.50","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-2.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1781828936%2Fx9nvhh7chauqug1urmwr.jpg","mods":[]},{"name":"Presidente","desc":"Dominican Republic's iconic beer.","price":"$9.50","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-5.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1781828836%2Fstaelmqfvnx5f9iqzo5n.jpg","mods":[]},{"name":"Modelo","desc":"","price":"$6.50","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-1.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1781828879%2Feuz1f5twqwbedciqteaq.jpg","mods":[]},{"name":"Corona","desc":"","price":"$6.50","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-5.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1781828896%2Fbvk8qcuewq3qc7cueg6k.jpg","mods":[]},{"name":"Piña Colada","desc":"","price":"$14.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-5.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1781829015%2Fkwff4cj6uwtrzznifsvk.jpg","mods":[]},{"name":"Coquito","desc":"Coquito — Puerto Rican coconut cream drink with rum.","price":"$14.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-3.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1789232898%2Fiphewwk7ulluhk0vqtew.png","mods":[]},{"name":"Mojito","desc":"","price":"$14.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-5.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1789231783%2Fvf3v2odpljuec93qx1mt.jpg","mods":[]},{"name":"Tropical Mojito","desc":"","price":"$14.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-3.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1789232917%2Fe2sfx9pbiuvkotmzgceu.png","mods":[]},{"name":"Tamarind Margarita","desc":"Tamarindo Margarita — tamarind margarita.","price":"$14.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-2.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1789232926%2Fo7gdycckmmjjo3anr8ex.png","mods":[]},{"name":"Sangria","desc":"","price":"$12.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-2.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1789232935%2Fdz6fx1b76yalya1oxyyz.png","mods":[]},{"name":"Alcoholic Coquito Bottle (750 ml)","desc":"Coquito — 750 ml bottle of Puerto Rican coconut cream drink with rum.","price":"$35.00","img":"https://image-cdn.chowlyinc.com/650%2Cfit/https%3A%2F%2Fres-5.cloudinary.com%2Fupserve%2Fimage%2Fupload%2Fv1789232889%2Fnr1elprncgwnqhqoecwq.png","mods":[]}]}]};

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

  var mount = "chowly-menu";
  var cs = document.currentScript;
  if (cs && cs.dataset && cs.dataset.target) mount = cs.dataset.target;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { chowlyRenderMenu(DATA, mount); });
  } else {
    chowlyRenderMenu(DATA, mount);
  }
})();
