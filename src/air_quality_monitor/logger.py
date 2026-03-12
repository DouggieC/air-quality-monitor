# Sets up centralised logging for the whole app
import logging
from pathlib import Path

def setup_logging(log_level: str, log_dir: Path) -> None:
    # Main logger configuration
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'air_quality_monitor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # OPTIONAL - override level for sspecific modules
    #logging.getLogger('air_quality_monitor.client').setLevel(logging.DEBUG)
    #logging.getLogger('air_quality_monitor.storage').setLevel(logging.WARNING)

