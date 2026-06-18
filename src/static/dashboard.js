/* MusicMV dashboard - binds the animated UI to the REAL /api/dashboard data. */
(function () {
  "use strict";
  var RM = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var state = { data: null, filter: "", view: "all" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>\"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '\"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function avatarUrl(name) { return "/api/dashboard/avatar/" + encodeURIComponent(name); }
  function initials(name) { return (name || "?").trim().charAt(0).toUpperCase(); }

  function toast(msg) {
    var t = $("#toast"); if (!t) return;
    t.textContent = msg; t.classList.add("show");
    clearTimeout(t._t); t._t = setTimeout(function () { t.classList.remove("show"); }, 2600);
  }

  function countUp(el, target) {
    target = Number(target) || 0;
    if (RM) { el.textContent = target; return; }
    var start = 0, dur = 900, t0 = null;
    function step(ts) {
      if (!t0) t0 = ts;
      var p = Math.min((ts - t0) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(start + (target - start) * eased);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function revealAll() {
    var els = document.querySelectorAll(".reveal");
    if (RM || !("IntersectionObserver" in window)) {
      els.forEach(function (e) { e.classList.add("in"); }); return;
    }
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    els.forEach(function (e) { io.observe(e); });
  }

  function flatVideos(data) {
    var out = [];
    (data.artists || []).forEach(function (a) {
      (a.primary || []).forEach(function (v) {
        out.push({ artist: a.name, title: v.title, size_mb: v.size_mb, path: v.path, feat: false });
      });
      (a.collaborations || []).forEach(function (v) {
        out.push({ artist: a.name, title: v.title, size_mb: 0, path: v.path, feat: true });
      });
    });
    return out;
  }

  function reveal(path, mode) {
    fetch("/api/dashboard/reveal", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path, mode: mode || "open" })
    }).then(function (r) { return r.json(); }).then(function (j) {
      toast(j.ok ? "Opening in your player\u2026" : (j.message || "Could not open file"));
    }).catch(function () { toast("Could not reach the app"); });
  }

  function renderArtists() {
    var grid = $("#artist-grid"); var data = state.data; if (!grid) return;
    var list = (data.artists || []).filter(function (a) {
      return !state.filter || a.name.toLowerCase().indexOf(state.filter) > -1;
    });
    $("#artists-hint").textContent = list.length + " artist" + (list.length === 1 ? "" : "s");
    if (!list.length) { grid.innerHTML = '<div class="empty">No artists match.</div>'; return; }
    grid.innerHTML = list.map(function (a, i) {
      var img = a.has_avatar
        ? '<img loading="lazy" src="' + avatarUrl(a.name) + '" alt="' + esc(a.name) + '" onerror="this.outerHTML=&quot;<div class=\\&quot;ph\\&quot;>' + esc(initials(a.name)) + '</div>&quot;"/>'
        : '<div class="ph">' + esc(initials(a.name)) + "</div>";
      return '<button class="artist" data-artist="' + esc(a.name) + '" style="animation-delay:' + (i * 35) + 'ms">' +
        '<div class="ring2">' + img + '<span class="count-pill">' + a.counts.primary + "</span></div>" +
        '<div class="nm">' + esc(a.name) + "</div>" +
        '<div class="rl">' + a.counts.primary + " videos" + (a.counts.collaborations ? " \u00b7 " + a.counts.collaborations + " feat." : "") + "</div>" +
        "</button>";
    }).join("");
    grid.querySelectorAll(".artist").forEach(function (el) {
      el.addEventListener("click", function () {
        state.filter = el.getAttribute("data-artist").toLowerCase();
        $("#search").value = el.getAttribute("data-artist");
        renderVideos();
        $("#library-block").scrollIntoView({ behavior: RM ? "auto" : "smooth", block: "start" });
      });
    });
  }

  function renderVideos() {
    var grid = $("#video-grid"); var data = state.data; if (!grid) return;
    var vids = flatVideos(data).filter(function (v) {
      if (!state.filter) return true;
      return v.title.toLowerCase().indexOf(state.filter) > -1 || v.artist.toLowerCase().indexOf(state.filter) > -1;
    });
    $("#library-hint").textContent = vids.length + " video" + (vids.length === 1 ? "" : "s");
    if (!vids.length) { grid.innerHTML = '<div class="empty">No videos match your search.</div>'; return; }
    grid.innerHTML = vids.slice(0, 60).map(function (v, i) {
      var art = '<img loading="lazy" src="' + avatarUrl(v.artist) + '" alt="" onerror="this.style.display=&quot;none&quot;"/>';
      var badge = v.feat ? '<span class="badge feat">feat.</span>' : '<span class="badge">MV</span>';
      var size = v.size_mb ? '<span class="size">' + v.size_mb + ' MB</span>' : "";
      return '<article class="video" tabindex="0" data-path="' + esc(v.path) + '" style="animation-delay:' + (i * 25) + 'ms">' +
        '<div class="thumb">' + art + badge + size +
        '<div class="play"><span><svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 4l14 8-14 8z"/></svg></span></div></div>' +
        '<div class="v-meta"><h4>' + esc(v.title) + "</h4><p>" + esc(v.artist) + "</p></div></article>";
    }).join("");
    grid.querySelectorAll(".video").forEach(function (el) {
      var p = el.getAttribute("data-path");
      el.addEventListener("click", function () { reveal(p, "open"); });
      el.addEventListener("keydown", function (e) { if (e.key === "Enter") reveal(p, "open"); });
    });
  }

  function renderMissing() {
    var box = $("#miss-list"); var data = state.data; if (!box) return;
    var all = [];
    (data.artists || []).forEach(function (a) {
      (a.missing || []).forEach(function (m) { all.push({ artist: a.name, title: m.title, album: m.album, deezer: m.deezer }); });
    });
    if (!all.length) {
      box.innerHTML = '<div class="empty">No missing-track data yet.<br>Run the pipeline to generate <b>music_videos.txt</b> with Deezer Top-50 comparisons.</div>';
      return;
    }
    box.innerHTML = all.slice(0, 80).map(function (m) {
      return '<div class="miss">' +
        '<span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v4m0 4h.01"/></svg></span>' +
        '<div class="mt"><h5>' + esc(m.title) + "</h5><p>" + esc(m.album || m.artist) + "</p></div>" +
        '<a class="dl" href="' + esc(m.deezer) + '" target="_blank" rel="noopener" aria-label="Open on Deezer">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></a></div>';
    }).join("");
  }

  function renderRing() {
    var t = state.data.totals || {}; var have = t.videos || 0; var miss = t.missing || 0;
    var denom = have + miss; var pct = denom > 0 ? Math.round(have / denom * 100) : 100;
    var fg = $("#ring-fg"); var C = 2 * Math.PI * 52;
    if (fg) { fg.style.strokeDasharray = C; setTimeout(function () { fg.style.strokeDashoffset = C * (1 - pct / 100); }, 120); }
    var pctEl = $("#ring-pct"); if (pctEl) countUp2(pctEl, pct);
  }
  function countUp2(el, target) {
    if (RM) { el.textContent = target + "%"; return; }
    var t0 = null;
    function step(ts) { if (!t0) t0 = ts; var p = Math.min((ts - t0) / 1000, 1); el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + "%"; if (p < 1) requestAnimationFrame(step); }
    requestAnimationFrame(step);
  }

  function applyView() {
    var ab = $("#artists-block"), lb = $("#library-block");
    ab.classList.toggle("is-hidden", state.view === "library" || state.view === "missing");
    lb.classList.toggle("is-hidden", state.view === "artists" || state.view === "missing");
  }

  function bind() {
    $("#search").addEventListener("input", function (e) {
      state.filter = e.target.value.trim().toLowerCase(); renderArtists(); renderVideos();
    });
    $("#nav").querySelectorAll(".nav-item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        $("#nav").querySelectorAll(".nav-item").forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active"); state.view = btn.getAttribute("data-view"); applyView();
      });
    });
  }

  function render() {
    var d = state.data;
    countUp($("#st-artists"), d.totals.artists);
    countUp($("#st-videos"), d.totals.videos);
    countUp($("#st-collabs"), d.totals.collaborations);
    countUp($("#st-missing"), d.totals.missing);
    renderArtists(); renderVideos(); renderMissing(); renderRing();
    $("#foot-status").textContent = d.ok ? "Library loaded" : "No archive";
    $("#foot-path").textContent = d.path || "path not set";
    revealAll();
  }

  function boot() {
    bind();
    fetch("/api/dashboard").then(function (r) { return r.json(); }).then(function (d) {
      state.data = d;
      if (!d.ok) toast(d.message || "Archive not found");
      render();
    }).catch(function () {
      state.data = { ok: false, artists: [], totals: { artists: 0, videos: 0, collaborations: 0, missing: 0 }, path: "" };
      toast("Could not load /api/dashboard"); render();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
