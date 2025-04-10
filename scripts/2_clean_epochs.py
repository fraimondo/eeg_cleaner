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
import numpy as np
from mne.utils import logger
from sklearn.decomposition import PCA

from cleaner import is_cleaned, reject, update_log
from cleaner.utils import configure_logging, remove_file_logging

# Read an epochs file, plot and select bad channels.

default_scaling = 75e-6
default_nepochs = 10

parser = ArgumentParser(description="Clean an Epochs file.")
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
    help=(f"Scaling to use when plotting EEG signals (Default {default_scaling})"),
)

parser.add_argument(
    "--nepochs",
    metavar="nepochs",
    type=float,
    nargs="?",
    default=default_nepochs,
    help=f"Number of epochs to plot (default {default_nepochs})",
)


parser.add_argument(
    "--reset",
    dest="reset",
    default=False,
    action="store_true",
    help=("Reset bad epochs"),
)

parser.add_argument(
    "--pattern",
    metavar="pattern",
    type=str,
    nargs="?",
    default=None,
    help=(
        "Pattern to use to select the files. "
        "If None, a default EPOCHS fif pattern will be used. "
    ),
)

parser.add_argument(
    "--redo",
    action="store_true",
    help=("If set, the script will redo the cleaning even if it has been done before."),
)

parser.add_argument(
    "--pca",
    type=int,
    default=0,
    help=(
        "Number of PCA components to append to the data for visualization purposes. "
        "If 0, no PCA is used. (default 0)"
    ),
)

args = parser.parse_args()
path = args.path
scaling = args.scaling
nepochs = args.nepochs
pattern = args.pattern
redo = args.redo
reset = args.reset
n_pca = args.pca

if isinstance(path, list):
    path = path[0]

if not isinstance(path, Path):
    path = Path(path)

if isinstance(scaling, list):
    scaling = scaling[0]

if isinstance(nepochs, list):
    nepochs = nepochs[0]

if isinstance(pattern, list):
    pattern = pattern[0]

if isinstance(reset, list):
    reset = reset[0]


configure_logging(path)
logger.info("Started EPOCHS cleaner")
if path.is_file():
    # If the path is a file, use it
    epochs = [path]
else:
    if pattern is None:
        pattern = "**/eeg/**/*eeg_epo.fif"
        logger.info(f"No pattern provided. Using default pattern {pattern}.")
    epochs = path.glob(pattern)


for t_fname in epochs:
    if not redo and is_cleaned(t_fname, "epochs"):
        logger.info(f"File {t_fname} already cleaned. Skipping.")
        continue

    logger.info(f"Loading file {t_fname}")
    t_epochs = mne.read_epochs(
        t_fname,
        preload=True,
    )
    logger.info(f"Cleaning {t_fname}")

    # selection = t_epochs.selection
    # Mark previous bad epochs
    if reset is False:
        logger.info("Setting previous bad epochs")
        reject(path, t_epochs)

    if n_pca > 0:
        pca = mne.decoding.UnsupervisedSpatialFilter(PCA(n_pca), average=False)
        logger.info("Fitting PCA (n_pca = {})".format(n_pca))
        picks = mne.pick_types(
            t_epochs.info, meg=False, eeg=True, eog=False, stim=False, exclude="bads"
        )
        pca_data = pca.fit_transform(t_epochs.get_data()[:, picks, :])
        blank = np.zeros((pca_data.shape[0], 2, pca_data.shape[2]))
        pca_data = np.concatenate([blank, pca_data], axis=1)
        ch_names = ["Blank1", "Blank2"]
        ch_names += ["PCA{}".format(x) for x in range(n_pca)]
        ch_types = ["misc"] * len(ch_names)

        pca_info = t_epochs.info.copy()
        mapping = {k: "misc" for k in pca_info["ch_names"][: n_pca + 2]}
        pca_info.set_channel_types(mapping)
        pca_info = mne.pick_info(pca_info, list(range(n_pca + 2)))
        rename = dict(
            zip(
                pca_info["ch_names"],
                ["Blank1", "Blank2"] + [f"PCA{x}" for x in range(n_pca)],
            )
        )
        pca_info.rename_channels(rename)
        pca_epochs = mne.EpochsArray(pca_data, pca_info)
        t_epochs.add_channels([pca_epochs])
    # Plot
    picks = mne.pick_types(t_epochs.info, eeg=True, misc=True)
    t_epochs.plot(
        block=True,
        n_epochs=nepochs,
        picks=picks,
        scalings={"eeg": scaling, "misc": 1e-4},
    )

    # Save new channels
    update_log(t_fname, t_epochs)

logger.info("Finished EPOCHS cleaner")
remove_file_logging()
