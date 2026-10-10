"""Repeated signal reads reuse owned data without hiding file or setting changes."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import os
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from RosettaX.utils import io
from RosettaX.utils.reader import FCSFile


@pytest.fixture
def signal_file(tmp_path, monkeypatch):
    """Create a temporary signal file for cache checks."""
    io._signal_cache.clear()
    path = tmp_path / "signal.fcs"
    FCSFile.builder_from_dataframe(
        pd.DataFrame(
            {
                "SSC": [-1.0, 0.0, 2.0, np.nan, 4.0],
                "FSC": [10.0, 20.0, 30.0, 40.0, 50.0],
            }
        )
    ).write(path)
    reader = Mock(wraps=FCSFile)
    monkeypatch.setattr(io, "FCSFile", reader)
    yield path, reader
    io._signal_cache.clear()


def test_reuses_signal_without_sharing_mutable_results(signal_file):
    """Check reuses signal without sharing mutable results."""
    path, reader = signal_file
    first = io.load_signal(path, "SSC")
    first[0] = 1000
    second = io.load_signal(path, "SSC")
    assert second.tolist() == [-1.0, 0.0, 2.0, 4.0]
    assert reader.call_count == 1
    assert not np.shares_memory(first, second)


def test_settings_and_channel_have_distinct_cache_entries(signal_file):
    """Check settings and channel have distinct cache entries."""
    path, reader = signal_file
    assert io.load_signal(path, "SSC", 2).tolist() == [-1.0, 0.0]
    assert io.load_signal(path, "SSC", 2, True).tolist() == [2.0, 4.0]
    assert io.load_signal(path, "FSC", 2).tolist() == [10.0, 20.0]
    io.load_signal(path, "SSC", 2, True)
    assert reader.call_count == 3


def test_replaced_file_invalidates_even_with_same_size_and_mtime(signal_file):
    """Check replaced file invalidates even with same size and mtime."""
    path, reader = signal_file
    io.load_signal(path, "SSC")
    original_stat = path.stat()
    replacement = path.with_name("replacement.fcs")
    FCSFile.builder_from_dataframe(
        pd.DataFrame(
            {
                "SSC": [-1.0, 0.0, 8.0, np.nan, 9.0],
                "FSC": [10.0, 20.0, 30.0, 40.0, 50.0],
            }
        )
    ).write(replacement)
    os.utime(replacement, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    replacement.replace(path)
    assert path.stat().st_size == original_stat.st_size
    assert io.load_signal(path, "SSC").tolist() == [-1.0, 0.0, 8.0, 9.0]
    assert reader.call_count == 2
    path.unlink()
    with pytest.raises(FileNotFoundError):
        io.load_signal(path, "SSC")


def test_cache_evicts_by_bytes_and_skips_oversized_signals(signal_file, monkeypatch):
    """Check cache evicts by bytes and skips oversized signals."""
    path, reader = signal_file
    monkeypatch.setattr(io, "_SIGNAL_CACHE_MAX_BYTES", 40)
    io.load_signal(path, "SSC")  # 32 bytes
    io.load_signal(path, "FSC")  # 40 bytes, evicts SSC
    io.load_signal(path, "SSC")
    assert reader.call_count == 3
    assert sum(value.nbytes for value in io._signal_cache.values()) <= 40
    monkeypatch.setattr(io, "_SIGNAL_CACHE_MAX_BYTES", 16)
    io._signal_cache.clear()
    io.load_signal(path, "SSC")
    io.load_signal(path, "SSC")
    assert reader.call_count == 5
    assert not io._signal_cache
