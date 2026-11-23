/* GameDev Studio panel: tools, QA runs and reports for one game. Served by scripts/studio_panel.py. */
  (() => {
    "use strict";
    const T = JSON.parse(document.getElementById("panel-texts").textContent);
    const TOKEN = document.querySelector('meta[name="studio-token"]').content;
    const $ = (s, r = document) => r.querySelector(s);
    const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    const fmt = (s, o) => s.replace(/\{(\w+)\}/g, (_, k) => o[k]);
    let state = null, tab = "tools", filter = "all", selected = null, job = null;

    async function api(path, body) {
      const response = await fetch(path, body === undefined ? { cache: "no-store" } : {
        method: "POST", headers: { "Content-Type": "application/json", "X-Studio-Token": TOKEN }, body: JSON.stringify(body) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || response.statusText);
      return data;
    }
    async function refresh() { state = await api("/api/state"); render(); }

    function tabs() {
      $("#tabs").innerHTML = [["tools", T.tab_tools], ["qa", T.tab_qa], ["reports", T.tab_reports]].map(([id, label]) =>
        `<button type="button" role="tab" aria-selected="${tab === id}" data-tab="${id}">${esc(label)}</button>`).join("");
    }

    function costBadge(tool) {
      const kind = tool.cost;
      return `<span class="badge cost-${kind}">${esc(T[kind])}</span>` + (tool.account && kind === "free" ? `<span class="badge cost-account">${esc(T.account)}</span>` : "");
    }
    function statusPill(tool) {
      if (tool.pending) return `<span class="pill" data-status="unverified">${esc(T.pending)}</span>`;
      return tool.installed ? `<span class="pill" data-status="passed">${esc(T.installed)}</span>` : `<span class="pill" data-status="not_run">${esc(T.missing)}</span>`;
    }
    function toolCard(tool) {
      const actions = [];
      if (tool.install_steps && !tool.pending) {
        actions.push(`<button type="button" class="action ${tool.installed ? "" : "primary"}" data-install="${tool.id}">${esc(tool.installed ? T.reinstall : T.install)}</button>`);
      }
      actions.push(`<a class="action" href="${esc(tool.source)}" target="_blank" rel="noopener">${esc(T.source)} ↗</a>`);
      const manual = !tool.install_steps && tool.manual && !tool.installed ? `<p class="manual"><b>${esc(tool.owner_only ? T.who_owner : T.manual)}.</b> ${esc(tool.manual)}</p>` : "";
      const config = tool.config.map((item) => item.kind === "secret" ? `
        <form class="field" data-config="${tool.id}" data-key="${esc(item.key)}">
          <label>${esc(item.label)} <code>${esc(item.key)}</code></label>
          <div class="field-row"><input type="password" autocomplete="off" spellcheck="false" placeholder="${item.set ? "•••••••• " + esc(T.key_saved) : esc(T.key_placeholder)}">
          <button class="action small" type="submit">${esc(T.save)}</button></div>
          <p class="hint">${esc(T.secret_note)}</p></form>` : `
        <form class="field" data-config="${tool.id}" data-key="${esc(item.key)}">
          <label>${esc(item.label)}</label>
          <div class="field-row"><input type="text" spellcheck="false" value="${esc(item.value)}">
          <button class="action small" type="submit">${esc(T.save)}</button></div></form>`).join("");
      const owner = tool.owner_only && !tool.pending ? `
        <form class="field" data-owner="${tool.id}"><label>${esc(T.decision)}</label>
          <div class="field-row"><input type="url" spellcheck="false" placeholder="https://github.com/…/issues/…" value="${esc(tool.decision)}">
          <button class="action small" type="submit">${esc(T.save)}</button></div></form>` : "";
      const toggle = !tool.owner_only && !tool.pending ? `<label class="switch"><input type="checkbox" data-enable="${tool.id}" ${tool.enabled ? "checked" : ""}><span></span>${esc(T.enabled)}</label>` : "";
      const meta = [tool.requires.length ? `${esc(T.requires)}: ${tool.requires.map(esc).join(", ")}` : "",
        tool.used_by.length ? `${esc(T.used_by)}: ${tool.used_by.map((s) => `<code>${esc(s)}</code>`).join(" ")}` : ""].filter(Boolean).join(" · ");
      return `<article class="tool-card ${tool.installed ? "is-installed" : ""} ${tool.cost === "paid" ? "is-paid" : ""}">
        <header><div><h3>${esc(tool.name)}</h3><p class="tool-meta">${costBadge(tool)}<span class="badge">${esc(tool.licence)}</span>
          <span class="badge">${esc(T["scope_" + tool.scope])}</span></p></div>${statusPill(tool)}</header>
        <p class="gives">${esc(tool.gives)}</p>
        ${tool.requirements ? `<p class="requirements">${esc(T.needs)}: ${esc(tool.requirements)}</p>` : ""}
        ${tool.commercial !== "ok" ? `<p class="licence-note" data-commercial="${tool.commercial_effective}"><b>${esc(T["commercial_" + tool.commercial_effective])}.</b> ${tool.owner_accepted_risk ? "" : esc(tool.licence_note)}</p>` : ""}
        ${tool.licence_gate.length ? `<label class="switch"><input type="checkbox" data-risk="${tool.id}" ${tool.owner_accepted_risk ? "checked" : ""}><span></span>${esc(T.accept_risk)}</label>
        ${tool.owner_accepted_risk ? "" : `<details class="licence-gate"><summary>${esc(T.licence_gate)}</summary><ol>${tool.licence_gate.map((line) => `<li>${esc(line)}</li>`).join("")}</ol></details>`}` : ""}
        ${tool.cost_note ? `<p class="cost-note">${esc(tool.cost_note)}${tool.cost === "paid" ? " " + esc(T.paid_note) : ""}</p>` : ""}
        <p class="detail mono">${esc(tool.detail)}</p>
        ${manual}${config}${owner}
        <footer>${toggle}<span class="spacer"></span>${actions.join("")}</footer>
        ${meta ? `<p class="tool-foot">${meta}</p>` : ""}</article>`;
    }
    function toolsView() {
      const tools = state.tools;
      const shown = tools.filter((t) => filter === "all" || (filter === "recommended" && t.recommended) ||
        (filter === "missing" && !t.installed && !t.pending) || (filter === "paid" && t.cost !== "free"));
      const summary = fmt(T.summary, { installed: tools.filter((t) => t.installed).length, total: tools.length,
        paid: tools.filter((t) => t.cost === "paid").length, pending: tools.filter((t) => t.pending).length });
      const groups = state.groups.map((group) => {
        const items = shown.filter((t) => t.group === group.id);
        if (!items.length) return "";
        return `<section class="section"><div class="section-head"><h2>${esc(group.name)}<span class="count">${items.length}</span></h2></div>
          <div class="tool-grid">${items.map(toolCard).join("")}</div></section>`;
      }).join("");
      const chips = ["all", "recommended", "missing", "paid"].map((id) =>
        `<button type="button" class="filter" aria-pressed="${filter === id}" data-filter="${id}">${esc(T["filter_" + id])}</button>`).join("");
      return `<header class="summary-title"><div><p class="eyebrow">${esc(T.game)} · ${esc(state.game_name)}</p>
        <h1>${esc(T.tools_title)}</h1><p class="subtitle">${esc(summary)}</p></div><div class="filters">${chips}</div></header>${groups}`;
    }

    function scenarioCard(item) {
      if (item.error) return `<button type="button" class="scenario" data-scenario="${esc(item.file)}" aria-pressed="${selected === item.file}">
        <b>${esc(item.name)}</b><span class="pill" data-status="failed">${esc(T.invalid)}</span><small>${esc(item.error)}</small></button>`;
      const dot = (side) => `<span class="dot ${item.builds[side].up ? "up" : "down"}" title="${esc(item.builds[side].url)}"></span>${esc(T[side])}`;
      return `<button type="button" class="scenario" data-scenario="${esc(item.file)}" aria-pressed="${selected === item.file}">
        <b>${esc(item.title)}</b><small class="mono">${esc(item.file)} · ${item.steps} · ${item.profiles.length}</small>
        <span class="builds">${dot("before")} ${dot("after")}</span></button>`;
    }
    function qaView() {
      const items = state.scenarios;
      if (!items.length) return `<header class="summary-title"><div><p class="eyebrow">${esc(T.game)} · ${esc(state.game_name)}</p><h1>${esc(T.qa_title)}</h1></div></header>
        <div class="empty-state panel"><p>${esc(T.no_scenarios)}</p><button type="button" class="action primary" data-example>${esc(T.make_example)}</button></div>`;
      if (!items.some((i) => i.file === selected)) selected = (items.find((i) => !i.error) || items[0]).file;
      const item = items.find((i) => i.file === selected);
      let detail = "";
      if (item && !item.error) {
        const profiles = item.profiles.map((p) => `<label class="profile"><input type="checkbox" name="profile" value="${esc(p.name)}" checked>
          <span><b>${esc(p.label || p.name)}</b><small class="mono">${p.width}×${p.height}${p.dpr !== 1 ? " @" + p.dpr + "x" : ""} · ${esc(p.input)}${p.locale ? " · " + esc(p.locale) : ""}</small></span></label>`).join("");
        const builds = ["before", "after"].map((side) => `<li><span class="dot ${item.builds[side].up ? "up" : "down"}"></span>
          <b>${esc(T[side])}</b> <code>${esc(item.builds[side].url)}</code> <code>${esc(item.builds[side].commit)}</code>
          <span class="muted">${esc(item.builds[side].up ? T.build_up : T.build_down)}</span></li>`).join("");
        detail = `<form class="run panel featured" id="run">
          <h2>${esc(item.title)}</h2><p class="muted"><a href="${esc(item.issue)}" target="_blank" rel="noopener">${esc(item.issue)}</a></p>
          <ul class="build-list">${builds}</ul>
          ${item.builds.before.up && item.builds.after.up ? "" : `<p class="callout warning">${esc(T.builds_hint)}</p>`}
          <div class="section-head"><h2>${esc(T.profiles)}<span class="count">${item.profiles.length}</span></h2></div>
          <div class="profiles">${profiles}</div>
          <div class="section-head"><h2>${esc(T.options)}</h2></div>
          <div class="options"><label class="switch"><input type="checkbox" name="video"><span></span>${esc(T.video)}</label>
            <label class="switch"><input type="checkbox" name="step_frames" ${item.step_frames ? "checked" : ""}><span></span>${esc(T.step_frames)}</label>
            <label class="select">${esc(T.language)} <select name="lang"><option value="ru" ${state.lang === "ru" ? "selected" : ""}>Русский</option><option value="en" ${state.lang === "en" ? "selected" : ""}>English</option></select></label></div>
          <button type="submit" class="action primary big">${esc(T.run)} →</button></form>`;
      } else if (item) {
        detail = `<div class="run panel"><p class="callout danger">${esc(item.error)}</p></div>`;
      }
      return `<header class="summary-title"><div><p class="eyebrow">${esc(T.game)} · ${esc(state.game_name)}</p><h1>${esc(T.qa_title)}</h1></div></header>
        <div class="qa-layout"><div class="scenario-list"><div class="section-head"><h2>${esc(T.scenarios)}<span class="count">${items.length}</span></h2></div>${items.map(scenarioCard).join("")}</div>${detail}</div>`;
    }

    function reportsView() {
      const runs = state.runs;
      const cards = runs.map((run) => `<a class="run-card" href="${esc(run.report)}" target="_blank" rel="noopener">
        <span class="run-thumb">${run.thumb ? `<img src="${esc(run.thumb)}" alt="" loading="lazy">` : ""}</span>
        <span class="run-body"><b>${esc(run.title)}</b><small class="mono">${esc(run.created)} · ${run.profiles.map(esc).join(", ")}</small>
        <span class="pill" data-status="${run.passed ? "passed" : "failed"}">${esc(run.passed ? T.passed : T.failed_run)}</span></span></a>`).join("");
      return `<header class="summary-title"><div><p class="eyebrow">${esc(T.game)} · ${esc(state.game_name)}</p><h1>${esc(T.reports_title)}</h1></div></header>
        ${runs.length ? `<div class="run-grid">${cards}</div>` : `<div class="empty-state panel"><p>${esc(T.no_reports)}</p></div>`}`;
    }

    function render() {
      tabs();
      $("#stop").textContent = T.stop;
      $("#app").innerHTML = tab === "tools" ? toolsView() : tab === "qa" ? qaView() : reportsView();
    }

    function dialog(title, body, actions) {
      $("#dialog-title").textContent = title;
      $("#dialog-body").innerHTML = body;
      $("#dialog-actions").innerHTML = "";
      actions.forEach(([label, primary, handler]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action" + (primary ? " primary" : "");
        button.textContent = label;
        button.addEventListener("click", () => { $("#dialog").hidden = true; if (handler) handler(); });
        $("#dialog-actions").append(button);
      });
      $("#dialog").hidden = false;
      $("#dialog-actions button:last-child").focus();
    }

    async function follow(view) {
      job = view;
      const drawer = $("#drawer");
      drawer.hidden = false;
      $("#drawer-title").textContent = view.title;
      $("#drawer-close").textContent = T.close;
      $("#drawer-log").textContent = "";
      $("#drawer-link").hidden = true;
      let since = 0;
      while (true) {
        const update = await api(`/api/jobs/${view.id}?since=${since}`);
        since = update.next;
        const log = $("#drawer-log");
        if (update.lines.length) { log.textContent += update.lines.join("\n") + "\n"; log.scrollTop = log.scrollHeight; }
        const step = [...log.textContent.matchAll(/\[(\d+)\/(\d+)\]/g)].pop();
        $("#drawer-progress").hidden = !step;
        if (step) $("#drawer-progress span").style.width = (Number(step[1]) - (update.status === "running" ? 0.5 : 0)) / Number(step[2]) * 100 + "%";
        const status = $("#drawer-status");
        status.dataset.status = update.status === "running" ? "pending" : update.status === "done" ? "passed" : "failed";
        status.textContent = update.status === "running" ? T.running : update.status === "done" ? T.done : T.failed;
        if (update.status !== "running") {
          if (update.result.report) {
            const link = $("#drawer-link");
            link.href = update.result.report; link.target = "_blank"; link.textContent = T.open_report + " →"; link.hidden = false;
          }
          job = null;
          await refresh();
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 600));
      }
    }

    function flash(target, text, bad) {
      const note = document.createElement("span");
      note.className = "flash" + (bad ? " bad" : "");
      note.textContent = text;
      target.append(note);
      setTimeout(() => note.remove(), 3500);
    }

    document.addEventListener("click", async (event) => {
      const t = event.target;
      const tabButton = t.closest("[data-tab]");
      if (tabButton) { tab = tabButton.dataset.tab; render(); return; }
      const chip = t.closest("[data-filter]");
      if (chip) { filter = chip.dataset.filter; render(); return; }
      const scenario = t.closest("[data-scenario]");
      if (scenario) { selected = scenario.dataset.scenario; render(); return; }
      if (t.closest("[data-example]")) { try { await api("/api/qa/example", {}); await refresh(); } catch (e) { dialog(T.failed, `<p>${esc(e.message)}</p>`, [[T.close, true]]); } return; }
      const install = t.closest("[data-install]");
      if (install) {
        const tool = state.tools.find((x) => x.id === install.dataset.install);
        const body = `<p>${esc(T.confirm_body)}</p><pre class="command">${tool.install_steps.map((step) => esc(step.join(" "))).join("\n")}</pre>` +
          (state.platform === "windows" ? `<p class="muted">${esc(T.confirm_windows)}</p>` : "") +
          (tool.cost !== "free" ? `<p class="callout warning">${esc(tool.cost_note)} ${esc(T.paid_note)}</p>` : "");
        dialog(fmt(T.confirm_title, { name: tool.name }), body, [[T.cancel, false], [T.yes, true, async () => {
          try { await follow(await api("/api/tools/install", { id: tool.id, confirm: true })); }
          catch (e) { dialog(T.failed, `<p>${esc(e.message)}</p>`, [[T.close, true]]); }
        }]]);
        return;
      }
      if (t.closest("#drawer-close")) { $("#drawer").hidden = true; return; }
      if (t.closest("#stop")) { await api("/api/shutdown", {}).catch(() => {}); document.body.innerHTML = `<main class="page"><p class="callout">${esc(T.stopped)}</p></main>`; }
    });
    document.addEventListener("change", async (event) => {
      const toggle = event.target.closest("[data-enable], [data-risk]");
      if (!toggle) return;
      try {
        if (toggle.dataset.risk) await api("/api/tools/risk", { id: toggle.dataset.risk, accepted: toggle.checked });
        else await api("/api/tools/enable", { id: toggle.dataset.enable, enabled: toggle.checked });
      }
      catch (e) { toggle.checked = !toggle.checked; flash(toggle.parentElement, e.message, true); return; }
      if (toggle.dataset.risk) await refresh();
    });
    document.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      try {
        if (form.id === "run") {
          const data = new FormData(form);
          const view = await api("/api/qa/run", { file: selected, profiles: data.getAll("profile"), video: data.has("video"),
            step_frames: data.has("step_frames"), lang: data.get("lang") });
          await follow(view);
          return;
        }
        const input = form.querySelector("input");
        if (form.dataset.licence) {
          await api("/api/tools/licence", { id: form.dataset.licence, url: input.value.trim() });
        } else if (form.dataset.owner) {
          await api("/api/tools/enable", { id: form.dataset.owner, enabled: Boolean(input.value.trim()), decision: input.value.trim() });
        } else {
          await api("/api/tools/config", { id: form.dataset.config, key: form.dataset.key, value: input.value });
          if (input.type === "password") input.value = "";
        }
        await refresh();
      } catch (e) {
        flash(form, e.message, true);
      }
    });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") $("#dialog").hidden = true; });
    refresh().catch((e) => { $("#app").innerHTML = `<p class="callout danger">${esc(e.message)}</p>`; });
  })();
