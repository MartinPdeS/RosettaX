import pytest

from RosettaX.utils import browser_profiles
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
    default_profile_label = library.get_profile_label(DEFAULT_PROFILE_FILENAME)

    assert library.build_options() == [
        {
            "label": default_profile_label,
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


def test_build_options_prefers_profile_name_from_payload():
    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "custom": {
                    "profile_name": "Readable Custom Name",
                },
            },
            "selected_profile": "custom",
        }
    )

    default_profile_label = library.get_profile_label(DEFAULT_PROFILE_FILENAME)

    assert library.build_options() == [
        {
            "label": default_profile_label,
            "value": DEFAULT_PROFILE_FILENAME,
        },
        {
            "label": "Readable Custom Name",
            "value": "custom.json",
        },
    ]


def test_from_dict_refreshes_packaged_profile_name_from_disk(monkeypatch):
    monkeypatch.setattr(
        browser_profiles.directories,
        "list_profiles",
        lambda: ["default_profile"],
    )

    monkeypatch.setattr(
        browser_profiles.RuntimeConfig,
        "from_profile_name",
        lambda profile_name: browser_profiles.RuntimeConfig.from_dict(
            {
                "profile_name": "Disk Default Name",
                "ui": {
                    "theme_mode": "light",
                    "show_graphs": True,
                    "show_preset_configuration": False,
                },
            }
        ),
    )

    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "default_profile": {
                    "profile_name": "Old Browser Name",
                    "ui": {
                        "theme_mode": "light",
                        "show_graphs": True,
                        "show_preset_configuration": False,
                    },
                },
            },
            "selected_profile": "default_profile",
        }
    )

    assert library.get_profile_label(DEFAULT_PROFILE_FILENAME) == "Disk Default Name"


def test_create_profile_copies_source_and_selects_new_profile():
    library = BrowserProfileLibrary.from_dict(
        {
            "profiles": {
                "base": {"profile_name": "Base profile"},
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
    created_payload = created_library.get_profile_payload("new profile")

    assert created_payload is not None
    assert created_payload["profile_name"] == "new profile"
    assert created_payload["profile_name"] != library.get_profile_payload("base")["profile_name"]


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