"""Read the instrument catalog and resolve FCS instrument rules."""

import json
import logging
import tomllib
from pathlib import Path
from typing import Any

INSTRUMENT_CATALOG_PATH = Path(__file__).resolve().parents[2] / "assets" / "instrument_catalog.toml"
logger = logging.getLogger(__name__)


def load_instrument_catalog(*, path: Path = INSTRUMENT_CATALOG_PATH) -> dict[str, Any]:
    """Read the instrument and shared channel tables from the packaged TOML file."""
    with path.open("rb") as catalog_file:
        return tomllib.load(catalog_file)


def load_instrument_rules(*, path: Path) -> list[dict[str, Any]]:
    """Read channel rules from TOML or an existing JSON rule file."""
    try:
        if path.suffix == ".toml":
            instruments = load_instrument_catalog(path=path)["instruments"]
            return [
                {
                    "name": " ".join(filter(None, (instrument.get("manufacturer"), instrument["model"]))),
                    "instrument_aliases": instrument.get("instrument_aliases", []),
                    "detector_channels": instrument.get("detector_channels", {}),
                    "rosetta_channels": {
                        role: instrument.get("rosetta_channels", {}).get(role)
                        for role in ("scattering", "green_fluorescence")
                    },
                }
                for instrument in instruments.values()
                if instrument.get("instrument_aliases")
            ]
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("Failed to load instrument rules from %s", path)
        return []

    rules = payload.get("rules") if isinstance(payload, dict) else None
    if not isinstance(rules, list):
        return []
    return [
        rule for rule in rules
        if isinstance(rule, dict) and isinstance(rule.get("instrument_aliases"), list)
    ]


def match_instrument_rule(
    *, instrument_name: str, rules: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the most specific rule, leaving equally specific matches unresolved."""
    instrument_token = "".join(character for character in instrument_name.casefold() if character.isalnum())
    if not instrument_token:
        return None

    best_score = 0
    best_rule = None
    for rule in rules:
        aliases = (
            "".join(character for character in str(alias).casefold() if character.isalnum())
            for alias in rule.get("instrument_aliases", [])
        )
        score = max((len(alias) for alias in aliases if alias and alias in instrument_token), default=0)
        if score > best_score:
            best_score, best_rule = score, rule
        elif score == best_score:
            best_rule = None
    return best_rule


def match_recording_instrument(*, instrument_name: str, channel_names: list[str]) -> dict[str, Any] | None:
    """Resolve the catalog model, including a MALS-equipped variant for recordings with that channel."""
    instruments = load_instrument_catalog()["instruments"]
    rules = [dict(instrument, catalog_key=key) for key, instrument in instruments.items()]
    match = match_instrument_rule(instrument_name=instrument_name, rules=rules)
    if match and match.get("mals_variant") and any(scatter_region(channel_name=name) == "mals" for name in channel_names):
        key = match["mals_variant"]
        return dict(instruments[key], catalog_key=key)
    return match


def scatter_region(*, channel_name: str) -> str | None:
    """Identify a labeled SALS, LALS, or MALS region in an FCS parameter name."""
    token = "".join(character for character in channel_name.casefold() if character.isalnum())
    for region, label in (("sals", "smallangle"), ("lals", "largeangle"), ("mals", "mediumangle")):
        if region in token or label in token:
            return region
    return None
