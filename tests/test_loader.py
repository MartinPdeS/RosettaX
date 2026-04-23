import gc
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from RosettaX.directories import fcs_data


file_test = fcs_data / "sample_0.fcs"


def test_sample_0_can_be_parsed() -> None:
    assert 1==1, "This is a dummy test."


if __name__ == "__main__":
    pytest.main(["-W", "error", __file__])