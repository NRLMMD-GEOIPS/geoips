# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""
import pytest
import copy
from pydantic import ValidationError


from geoips.pydantic import products

