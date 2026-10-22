{
    "name": "Agent Chat",
    "summary": "A 'Business Agent' contact in Odoo's chat that answers business questions with a LangGraph agent",
    "version": "17.0.2.0.0",
    "category": "Productivity",
    "depends": ["mail", "crm", "sale_management"],
    "data": ["data/bot_data.xml"],
    "assets": {
        "web.assets_backend": [
            "agent_chat/static/src/scss/agent_chat.scss",
            "agent_chat/static/src/js/ai_systray.js",
            "agent_chat/static/src/xml/ai_systray.xml",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
}
