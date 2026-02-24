import gc
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from RosettaX.directories import fcs_data
from RosettaX.reader import FCSDataFrameFile


file_test = fcs_data / "sample_0.fcs"


def test_sample_0_can_be_parsed() -> None:
    with FCSDataFrameFile(file_test, writable=False) as fcs_file:
        df_view = fcs_file.dataframe_view

        assert isinstance(df_view, pd.DataFrame)
        assert df_view.shape[0] > 0
        assert df_view.shape[1] > 0

        keywords = fcs_file.text["Keywords"]
        assert int(keywords["$TOT"]) == df_view.shape[0]
        assert int(keywords["$PAR"]) == df_view.shape[1]

        del df_view
        gc.collect()


def test_sample_0_zero_copy_dataframe_view_shares_memory() -> None:
    with FCSDataFrameFile(file_test, writable=False) as fcs_file:
        df_view = fcs_file.dataframe_view

        fcs_file._ensure_records_loaded()
        assert fcs_file._records is not None

        first_column = df_view.columns[0]
        arr = df_view[first_column].to_numpy(copy=False)

        assert np.shares_memory(arr, fcs_file._records)

        del arr
        del df_view
        gc.collect()


def test_sample_0_roundtrip_via_template(tmp_path: Path) -> None:
    # Use dataframe_copy so the template file can close cleanly.
    with FCSDataFrameFile(file_test, writable=False) as template_file:
        df_copy = template_file.dataframe_copy(deep=True)

        builder = FCSDataFrameFile.builder_from_dataframe(
            df_copy,
            template=template_file,
            force_float32=True,
        )

        out_path = tmp_path / "sample_0_roundtrip.fcs"
        builder.write(str(out_path))

        del df_copy
        gc.collect()

    with FCSDataFrameFile(str(out_path), writable=False) as reread_file:
        reread_view = reread_file.dataframe_view
        reread_copy = reread_file.dataframe_copy(deep=True)

        assert reread_view.shape == reread_copy.shape
        assert reread_copy.shape[0] > 0
        assert reread_copy.shape[1] > 0

        del reread_view
        del reread_copy
        gc.collect()


def test_sample_0_roundtrip_with_added_column(tmp_path: Path) -> None:
    with FCSDataFrameFile(file_test, writable=False) as template_file:
        df_copy = template_file.dataframe_copy(deep=True)

        added = np.zeros(df_copy.shape[0], dtype=np.float32)
        df_copy["calibrated_signal"] = added

        builder = FCSDataFrameFile.builder_from_dataframe(
            df_copy,
            template=template_file,
            force_float32=True,
        )

        out_path = tmp_path / "sample_0_with_added_column.fcs"
        builder.write(str(out_path))

        del df_copy
        gc.collect()

    with FCSDataFrameFile(str(out_path), writable=False) as reread_file:
        reread_copy = reread_file.dataframe_copy(deep=True)

        assert "calibrated_signal" in reread_copy.columns
        np.testing.assert_allclose(reread_copy["calibrated_signal"].to_numpy(), added)

        del reread_copy
        gc.collect()


def test_text_delimiter_escaping_roundtrip(tmp_path: Path) -> None:
    with FCSDataFrameFile(file_test, writable=False) as template_file:
        df_copy = template_file.dataframe_copy(deep=True)

        builder = FCSDataFrameFile.builder_from_dataframe(
            df_copy,
            template=template_file,
            force_float32=True,
        )

        # Include the delimiter in the value. The file's delimiter can be '/' in your sample.
        # Writer escapes delimiter by doubling it; parser unescapes it.
        delimiter = template_file.delimiter
        builder.keywords["$TEST"] = f"A{delimiter}B"

        out_path = tmp_path / "escaped_keyword.fcs"
        builder.write(str(out_path))

        del df_copy
        gc.collect()

    with FCSDataFrameFile(str(out_path), writable=False) as reread_file:
        delimiter = reread_file.delimiter
        assert reread_file.text["Keywords"].get("$TEST") == f"A{delimiter}B"

        gc.collect()


def test_reject_non_list_mode(tmp_path: Path) -> None:
    with FCSDataFrameFile(file_test, writable=False) as template_file:
        df_copy = template_file.dataframe_copy(deep=True)

        builder = FCSDataFrameFile.builder_from_dataframe(
            df_copy,
            template=template_file,
            force_float32=True,
        )
        builder.keywords["$MODE"] = "C"

        out_path = tmp_path / "non_list_mode.fcs"
        builder.write(str(out_path))

        del df_copy
        gc.collect()

    with FCSDataFrameFile(str(out_path), writable=False) as fcs_file:
        with pytest.raises(ValueError, match=r'Only \$MODE="L" is supported'):
            _ = fcs_file.dataframe_view

        gc.collect()

if __name__ == "__main__":
    pytest.main(["-W", "error", __file__])