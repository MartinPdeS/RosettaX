# -*- coding: utf-8 -*-

from RosettaX.utils.fcs_metadata import FCSMetadata


def test_fcs_metadata_exposes_common_keyword_fields() -> None:
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
