#!/usr/bin/env python3
"""Compare two local web builds with a declarative browser QA scenario."""

import argparse
from html import escape
import json
from pathlib import Path
import re
from string import Template
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from urllib.parse import urlsplit

from render_review import COPY, STYLES, render
from review_evidence import ISSUE_URL, build, require_keys


VIEWPORTS = {"portrait": (390, 844), "landscape": (844, 390), "square": (512, 512)}
INDEX_TEMPLATE = STYLES.with_name("qa-index.html")
INDEX_COPY = {
    "en": {
        "title": "Web build QA", "data": "Results JSON", "actions": "Report links",
        "portrait": "Portrait", "landscape": "Landscape", "square": "Square",
        "passed": "Passed", "failed": "Failed", "open": "Review captures",
        "problems": "Diagnostics", "timing": "Time to ready", "unit": "ms",
        "candidate": "Candidate capture", "baseline": "Baseline capture",
    },
    "ru": {
        "title": "Проверка веб-сборок", "data": "Результаты JSON", "actions": "Ссылки отчёта",
        "portrait": "Портрет", "landscape": "Альбом", "square": "Квадрат",
        "passed": "Пройдено", "failed": "Ошибка", "open": "Смотреть кадры",
        "problems": "Диагностика", "timing": "До готовности", "unit": "мс",
        "candidate": "Кадр новой сборки", "baseline": "Кадр исходной сборки",
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


def check(result, name, kind, operation, browser_error):
    try:
        detail = operation()
    except (browser_error, AssertionError, RuntimeError) as error:
        detail = str(error)
        passed = False
    else:
        passed = True
    result["checks"].append({"name": name, "type": kind, "passed": passed, "detail": detail})
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
        expect(locator).to_have_text(step["text"], timeout=config["timeout_ms"])
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
    if (box["x"] < -0.5 or box["y"] < -0.5 or box["x"] + box["width"] > width + 0.5
            or box["y"] + box["height"] > height + 0.5):
        raise RuntimeError(f"{selector} bounds {box} exceed the {width} × {height} layout viewport")
    clipped = page.locator(selector).evaluate("""element => {
        const style = getComputedStyle(element);
        const clips = value => ['hidden', 'clip'].includes(value);
        return (clips(style.overflowX) && element.clientWidth && element.scrollWidth > element.clientWidth) ||
               (clips(style.overflowY) && element.clientHeight && element.scrollHeight > element.clientHeight);
    }""")
    if clipped:
        raise RuntimeError(f"{selector} has content that exceeds its clipped bounds")
    return f"{selector} fits the viewport"


def assert_no_overlap(page, left, right):
    first, second = visible_box(page, left), visible_box(page, right)
    width = min(first["x"] + first["width"], second["x"] + second["width"]) - max(first["x"], second["x"])
    height = min(first["y"] + first["height"], second["y"] + second["height"]) - max(first["y"], second["y"])
    if width > 0.5 and height > 0.5:
        raise RuntimeError(f"{left} and {right} overlap by {width:.1f} × {height:.1f} CSS pixels")
    return f"{left} and {right} do not overlap"


def inspect_layout(page, layout, result, browser_error):
    for selector in layout.get("within", []):
        check(result, selector, "within", lambda: assert_within(page, selector), browser_error)
    for left, right in layout.get("no_overlap", []):
        check(result, f"{left} / {right}", "no_overlap",
              lambda: assert_no_overlap(page, left, right), browser_error)


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
            video = page.video
            page.on("pageerror", lambda error: result["errors"].append(f"Page error: {error}"))
            page.on("framenavigated", observe_navigation)
            ready = check(result, "Ready", "navigation",
                          lambda: open_build(page, url, config["ready_selector"], result), failure)
            if ready:
                for index, step in enumerate(config["steps"], 1):
                    if left_origin:
                        break
                    if not check(result, step.get("label", f"step {index}"), "step",
                                 lambda: run_step(page, step, playwright.expect, config, url), failure):
                        break
                else:
                    if not left_origin:
                        inspect_layout(page, config["layout"], result, failure)
            if not left_origin and origin(page.url) == initial_origin:
                try:
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
               f"{COPY[lang]['before']} / {COPY[lang]['after']} · {width} × {height}",
               "pending", lang, from_capture=True)
        result["report"] = f"{name}/review.html"
    except (OSError, ValueError, RuntimeError) as error:
        result["report_error"] = str(error)
    return result


def viewport_card(out, viewport, lang):
    copy = INDEX_COPY[lang]
    name = viewport["name"]
    passed = viewport["report"] and all(build["scenario_passed"] for build in viewport["builds"].values())
    status = "passed" if passed else "failed"
    metrics = []
    diagnostics = []
    for side, result in viewport["builds"].items():
        label = COPY[lang][side]
        time = result["ready_ms"]
        timing = f'{time} {copy["unit"]}' if time is not None else "—"
        side_status = "passed" if result["scenario_passed"] else "failed"
        metrics.append(
            f'<div class="metric"><dt>{label}</dt><dd class="time">{timing}</dd>'
            f'<dd class="pill" data-status="{side_status}">{copy[side_status]}</dd></div>'
        )
        failures = [item["detail"] for item in result["checks"] if not item["passed"]]
        for failure in [*failures, *result["errors"]]:
            diagnostics.append(f'<pre>{label} · {escape(failure)}</pre>')
    if "report_error" in viewport:
        diagnostics.append(f'<pre>{escape(viewport["report_error"])}</pre>')
    details = ""
    if diagnostics:
        details = (f'<details class="diagnostics"><summary>{copy["problems"]} ({len(diagnostics)})</summary>'
                   f'{"".join(diagnostics)}</details>')
    thumbnail = ""
    footer = ""
    if viewport["report"]:
        for side, label in (("after", "candidate"), ("before", "baseline")):
            path = f"{name}/{side}.png"
            if (out / path).is_file():
                thumbnail = (f'<div class="thumb"><img src="{path}" alt="{copy[label]}" '
                             'loading="lazy" decoding="async"></div>')
                break
        report = escape(viewport["report"], quote=True)
        footer = (f'<div class="card-footer"><a class="action primary" href="{report}">'
                  f'{copy["open"]}<span aria-hidden="true">→</span></a></div>')
    return (
        f'<section class="viewport-card panel"><div class="viewport-content">'
        f'<div class="viewport-head"><div><h2>{copy[name]}</h2>'
        f'<p>{viewport["width"]} × {viewport["height"]}</p></div>'
        f'<span class="pill" data-status="{status}">{copy[status]}</span></div>'
        f'{thumbnail}<p class="metrics-label">{copy["timing"]}</p>'
        f'<dl class="metrics">{"".join(metrics)}</dl>'
        f'{footer}{details}</div></section>'
    )


def write_index(out, summary, lang):
    copy = INDEX_COPY[lang]
    status = "passed" if summary["passed"] else "failed"
    issue = summary["issue"]
    page = Template(INDEX_TEMPLATE.read_text(encoding="utf-8")).substitute(
        lang=lang,
        styles=STYLES.read_text(encoding="utf-8"),
        title=copy["title"],
        data_label=copy["data"],
        actions_label=copy["actions"],
        issue_url=escape(issue, quote=True),
        issue_number=issue.rsplit("/", 1)[1],
        issue_label=COPY[lang]["issue_label"],
        overall_key=status,
        overall_status=copy[status],
        cards="".join(viewport_card(out, viewport, lang) for viewport in summary["viewports"]),
    )
    with (out / "index.html").open("x", encoding="utf-8", newline="\n") as file:
        file.write(page)


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
    passed = all(viewport["report"] and all(build["scenario_passed"] for build in viewport["builds"].values())
                 for viewport in results)
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
