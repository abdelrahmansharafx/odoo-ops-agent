/** @odoo-module **/
import { Component, useState, useRef, onPatched } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class AgentChat extends Component {
    static template = "agent_chat.AgentChat";

    setup() {
        this.rpc = useService("rpc");
        this.listRef = useRef("list");
        this.state = useState({ open: false, busy: false, input: "", messages: [] });
        onPatched(() => {
            const el = this.listRef.el;
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });
    }

    toggle() {
        this.state.open = !this.state.open;
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.send();
        }
    }

    async send() {
        const question = this.state.input.trim();
        if (!question || this.state.busy) {
            return;
        }
        this.state.messages.push({ role: "user", text: question });
        this.state.input = "";
        this.state.busy = true;
        try {
            const res = await this.rpc("/agent_chat/ask", { question });
            if (res.error) {
                this.state.messages.push({ role: "error", text: res.error });
            } else {
                const meta = `${res.tools.join(", ") || "no tools"} · ${res.latency_s}s`;
                this.state.messages.push({ role: "agent", text: res.answer, meta });
            }
        } catch (err) {
            this.state.messages.push({ role: "error", text: "Request failed. Is the agent service running?" });
        } finally {
            this.state.busy = false;
        }
    }
}

registry.category("systray").add("agent_chat.AgentChat", { Component: AgentChat }, { sequence: 1 });
