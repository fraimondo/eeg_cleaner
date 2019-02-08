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
from cleaner.report import create_ica_report
from cleaner.utils import configure_logging, remove_file_logging

# Read an epochs file, and ica file, apply and plot.
# Option A: Create report for ICA cleaning
# Option B: Interactive (slow)

default_scaling = 75e-6
default_nepochs = 10

parser = ArgumentParser(description='Clean a RAW (continous) file.')
parser.add_argument('--path', metavar='path', nargs=1, type=str,
                    help='Path with the Epochs file or the subjects folder '
                         '(if using NICE Extensions package).',
                    required=True)

parser.add_argument('--icaname', metavar='icaname', nargs=1, type=str,
                    help='Name of the ICA file '
                    '(if not using NICE Extensions package).',
                    default=None)
    
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
                    help=('NICE Extensions config to use for reading Epochs. '
                          'Defaults to None (do not use NICE Extensions)'))


parser.add_argument('--icaconfig', metavar='icaconfig', type=str, nargs='?',
                    default=None,
                    help=('NICE Extensions config to use for reading ICA. '
                          'Defaults to None (do not use NICE Extensions)'))

parser.add_argument('--interactive', dest='interactive', default=False, 
                    action='store_true', 
                    help=('If True, plot ica sources and run in interactive '
                          'mode. Otherwise, create a report. '
                          '(Default is False)'))


parser.add_argument('--raw', dest='raw', default=False, 
                    action='store_true', 
                    help=('If True, read a raw file instead of an '
                          'epochs files (Default is False).'))

parser.add_argument('--results', metavar='results', type=str, nargs='?',
                    default=None,
                    help=('Path to the report results file to apply. '
                          'If None and --interactive is not specified, '
                          'the report will be created'))

args = parser.parse_args()
path = args.path
icaname = args.icaname
scaling = args.scaling
nepochs = args.nepochs
config = args.config
icaconfig = args.icaconfig
interactive = args.interactive
raw = args.raw
results = args.results

if isinstance(path, list):
    path = path[0]

if isinstance(icaname, list):
    icaname = icaname[0]

if isinstance(scaling, list):
    scaling = scaling[0]

if isinstance(nepochs, list):
    nepochs = nepochs[0]

if isinstance(config, list):
    config = config[0]

if isinstance(interactive, list):
    interactive = interactive[0]

if isinstance(results, list):
    results = results[0]

configure_logging(path)
logger.info('Started ICA cleaner')

if interactive is True:
    logger.info('Running in interactive mode')
elif results is None:
    logger.info('Creating ICA report')
else:
    logger.info('Applying ICA results from {}'.format(results))

if icaname is None and icaconfig is None:
    raise ValueError('Need the ICA file name or the NICE-Extensions config')

epochs = None

def _read_epochs(path, config):
    if config is None:
        epochs = mne.read_epochs(path, preload=True)
        fname = path
    else:
        import nice_ext
        epochs = nice_ext.api.read(path, config=config)
    return epochs


def _read_raw(path, config):
    if config is None:
        raw = mne.io.read_raw_fif(path, preload=True)
        fname = path
    else:
        import nice_ext
        raw = nice_ext.api.read(path, config=config)
    return raw

def _read_ica(icapath, icaconfig):
    if icaconfig is None:
        ica = mne.preprocessing.read_ica(icapath)
    else:
        import nice_ext
        ica = nice_ext.api.read(icapath, config=icaconfig)
    return ica

if raw is True:
    suffix = '-raw.fif'
    inst = _read_raw(path, config)
    fname = inst.filenames[0]
    if fname.endswith('-ica-raw.fif'):
        suffix = '-ica-raw.fif'
else:
    suffix = '-epo.fif'
    inst = _read_epochs(path, config)
    fname = inst.filename
    if fname.endswith('-ica-epo.fif'):
        suffix = '-ica-epo.fif'
reject(path, inst)
nname = icaname
if icaname == 'auto':
    if raw is True:
        nname = op.basename(fname).replace(suffix, '-raw-ica.fif')
    else:
        nname = op.basename(fname).replace(suffix, '-epo-ica.fif')
ica = _read_ica(op.join(op.dirname(path), nname), icaconfig)

inst.pick_channels(ica.ch_names)

rname = results
if results == 'auto':
    if raw is True:
        rname = fname.replace(suffix, '-raw-ica.json')
    else:
        rname = fname.replace(suffix, '-epo-ica.json')

if interactive is False and results is not None:
    with open(rname, 'r') as f:
        rejected = json.load(f)
    ica.exclude = rejected['reject']
    update_log(op.join(op.dirname(path), nname), ica)
elif interactive is True:
    # TODO: Plot ica sources
    reject(op.join(op.dirname(path), nname), ica)
    ica.plot_sources(inst, block=True)
    update_log(op.join(op.dirname(path), nname), ica)

else:
    reject(path, ica)
    report = create_ica_report(ica, inst, nname)
    report_fname = op.basename(nname).replace('-ica.fif', 'ica-report.html')
    
    report.save(op.join(op.dirname(path), report_fname), 
                overwrite=True, open_browser=False)
