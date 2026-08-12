#!/usr/bin/env python3
"""God Peace hub entry point."""

from __future__ import annotations

import sys

from config import APP_NAME
from single_instance import ensure_single_instance


if __name__ == "__main__":
    if not ensure_single_instance(window_title=APP_NAME):
        sys.exit(0)
    from app import main

    main()
