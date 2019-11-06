from copy import deepcopy
import numpy as np
import mne
from mne.utils import logger


# 1. Run 1_clean_raw.py

#  %run 1_clean_raw.py --path='/Users/fraimondo/data/lg_controls/subjects/jaco/test-raw.fif'

# 2. Filter and cut

import cleaner
raw_fname = '/Users/fraimondo/data/lg_controls/subjects/jaco/test-raw.fif'
raw = mne.io.read_raw_fif(raw_fname, preload=True)
cleaner.reject(raw_fname, raw, required=True)

epochs = nice_ext.api.preprocess(raw, 'icm/lg/raw/egi')

from sklearn.decomposition import PCA
n_pca = 20


picks = mne.pick_types(epochs.info, meg=False, eeg=True, eog=False,
                        stim=False, exclude='bads')

pca = mne.decoding.UnsupervisedSpatialFilter(PCA(n_pca), average=False)
logger.info('Fitting PCA (n_pca = {})'.format(n_pca))
pca_data = pca.fit_transform(epochs.get_data()[:, picks, :])
blank = np.zeros((pca_data.shape[0], 2, pca_data.shape[2]))
pca_data = np.concatenate([blank, pca_data], axis=1)
ch_names = ['Blank1', 'Blank2']
ch_names += ['PCA{}'.format(x) for x in range(n_pca)]
ch_types = ['misc'] * len(ch_names)
info = mne.create_info(ch_names, epochs.info['sfreq'], ch_types)
for field in ['description', 'highpass', 'lowpass', 'meas_date',
              'custom_ref_applied']:
    info[field] = epochs.info[field]
pca_epochs = mne.EpochsArray(pca_data, info)
epochs.add_channels([pca_epochs])

epochs_fname = op.join(op.dirname(path), 'test-pca-epo.fif')
epochs.save(epochs_fname)

# %run 2_clean_epochs.py --path='/Users/fraimondo/data/lg_controls/subjects/jaco/test-pca-epo.fif'


epochs = mne.read_epochs(epochs_fname)
cleaner.reject(epochs_fname, epochs, required=True)
epochs.pick_types(eeg=True, exclude=[])
epochs_fname = epochs_fname.replace('-pca-epo.fif', '-ica-epo.fif')
epochs.save(epochs_fname)

picks = mne.pick_types(epochs.info, meg=False, eeg=True, eog=False,
                        stim=False, exclude='bads')
ica = mne.preprocessing.ICA(
    n_components=0.99, max_pca_components=None, max_iter=512,
    method='extended-infomax', verbose=True)
ica.fit(epochs, picks=picks, verbose=True)
ica_fname = epochs_fname.replace('-ica-epo.fif', '-epo-ica.fif')
ica.save(ica_fname)


# %run 3_clean_ica.py --path='/Users/fraimondo/data/lg_controls/subjects/jaco/test-ica-epo.fif' --icaname='auto'