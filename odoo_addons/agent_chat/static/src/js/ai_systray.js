/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/** Sparkle icon in the top bar: opens the Business Agent chat (a normal Odoo chat window). */
class AiSystray extends Component {
    static template = "agent_chat.AiSystray";

    setup() {
        this.orm = useService("orm");
        this.threadService = useService("mail.thread");
        this.botPartnerId = null;
    }

    async onClick() {
        if (!this.botPartnerId) {
            const [bot] = await this.orm.searchRead("res.users", [["login", "=", "business_agent"]], ["partner_id"], { limit: 1 });
            this.botPartnerId = bot && bot.partner_id[0];
        }
        if (this.botPartnerId) {
            await this.threadService.openChat({ partnerId: this.botPartnerId });
        }
    }
}

registry.category("systray").add("agent_chat.AiSystray", { Component: AiSystray }, { sequence: 5 });
