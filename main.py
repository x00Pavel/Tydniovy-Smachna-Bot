#!/usr/bin/env python3
"""Entry point for the Telegram meal planner bot"""

import sys

try:
    from src.bot import main
    import asyncio

    asyncio.run(main())
except KeyboardInterrupt:
    print("\nBot stopped by user.")
    sys.exit(0)
except Exception as e:
    print(f"Fatal error: {e}", file=sys.stderr)
    sys.exit(1)
