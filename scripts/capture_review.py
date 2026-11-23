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


BUILTIN_PROFILES = {
    "portrait": {"width": 390, "height": 844},
    "landscape": {"width": 844, "height": 390},
    "square": {"width": 512, "height": 512},
}
VIEWPORTS = {name: (value["width"], value["height"]) for name, value in BUILTIN_PROFILES.items()}
PROFILE_FIELDS = {"width", "height", "dpr", "locale", "timezone", "input", "color_scheme", "label", "mobile"}
PROFILE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
LOCALE = re.compile(r"[a-z]{2,3}(?:-[A-Z][A-Za-z]{1,3})?")
TIMEZONE = re.compile(r"[A-Za-z_]+(?:/[A-Za-z0-9_+-]+){0,2}")
COMPARISONS = {"equals", "not_equals", "at_least", "at_most", "includes", "exists"}
STATE_JS = """path => {
  const bridge = window.__gameTest;
  if (!bridge || typeof bridge.state !== 'function') return {bridge: false};
  let value = bridge.state();
  for (const key of path.split('.').filter(Boolean)) { if (value === null || value === undefined) break; value = value[key]; }
  return {bridge: true, defined: value !== undefined, value: value === undefined ? null : JSON.parse(JSON.stringify(value))};
}"""
COMMAND_JS = """async ([name, args]) => {
  const bridge = window.__gameTest;
  if (!bridge || typeof bridge.command !== 'function') throw new Error('window.__gameTest.command is missing');
  const result = await bridge.command(name, args);
  return result === undefined ? null : JSON.parse(JSON.stringify(result));
}"""
INDEX_COPY = {
    "en": {
        "title": "Web build QA", "data": "Results JSON", "actions": "Report links",
        "portrait": "Portrait", "landscape": "Landscape", "square": "Square",
        "passed": "Passed", "failed": "Failed", "open": "Open the check inspector",
        "problems": "Full diagnostics", "timing": "Ready in", "unit": "ms",
        "candidate": "Candidate capture", "baseline": "Baseline capture", "markers": "Markers",
        "eyebrow": "Browser QA · Issue", "baseline_label": "Baseline", "candidate_label": "Candidate",
        "stat_viewports": "Profiles passed", "stat_checks": "Candidate checks passed",
        "stat_errors": "Browser errors", "stat_ready": "Slowest candidate ready",
        "checks": "checks", "no_capture": "No capture", "more": "more", "layouts": "Layouts",
        "input_touch": "touch", "input_mouse": "mouse",
        "note": "Every number on this page was measured by the runner in Chromium. Device, GPU and platform behaviour need their own evidence.",
    },
    "ru": {
        "title": "Проверка веб-сборок", "data": "Результаты JSON", "actions": "Ссылки отчёта",
        "portrait": "Портрет", "landscape": "Альбом", "square": "Квадрат",
        "passed": "Пройдено", "failed": "Ошибка", "open": "Открыть разбор проверок",
        "problems": "Полная диагностика", "timing": "Готова за", "unit": "мс",
        "candidate": "Кадр новой сборки", "baseline": "Кадр исходной сборки", "markers": "Маркеры",
        "eyebrow": "Браузерный QA · задача", "baseline_label": "Исходная", "candidate_label": "Новая",
        "stat_viewports": "Профилей пройдено", "stat_checks": "Проверок новой сборки",
        "stat_errors": "Ошибок браузера", "stat_ready": "Самая долгая загрузка",
        "checks": "проверок", "no_capture": "Кадра нет", "more": "ещё", "layouts": "Профили экрана",
        "input_touch": "тач", "input_mouse": "мышь",
        "note": "Все числа на странице измерены раннером в Chromium. Поведение на устройствах, GPU и платформах требует отдельных доказательств.",
    },
}
LOOPBACK = {"localhost", "127.0.0.1", "::1"}
STEP_FIELDS = {
    "click": {"selector"}, "tap": {"selector"}, "visible": {"selector"},
    "press": {"selector", "key"}, "text": {"selector", "text"}, "reload": set(),
    "tap_at": {"selector", "x", "y"}, "state": {"path"}, "command": {"name"}, "wait": {"ms"}, "frame": set(),
}
STEP_OPTIONAL = {"state": COMPARISONS, "command": {"args"}}


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
    if not isinstance(steps, list) or len(steps) > 80:
        raise ValueError("steps must be a list of at most 80 actions")
    for index, step in enumerate(steps, 1):
        name = f"step {index}"
        action = step.get("action") if isinstance(step, dict) else None
        if not isinstance(action, str) or action not in STEP_FIELDS:
            raise ValueError(f"{name} has an unsupported action")
        required = {"action"} | STEP_FIELDS[action]
        check_fields(step, required, {"label"} | STEP_OPTIONAL.get(action, set()), name)
        for key in ("selector", "key", "label", "path", "name"):
            if key in step:
                check_string(step[key], f"{name}.{key}")
        if "text" in step:
            check_string(step["text"], f"{name}.text", empty=True)
        if action == "tap_at":
            for axis in ("x", "y"):
                if type(step[axis]) not in (int, float) or not 0 <= step[axis] <= 1:
                    raise ValueError(f"{name}.{axis} must be a fraction of the element between 0 and 1")
        if action == "wait" and (type(step["ms"]) is not int or not 0 <= step["ms"] <= 10_000):
            raise ValueError(f"{name}.ms must be an integer between 0 and 10000")
        if action == "state":
            used = COMPARISONS & step.keys()
            if len(used) != 1:
                raise ValueError(f"{name} needs exactly one of {sorted(COMPARISONS)}")
            if "exists" in used and type(step["exists"]) is not bool:
                raise ValueError(f"{name}.exists must be true or false")
            if used & {"at_least", "at_most"} and type(step[next(iter(used))]) not in (int, float):
                raise ValueError(f"{name}: at_least and at_most compare numbers")
            if not re.fullmatch(r"[A-Za-z0-9_$]+(?:\.[A-Za-z0-9_$]+)*", step["path"]):
                raise ValueError(f"{name}.path must be dotted keys such as player.score")
        if action == "command":
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", step["name"]):
                raise ValueError(f"{name}.name must be a short command name")
            if "args" in step and len(json.dumps(step["args"])) > 2048:
                raise ValueError(f"{name}.args must stay under 2 KB of JSON")


