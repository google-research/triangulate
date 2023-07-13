# Copyright 2023 The triangulate Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sampling utilities."""

from typing import List
import numpy as np

rng = np.random.default_rng(seed=654)


def sample_zipfian(
    num_samples: int, zipf_param: float = 1.5, support_size: int = 10
) -> np.ndarray:
  """Generate a sample set from a Zipfian distribution over an integer interval.

  Args:

  Args:

  Args:
      num_samples: The number of samples to return
      zipf_param: The powerlaw exponent
      support_size:  The size of the support, i.e. the width of the interval

  Returns:
      A sample set from a Zipfian
  """

  weights = 1.0 / np.power(np.arange(1, support_size + 1), zipf_param)
  weights /= np.sum(weights)

  return rng.choice(np.arange(1, support_size + 1), size=num_samples, p=weights)


def sample_wo_replacement_uniform(
    num_samples: int, support: List[int]
) -> np.ndarray:
  """Uniformly sample num_samples from [1, suppport].

  Args:
      num_samples: The number of samples to return
      support:  The upper bound of the sampled interval

  Returns:
      A sample set from the uniform over the support
  """
  if num_samples > len(support):
    raise ValueError(
        "When sampling without replacement, the number of samples"
        " cannot exceed the cardinality of the set."
    )
  return rng.choice(support, size=num_samples, replace=False)
