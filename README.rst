.. -*- mode: rst -*-

`NICE-EEG Cleaner`
=======================================================

Get the latest code
^^^^^^^^^^^^^^^^^^^

To get the latest code using git, simply type::

    git clone git://github.com/fraimondo/eeg-cleaner.git

Install cleaner
^^^^^^^^^^^^^^^^^^

NICE-EEG cleaner must be installed in development mode, go in the source
code directory and do::

    python setup.py develop


Dependencies
^^^^^^^^^^^^

The required dependencies to build the software are:
* python >= 3.4
* mne-python >= 0.13: http://mne-tools.github.io/stable/index.html


Using NICE-EEG Cleaner
^^^^^^^^^^^^^^^^^^^^^^

NICE-EEG Cleaner is a collection of scripts that allows to tag and clean EEG 
recordings, both continous and epoched data.

In the ``scripts`` folder you can find 3 scripts:

* 1_clean_raw.py
   The intention of this script is to mark bad EEG channels on continous recordings.
* 2_clean_epochs.py
* 3_clean_ica.py

The inteded way of use is to:

1. Run the script ``1_clean_raw.py`` to annotate the bad channels.

2. Preprocess the continous data and create an epochs file. Recommended steps:

   - Filter
   - Cut data into epochs

3. Run the script ``2_clean_epochs.py`` to annotate the bad epochs.

4. Run ICA on the preprocessed epochs. Once this step is done, the parameters in step 2 can't be changed.

5. Run the script ``3_clean_ica.py`` to annotate the bad components.

6. Finish the preprocessing:

   - Apply ICA
   - Interpolate bad channels
   - Re-Reference


Steps 1, 3 and 5 updates a file named `eeg_cleaner.json` with 
all the information needed to preprocess the raw files and recreate the clean
data. Some parameters can be changed at different steps. For example, changing
the filters in step 2 mean that step 4 needs to be re-run, but not step 2, as
the way that epochs were cut did not change. Nevertheless, the scripts will
tell you when an inconsistency is found.

The EEG cleaner relies on file names, so if any file is renamed, the 
``eeg_cleaner.json`` file should be updated.


Licensing
^^^^^^^^^

NICE-EEG Cleaner is licensed under the GNU Affero General Public License version 3:

    This software is OSI Certified Open Source Software.
    OSI Certified is a certification mark of the Open Source Initiative.

    Copyright (c) 2019, authors of NICE-EEG Cleaner - All rights reserved.

    * This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

    * You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.

    * You can be released from the requirements of the license by purchasing a commercial license. Buying such a license is mandatory as soon as you develop commercial activities as mentioned in the GNU Affero General Public License version 3 without disclosing the source code of your own applications.
