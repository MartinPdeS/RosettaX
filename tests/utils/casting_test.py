# -*- coding: utf-8 -*-

import math

import numpy as np
import pytest

from RosettaX.utils.casting import as_float
from RosettaX.utils.casting import as_float_list
from RosettaX.utils.casting import as_int
from RosettaX.utils.casting import as_optional_float
from RosettaX.utils.casting import as_optional_int
from RosettaX.utils.casting import as_required_float
from RosettaX.utils.casting import as_required_int
from RosettaX.utils.casting import coerce_optional_integer
from RosettaX.utils.casting import coerce_optional_number
from RosettaX.utils.casting import coerce_optional_string
from RosettaX.utils.casting import format_float_list_for_input
from RosettaX.utils.casting import parse_float_list


class Test_Casting:
    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            (None, None),
            ("", None),
            ("   ", None),
            ("1.25", 1.25),
            ("1,25", 1.25),
            (1, 1.0),
            (1.5, 1.5),
            ("not a number", None),
            (object(), None),
        ],
    )
    def test_as_float_parses_supported_values(
        self,
        raw_value: object,
        expected_value: float | None,
    ) -> None:
        assert as_float(raw_value) == expected_value

    @pytest.mark.parametrize(
        "raw_value",
        [
            math.nan,
            math.inf,
            -math.inf,
            "nan",
            "inf",
            "-inf",
        ],
    )
    def test_as_float_rejects_non_finite_values(self, raw_value: object) -> None:
        assert as_float(raw_value) is None

    @pytest.mark.parametrize(
        ("raw_value", "default_value", "minimum_value", "maximum_value", "expected_value"),
        [
            ("5", 0, 1, 10, 5),
            ("0", 5, 1, 10, 1),
            ("11", 5, 1, 10, 10),
            ("invalid", 5, 1, 10, 5),
            (None, 5, 1, 10, 5),
        ],
    )
    def test_as_int_parses_defaults_and_clamps(
        self,
        raw_value: object,
        default_value: int,
        minimum_value: int,
        maximum_value: int,
        expected_value: int,
    ) -> None:
        assert as_int(raw_value, default_value, minimum_value, maximum_value) == expected_value

    @pytest.mark.parametrize(
        ("raw_value", "expected_values"),
        [
            (None, []),
            ("", []),
            ("   ", []),
            ("1, 2, 3", [1.0, 2.0, 3.0]),
            ("1; 2; 3", [1.0, 2.0, 3.0]),
            ("1 2 3", [1.0, 2.0, 3.0]),
            ("1, invalid, 3", [1.0, 3.0]),
            ([1, "2", "invalid", 3.5], [1.0, 2.0, 3.5]),
            ((1, 2, 3), [1.0, 2.0, 3.0]),
            (np.asarray([[1, 2], [3, 4]]), [1.0, 2.0, 3.0, 4.0]),
            (5, [5.0]),
        ],
    )
    def test_as_float_list_parses_supported_values(
        self,
        raw_value: object,
        expected_values: list[float],
    ) -> None:
        parsed_values = as_float_list(raw_value)

        assert isinstance(parsed_values, np.ndarray)
        assert parsed_values.dtype == float
        assert parsed_values.tolist() == expected_values

    def test_parse_float_list_returns_python_list(self) -> None:
        parsed_values = parse_float_list("1, 2, 3")

        assert parsed_values == [1.0, 2.0, 3.0]
        assert isinstance(parsed_values, list)

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            ("1.25", 1.25),
            (1.25, 1.25),
            ("", None),
            (None, None),
            ("invalid", None),
        ],
    )
    def test_as_optional_float(
        self,
        raw_value: object,
        expected_value: float | None,
    ) -> None:
        assert as_optional_float(raw_value) == expected_value

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            ("5", 5),
            (5, 5),
            ("", None),
            (None, None),
            ("invalid", None),
        ],
    )
    def test_as_optional_int(
        self,
        raw_value: object,
        expected_value: int | None,
    ) -> None:
        assert as_optional_int(raw_value) == expected_value

    def test_as_required_float_returns_float_for_valid_value(self) -> None:
        assert as_required_float("1.25", "wavelength") == 1.25

    @pytest.mark.parametrize(
        "raw_value",
        [
            None,
            "",
            "invalid",
        ],
    )
    def test_as_required_float_raises_for_invalid_value(self, raw_value: object) -> None:
        with pytest.raises(ValueError, match="Invalid value for wavelength"):
            as_required_float(raw_value, "wavelength")

    def test_as_required_int_returns_integer_for_valid_value(self) -> None:
        assert as_required_int("5", "event_count") == 5

    @pytest.mark.parametrize(
        "raw_value",
        [
            None,
            "",
            "invalid",
        ],
    )
    def test_as_required_int_raises_for_invalid_value(self, raw_value: object) -> None:
        with pytest.raises(ValueError, match="Invalid value for event_count"):
            as_required_int(raw_value, "event_count")

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            ("1.25", 1.25),
            ("1,25", 1.25),
            ("invalid", None),
            (None, None),
        ],
    )
    def test_coerce_optional_number(
        self,
        raw_value: object,
        expected_value: float | None,
    ) -> None:
        assert coerce_optional_number(raw_value) == expected_value

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            ("5", 5),
            ("5.9", 5),
            ("invalid", None),
            (None, None),
        ],
    )
    def test_coerce_optional_integer(
        self,
        raw_value: object,
        expected_value: int | None,
    ) -> None:
        assert coerce_optional_integer(raw_value) == expected_value

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            (" FSC-A ", "FSC-A"),
            ("", None),
            ("   ", None),
            (None, None),
            (123, "123"),
        ],
    )
    def test_coerce_optional_string(
        self,
        raw_value: object,
        expected_value: str | None,
    ) -> None:
        assert coerce_optional_string(raw_value) == expected_value

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            ([1, 2, 3], "1, 2, 3"),
            ([1.23456789], "1.23457"),
            ("1, 2, invalid, 3", "1, 2, 3"),
            (None, ""),
        ],
    )
    def test_format_float_list_for_input(
        self,
        raw_value: object,
        expected_value: str,
    ) -> None:
        assert format_float_list_for_input(raw_value) == expected_value


if __name__ == "__main__":
    pytest.main(["-W error", __file__])