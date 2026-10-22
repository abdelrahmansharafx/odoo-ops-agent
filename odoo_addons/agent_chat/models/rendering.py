"""HTML for the bot's chat messages. Pure Python (no Odoo imports) so it is unit-testable."""
from markupsafe import Markup, escape

# kind -> (text colour, border/background rgb); Odoo's sanitizer drops the `background` shorthand, so use background-color
CHIP_COLORS = {
    "model": ("#1a56db", "66,133,244"),
    "rag": ("#137333", "52,168,83"),
    "odoo": ("#714b67", "113,75,103"),
    "time": ("#5f6368", "95,99,104"),
}


def _chip(kind, text):
    color, rgb = CHIP_COLORS[kind]
    return Markup(
        '<span style="display:inline-block;margin:4px 6px 0 0;padding:2px 10px;border-radius:12px;'
        'font-size:12px;font-weight:500;color:{color};background-color:rgba({rgb},.16);'
        'border:1px solid rgba({rgb},.45)">{text}</span>'
    ).format(color=color, rgb=Markup(rgb), text=text)


def thinking_html():
    """Spinning sparkle, shimmering word and skeleton lines; all animation lives in the addon's stylesheet."""
    return Markup(
        '<div class="o_agent_thinking"><span class="o_agent_spark"></span>'
        '<span class="o_agent_thinking_text">Thinking</span></div>'
        '<div class="o_agent_skeleton"><span></span><span></span></div>'
    )


def answer_html(data):
    """Final answer plus coloured tags: model, RAG documents, Odoo tools and time."""
    chips = [_chip("model", data["model"])] if data.get("model") else []
    chips += [_chip("rag", f"RAG · {s}") for s in data.get("sources", [])]
    chips += [_chip("odoo", f"Odoo · {t}") for t in dict.fromkeys(data.get("tools", [])) if t != "search_process_docs"]
    chips.append(_chip("time", f"{data['latency_s']:.1f}s"))
    return Markup(data["answer_html"]) + Markup("<div>") + Markup("").join(chips) + Markup("</div>")


def error_html(text):
    return Markup("<p>{}</p>").format(escape(text))
