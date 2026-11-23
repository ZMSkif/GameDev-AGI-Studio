/* GameDev Studio offline reports: zoom viewer, measured markers, video seeking, before/after slider. */
(() => {
  "use strict";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const text = (document.documentElement.dataset.ui || "").split("|");
  const label = (index, fallback) => text[index] || fallback;

  /* ---------- Zoom viewer ---------- */
  let viewer = null;
  function buildViewer() {
    const root = document.createElement("div");
    root.className = "lightbox";
    root.hidden = true;
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.innerHTML =
      '<div class="lightbox-bar"><span class="caption"></span>' +
      '<button type="button" class="action small" data-act="prev" aria-label="' + label(0, "Previous") + '">←</button>' +
      '<button type="button" class="action small" data-act="next" aria-label="' + label(1, "Next") + '">→</button>' +
      '<button type="button" class="action small" data-act="out" aria-label="' + label(2, "Zoom out") + '">−</button>' +
      '<span class="zoom-level">100%</span>' +
      '<button type="button" class="action small" data-act="in" aria-label="' + label(3, "Zoom in") + '">+</button>' +
      '<button type="button" class="action small" data-act="fit">' + label(4, "Fit") + '</button>' +
      '<button type="button" class="action small" data-act="actual">1:1</button>' +
      '<button type="button" class="action small" data-act="markers" hidden>' + label(5, "Markers") + '</button>' +
      '<a class="action small" data-act="open" target="_blank" rel="noopener">' + label(6, "Original") + '</a>' +
      '<button type="button" class="action small primary" data-act="close" aria-label="' + label(7, "Close") + '">✕</button></div>' +
      '<div class="lightbox-stage"></div>' +
      '<div class="lightbox-hint">' + label(8, "Wheel or +/− to zoom · drag to pan · ←/→ to switch · Esc to close") + '</div>';
    document.body.append(root);
    const stage = $(".lightbox-stage", root);
    const state = { items: [], index: 0, scale: 1, x: 0, y: 0, width: 1, height: 1, node: null, markers: true };

    function apply() {
      if (!state.node) return;
      state.node.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
      $(".zoom-level", root).textContent = Math.round(state.scale * 100) + "%";
      stage.classList.toggle("pixel", state.scale >= 3);
    }
    function fit() {
      const box = stage.getBoundingClientRect();
      state.scale = Math.min(1, (box.width - 32) / state.width, (box.height - 32) / state.height) || 1;
      state.x = -state.width * state.scale / 2;
      state.y = -state.height * state.scale / 2;
      apply();
    }
    function zoomAt(factor, cx, cy) {
      const box = stage.getBoundingClientRect();
      const px = (cx ?? box.left + box.width / 2) - box.left - box.width / 2;
      const py = (cy ?? box.top + box.height / 2) - box.top - box.height / 2;
      const next = Math.min(16, Math.max(0.05, state.scale * factor));
      const ratio = next / state.scale;
      state.x = px - (px - state.x) * ratio;
      state.y = py - (py - state.y) * ratio;
      state.scale = next;
      apply();
    }
    function show(index) {
      state.index = (index + state.items.length) % state.items.length;
      const source = state.items[state.index];
      const frame = source.closest(".frame");
      const image = source.tagName === "IMG" ? source : $("img", source);
      stage.replaceChildren();
      const node = frame ? frame.cloneNode(true) : image.cloneNode();
      node.removeAttribute("data-zoom");
      $$("[data-zoom]", node).forEach((item) => item.removeAttribute("data-zoom"));
      $$("[id]", node).forEach((item) => item.removeAttribute("id"));
      node.dataset.markers = state.markers ? "on" : "off";
      stage.append(node);
      state.node = node;
      state.width = image.naturalWidth || image.width;
      state.height = image.naturalHeight || image.height;
      const inner = node.tagName === "IMG" ? node : $("img", node);
      inner.style.width = state.width + "px";
      inner.style.height = state.height + "px";
      inner.style.maxHeight = "none";
      $(".caption", root).textContent = source.dataset.caption || image.alt || "";
      $('[data-act="open"]', root).href = image.getAttribute("src");
      $('[data-act="markers"]', root).hidden = !frame || !$(".marker", frame);
      const many = state.items.length > 1;
      $('[data-act="prev"]', root).hidden = !many;
      $('[data-act="next"]', root).hidden = !many;
      fit();
    }
    function open(source) {
      const group = source.dataset.zoomGroup;
      state.items = group ? $$(`[data-zoom][data-zoom-group="${group}"]`) : [source];
      root.hidden = false;
      document.body.style.overflow = "hidden";
      show(Math.max(0, state.items.indexOf(source)));
      $('[data-act="close"]', root).focus();
    }
    function close() {
      root.hidden = true;
      document.body.style.overflow = "";
      stage.replaceChildren();
      state.node = null;
    }
    root.addEventListener("click", (event) => {
      const act = event.target.closest("[data-act]")?.dataset.act;
      if (act === "close") close();
      else if (act === "prev") show(state.index - 1);
      else if (act === "next") show(state.index + 1);
      else if (act === "in") zoomAt(1.5);
      else if (act === "out") zoomAt(1 / 1.5);
      else if (act === "fit") fit();
      else if (act === "actual") { state.scale = 1; state.x = -state.width / 2; state.y = -state.height / 2; apply(); }
      else if (act === "markers") { state.markers = !state.markers; if (state.node) state.node.dataset.markers = state.markers ? "on" : "off"; }
    });
    stage.addEventListener("wheel", (event) => {
      event.preventDefault();
      zoomAt(event.deltaY < 0 ? 1.15 : 1 / 1.15, event.clientX, event.clientY);
    }, { passive: false });
    let drag = null;
    stage.addEventListener("pointerdown", (event) => {
      drag = { x: event.clientX - state.x, y: event.clientY - state.y };
      stage.setPointerCapture(event.pointerId);
      stage.classList.add("dragging");
    });
    stage.addEventListener("pointermove", (event) => {
      if (!drag) return;
      state.x = event.clientX - drag.x;
      state.y = event.clientY - drag.y;
      apply();
    });
    const stop = () => { drag = null; stage.classList.remove("dragging"); };
    stage.addEventListener("pointerup", stop);
    stage.addEventListener("pointercancel", stop);
    stage.addEventListener("dblclick", (event) => zoomAt(2, event.clientX, event.clientY));
    document.addEventListener("keydown", (event) => {
      if (root.hidden) return;
      if (event.key === "Escape") close();
      else if (event.key === "ArrowLeft") show(state.index - 1);
      else if (event.key === "ArrowRight") show(state.index + 1);
      else if (event.key === "+" || event.key === "=") zoomAt(1.5);
      else if (event.key === "-") zoomAt(1 / 1.5);
      else if (event.key === "0") fit();
    });
    addEventListener("resize", () => { if (!root.hidden) fit(); });
    return { open };
  }
  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-zoom]");
    if (!target || event.button !== 0 || event.metaKey || event.ctrlKey) return;
    event.preventDefault();
    viewer = viewer || buildViewer();
    viewer.open(target);
  });

  /* ---------- Markers ---------- */
  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-toggle-markers]");
    if (toggle) {
      const on = toggle.getAttribute("aria-pressed") !== "true";
      toggle.setAttribute("aria-pressed", String(on));
      $$(".frame").forEach((frame) => { frame.dataset.markers = on ? "on" : "off"; });
      return;
    }
    const show = event.target.closest("[data-show-region]");
    if (show) {
      const ids = show.dataset.showRegion.split(" ");
      $$(".marker.highlight").forEach((marker) => marker.classList.remove("highlight"));
      const markers = ids.map((id) => document.getElementById(id)).filter(Boolean);
      markers.forEach((marker) => marker.classList.add("highlight"));
      const frame = markers[0]?.closest(".frame");
      if (frame) {
        frame.dataset.markers = "on";
        frame.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => markers.forEach((marker) => marker.classList.remove("highlight")), 2600);
      }
    }
  });

  /* ---------- Video seeking ---------- */
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-seek]");
    if (!button) return;
    const video = document.getElementById(button.dataset.video);
    if (!video) return;
    const seconds = Number(button.dataset.seek);
    const go = () => {
      video.currentTime = Math.min(seconds, Math.max(0, (video.duration || seconds) - 0.05));
      video.pause();
      video.scrollIntoView({ behavior: "smooth", block: "center" });
    };
    if (video.readyState >= 1) go();
    else { video.addEventListener("loadedmetadata", go, { once: true }); video.load(); }
  });
  $$("video[data-time-readout]").forEach((video) => {
    const readout = document.getElementById(video.dataset.timeReadout);
    video.addEventListener("timeupdate", () => { readout.textContent = video.currentTime.toFixed(2) + " s"; });
  });

  /* ---------- Step frames ---------- */
  document.addEventListener("click", (event) => {
    const opener = event.target.closest("[data-open-frame]");
    if (!opener) return;
    const target = document.getElementById(opener.dataset.openFrame);
    if (target) target.click();
  });

  /* ---------- Notes (kept in this browser, exported as JSON) ---------- */
  const noteKey = "gds-notes:" + location.pathname;
  const readNotes = () => { try { return JSON.parse(localStorage.getItem(noteKey) || "{}"); } catch (error) { return {}; } };
  const writeNotes = (notes) => { try { localStorage.setItem(noteKey, JSON.stringify(notes)); } catch (error) { /* storage may be off */ } };
  const countNotes = () => {
    const count = Object.values(readNotes()).filter((note) => note.text && note.text.trim()).length;
    $$("[data-notes-count]").forEach((node) => { node.textContent = count; });
    $$("[data-note]").forEach((button) => {
      const note = readNotes()[button.dataset.note];
      button.classList.toggle("primary", Boolean(note && note.text && note.text.trim()));
    });
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-note]");
    if (!button) return;
    const id = button.dataset.note;
    const host = button.closest(".check");
    let box = host && host.querySelector("textarea.note-box");
    if (box) { box.hidden = !box.hidden; if (!box.hidden) box.focus(); return; }
    box = document.createElement("textarea");
    box.className = "note-box";
    box.rows = 3;
    box.placeholder = document.documentElement.dataset.notePlaceholder || "";
    box.value = (readNotes()[id] || {}).text || "";
    box.addEventListener("input", () => {
      const notes = readNotes();
      let context = {};
      try { context = JSON.parse(button.dataset.noteContext || "{}"); } catch (error) { context = {}; }
      notes[id] = { ...context, text: box.value, updated: new Date().toISOString() };
      writeNotes(notes);
      countNotes();
    });
    host.append(box);
    box.focus();
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-notes-export]")) return;
    const notes = Object.values(readNotes()).filter((note) => note.text && note.text.trim());
    const payload = { report: document.title, page: location.pathname.split("/").slice(-2).join("/"),
      revisions: $$(".metadata code").map((node) => node.parentElement.title || node.textContent),
      exported: new Date().toISOString(), notes };
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    link.download = "review-notes.json";
    document.body.append(link);
    link.click();
    link.remove();
  });
  countNotes();

  /* ---------- Before/after slider ---------- */
  const gallery = $("#gallery");
  if (gallery) {
    const before = $$('[data-role="before"] img', gallery);
    const after = $$('[data-role="after"] img', gallery);
    if (before.length === 1 && after.length === 1) {
      const originals = [before[0], after[0]];
      const comparison = $("#comparison");
      const layered = $("#layered");
      const reveal = $("#reveal");
      const switches = $("#switches");
      const enable = () => {
        const [earlier, later] = originals;
        if (!switches || !switches.hidden || !earlier.naturalWidth || earlier.naturalWidth !== later.naturalWidth ||
            earlier.naturalHeight !== later.naturalHeight) return;
        const ratio = earlier.naturalWidth / earlier.naturalHeight;
        layered.style.setProperty("--ratio", ratio);
        layered.style.maxWidth = (ratio * 62) + "vh";
        const base = later.cloneNode();
        const top = earlier.cloneNode();
        base.removeAttribute("data-zoom"); top.removeAttribute("data-zoom");
        top.className = "before";
        layered.prepend(base, top);
        switches.hidden = false;
      };
      originals.forEach((image) => image.addEventListener("load", enable));
      enable();
      const setCompare = (compare) => {
        comparison.hidden = !compare;
        originals.forEach((image) => { image.closest("figure").hidden = compare; });
        $("#grid-button").setAttribute("aria-pressed", String(!compare));
        $("#compare-button").setAttribute("aria-pressed", String(compare));
      };
      reveal?.addEventListener("input", () => layered.style.setProperty("--position", reveal.value + "%"));
      $("#grid-button")?.addEventListener("click", () => setCompare(false));
      $("#compare-button")?.addEventListener("click", () => setCompare(true));
    }
  }
})();