def check_profile(name, value):
    if not PROFILE_NAME.fullmatch(name) or len(name) > 40:
        raise ValueError(f"profile name {name!r} must be short kebab-case")
    check_fields(value, {"width", "height"}, PROFILE_FIELDS - {"width", "height"}, f"profile {name}")
    for key, low, high in (("width", 200, 4096), ("height", 200, 4096)):
        if type(value[key]) is not int or not low <= value[key] <= high:
            raise ValueError(f"profile {name}.{key} must be an integer between {low} and {high}")
    if "dpr" in value and (type(value["dpr"]) not in (int, float) or not 1 <= value["dpr"] <= 4):
        raise ValueError(f"profile {name}.dpr must be between 1 and 4")
    if "locale" in value and (not isinstance(value["locale"], str) or not LOCALE.fullmatch(value["locale"])):
        raise ValueError(f"profile {name}.locale must look like en or pt-BR")
    if "timezone" in value and (not isinstance(value["timezone"], str) or not TIMEZONE.fullmatch(value["timezone"])):
        raise ValueError(f"profile {name}.timezone must be an IANA name such as Europe/Kyiv")
    if value.get("input", "touch") not in {"touch", "mouse"}:
        raise ValueError(f"profile {name}.input must be touch or mouse")
    if value.get("color_scheme", "dark") not in {"light", "dark", "no-preference"}:
        raise ValueError(f"profile {name}.color_scheme must be light, dark or no-preference")
    if "mobile" in value and type(value["mobile"]) is not bool:
        raise ValueError(f"profile {name}.mobile must be true or false")
    if "label" in value:
        check_string(value["label"], f"profile {name}.label", limit=60)


def resolve_profiles(config, only=None):
    """The ordered list of profiles to run: built-in names or the scenario's own profiles."""
    custom = config.get("profiles", {})
    if not isinstance(custom, dict) or len(custom) > 30:
        raise ValueError("profiles must be an object with at most 30 entries")
    for name, value in custom.items():
        check_profile(name, value)
    known = {**BUILTIN_PROFILES, **custom}
    names = config.get("viewports", list(custom) or list(BUILTIN_PROFILES))
    if (not isinstance(names, list) or not names or len(names) != len(set(names))
            or any(not isinstance(name, str) or name not in known for name in names)):
        raise ValueError(f"viewports must list distinct profile names from {sorted(known)}")
    if only:
        missing = [name for name in only if name not in names]
        if missing:
            raise ValueError(f"--profiles names not in this scenario: {missing}")
        names = [name for name in names if name in only]
    return [{"name": name, "dpr": 1, "input": "touch", **known[name]} for name in names]


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
                 {"viewports", "profiles", "layout", "timeout_ms", "step_frames", "title"}, "config")
    if not isinstance(config["issue"], str) or not ISSUE_URL.fullmatch(config["issue"]):
        raise ValueError("Expected the full GitHub Issue URL")
    for side in ("before", "after"):
        check_build(config[side], side)
    check_string(config["ready_selector"], "ready_selector")
    check_steps(config["steps"])
    resolved = resolve_profiles(config)
    viewports = [profile["name"] for profile in resolved]
    if "step_frames" in config and type(config["step_frames"]) is not bool:
        raise ValueError("step_frames must be true or false")
    if "title" in config:
        check_string(config["title"], "title", limit=120)
    layout = config.get("layout", {})
    check_layout(layout)
    timeout_ms = config.get("timeout_ms", 10_000)
    if type(timeout_ms) is not int or not 100 <= timeout_ms <= 60_000:
        raise ValueError("timeout_ms must be an integer between 100 and 60000")
    return {**config, "viewports": viewports, "resolved_profiles": resolved, "layout": layout,
            "timeout_ms": timeout_ms}


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


