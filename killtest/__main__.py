"""Entry point: read the frozen snapshot in data/, run the pre-registered backtest, log the
verdict. Exits 0 regardless of ALIVE/DEAD — a correct DEAD is a successful run.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from killtest.pipeline import run
from qf.datasource import LocalParquetSource
from qf.logging_config import configure_logging

logger = structlog.get_logger(__name__)


def main() -> int:
    configure_logging("INFO")
    source = LocalParquetSource(Path(__file__).resolve().parent.parent / "data")
    verdict = run(source)
    logger.info("run_complete", verdict=verdict.label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
