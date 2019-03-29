import os.path as op
import logging

from mne.utils import logger, set_log_file
from mne.utils._logging import WrapStdOut

def configure_logging(path):
    """Set format to file logging and add stdout logging
       Log file messages will be: DATE - LEVEL - MESSAGE
    """
    fname = op.join(op.dirname(path), 'eeg_cleaner.log')
    set_log_file(fname, overwrite=False)
    handlers = logger.handlers
    file_output_format = '%(asctime)s %(levelname)s %(message)s'
    date_format = '%d/%m/%Y %H:%M:%S'
    output_format = '%(message)s'
    for h in handlers:
        if not isinstance(h, logging.FileHandler):
            logger.removeHandler(h)
            print('Removing handler {}'.format(h))
        else:
            h.setFormatter(logging.Formatter(file_output_format,
                                             datefmt=date_format))
    lh = logging.StreamHandler(WrapStdOut())
    lh.setFormatter(logging.Formatter(output_format))
    logger.addHandler(lh)


def remove_file_logging():
    """Close and remove logging to file"""
    handlers = logger.handlers
    for h in handlers:
        if isinstance(h, logging.FileHandler):
            h.close()
            logger.removeHandler(h)