def describe(value):
    return json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value


def state_matches(step, observed):
    value, defined = observed.get("value"), observed.get("defined", False)
    if "exists" in step:
        return defined == step["exists"]
    if not defined:
        return False
    if "equals" in step:
        return value == step["equals"]
    if "not_equals" in step:
        return value != step["not_equals"]
    if "includes" in step:
        return isinstance(value, (list, str)) and step["includes"] in value
    if type(value) not in (int, float) or isinstance(value, bool):
        return False
    return value >= step["at_least"] if "at_least" in step else value <= step["at_most"]


def expectation(step):
    for key in ("equals", "not_equals", "at_least", "at_most", "includes", "exists"):
        if key in step:
            return f"{step['path']} {key.replace('_', ' ')} {describe(step[key])}"
    return step["path"]


def wait_for_state(page, step, timeout_ms):
    """Poll the game's test bridge until the state matches or the timeout passes."""
    deadline = perf_counter() + timeout_ms / 1000
    observed = {}
    while True:
        observed = page.evaluate(STATE_JS, step["path"])
        if not observed.get("bridge"):
            raise Finding("The game exposes no window.__gameTest.state() bridge",
                          expected="window.__gameTest.state()", actual="missing")
        if state_matches(step, observed):
            return f"{expectation(step)} (observed {describe(observed.get('value'))})"
        if perf_counter() >= deadline:
            actual = describe(observed.get("value")) if observed.get("defined") else "undefined"
            raise Finding(f"State {step['path']} did not match within {timeout_ms} ms",
                          expected=expectation(step), actual=actual)
        page.wait_for_timeout(100)


def run_step(page, step, expect, config, url, profile):
    action = step["action"]
    if action == "reload":
        response = page.reload(wait_until="domcontentloaded")
        wait_until_ready(page, response, url, config["ready_selector"])
        return f"reload until visible {config['ready_selector']}"
    if action == "wait":
        page.wait_for_timeout(step["ms"])
        return f"waited {step['ms']} ms"
    if action == "frame":
        return "checkpoint"
    if action == "state":
        return wait_for_state(page, step, config["timeout_ms"])
    if action == "command":
        result = page.evaluate(COMMAND_JS, [step["name"], step.get("args")])
        return f"command {step['name']}" + (f" → {describe(result)}" if result is not None else "")
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
    elif action == "tap_at":
        box = visible_box(page, step["selector"])
        position = {"x": box["width"] * step["x"], "y": box["height"] * step["y"]}
        (locator.first.tap if profile["input"] == "touch" else locator.first.click)(position=position)
        return f"{'tap' if profile['input'] == 'touch' else 'click'} {step['selector']} at {step['x']:.2f}, {step['y']:.2f}"
    elif action == "tap" and profile["input"] != "touch":
        locator.click()
        return f"click {step['selector']} (mouse profile)"
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


def capture_side(browser, playwright, config, profile, directory, side, recording, step_frames):
    viewport = {"width": profile["width"], "height": profile["height"]}
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
        options = {"viewport": viewport, "has_touch": profile["input"] == "touch",
                   "device_scale_factor": profile["dpr"], "is_mobile": profile.get("mobile", False)}
        for key, option in (("locale", "locale"), ("timezone", "timezone_id"), ("color_scheme", "color_scheme")):
            if key in profile:
                options[option] = profile[key]
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
            def frame(index):
                """A capture of the page right after a check, linked from that check."""
                if left_origin or origin(page.url) != initial_origin:
                    return
                name = f"steps/{side}-{index:02d}.png"
                try:
                    (directory / "steps").mkdir(exist_ok=True)
                    (directory / name).write_bytes(page.screenshot(animations="disabled"))
                except (failure, OSError) as error:
                    result["errors"].append(f"Step frame {index}: {error}")
                    return
                result["checks"][-1]["frame"] = name
                captures.append({"path": name, "role": "step"})

            ready = check(result, "Ready", "navigation",
                          lambda: open_build(page, url, config["ready_selector"], result), failure, clock)
            if step_frames:
                frame(0)
            if ready:
                for index, step in enumerate(config["steps"], 1):
                    if left_origin:
                        break
                    passed = check(result, step.get("label", f"step {index}"), "step",
                                   lambda: run_step(page, step, playwright.expect, config, url, profile),
                                   failure, clock)
                    result["checks"][-1]["action"] = step["action"]
                    if step_frames or step["action"] == "frame" or not passed:
                        frame(index)
                    if not passed:
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


