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
import mne
from mne.utils import logger
import os.path as op

from argparse import ArgumentParser

from cleaner import reject, update_log
from cleaner.utils import configure_logging, remove_file_logging

# Read an epochs file, plot and select bad channels.

default_scaling = 75e-6
default_nepochs = 10

parser = ArgumentParser(description='Clean a RAW (continous) file.')
parser.add_argument('--path', metavar='path', nargs=1, type=str,
                    help='Path with the file or the subjects folder (if using '
                          'NICE Extensions package).',
                    required=True)
    
parser.add_argument('--scaling', metavar='scaling', type=float, nargs='?',
                    default=default_scaling,
                    help=('Scaling to use when plotting EEG signals '
                          '(Default {})'.format(default_scaling)))

parser.add_argument('--nepochs', metavar='nepochs', type=float, nargs='?',
                    default=default_nepochs,
                    help=('Number of epochs to plot (default {})'.format(
                        default_nepochs)))

parser.add_argument('--config', metavar='config', type=str, nargs='?',
                    default=None,
                    help=('NICE Extensions config to use for reading. '
                          'Defaults to None (do not use NICE Extensions)'))

parser.add_argument('--reset', dest='reset', default=False, action='store_true',
                    help=('Reset bad epochs'))

args = parser.parse_args()
path = args.path
scaling = args.scaling
nepochs = args.nepochs
config = args.config
reset = args.reset

if isinstance(path, list):
    path = path[0]

if isinstance(scaling, list):
    scaling = scaling[0]

if isinstance(nepochs, list):
    nepochs = nepochs[0]

if isinstance(config, list):
    config = config[0]

if isinstance(reset, list):
    reset = reset[0]


configure_logging(path)
logger.info('Started EPOCHS cleaner')

if config is None:
    epochs = mne.read_epochs(path, preload=True)
    fname = path
else:
    import nice_ext
    epochs = nice_ext.api.read(path, config=config)

if not isinstance(epochs, list):
    epochs = [epochs]

if reset is True:
    logger.info('Reseting bad epochs')

for t_epochs in epochs:
    fname = op.basename(t_epochs.filename)
    logger.info('Cleaning {}'.format(fname))

    # selection = t_epochs.selection
    # Mark previous bad epochs
    if reset is False:
        reject(path, t_epochs)

    # Plot
    picks = mne.pick_types(t_epochs.info, eeg=True, misc=True)
    t_epochs.plot(block=True, n_epochs=nepochs, picks=picks,
                  scalings={'eeg': scaling, 'misc': 1e-4})

    # Save new channels
    update_log(path, t_epochs)

logger.info('Finished EPOCHS cleaner')
remove_file_logging()