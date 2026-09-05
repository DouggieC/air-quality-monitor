# Sets up centralised logging for the whole app
import logging
from pathlib import Path


def setup_logging(log_level: str, log_dir: Path, log_to_file: bool) -> None:
    # Main logger configuration
    # Always log to stdout
    handlers = [logging.StreamHandler()]

    # If LOG_TO_FILE is 'true' or unset, log to file as well
    if log_to_file:
        handlers.append(logging.FileHandler(log_dir / "air_quality_monitor.log", encoding="utf-8")) 

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        handlers=handlers,
    )

    # OPTIONAL - override level for sspecific modules
    # logging.getLogger('air_quality_monitor.client').setLevel(logging.DEBUG)
    # logging.getLogger('air_quality_monitor.storage').setLevel(logging.WARNING)
