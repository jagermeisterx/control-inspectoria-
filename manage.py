#!/usr/bin/env python
import os
import sys
from urllib.parse import urlparse


def _log_db_target():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("[db-diag] DATABASE_URL no definida", file=sys.stderr, flush=True)
        return
    p = urlparse(url)
    print(
        f"[db-diag] host={p.hostname} port={p.port} "
        f"user={p.username} db={p.path.lstrip('/')}",
        file=sys.stderr,
        flush=True,
    )


def main():
    _log_db_target()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inspectoria.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
