#!/usr/bin/env python3
"""Compare two local web builds with a declarative browser QA scenario."""

import argparse
from html import escape
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from urllib.parse import urlsplit

from render_review import COPY, render
from report_ui import attr, frame, markers, page, url as file_url, write_new
from review_evidence import ISSUE_URL, build, require_keys


VIEWPORTS = {"portrait": (390, 844), "landscape": (844, 390), "square": (512, 512)}
INDEX_COPY = {
    "en": {
        "title": "Web build QA", "data": "Results JSON", "actions": "Report links",
        "portrait": "Portrait", "landscape": "Landscape", "square": "Square",
        "passed": "Passed", "failed": "Failed", "open": "Open the check inspector",
        "problems": "Full diagnostics", "timing": "Ready in", "unit": "ms",
        "candidate": "Candidate capture", "baseline": "Baseline capture", "markers": "Markers",
        "eyebrow": "Browser QA · Issue", "baseline_label": "Baseline", "candidate_label": "Candidate",
        "stat_viewports": "Layouts passed", "stat_checks": "Candidate checks passed",
        "stat_errors": "Browser errors", "stat_ready": "Slowest candidate ready",
        "checks": "checks", "no_capture": "No capture", "more": "more", "layouts": "Layouts",
        "note": "Every number on this page was measured by the runner in Chromium. Device, GPU and platform behaviour need their own evidence.",
    },
    "ru": {
        "title": "Проверка веб-сборок", "data": "Результаты JSON", "actions": "Ссылки отчёта",
        "portrait": "Портрет", "landscape": "Альбом", "square": "Квадрат",
        "passed": "Пройдено", "failed": "Ошибка", "open": "Открыть разбор проверок",
        "problems": "Полная диагностика", "timing": "Готова за", "unit": "мс",
        "candidate": "Кадр новой сборки", "baseline": "Кадр исходной сборки", "markers": "Маркеры",
        "eyebrow": "Браузерный QA · задача", "baseline_label": "Исходная", "candidate_label": "Новая",
        "stat_viewports": "Размеров пройдено", "stat_checks": "Проверок новой сборки",
        "stat_errors": "Ошибок браузера", "stat_ready": "Самая долгая загрузка",
        "checks": "проверок", "no_capture": "Кадра нет", "more": "ещё", "layouts": "Размеры экрана",
        "note": "Все числа на странице измерены раннером в Chromium. Поведение на устройствах, GPU и платформах требует отдельных доказательств.",
    },
}
LOOPBACK = {"localhost", "127.0.0.1", "::1"}
STEP_FIELDS = {
    "click": {"selector"}, "tap": {"selector"}, "visible": {"selector"},
    "press": {"selector", "key"}, "text": {"selector", "text"}, "reload": set(),
}


def check_fields(value, required, optional, name):
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise ValueError(f"{name} needs fields {sorted(required)} and may also use {sorted(optional)}")


def check_string(value, name, limit=512, empty=False):
    if not isinstance(value, str) or len(value) > limit or (not empty and not value.strip()):
        raise ValueError(f"Expected a string for {name} with at most {limit} characters")


def origin(url):
    parts = urlsplit(url)
    port = parts.port
    if port is None:
        port = {"http": 80, "https": 443}.get(parts.scheme)
    return parts.scheme, parts.hostname, port


def check_build(value, name):
    require_keys(value, {"url", "commit"}, name)
    url = value["url"]
    check_string(url, f"{name}.url", limit=2048)
    parts = urlsplit(url)
    scheme, host, port = origin(url)
    if (scheme not in {"http", "https"} or host not in LOOPBACK or not port
            or parts.username is not None or re.search(r"[\s\\]", url)):
        raise ValueError(f"{name}.url must be a loopback HTTP(S) URL without credentials")
    commit = value["commit"]
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"{name}.commit must be a full lowercase Git commit SHA")


def check_steps(steps):
    if not isinstance(steps, list) or len(steps) > 50:
        raise ValueError("steps must be a list of at most 50 actions")
    for index, step in enumerate(steps, 1):
        name = f"step {index}"
        action = step.get("action") if isinstance(step, dict) else None
        if not isinstance(action, str) or action not in STEP_FIELDS:
            raise ValueError(f"{name} has an unsupported action")
        required = {"action"} | STEP_FIELDS[action]
        check_fields(step, required, {"label"}, name)
        for key in step.keys() - {"action"}:
            check_string(step[key], f"{name}.{key}", empty=key == "text")


