# Process arrow style

Every workflow arrow is a native triangle named `RosettaX Process Arrowhead …`.
Arrows use geometry, with no arrow glyph, connector stroke, or separate text box.

The shared size and color are in `arrow-style.json`. To apply a change:

```sh
python3 -m pip install -r presentation/requirements.txt
python3 presentation/update_process_arrows.py
```

The updater starts with the current Keynote deck, preserves manual slide edits and
presenter notes, updates only the named arrowhead shapes, and refreshes the Keynote,
PDF, and PowerPoint files. Arrow centers remain where they were placed on the slide.

`build_editable_deck.py` is the source for the complete visual rebuild. Rebuilding
replaces slide layouts; use the arrow updater for later changes to arrows alone.
