import json
import logging
import threading
import time

import requests

import psycopg2.errors

from odoo import SUPERUSER_ID, api, models
from odoo.modules.registry import Registry
from odoo.tools import html2plaintext

from .rendering import answer_html, error_html, status_html

_logger = logging.getLogger(__name__)

DEFAULT_AGENT_URL = "http://agent:8000"


def _in_env(dbname, fn):
    """Run fn(env) in its own committed transaction, so every update is visible to the chat right away."""
    for attempt in range(4):  # concurrent chat updates can occasionally conflict; just retry
        try:
            with Registry(dbname).cursor() as cr:
                return fn(api.Environment(cr, SUPERUSER_ID, {}))
        except psycopg2.errors.SerializationFailure:
            if attempt == 3:
                raise
            time.sleep(0.4 * (attempt + 1))


def _stream_answer(dbname, channel_id, bot_partner_id, url, question):
    """Background thread: post a live status message, update it as the agent works, then show the answer."""
    steps = [{"stage": "gemini", "label": "Reading your question"}]
    message_id = _in_env(dbname, lambda env: env["discuss.channel"].browse(channel_id).message_post(
        body=status_html(steps), author_id=bot_partner_id, message_type="comment",
        subtype_xmlid="mail.mt_comment").id)

    def show(body):
        _in_env(dbname, lambda env: env["discuss.channel"].browse(channel_id)._message_update_content(
            env["mail.message"].browse(message_id), body, strict=False))

    try:
        with requests.post(f"{url.rstrip('/')}/ask/stream", json={"question": question},
                           stream=True, timeout=(10, 180)) as resp:
            resp.raise_for_status()
            final = None
            for line in resp.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if event["type"] == "status":
                    if steps[-1]["label"] != event["label"]:
                        steps.append(event)
                        show(status_html(steps))
                elif event["type"] == "result":
                    final = event
                elif event["type"] == "error":
                    raise RuntimeError(event["detail"])
        if final is None:
            raise RuntimeError("the agent returned no answer")
        show(answer_html(final))
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        _logger.warning("agent call failed: %s", exc)
        show(error_html("Sorry, I couldn't get an answer from the agent. Please try again in a moment."))


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
        args = (self.env.cr.dbname, self.id, bot_partner.id, url, question)
        # Only start once the user's own message is committed; writing the bot's reply while that
        # transaction is still open conflicts on the chat-member row.
        self.env.cr.postcommit.add(lambda: threading.Thread(target=_stream_answer, args=args, daemon=True).start())