def check_layout(layout):
    check_fields(layout, set(), {"within", "no_overlap"}, "layout")
    for name, entries in layout.items():
        if not isinstance(entries, list) or len(entries) > 30:
            raise ValueError(f"layout.{name} must be a list of at most 30 entries")
        for entry in entries:
            if name == "within":
                check_string(entry, "layout.within selector")
                continue
            if not isinstance(entry, list) or len(entry) != 2:
                raise ValueError("layout.no_overlap entries must be pairs of selectors")
            for selector in entry:
                check_string(selector, "layout.no_overlap selector")


def load_config(path):
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    check_fields(config, {"issue", "before", "after", "ready_selector", "steps"},
                 {"viewports", "layout", "timeout_ms"}, "config")
    if not isinstance(config["issue"], str) or not ISSUE_URL.fullmatch(config["issue"]):
        raise ValueError("Expected the full GitHub Issue URL")
    for side in ("before", "after"):
        check_build(config[side], side)
    check_string(config["ready_selector"], "ready_selector")
    check_steps(config["steps"])
    viewports = config.get("viewports", list(VIEWPORTS))
    if (not isinstance(viewports, list) or not viewports
            or any(not isinstance(name, str) or name not in VIEWPORTS for name in viewports)
            or len(viewports) != len(set(viewports))):
        raise ValueError("viewports must contain distinct names from portrait, landscape and square")
    layout = config.get("layout", {})
    check_layout(layout)
    timeout_ms = config.get("timeout_ms", 10_000)
    if type(timeout_ms) is not int or not 100 <= timeout_ms <= 60_000:
        raise ValueError("timeout_ms must be an integer between 100 and 60000")
    return {**config, "viewports": viewports, "layout": layout, "timeout_ms": timeout_ms}


def write_json(path, document):
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(document, file, ensure_ascii=False, indent=2)
        file.write("\n")


class Finding(RuntimeError):
    """A failed check that carries the measured page regions and values behind it."""

    def __init__(self, message, regions=(), **values):
        super().__init__(message)
        self.regions = list(regions)
        self.values = values


def region(label, box, role):
    return {"label": label, "role": role, **{key: round(box[key], 1) for key in ("x", "y", "width", "height")}}


def check(result, name, kind, operation, browser_error, clock=None):
    """Run one check and record its outcome, the moment it ran and any measured regions or values."""
    entry = {"name": name, "type": kind}
    if clock is not None:
        entry["at_ms"] = round((perf_counter() - clock) * 1000)
    try:
        outcome = operation()
    except Finding as error:
        detail, passed = str(error), False
        if error.regions:
            entry["regions"] = error.regions
        entry.update(error.values)
    except (browser_error, AssertionError, RuntimeError) as error:
        detail, passed = str(error), False
    else:
        passed = True
        if isinstance(outcome, tuple):
            outcome, regions = outcome
            if regions:
                entry["regions"] = regions
        detail = outcome
    entry.update(passed=passed, detail=detail)
    result["checks"].append(entry)
    return passed


def wait_until_ready(page, response, url, selector):
    if response is None or not response.ok:
        status = response.status if response else "no response"
        raise RuntimeError(f"Build navigation returned {status}")
    if origin(page.url) != origin(url):
        raise RuntimeError("Build navigation left its configured origin")
    page.locator(selector).wait_for(state="visible")


def open_build(page, url, selector, result):
    start = perf_counter()
    response = page.goto(url, wait_until="domcontentloaded")
    wait_until_ready(page, response, url, selector)
    result["ready_ms"] = round((perf_counter() - start) * 1000, 1)
    return f"{result['ready_ms']} ms to visible {selector}"


