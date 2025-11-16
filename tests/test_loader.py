import pytest
from RosettaX.reader import read_fcs_file

def test_dummy():
    data = read_fcs_file("tests/data/sample.fcs")
    print(data)
    assert True



if __name__ == "__main__":
    pytest.main(["-W error", __file__])