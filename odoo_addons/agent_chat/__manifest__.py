{
    "name": "Agent Chat",
    "summary": "Ask business questions to the LangGraph agent from the Odoo top bar",
    "version": "17.0.1.0.0",
    "category": "Productivity",
    "depends": ["web", "crm", "sale_management"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "agent_chat/static/src/js/agent_chat.js",
            "agent_chat/static/src/xml/agent_chat.xml",
            "agent_chat/static/src/scss/agent_chat.scss",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
}
