/* Miqyas site: the menu on every page, and the results explorer and trial tiles drawn from /assets/site-data.json
   (built by scripts/build_site_data.py from the trials' results.json; no number is typed in a page). */
(function () {
  "use strict";
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") e.textContent = attrs[k];
      else if (k === "style") e.setAttribute("style", attrs[k]);
      else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) e.appendChild(c); });
    return e;
  }

  // menu
  document.querySelectorAll(".mq-nav").forEach(function (nav) {
    var btn = nav.querySelector(".mq-menu-btn");
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("mq-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (ev) {
      if (!nav.contains(ev.target)) { nav.classList.remove("mq-open"); btn.setAttribute("aria-expanded", "false"); }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") { nav.classList.remove("mq-open"); btn.setAttribute("aria-expanded", "false"); }
    });
  });

  var explorer = document.getElementById("mq-explorer");
  var trials = document.getElementById("mq-trials");
  if (!explorer && !trials) return;

  fetch("/assets/site-data.json").then(function (r) { return r.json(); }).then(function (data) {
    var colour = function (name) { var m = data.models[name]; return m ? m.colour : "#6E7178"; };
    var lab = function (name) { var m = data.models[name]; return m ? m.lab : ""; };
    if (explorer) drawExplorer(explorer, data, colour, lab);
    if (trials) drawTrials(trials, data, colour);
  }).catch(function () {
    [explorer, trials].forEach(function (n) { if (n) n.appendChild(el("p", { text: "تعذّر تحميل البيانات.", style: "color:#6E7178" })); });
  });

  function plot(bars, opts) {
    var H = opts.height, box = el("div", { class: "mq-plot", style: "height:" + H + "px" });
    var y = function (x) { return (x + 20) / 70 * H; };
    bars.forEach(function (b, i) {
      var bottom = 0, h, ciB = null, ciH = null, val;
      if (opts.diff) { bottom = b.v >= 0 ? y(0) : y(b.v); h = Math.abs(b.v) / 70 * H; ciB = y(b.lo); ciH = y(b.hi) - y(b.lo); val = (b.v > 0 ? "+" : "") + b.v.toFixed(1); }
      else if (b.of) { h = b.v / b.of * H; val = b.v + "/" + b.of; }
      else { h = b.v / 100 * (H - 18); if (b.lo !== undefined) { ciB = b.lo / 100 * (H - 18); ciH = (b.hi - b.lo) / 100 * (H - 18); } val = b.v.toFixed(1); }
      var tip = (b.name || b.label) + ": " + val + (b.lo !== undefined ? " · فترة الثقة 95%: " + b.lo.toFixed(1) + " إلى " + b.hi.toFixed(1) : "");
      var col = el("div", { class: "mq-col", title: tip }, [
        el("div", { class: "mq-bar-v", style: "bottom:" + bottom + "px;height:" + Math.max(2, h) + "px;background:" + opts.colour(b) + ";animation-delay:" + (i * 0.05) + "s" },
          [el("span", { dir: "ltr", text: val })]),
        ciH ? el("div", { class: "mq-ci", style: "bottom:" + ciB + "px;height:" + ciH + "px" }) : null
      ]);
      box.appendChild(col);
    });
    return box;
  }

  function names(bars, lab) {
    return el("div", { class: "mq-names" }, bars.map(function (b) {
      return el("span", { dir: "ltr" }, [document.createTextNode(b.name || b.label), lab && lab(b.name) ? el("small", { text: lab(b.name) }) : null]);
    }));
  }

  function drawExplorer(root, data, colour, lab) {
    var state = { view: 0, auto: true }, timer;
    var tabs = el("div", { class: "mq-tabs", role: "tablist", "aria-label": "النتائج" });
    var auto = el("button", { type: "button", class: "mq-ghost" });
    var text = el("p", { style: "margin:20px 0;font-size:16px;line-height:1.6;max-width:820px" });
    var grid = el("div", { class: "mq-grid" });
    var note = el("p", { style: "margin:16px 0 0;font-size:13px;line-height:1.6;color:#6E7178" });
    root.appendChild(el("div", { style: "display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px" }, [tabs, auto]));
    [text, grid, note].forEach(function (n) { root.appendChild(n); });
    function render() {
      var V = data.explorer[state.view];
      tabs.innerHTML = "";
      data.explorer.forEach(function (t, i) {
        var b = el("button", { type: "button", role: "tab", class: "mq-pill" + (state.auto ? " mq-auto" : ""), "aria-selected": i === state.view ? "true" : "false" },
          [document.createTextNode(t.label), el("span", { class: "mq-progress" })]);
        b.addEventListener("click", function () { state.view = i; state.auto = false; render(); });
        tabs.appendChild(b);
      });
      auto.textContent = state.auto ? "إيقاف التبديل" : "تبديل تلقائي";
      text.textContent = V.text;
      note.textContent = "الخط الرفيع على كل عمود: فترة الثقة 95%. لكل نموذج لونه في كل الرسوم. " + V.note;
      grid.innerHTML = "";
      V.cards.forEach(function (c) {
        var bars = c.bars.slice().sort(function (a, b) { return b.v - a.v; });
        grid.appendChild(el("div", { class: "mq-card" }, [
          el("h3", { text: c.title }), el("p", { class: "mq-sub", text: c.sub }),
          plot(bars, { height: 230, diff: c.diff, colour: function (b) { return colour(b.name); } }), names(bars, lab)
        ]));
      });
    }
    auto.addEventListener("click", function () { state.auto = !state.auto; render(); });
    timer = setInterval(function () { if (state.auto) { state.view = (state.view + 1) % data.explorer.length; render(); } }, 8000);
    render();
  }

  function drawTrials(root, data, colour) {
    var state = { type: "all" };
    var filters = el("div", { class: "mq-filters", role: "group", "aria-label": "نوع التجربة" });
    var grid = el("div", { class: "mq-grid-tiles", style: "margin-top:24px" });
    root.appendChild(filters); root.appendChild(grid);
    var limit = parseInt(root.getAttribute("data-limit") || "0", 10);
    function render() {
      filters.innerHTML = "";
      [["all", "الكل"]].concat(Object.keys(data.types).map(function (k) { return [k, data.types[k]]; })).forEach(function (o) {
        var n = o[0] === "all" ? data.trials.length : data.trials.filter(function (t) { return t.type === o[0]; }).length;
        var b = el("button", { type: "button", class: "mq-filter", "aria-pressed": state.type === o[0] ? "true" : "false" },
          [document.createTextNode(o[1] + " "), el("span", { class: "mq-n", text: String(n) })]);
        b.addEventListener("click", function () { state.type = o[0]; render(); });
        filters.appendChild(b);
      });
      grid.innerHTML = "";
      var list = data.trials.filter(function (t) { return state.type === "all" || t.type === state.type; });
      if (limit) list = list.slice(0, limit);
      list.forEach(function (t) {
        var max = t.bars.length ? Math.max.apply(null, t.bars.map(function (b) { return b.v; })) : null;
        grid.appendChild(el("a", { class: "mq-tile", href: t.url }, [
          el("div", { class: "mq-tile-top" }, [el("span", { text: t.metric }), el("span", { class: "mq-n", text: max === null ? "" : max.toFixed(1) + "%" })]),
          t.bars.length ? plot(t.bars, { height: 96, colour: function (b) { return colour(t.model || b.label); } }) : null,
          t.bars.length ? names(t.bars) : null,
          el("div", { class: "mq-tile-meta" }, [document.createTextNode(t.type_label + " · "), el("span", { class: "mq-n", text: t.date })]),
          el("div", { class: "mq-tile-title", text: t.title })
        ]));
      });
    }
    render();
  }
})();
