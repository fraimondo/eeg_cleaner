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

from argparse import ArgumentParser
from pathlib import Path

import mne
from mne.utils import logger

from cleaner import reject, update_log, is_cleaned
from cleaner.utils import configure_logging, remove_file_logging

# Read a raw file, plot and select bad channels.

default_scaling = 30e-6
default_lpass = 40
default_hpass = 1


parser = ArgumentParser(description="Clean a RAW (continous) file.")
parser.add_argument(
    "--path",
    metavar="path",
    nargs=1,
    type=str,
    help="Path with the file or the BIDS directory.",
    required=True,
)

parser.add_argument(
    "--scaling",
    metavar="scaling",
    type=float,
    nargs="?",
    default=default_scaling,
    help=(
        f"Scaling to use when plotting EEG signals (Default {default_scaling}"
    ),
)

parser.add_argument(
    "--hpass",
    metavar="hpass",
    type=float,
    nargs="?",
    default=default_hpass,
    help=(
        "Frequency of the High Pass filter. Used only for"
        f"plotting. (Default {default_hpass})"
    ),
)

parser.add_argument(
    "--lpass",
    metavar="lpass",
    type=float,
    nargs="?",
    default=default_lpass,
    help=(
        "Frequency of the Low Pass filter. Used only for"
        f"plotting. (Default {default_lpass})"
    ),
)

parser.add_argument(
    "--pattern",
    metavar="pattern",
    type=str,
    nargs="?",
    default=None,
    help=(
        "Pattern to use to select the files. "
        "If None, a default RAW fif pattern will be used. "
    ),
)

parser.add_argument(
    "--nchans",
    metavar="nchans",
    default=20,
    type=int,
    help="Number of channels to plot. Default 20.",
)

parser.add_argument(
    "--redo",
    action="store_true",
    help=(
        "If set, the script will redo the cleaning even if it "
        "has been done before."
    ),
)
args = parser.parse_args()
path = args.path
scaling = args.scaling
hpass = args.hpass
lpass = args.lpass
pattern = args.pattern
redo = args.redo

if isinstance(path, list):
    path = path[0]

path = Path(path)

if not path.exists():
    raise FileNotFoundError(f"Path {path} does not exist.")

if isinstance(scaling, list):
    scaling = scaling[0]

if isinstance(hpass, list):
    hpass = hpass[0]

if isinstance(lpass, list):
    lpass = lpass[0]

if isinstance(pattern, list):
    pattern = pattern[0]

configure_logging(path)
logger.info("Started RAW cleaner")

if path.is_file():
    # If the path is a file, use it
    raws = [path]
else:
    if pattern is None:
        pattern = "**/eeg/**/*eeg.fif"
        logger.info(f"No pattern provided. Using default pattern {pattern}.")
    raws = path.glob(pattern)

for t_fname in raws:
    if not redo and is_cleaned(t_fname, "raws"):
        logger.info(f"File {t_fname} already cleaned. Skipping.")
        continue
    logger.info(f"Loading file {t_fname}")
    t_raw = mne.io.read_raw_fif(t_fname, preload=True)

    logger.info(f"Cleaning {t_fname}")
    # Mark previous bad channels
    reject(t_fname, t_raw)

    logger.info(f"Filtering {hpass} - {lpass}")
    t_raw.filter(hpass, lpass)

    # Plot
    t_raw.plot(block=True, scalings={"eeg": scaling}, n_channels=args.nchans)

    # Save new channels
    update_log(t_fname, t_raw)

logger.info("Finished RAW cleaner")
remove_file_logging()
