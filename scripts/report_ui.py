"""Shared building blocks for GameDev Studio's offline HTML reports.

Every report is a single HTML file with the stylesheet and script inlined, so it
opens from disk without a server. Media stay next to the report and are linked
relatively. Nothing here reaches the network.
"""

from html import escape
from pathlib import Path
from string import Template
from urllib.parse import quote


UI = Path(__file__).resolve().parents[1] / "ui"
STYLES = UI / "report.css"
SCRIPT = UI / "report.js"
BRAND = UI / "brand-mark.svg"

# Labels the viewer script shows, in order: prev, next, zoom out, zoom in, fit, markers, original, close, hint.
VIEWER_LABELS = {
    "en": ["Previous", "Next", "Zoom out", "Zoom in", "Fit", "Markers", "Original", "Close",
           "Wheel or +/− to zoom · drag to pan · ←/→ to switch · Esc to close"],
    "ru": ["Предыдущий", "Следующий", "Уменьшить", "Увеличить", "Вписать", "Маркеры", "Оригинал", "Закрыть",
           "Колесо или +/− — зум · перетаскивание — сдвиг · ←/→ — следующий · Esc — закрыть"],
}


def attr(value):
    return escape(str(value), quote=True)


def url(path):
    """A relative, percent-encoded URL for a file next to the report."""
    return attr(quote(Path(path).as_posix(), safe="/"))


def viewer_labels(lang):
    return attr("|".join(VIEWER_LABELS.get(lang, VIEWER_LABELS["en"])))


def brand_mark():
    """The studio's own mark, inlined so the report needs no extra file."""
    svg = BRAND.read_text(encoding="utf-8").strip()
    return svg.replace("<svg ", '<svg class="brand-mark" aria-hidden="true" ', 1).replace(' role="img" aria-label="GameDev Studio"', "")


def page(template_name, lang, **values):
    """Fill a template from ui/ with the shared stylesheet, script and viewer labels."""
    template = Template((UI / template_name).read_text(encoding="utf-8"))
    return template.substitute(
        lang=lang,
        styles=STYLES.read_text(encoding="utf-8"),
        script=SCRIPT.read_text(encoding="utf-8"),
        viewer_labels=viewer_labels(lang),
        brand_mark=brand_mark(),
        **values,
    )


def write_new(path, content):
    """Write a report without overwriting an existing file."""
    with Path(path).open("x", encoding="utf-8", newline="\n") as output:
        output.write(content)


def markers(regions, width, height, failed, id_prefix=""):
    """Absolutely positioned boxes, in percent of the capture, for regions measured in CSS pixels."""
    if not regions or not width or not height:
        return ""
    parts = []
    for index, item in enumerate(regions):
        left = max(0.0, item["x"]) / width * 100
        top = max(0.0, item["y"]) / height * 100
        right = min(width, item["x"] + item["width"]) / width * 100
        bottom = min(height, item["y"] + item["height"]) / height * 100
        if right <= left or bottom <= top:
            continue
        identifier = f' id="{attr(id_prefix)}-{index}"' if id_prefix else ""
        role = item.get("role", "element")
        parts.append(
            f'<span class="marker"{identifier} data-role="{attr(role)}" data-failed="{str(bool(failed)).lower()}" '
            f'style="left:{left:.3f}%;top:{top:.3f}%;width:{right - left:.3f}%;height:{bottom - top:.3f}%">'
            f'<span class="marker-label">{escape(item.get("label", ""))}</span></span>'
        )
    return "".join(parts)


def frame(src, alt, *, overlay="", group="", caption="", lazy=True):
    """An image that opens in the zoom viewer, with optional markers drawn over it."""
    loading = ' loading="lazy"' if lazy else ""
    zoom_group = f' data-zoom-group="{attr(group)}"' if group else ""
    return (
        f'<span class="frame" data-markers="on" data-zoom{zoom_group} data-caption="{attr(caption or alt)}">'
        f'<img src="{src}" alt="{attr(alt)}" decoding="async"{loading}>{overlay}</span>'
    )


def seconds(milliseconds):
    return f"{milliseconds / 1000:.2f}"
