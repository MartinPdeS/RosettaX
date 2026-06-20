# -*- coding: utf-8 -*-

from RosettaX.pages.p02_fluorescence.state import FluorescencePageState


class Test_FluorescencePageState:
    def test_reference_table_rows_defaults_to_none_when_missing(self) -> None:
        page_state = FluorescencePageState.from_dict(
            {
                "uploaded_fcs_path": "/tmp/example.fcs",
                "uploaded_filename": "example.fcs",
            }
        )

        assert page_state.reference_table_rows is None

    def test_update_persists_reference_table_rows(self) -> None:
        page_state = FluorescencePageState.empty().update(
            reference_table_rows=[
                {
                    "col1": "500",
                    "col2": "12345",
                }
            ]
        )

        serialized_state = page_state.to_dict()
        restored_state = FluorescencePageState.from_dict(serialized_state)

        assert restored_state.reference_table_rows == [
            {
                "col1": "500",
                "col2": "12345",
            }
        ]
