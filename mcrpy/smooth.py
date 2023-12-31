"""
   Copyright 10/2020 - 04/2021 Paul Seibert for Diploma Thesis at TU Dresden
   Copyright 05/2021 - 12/2021 TU Dresden (Paul Seibert as Scientific Assistant)
   Copyright 2022 TU Dresden (Paul Seibert as Scientific Employee)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import argparse
import logging
import os

import numpy as np
from scipy.ndimage import gaussian_filter

from mcrpy.src import fileutils
from mcrpy.src.Microstructure import Microstructure

def gaussian_smoothing(microstructure: np.ndarray, strength: float = 1.0):
    microstructure = gaussian_filter(microstructure, strength, mode='wrap')
    return np.round(microstructure)

def smooth(microstructure: Microstructure, method: str = 'gaussian', strength: float = 1.0):
    assert microstructure.has_phases
    if method == 'gaussian':
        f = gaussian_smoothing
    else:
        raise NotImplementedError(f'Smoothing method {method} was chosen, but is not implemented.')
    with microstructure.use_multiphase_encoding() as x:
        _smooth_multiphase(x, microstructure, f, strength)
    return microstructure

def _smooth_multiphase(x, microstructure, f, strength):
    ms_encoded = x.numpy()[0]
    phases = list(range(ms_encoded.shape[-1]))
    vfs = np.array([np.average(ms_encoded[..., phase]) for phase in phases])
    largest_phase = np.argmax(vfs)

    ms_smoothed = np.zeros(ms_encoded.shape)
    largest_indicator_function = np.ones(microstructure.spatial_shape)
    for phase in phases:
        if phase == largest_phase:
            continue
        ms_smoothed[..., phase] = f(ms_encoded[..., phase].astype(np.float64), strength)
        largest_indicator_function -= ms_smoothed[..., phase]
    ms_smoothed[..., largest_phase] = largest_indicator_function
    x.assign(ms_smoothed.reshape(x.numpy().shape))

def main(args):
    """Main function for smooting script. This wraps some i/o around the smooth() function in order to make it usable
    via a command line interface and via a GUI. When mcrpy is used as a Python module directly, this main function is not called."""
    if not os.path.isfile(args.microstructure_filename):
        raise ValueError(f'Given file {args.microstructure_filename} does not exist!')
    if not args.microstructure_filename.endswith('.npy'):
        raise ValueError(f'Given file {args.microstructure_filename} should be a .npy-file!')

    ms = Microstructure.from_npy(args.microstructure_filename, use_multiphase=True)

    ms_smoothed = smooth(ms)

    filename_additive = '' if args.info is None else f'_{args.info}'
    filename = f'{args.microstructure_filename[:-4]}{filename_additive}_smoothed.npy'
    ms_smoothed.to_npy(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('microstructure_filename', type=str)
    parser.add_argument('--method', type=str, default='gaussian')
    parser.add_argument('--strength', type=str, default=1.0)
    parser.add_argument('--info', type=str, default=None)
    args = parser.parse_args()
    main(args)
