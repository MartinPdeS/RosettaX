"""Regression tests for utils FCS metadata."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


from RosettaX.utils.fcs_metadata import FCSMetadata


def test_fcs_metadata_exposes_common_keyword_fields() -> None:
    """Check FCS metadata exposes common keyword fields."""
    metadata = FCSMetadata(
        file_path="example.fcs",
        header={"FCS version": "FCS3.1"},
        text={
            "Keywords": {
                "$TOT": "12345",
                "$PAR": "2",
                "$DATATYPE": "F",
                "$MODE": "L",
            },
            "Detectors": {
                1: {"N": "FSC-A"},
                2: {"N": "SSC-A"},
            },
        },
        delimiter="|",
    )

    assert metadata.number_of_events == 12345
    assert metadata.number_of_parameters == 2
    assert metadata.datatype == "F"
    assert metadata.mode == "L"
