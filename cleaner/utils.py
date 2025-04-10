# NICE-EEG Cleaner
# Copyright (C) 2019 - Authors of NICE-EEG-Cleaner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# You can be released from the requirements of the license by purchasing a
# commercial license. Buying such a license is mandatory as soon as you
# develop commercial activities as mentioned in the GNU Affero General Public
# License version 3 without disclosing the source code of your own
# applications.
#
import logging
from pathlib import Path

from mne.utils import logger, set_log_file
from mne.utils._logging import WrapStdOut


def configure_logging(path):
    """Set format to file logging and add stdout logging
    Log file messages will be: DATE - LEVEL - MESSAGE
    """
    if not isinstance(path, Path):
        path = Path(path)
    if path.is_file():
        path = path.parent
    fname = path / "eeg_cleaner.log"
    set_log_file(fname, overwrite=False)
    handlers = logger.handlers
    file_output_format = "%(asctime)s %(levelname)s %(message)s"
    date_format = "%d/%m/%Y %H:%M:%S"
    output_format = "%(message)s"
    for h in handlers:
        if not isinstance(h, logging.FileHandler):
            logger.removeHandler(h)
            print("Removing handler {}".format(h))
        else:
            h.setFormatter(
                logging.Formatter(file_output_format, datefmt=date_format)
            )
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
