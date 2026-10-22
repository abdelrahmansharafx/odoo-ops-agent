import logging
import threading

import requests
from markupsafe import Markup, escape

from odoo import SUPERUSER_ID, api, models
from odoo.modules.registry import Registry
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

DEFAULT_AGENT_URL = "http://agent:8000"


def _agent_reply(url, question):
    """Ask the agent service; always returns HTML to post (a friendly error on failure)."""
    try:
        resp = requests.post(f"{url.rstrip('/')}/ask", json={"question": question}, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        footer = f'<br/><small style="opacity:.6">{escape(", ".join(data["tools"]) or "no tools")} · {data["latency_s"]}s</small>'
        return Markup(data["answer_html"]) + Markup(footer)
    except requests.RequestException as exc:
        _logger.warning("agent call failed: %s", exc)
        return Markup("<p>Sorry, I couldn't reach the agent service. Please try again in a moment.</p>")


def _post_reply(dbname, channel_id, bot_partner_id, url, question):
    """Runs in a background thread so the user's message post returns immediately."""
    body = _agent_reply(url, question)
    with Registry(dbname).cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        env["discuss.channel"].browse(channel_id).message_post(
            body=body, author_id=bot_partner_id, message_type="comment", subtype_xmlid="mail.mt_comment",
        )


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_post_after_hook(self, message, msg_vals):
        self._agent_chat_maybe_answer(msg_vals)
        return super()._message_post_after_hook(message, msg_vals)

    def _agent_chat_maybe_answer(self, msg_vals):
        if self._name != "discuss.channel" or len(self) != 1 or self.channel_type != "chat":
            return
        bot = self.env.ref("agent_chat.user_business_agent", raise_if_not_found=False)
        if not bot or msg_vals.get("message_type") != "comment":
            return
        bot_partner = bot.partner_id
        if msg_vals.get("author_id") == bot_partner.id or bot_partner not in self.channel_partner_ids:
            return
        question = html2plaintext(msg_vals.get("body") or "").strip()
        if not question:
            return
        url = self.env["ir.config_parameter"].sudo().get_param("agent_chat.url", DEFAULT_AGENT_URL)
        threading.Thread(
            target=_post_reply,
            args=(self.env.cr.dbname, self.id, bot_partner.id, url, question),
            daemon=True,
        ).start()