def run_step(page, step, expect, config, url):
    action = step["action"]
    if action == "reload":
        response = page.reload(wait_until="domcontentloaded")
        wait_until_ready(page, response, url, config["ready_selector"])
        return f"reload until visible {config['ready_selector']}"
    locator = page.locator(step["selector"])
    if action == "visible":
        locator.wait_for(state="visible")
    elif action == "text":
        try:
            expect(locator).to_have_text(step["text"], timeout=config["timeout_ms"])
        except AssertionError as error:
            actual = None
            try:
                actual = locator.first.inner_text(timeout=500)
            except Exception:  # The element may be gone; the expectation message still stands.
                pass
            values = {"expected": step["text"]}
            if actual is not None:
                values["actual"] = actual
            raise Finding(str(error).splitlines()[0] if str(error) else "Text did not match",
                          **values) from None
    elif action == "press":
        locator.press(step["key"])
    else:
        getattr(locator, action)()
    return f"{action} {step['selector']}"


def visible_box(page, selector):
    locator = page.locator(selector)
    locator.wait_for(state="visible")
    box = locator.bounding_box()
    if box is None or box["width"] <= 0 or box["height"] <= 0:
        raise RuntimeError(f"{selector} has no visible bounds")
    return box


def assert_within(page, selector):
    box = visible_box(page, selector)
    width, height = page.evaluate("() => [document.documentElement.clientWidth, document.documentElement.clientHeight]")
    regions = [region(selector, box, "element")]
    if (box["x"] < -0.5 or box["y"] < -0.5 or box["x"] + box["width"] > width + 0.5
            or box["y"] + box["height"] > height + 0.5):
        shown = {key: round(box[key], 1) for key in ("x", "y", "width", "height")}
        raise Finding(f"{selector} bounds {shown} exceed the {width} × {height} layout viewport", regions,
                      expected=f"inside 0,0 – {width} × {height}",
                      actual=f"x {shown['x']}, y {shown['y']}, {shown['width']} × {shown['height']}")
    clipped = page.locator(selector).evaluate("""element => {
        const style = getComputedStyle(element);
        const clips = value => ['hidden', 'clip'].includes(value);
        return (clips(style.overflowX) && element.clientWidth && element.scrollWidth > element.clientWidth) ||
               (clips(style.overflowY) && element.clientHeight && element.scrollHeight > element.clientHeight);
    }""")
    if clipped:
        raise Finding(f"{selector} has content that exceeds its clipped bounds", regions,
                      expected="content fits its box", actual="content is clipped")
    return f"{selector} fits the viewport", regions


def assert_no_overlap(page, left, right):
    first, second = visible_box(page, left), visible_box(page, right)
    width = min(first["x"] + first["width"], second["x"] + second["width"]) - max(first["x"], second["x"])
    height = min(first["y"] + first["height"], second["y"] + second["height"]) - max(first["y"], second["y"])
    regions = [region(left, first, "element"), region(right, second, "element")]
    if width > 0.5 and height > 0.5:
        overlap = {"x": max(first["x"], second["x"]), "y": max(first["y"], second["y"]),
                   "width": width, "height": height}
        raise Finding(f"{left} and {right} overlap by {width:.1f} × {height:.1f} CSS pixels",
                      [*regions, region("overlap", overlap, "overlap")],
                      expected="no shared area", actual=f"{width:.1f} × {height:.1f} px shared")
    return f"{left} and {right} do not overlap", regions


def inspect_layout(page, layout, result, browser_error, clock):
    for selector in layout.get("within", []):
        check(result, selector, "within", lambda: assert_within(page, selector), browser_error, clock)
    for left, right in layout.get("no_overlap", []):
        check(result, f"{left} / {right}", "no_overlap",
              lambda: assert_no_overlap(page, left, right), browser_error, clock)


