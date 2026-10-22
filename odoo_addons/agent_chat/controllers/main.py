import logging

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

DEFAULT_AGENT_URL = "http://agent:8000"


class AgentChatController(http.Controller):
    @http.route("/agent_chat/ask", type="json", auth="user")
    def ask(self, question):
        """Proxy the question to the agent service server-side (no CORS, service not exposed to the browser)."""
        question = (question or "").strip()
        if not question:
            return {"error": "Please type a question."}
        url = request.env["ir.config_parameter"].sudo().get_param("agent_chat.url", DEFAULT_AGENT_URL)
        try:
            resp = requests.post(f"{url.rstrip('/')}/ask", json={"question": question}, timeout=120)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            _logger.warning("agent call failed: %s", exc)
            detail = getattr(getattr(exc, "response", None), "text", "") or str(exc)
            return {"error": f"The agent is unavailable: {detail[:200]}"}
