"""Reproducible tw40ch build pipeline."""

__all__ = ["main"]


def main(argv=None):
    from .cli import main as run

    return run(argv)
