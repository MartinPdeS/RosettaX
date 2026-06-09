import pytest

from RosettaX.utils.browser_profiles import (
    DEFAULT_PROFILE_FILENAME,
    BrowserProfileLibrary,
)


def test_from_dict_normalizes_names_and_sorts_default_first():
    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "zeta": {},
                "alpha": {},
            },
            "selected_profile": "alpha",
        }
    )

    assert library.selected_profile == "alpha.json"
    assert list(library.profiles) == [
        "zeta.json",
        "alpha.json",
        DEFAULT_PROFILE_FILENAME,
    ]
    assert library.build_options() == [
        {
            "label": "Automatic",
            "value": DEFAULT_PROFILE_FILENAME,
        },
        {
            "label": "alpha",
            "value": "alpha.json",
        },
        {
            "label": "zeta",
            "value": "zeta.json",
        },
    ]


def test_from_dict_falls_back_to_default_for_missing_selection():
    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "custom": {},
            },
            "selected_profile": "missing",
        }
    )

    assert library.selected_profile == DEFAULT_PROFILE_FILENAME


def test_create_profile_copies_source_and_selects_new_profile():
    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "base": {},
            },
            "selected_profile": "base",
        }
    )

    created_library = library.create_profile(
        profile_name="new profile",
        source_profile_name="base",
        select_profile=True,
    )

    assert created_library.selected_profile == "new profile.json"
    assert created_library.get_profile_payload("new profile") == library.get_profile_payload(
        "base"
    )


def test_delete_profile_rejects_default_and_reselects_default():
    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "custom": {},
            },
            "selected_profile": "custom",
        }
    )

    with pytest.raises(ValueError, match="Cannot delete default profile"):
        library.delete_profile(profile_name=DEFAULT_PROFILE_FILENAME)

    updated_library = library.delete_profile(profile_name="custom")

    assert "custom.json" not in updated_library.profiles
    assert updated_library.selected_profile == DEFAULT_PROFILE_FILENAME