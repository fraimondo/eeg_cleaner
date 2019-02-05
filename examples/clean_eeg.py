from copy import deepcopy
import numpy as np
import mne
from mne.utils import logger


# 1. Run 1_clean_raw.py

#  %run 1_clean_raw.py --path='/Users/fraimondo/data/birmingham/words/S03/S03_EB-raw.fif'

# 2. Filter and cut

lpass = 45.
hpass = 0.5
n_jobs = -1
tmin = -.5
tmax = 2.

picks = mne.pick_types(raw.info, eeg=True, meg=True, ecg=True, exclude=[])
_filter_params = dict(method='iir',
                        l_trans_bandwidth=0.1,
                        iir_params=dict(ftype='butter', order=4))
filter_params = [
    dict(l_freq=hpass, h_freq=None,
            iir_params=dict(ftype='butter', order=4)),
    dict(l_freq=None, h_freq=lpass,
            iir_params=dict(ftype='butter', order=8))
]

for fp in filter_params:
    _filter_params2 = deepcopy(_filter_params)
    if fp.get('method') == 'fft':
        _filter_params2.pop('iir_params')
    if isinstance(fp, dict):
        _filter_params2.update(fp)
    raw.filter(picks=picks, n_jobs=n_jobs, **_filter_params2)

notches = [50, 100, 200]
logger.info('Notch filters at {}'.format(notches))
raw.notch_filter(notches, method='fft', n_jobs=n_jobs)

# This is for this specific files
evt_samples = (raw.annotations.onset + 117) * raw.info['sfreq']
evt_samples = evt_samples.astype(np.int)

evt_descriptions = [x.split('/')[-1] for x in raw.annotations.description]

evt_types = {'s1': 1, 's2': 2, 's4': 4, 's16': 16, 's32': 32}

events = [[x, 0, evt_types[y]] for (x, y) in 
            zip(evt_samples, evt_descriptions) if y in evt_types]

events = np.array(events)

baseline = (None, 0)
epochs = mne.Epochs(raw, events, evt_types, tmin=tmin, tmax=tmax,
                    preload=True, reject=None, picks=None,
                    baseline=baseline, verbose=False)