def profile_title(viewport, copy):
    return viewport.get("label") or copy.get(viewport["name"], viewport["name"])


def capture_viewport(browser, playwright, config, profile, directory, recording, lang, step_frames):
    name = profile["name"]
    directory.mkdir()
    width, height = profile["width"], profile["height"]
    details = {key: profile[key] for key in ("dpr", "input", "locale", "timezone", "color_scheme", "mobile", "label")
               if key in profile}
    result = {"name": name, "width": width, "height": height, **details, "report": None, "builds": {}}
    captures = []
    for side in ("before", "after"):
        side_result, assets = capture_side(browser, playwright, config, profile, directory, side,
                                           recording, step_frames)
        result["builds"][side] = side_result
        captures.extend(assets)
    scenario = {"issue": config["issue"], "revisions": {
        side: config[side]["commit"] for side in ("before", "after")
    }, **result}
    scenario["steps"] = config["steps"]
    write_json(directory / "scenario.json", {key: value for key, value in scenario.items() if key != "report"})
    plan = {"issue": config["issue"], "commit": config["after"]["commit"],
            "files": [*captures, {"path": "scenario.json", "role": "test"}]}
    plan_path = directory / "plan.json"
    write_json(plan_path, plan)
    try:
        build(directory, plan_path, directory / "manifest.json")
        render(directory, directory / "manifest.json", directory / "review.html",
               f"{profile_title(result, INDEX_COPY[lang])} · {width} × {height}",
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
                  caption=f'{profile_title(viewport, copy)} · {label}')
    return f'<figure data-role="{side}">{image}<figcaption>{label}</figcaption></figure>'


def profile_chips(viewport, copy):
    chips = []
    if viewport.get("dpr", 1) != 1:
        chips.append(f'@{viewport["dpr"]:g}x')
    if viewport.get("input"):
        chips.append(copy["input_" + viewport["input"]])
    for key in ("locale", "timezone"):
        if viewport.get(key):
            chips.append(escape(viewport[key]))
    return "".join(f'<span class="chip">{chip}</span>' for chip in chips)


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
        f'<div class="viewport-head"><div><h2>{escape(profile_title(viewport, copy))}</h2>'
        f'<p>{viewport["width"]} × {viewport["height"]}{profile_chips(viewport, copy)}</p></div>'
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
        title=escape(summary.get("title") or copy["title"]),
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


def run_capture(config, out, executable_path, recording, lang, step_frames=None, only=None, progress=None):
    """Run every selected profile. ``progress`` gets a short line before each profile."""
    profiles = resolve_profiles(config, only) if only else config["resolved_profiles"]
    step_frames = config.get("step_frames", False) if step_frames is None else step_frames
    progress = progress or (lambda line: None)
    try:
        import playwright.sync_api as playwright
    except ImportError as error:
        raise RuntimeError("Browser QA needs Python Playwright and a Chromium installation") from error
    try:
        with playwright.sync_playwright() as driver:
            browser = driver.chromium.launch(executable_path=executable_path)
            try:
                out.mkdir()
                results = []
                for number, profile in enumerate(profiles, 1):
                    progress(f"[{number}/{len(profiles)}] {profile['name']} {profile['width']}×{profile['height']}")
                    results.append(capture_viewport(browser, playwright, config, profile, out / profile["name"],
                                                    recording, lang, step_frames))
            finally:
                browser.close()
    except playwright.Error as error:
        raise RuntimeError(f"Browser QA could not run: {error}") from error
    passed = all(viewport_passed(viewport) for viewport in results)
    summary = {"version": 1, "issue": config["issue"], "title": config.get("title", ""), "builds": {
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
    parser.add_argument("--step-frames", action="store_true", help="Capture a frame after every scenario step")
    parser.add_argument("--profiles", help="Comma-separated subset of the scenario's profiles to run")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        out = args.out.absolute()
        if out.exists() or out.is_symlink():
            raise ValueError(f"Output directory already exists: {out}")
        only = [name.strip() for name in args.profiles.split(",") if name.strip()] if args.profiles else None
        passed = run_capture(config, out, args.executable_path, args.record_video, args.lang,
                             step_frames=True if args.step_frames else None, only=only,
                             progress=lambda line: print(line, flush=True))
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 2
    print(f"Browser QA: {out / 'index.html'}")
    return 0 if passed else 1


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    raise SystemExit(main())