def capture_side(browser, playwright, config, viewport, directory, side, recording):
    result = {"ready_ms": None, "scenario_passed": False, "errors": [], "checks": []}
    failure = playwright.Error
    captures = []
    context = None
    video = None
    left_origin = False
    url = config[side]["url"]
    initial_origin = origin(url)

    def route_request(route):
        request = route.request
        if (request.is_navigation_request() and request.frame.parent_frame is None
                and origin(request.url) != initial_origin):
            result["errors"].append("Main frame attempted to leave its configured origin")
            route.abort()
        else:
            route.continue_()

    def observe_navigation(frame):
        nonlocal left_origin
        if frame.parent_frame is None and origin(frame.url) != initial_origin:
            if not left_origin:
                result["errors"].append("Main frame left its configured origin")
            left_origin = True

    with TemporaryDirectory(dir=directory, prefix=".browser-") as scratch:
        options = {"viewport": viewport, "has_touch": True, "device_scale_factor": 1}
        if recording:
            options.update(record_video_dir=scratch, record_video_size=viewport)
        try:
            context = browser.new_context(**options)
            context.route("**/*", route_request)
            context.set_default_timeout(config["timeout_ms"])
            page = context.new_page()
            # The recorder starts with the page, so check times are measured from this moment.
            clock = perf_counter()
            video = page.video
            page.on("pageerror", lambda error: result["errors"].append(f"Page error: {error}"))
            page.on("framenavigated", observe_navigation)
            ready = check(result, "Ready", "navigation",
                          lambda: open_build(page, url, config["ready_selector"], result), failure, clock)
            if ready:
                for index, step in enumerate(config["steps"], 1):
                    if left_origin:
                        break
                    if not check(result, step.get("label", f"step {index}"), "step",
                                 lambda: run_step(page, step, playwright.expect, config, url), failure, clock):
                        break
                else:
                    if not left_origin:
                        inspect_layout(page, config["layout"], result, failure, clock)
            if not left_origin and origin(page.url) == initial_origin:
                try:
                    result["capture_ms"] = round((perf_counter() - clock) * 1000)
                    image = page.screenshot(animations="disabled")
                    if not left_origin and origin(page.url) == initial_origin:
                        (directory / f"{side}.png").write_bytes(image)
                        captures.append({"path": f"{side}.png", "role": side})
                except (failure, OSError) as error:
                    result["errors"].append(f"Screenshot: {error}")
        except (failure, OSError) as error:
            result["errors"].append(f"Browser: {error}")
        finally:
            if context is not None:
                try:
                    context.close()
                except failure as error:
                    result["errors"].append(f"Browser context: {error}")
        if video is not None and not left_origin:
            try:
                video.save_as(directory / f"{side}.webm")
                captures.append({"path": f"{side}.webm", "role": "clip"})
            except (failure, OSError) as error:
                result["errors"].append(f"Video: {error}")
    result["scenario_passed"] = bool(result["checks"]) and not result["errors"] and all(
        item["passed"] for item in result["checks"]
    )
    return result, captures


def capture_viewport(browser, playwright, config, name, directory, recording, lang):
    directory.mkdir()
    width, height = VIEWPORTS[name]
    result = {"name": name, "width": width, "height": height, "report": None, "builds": {}}
    captures = []
    for side in ("before", "after"):
        side_result, assets = capture_side(browser, playwright, config,
                                           {"width": width, "height": height}, directory, side, recording)
        result["builds"][side] = side_result
        captures.extend(assets)
    scenario = {"issue": config["issue"], "revisions": {
        side: config[side]["commit"] for side in ("before", "after")
    }, **result}
    write_json(directory / "scenario.json", {key: value for key, value in scenario.items() if key != "report"})
    plan = {"issue": config["issue"], "commit": config["after"]["commit"],
            "files": [*captures, {"path": "scenario.json", "role": "test"}]}
    plan_path = directory / "plan.json"
    write_json(plan_path, plan)
    try:
        build(directory, plan_path, directory / "manifest.json")
        render(directory, directory / "manifest.json", directory / "review.html",
               f"{INDEX_COPY[lang][name]} · {width} × {height}",
               "pending", lang, from_capture=True,
               qa={"viewport": result, "revisions": scenario["revisions"]})
        result["report"] = f"{name}/review.html"
    except (OSError, ValueError, RuntimeError) as error:
        result["report_error"] = str(error)
    return result


def viewport_passed(viewport):
    return bool(viewport["report"]) and all(build["scenario_passed"] for build in viewport["builds"].values())


def side_label(copy, side):
    return copy["candidate_label"] if side == "after" else copy["baseline_label"]


