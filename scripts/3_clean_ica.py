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

import json
from argparse import ArgumentParser
from pathlib import Path

import mne
from mne.utils import logger

from cleaner import reject, update_log, is_cleaned
from cleaner.report import create_ica_report
from cleaner.utils import configure_logging, remove_file_logging

# Read an epochs file, and ica file, apply and plot.
# Option A: Create report for ICA cleaning
# Option B: Interactive (slow)

default_scaling = 75e-6
default_ncomps = 10

parser = ArgumentParser(description="Apply ICA and clean.")
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
        f"Scaling to use when plotting EEG signals (Default {default_scaling})"
    ),
)


parser.add_argument(
    "--ncomps",
    metavar="ncomps",
    type=int,
    nargs="?",
    default=default_ncomps,
    help=f"Number of components to plot (default {default_ncomps})",
)

parser.add_argument(
    "--pattern",
    metavar="pattern",
    type=str,
    nargs="?",
    default=None,
    help=(
        "Pattern to use to select the files. "
        "If None, a default fif pattern will be used depending on the "
        "data type (epochs or raw). "
    ),
)

parser.add_argument(
    "--interactive",
    dest="interactive",
    default=False,
    action="store_true",
    help=(
        "If True, plot ica sources and run in interactive "
        "mode. Otherwise, create a report. "
        "(Default is False)"
    ),
)


parser.add_argument(
    "--raw",
    dest="raw",
    default=False,
    action="store_true",
    help=(
        "If True, read a raw file instead of an epochs files (Default is False)."
    ),
)

parser.add_argument(
    "--apply",
    dest="apply",
    default=False,
    action="store_true",
    help=("If True, apply ICA and store a cleaned file."),
)

parser.add_argument(
    "--redo",
    action="store_true",
    help=(
        "If set, the script will redo the cleaning even if it has been done before."
    ),
)


args = parser.parse_args()
path = args.path
scaling = args.scaling
pattern = args.pattern
ncomps = args.ncomps
interactive = args.interactive
raw = args.raw
apply = args.apply
redo = args.redo

if isinstance(path, list):
    path = path[0]

if not isinstance(path, Path):
    path = Path(path)

if isinstance(scaling, list):
    scaling = scaling[0]

if isinstance(ncomps, list):
    ncomps = ncomps[0]

if isinstance(interactive, list):
    interactive = interactive[0]

if isinstance(pattern, list):
    pattern = pattern[0]

configure_logging(path)
logger.info("Started ICA cleaner")

if interactive is True:
    logger.info("Running in interactive mode")
elif apply is False:
    logger.info("Creating ICA report")
else:
    logger.info("Applying ICA results")


if path.is_file():
    # If the path is a file, use it
    fnames = [path]
else:
    if pattern is None:
        if raw is True:
            pattern = "**/raw/**/*_eeg.fif"
        else:
            pattern = "**/eeg/**/*eeg_epo.fif"
        logger.info(f"No pattern provided. Using default pattern {pattern}.")
    fnames = path.glob(pattern)

reject_type = "raws" if raw is True else "epochs"

for t_fname in fnames:
    ica_fname = t_fname.parent / t_fname.name.replace(".fif", "-ica.fif")
    # We need an ICA decomposition
    if not ica_fname.exists():
        logger.info(f"ICA file {ica_fname} does not exist. Skipping.")
        continue

    is_ica_cleaned = is_cleaned(ica_fname, "icas")

    # In order to apply, we need the file to be cleaned
    if apply and not is_ica_cleaned:
        logger.info(f"Cannot apply ICA to {t_fname}. Not cleaned. Skipping.")

    # Skip if we don't need to redo
    if not apply and is_ica_cleaned and not redo:
        logger.info(f"File {t_fname} already cleaned. Skipping.")
        continue


    # Check if it was previously cleaned
    if not is_cleaned(t_fname, reject_type):
        logger.info(
            f"File {t_fname} not cleaned. Please do the raw/epoch cleaning "
            "first. Skipping."
        )
        continue

    if raw is True:
        logger.info("Loading raw file")
        inst = mne.io.read_raw_fif(t_fname, preload=True)
    else:
        logger.info("Loading epochs file")
        inst = mne.read_epochs(t_fname, preload=True)

    reject(path, inst)

    ica = mne.preprocessing.read_ica(ica_fname, verbose=True)

    inst.pick(ica.ch_names)

    results_fname = ica_fname.with_suffix(".json")

    if interactive is False and results_fname.exists():
        with open(results_fname, "r") as f:
            rejected = json.load(f)
        ica.exclude = rejected["reject"]
        update_log(t_fname, ica)
    elif interactive is True:
        # TODO: Plot ica sources
        reject(t_fname, ica)
        ica.plot_sources(inst, block=True)
        update_log(t_fname, ica)

    else:
        reject(t_fname, ica)
        report = create_ica_report(ica, inst, ica_fname, ncomponents=ncomps)
        report_fname = ica_fname.parent / ica_fname.name.replace(
            "-ica.fif", "-ica-report.html"
        )

        report.save(report_fname, overwrite=True, open_browser=False)
