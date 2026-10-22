"""Enables `python -m odoo_agent`; the CLI itself lives in cli.py."""
from .cli import main

raise SystemExit(main())
