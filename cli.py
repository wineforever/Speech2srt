"""Backward-compatible script entry point.

The installable command lives in :mod:`speech2srt.cli`; keeping this small
wrapper means existing ``python cli.py`` usage continues to work.
"""

from speech2srt.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