def thumb(out, viewport, side, copy):
    """A capture thumbnail with the regions of its failed checks marked."""
    path = f'{viewport["name"]}/{side}.png'
    label = side_label(copy, side)
    if not (out / path).is_file():
        return (f'<figure data-role="{side}"><figcaption>{label}</figcaption>'
                f'<span class="missing">{copy["no_capture"]}</span></figure>')
    result = viewport["builds"][side]
    overlay = "".join(markers(check.get("regions"), viewport["width"], viewport["height"], True)
                      for check in result.get("checks", []) if not check["passed"])
    alt = copy["candidate"] if side == "after" else copy["baseline"]
    image = frame(file_url(path), alt, overlay=overlay, group="index", lazy=False,
                  caption=f'{copy[viewport["name"]]} · {label}')
    return f'<figure data-role="{side}">{image}<figcaption>{label}</figcaption></figure>'


def viewport_card(out, viewport, lang):
    copy = INDEX_COPY[lang]
    name = viewport["name"]
    status = "passed" if viewport_passed(viewport) else "failed"
    sides = []
    failures = []
    diagnostics = []
    for side in ("before", "after"):
        result = viewport["builds"][side]
        checks = result["checks"]
        passed_count = sum(1 for item in checks if item["passed"])
        time = result["ready_ms"]
        timing = f'{time} {copy["unit"]}' if time is not None else "—"
        side_status = "passed" if result["scenario_passed"] else "failed"
        bar = "".join(f'<span data-passed="{str(item["passed"]).lower()}" title="{attr(item["name"])}"></span>'
                      for item in checks)
        sides.append(
            f'<div class="side"><dt>{side_label(copy, side)}'
            f'<span class="pill" data-status="{side_status}">{copy[side_status]}</span></dt>'
            f'<dd><span class="num">{passed_count}/{len(checks)}</span> {copy["checks"]}</dd>'
            f'<dd class="muted">{copy["timing"]} <span class="time">{timing}</span></dd>'
            f'<dd class="check-bar" aria-hidden="true">{bar}</dd></div>'
        )
        tag = side_label(copy, side)
        for item in checks:
            if not item["passed"]:
                failures.append((tag, item["name"], item["detail"]))
        for error in result["errors"]:
            failures.append((tag, "!", error))
        for item in [*(item["detail"] for item in checks if not item["passed"]), *result["errors"]]:
            diagnostics.append(f'<pre>{tag} · {escape(item)}</pre>')
    if "report_error" in viewport:
        failures.append(("!", "report", viewport["report_error"]))
        diagnostics.append(f'<pre>{escape(viewport["report_error"])}</pre>')
    shown = failures[:4]
    failure_list = ""
    if shown:
        rows = "".join(f'<li><span class="side-tag">{escape(tag)}</span><span><b>{escape(check)}</b> — '
                       f'{escape(detail.splitlines()[0] if detail else "")}</span></li>'
                       for tag, check, detail in shown)
        if len(failures) > len(shown):
            rows += f'<li><span class="side-tag">+{len(failures) - len(shown)}</span><span>{copy["more"]}</span></li>'
        failure_list = f'<ul class="failure-list">{rows}</ul>'
    details = ""
    if diagnostics:
        details = (f'<details class="diagnostics"><summary>{copy["problems"]} ({len(diagnostics)})</summary>'
                   f'{"".join(diagnostics)}</details>')
    footer = ""
    if viewport["report"]:
        report = escape(viewport["report"], quote=True)
        footer = (f'<div class="card-footer"><a class="action primary" href="{report}">'
                  f'{copy["open"]}<span aria-hidden="true">→</span></a></div>')
    return (
        f'<section class="viewport-card panel" data-status="{status}">'
        f'<div class="viewport-head"><div><h2>{copy[name]}</h2>'
        f'<p>{viewport["width"]} × {viewport["height"]}</p></div>'
        f'<span class="pill" data-status="{status}">{copy[status]}</span></div>'
        f'<div class="thumbs">{thumb(out, viewport, "before", copy)}{thumb(out, viewport, "after", copy)}</div>'
        f'<div class="viewport-content"><dl class="side-summary">{"".join(sides)}</dl>'
        f'{failure_list}{footer}{details}</div></section>'
    )


