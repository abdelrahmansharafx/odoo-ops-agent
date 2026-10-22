"""HTML for the bot's chat messages. Pure Python (no Odoo imports) so it is unit-testable."""
from markupsafe import Markup, escape

STAGE_ICONS = {"gemini": "✨", "rag": "📚", "odoo": "🗄️"}

# (background rgb, kind) per chip; translucent so it works in light and dark themes
CHIP_COLORS = {"model": "66,133,244", "rag": "52,168,83", "odoo": "113,75,103", "time": "128,128,128"}


def _chip(kind, text):
    return Markup(
        '<span style="display:inline-block;margin:4px 6px 0 0;padding:2px 10px;border-radius:12px;'
        'font-size:12px;background:rgba({c},.15);border:1px solid rgba({c},.4)">{t}</span>'
    ).format(c=Markup(CHIP_COLORS[kind]), t=text)


def status_html(steps):
    """Live progress list: finished steps get a check, the latest one is shown as in progress."""
    rows = []
    for i, step in enumerate(steps):
        active = i == len(steps) - 1
        rows.append(Markup('<div style="margin:3px 0;opacity:{o}">{mark} {icon} {label}{dots}</div>').format(
            o=Markup("1" if active else ".6"),
            mark="⏳" if active else "✅",
            icon=STAGE_ICONS.get(step["stage"], ""),
            label=step["label"],
            dots="…" if active else "",
        ))
    return Markup('<div><b>Business Agent is working</b></div>') + Markup("").join(rows)


def answer_html(data):
    """Final answer plus chips showing the model, RAG documents, Odoo tools and time."""
    chips = [_chip("model", f"✨ {data['model']}")] if data.get("model") else []
    chips += [_chip("rag", f"📚 RAG · {s}") for s in data.get("sources", [])]
    chips += [_chip("odoo", f"🗄️ Odoo · {t}") for t in dict.fromkeys(data.get("tools", [])) if t != "search_process_docs"]
    chips.append(_chip("time", f"⏱ {data['latency_s']:.1f}s"))
    return Markup(data["answer_html"]) + Markup("<div>") + Markup("").join(chips) + Markup("</div>")


def error_html(text):
    return Markup("<p>⚠️ {}</p>").format(escape(text))
