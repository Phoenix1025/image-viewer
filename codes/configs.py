import logging
from pathlib import Path

data_folder = Path(__file__).parents[1] / 'data'
data_folder.mkdir(exist_ok=True)

logs_folder = Path(__file__).parents[1] / 'logs'
logs_folder.mkdir(exist_ok=True)


def configure_logging(*, log_level=logging.ERROR, log_file=None):
    log_handlers = [logging.StreamHandler()]
    if log_file is not None:
        log_handlers = [logging.FileHandler(log_file, mode='w')]

    logging.basicConfig(
        level=log_level,
        handlers=log_handlers,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