def stats(summary, copy):
    viewports = summary["viewports"]
    passed = sum(1 for viewport in viewports if viewport_passed(viewport))
    checks = [item for viewport in viewports for item in viewport["builds"]["after"]["checks"]]
    checks_passed = sum(1 for item in checks if item["passed"])
    errors = sum(len(viewport["builds"][side]["errors"]) for viewport in viewports for side in ("before", "after"))
    ready = [viewport["builds"]["after"]["ready_ms"] for viewport in viewports
             if viewport["builds"]["after"]["ready_ms"] is not None]
    slowest = f'{max(ready):g}<small>{copy["unit"]}</small>' if ready else "—"
    tiles = [
        ("stat_viewports", f'{passed}<small>/ {len(viewports)}</small>', passed == len(viewports)),
        ("stat_checks", f'{checks_passed}<small>/ {len(checks)}</small>', checks_passed == len(checks)),
        ("stat_errors", str(errors), errors == 0),
        ("stat_ready", slowest, None),
    ]
    rendered = []
    for key, value, ok in tiles:
        state = "" if ok is None else f' data-status="{"passed" if ok else "failed"}"'
        rendered.append(f'<div class="stat"{state}><dt>{copy[key]}</dt><dd>{value}</dd></div>')
    return "".join(rendered)


def write_index(out, summary, lang):
    copy = INDEX_COPY[lang]
    status = "passed" if summary["passed"] else "failed"
    issue = summary["issue"]
    number = issue.rsplit("/", 1)[1]
    repo = issue.rsplit("/issues/", 1)[0]
    before, after = summary["builds"]["before"]["commit"], summary["builds"]["after"]["commit"]
    subtitle = (f'{copy["baseline_label"]} <a href="{attr(f"{repo}/commit/{before}")}"><code>{before[:12]}</code></a>'
                f'<span class="commit-arrow">→</span>{copy["candidate_label"]} '
                f'<a href="{attr(f"{repo}/commit/{after}")}"><code>{after[:12]}</code></a>')
    write_new(out / "index.html", page(
        "qa-index.html", lang,
        title=copy["title"],
        eyebrow=f'{copy["eyebrow"]} #{number}',
        subtitle=subtitle,
        data_label=copy["data"],
        actions_label=copy["actions"],
        markers_label=copy["markers"],
        issue_url=escape(issue, quote=True),
        issue_number=number,
        issue_label=COPY[lang]["issue_label"],
        overall_key=status,
        overall_status=copy[status],
        stats=stats(summary, copy),
        layouts_label=copy["layouts"],
        layout_count=len(summary["viewports"]),
        cards="".join(viewport_card(out, viewport, lang) for viewport in summary["viewports"]),
        note=copy["note"],
    ))


def run_capture(config, out, executable_path, recording, lang):
    try:
        import playwright.sync_api as playwright
    except ImportError as error:
        raise RuntimeError("Browser QA needs Python Playwright and a Chromium installation") from error
    try:
        with playwright.sync_playwright() as driver:
            browser = driver.chromium.launch(executable_path=executable_path)
            try:
                out.mkdir()
                results = [capture_viewport(browser, playwright, config, name, out / name, recording, lang)
                           for name in config["viewports"]]
            finally:
                browser.close()
    except playwright.Error as error:
        raise RuntimeError(f"Browser QA could not run: {error}") from error
    passed = all(viewport_passed(viewport) for viewport in results)
    summary = {"version": 1, "issue": config["issue"], "builds": {
        side: config[side] for side in ("before", "after")
    }, "viewports": results, "passed": passed}
    write_json(out / "summary.json", summary)
    write_index(out, summary, lang)
    return passed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="Local JSON scenario")
    parser.add_argument("--out", required=True, type=Path, help="New output directory")
    parser.add_argument("--executable-path", help="Path to an installed Chromium executable")
    parser.add_argument("--record-video", action="store_true", help="Capture WebM with Playwright's recorder")
    parser.add_argument("--lang", choices=COPY, default="en")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        out = args.out.absolute()
        if out.exists() or out.is_symlink():
            raise ValueError(f"Output directory already exists: {out}")
        passed = run_capture(config, out, args.executable_path, args.record_video, args.lang)
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 2
    print(f"Browser QA: {out / 'index.html'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
