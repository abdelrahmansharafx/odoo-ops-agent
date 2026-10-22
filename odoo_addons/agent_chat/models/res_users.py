from markupsafe import Markup

from odoo import models

GREETING = Markup(
    "<p>Hi! I'm the <b>Business Agent</b>. Ask me about leads, the pipeline, sales orders, "
    "customers or internal processes.</p>"
    "<p>For example: <i>How many leads are in the Qualified stage?</i></p>"
)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _init_messaging(self):
        self._agent_chat_ensure_dm()
        return super()._init_messaging()

    def _agent_chat_ensure_dm(self):
        """Give each internal user one chat with the agent (created once, so closing it sticks)."""
        bot = self.env.ref("agent_chat.user_business_agent", raise_if_not_found=False)
        if not bot or not self._is_internal() or self.id == bot.id:
            return
        existing = self.env["discuss.channel"].sudo().search([
            ("channel_type", "=", "chat"),
            ("channel_member_ids.partner_id", "=", bot.partner_id.id),
            ("channel_member_ids.partner_id", "=", self.partner_id.id),
        ], limit=1)
        if existing:
            return
        channel = self.env["discuss.channel"].channel_get([bot.partner_id.id, self.partner_id.id])
        channel = self.env["discuss.channel"].browse(channel["id"]).sudo()
        channel.message_post(body=GREETING, author_id=bot.partner_id.id, message_type="comment",
                             subtype_xmlid="mail.mt_comment")
