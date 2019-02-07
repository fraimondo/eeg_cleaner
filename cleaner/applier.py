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

import os.path as op
import numpy as np

import mne
from mne.utils import logger

from .io import read_log, save_log, _check_epochs_params, _check_ica_params


def reject(path, inst, required=False):
    """
    Apply the previously selected rejection (channels or epochs) to
    the instance
    """
    json_fname = op.join(op.dirname(path), 'eeg_cleaner.json') 
    if not op.exists(json_fname) and required is True:
        raise ValueError(
            'Missing eeg_cleaner.json. Did you clean this subject?')

    logs = read_log(path)
    if isinstance(inst, mne.io.BaseRaw):
        fname = op.basename(inst.filenames[0])
        t_log = logs['raws'].get(fname, {})
        old_bads = t_log.get('bads', [])
        mix_bads = list(set(old_bads + inst.info['bads']))
        inst.info['bads'] = mix_bads
        logger.info(
            'Setting previous bad channels {}'.format(inst.info['bads']))

    elif isinstance(inst, mne.BaseEpochs):
        fname = op.basename(inst.filename)
        t_log = logs['epochs'].get(fname, {})
        _check_epochs_params(inst, t_log)
        old_bads = t_log.get('bads', [])
        mix_bads = list(set(old_bads + inst.info['bads']))
        inst.info['bads'] = mix_bads
        logger.info(
            'Setting previous bad channels {}'.format(inst.info['bads']))

        prev_selection = t_log.get('selection', inst.selection)
        to_drop = [x for x in inst.selection if x not in prev_selection]
        drop_idx = []
        cur_idx = 0
        for i_epoch, dlog in enumerate(inst.drop_log):
            if len(dlog) == 0:
                if i_epoch in to_drop:
                    drop_idx.append(cur_idx)
                cur_idx += 1
        logger.info('Dropping previous bad epochs {}'.format(to_drop))
        inst.drop(drop_idx, reason='Inspection')
    elif isinstance(inst, mne.preprocessing.ICA):
        fname = op.basename(path)
        t_log = logs['icas'].get(fname, {})
        _check_ica_params(inst, t_log)
        inst.exclude = t_log.get('exclude', [])
        logger.info('Excluding components: {}'.format(inst.exclude))

    return inst

