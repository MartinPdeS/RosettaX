# # -*- coding: utf-8 -*-

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from MPSPlots import helper

import numpy as np
import pandas as pd


def _is_integer(value: str) -> bool:
    """Return True if the given string can be converted to an integer."""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


@dataclass
class FCSFile:
    """
    Reader for a single FCS file.

    This class parses the header and text segments on construction.
    Event data is read on demand with `read_all_data`.

    Attributes
    ----------
    file_path:
        Path to the FCS file on disk.
    header:
        Parsed header information, such as version and segment positions.
    text:
        Parsed text segment, containing general keywords and detector metadata.
        Keys:
            "Keywords" -> dict with all FCS keywords.
            "Detectors" -> dict mapping detector index to parameter metadata.
    delimiter:
        Character used as delimiter in the text segment.
    data:
        Event data as a pandas DataFrame, populated by `read_all_data`.
    """

    file_path: str
    header: Dict[str, Any] = field(init=False)
    text: Dict[str, Any] = field(init=False)
    delimiter: str | None = field(init=False, default=None)
    data: pd.DataFrame | None = field(init=False, default=None)

    # ------------------------------------------------------------------
    # Construction and segment parsing
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """Parse the FCS header and text segments."""
        self._validate_file()
        self.header = self._read_header()
        self.text, self.delimiter = self._read_text()


    def _validate_file(self) -> None:
        """Verify that the file exists and is large enough to contain a header."""
        if not os.path.isfile(self.file_path):
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(f'"{name}" does not exist.')

        # Original code used 257 as minimal size
        if os.path.getsize(self.file_path) < 257:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the file is smaller than allowed.'
            )

    def _read_header(self) -> Dict[str, Any]:
        """
        Read and parse the fixed size header segment of the FCS file.

        Returns
        -------
        dict
            Dictionary with keys:
            "FCS version", "Text start", "Text end", "Data start", "Data end".

        Raises
        ------
        FileNotFoundError
            If the FCS version or header fields are invalid.
        """
        with open(self.file_path, "rb") as handle:
            header_bytes = handle.read(256)

        try:
            fcs_version = header_bytes[:6].decode("ascii")
        except UnicodeDecodeError as exc:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the FCS version cannot be decoded.'
            ) from exc

        allowed_versions = {"FCS2.0", "FCS3.0", "FCS3.1"}
        if fcs_version not in allowed_versions:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the FCS version is undefined.'
            )

        try:
            text_start = int(header_bytes[10:18].strip())
            text_end = int(header_bytes[18:26].strip())
            data_start = int(header_bytes[26:34].strip())
            data_end = int(header_bytes[34:42].strip())
        except ValueError as exc:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the file segments are undefined.'
            ) from exc

        return {
            "FCS version": fcs_version,
            "Text start": text_start,
            "Text end": text_end,
            "Data start": data_start,
            "Data end": data_end,
        }

    def _read_text(self) -> Tuple[Dict[str, Any], str]:
        """
        Read and parse the text segment of the FCS file.

        The text segment contains keyword and detector metadata. Keywords are
        stored in `result["Keywords"]`, while per detector information is
        grouped into `result["Detectors"]`.

        Returns
        -------
        dict
            Dictionary with "Keywords" and "Detectors".
        str
            Delimiter character used in the text segment.

        Raises
        ------
        FileNotFoundError
            If the text segment cannot be decoded or parsed.
        """
        text_start = self.header["Text start"]
        text_end = self.header["Text end"]

        length = text_end - text_start + 1
        if length <= 0:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the text segment has invalid bounds.'
            )

        with open(self.file_path, "rb") as handle:
            handle.seek(text_start)
            raw = handle.read(length)

        try:
            text_section = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the text segment cannot be decoded.'
            ) from exc

        if not text_section:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the text segment is empty.'
            )

        delimiter = text_section[0]
        text_payload = text_section[1:]  # drop leading delimiter

        # Split into items and parse key value pairs
        items = text_payload.strip().split(delimiter)
        if len(items) < 2:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the text segment contains no key value pairs.'
            )

        parsed: Dict[str, Any] = {"Keywords": {}, "Detectors": {}}
        keywords = parsed["Keywords"]

        for index in range(0, len(items) - 1, 2):
            key = items[index].strip()
            value = items[index + 1].strip()

            if _is_integer(value):
                value = int(value)

            keywords[key] = value

        # Group detector parameters by channel index
        self._group_detectors(parsed)

        return parsed, delimiter

    def _group_detectors(self, parsed_text: Dict[str, Any]) -> None:
        """
        Group per detector keywords into `parsed_text["Detectors"]`.

        Parameters
        ----------
        parsed_text:
            Text dictionary as created by `_read_text`. It is modified in place.

        Notes
        -----
        Detector keywords have names of the form `$P{index}{suffix}`.
        These are collected under `parsed_text["Detectors"][index][suffix]`
        and removed from the `Keywords` dictionary.
        """
        keywords = parsed_text["Keywords"]
        detectors: Dict[int, Dict[str, Any]] = {}

        try:
            num_parameters = int(keywords["$PAR"])
        except KeyError as exc:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because `$PAR` is missing in the text segment.'
            ) from exc

        # Use a stable list, not a set, to keep iteration order deterministic
        detector_suffixes = [
            "B",
            "E",
            "N",
            "R",
            "D",
            "F",
            "G",
            "L",
            "O",
            "P",
            "S",
            "T",
            "V",
            "TYPE",
        ]

        for det_index in range(1, num_parameters + 1):
            det_info: Dict[str, Any] = {}

            for suffix in detector_suffixes:
                key = f"$P{det_index}{suffix}"
                if key in keywords:
                    det_info[suffix] = keywords.pop(key)

            detectors[det_index] = det_info

        parsed_text["Detectors"] = detectors

    # ------------------------------------------------------------------
    # Data reading
    # ------------------------------------------------------------------

    def read_all_data(self) -> pd.DataFrame:
        """
        Read the event data segment into a pandas DataFrame.

        The column names are taken from the detector keyword `$PnN` for each
        parameter, so the channel names correspond to the instrument settings.

        Returns
        -------
        pandas.DataFrame
            Event data with shape `(num_events, num_parameters)`.

        Raises
        ------
        FileNotFoundError
            If the data segment cannot be read or `$DATATYPE` is unsupported.
        """
        keywords = self.text["Keywords"]
        detectors = self.text["Detectors"]

        try:
            num_events = int(keywords["$TOT"])
            num_parameters = int(keywords["$PAR"])
            datatype_code = keywords["$DATATYPE"]
        except KeyError as exc:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because required data keywords are missing.'
            ) from exc

        data_start = self.header["Data start"]
        data_end = self.header["Data end"]

        # If data end is zero, FCS uses $BEGINDATA and $ENDDATA in text
        if data_end == 0:
            try:
                data_start = int(keywords["$BEGINDATA"])
                data_end = int(keywords["$ENDDATA"])
            except KeyError as exc:
                name = os.path.basename(self.file_path)
                raise FileNotFoundError(
                    f'"{name}" is not a valid FCS file because data positions are undefined.'
                ) from exc

        if data_end <= data_start:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the data segment has invalid bounds.'
            )

        file_size = os.path.getsize(self.file_path)
        if file_size < data_end:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" is not a valid FCS file because the data segment extends beyond the file size.'
            )

        # Map FCS $DATATYPE to NumPy dtypes
        dtype_mapping = {
            "F": np.float32,  # floating point
            "D": np.float64,  # double precision
            "I": np.int32,    # signed integer
            "L": np.uint32,   # unsigned integer
        }

        np_dtype = dtype_mapping.get(datatype_code)
        if np_dtype is None:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" uses unsupported $DATATYPE "{datatype_code}".'
            )

        total_elements = num_events * num_parameters
        data_length = data_end - data_start + 1

        # Build column headings using detector names `$PnN`
        column_headings = [
            detectors[index].get("N", f"P{index}") for index in range(1, num_parameters + 1)
        ]

        with open(self.file_path, "rb") as handle:
            handle.seek(data_start)
            raw = handle.read(data_length)

        array = np.frombuffer(raw, dtype=np_dtype, count=total_elements)
        if array.size != total_elements:
            name = os.path.basename(self.file_path)
            raise FileNotFoundError(
                f'"{name}" could not be fully read into a data array. '
                f"Expected {total_elements} elements, got {array.size}."
            )

        data = array.reshape((num_events, num_parameters))
        self.data = pd.DataFrame(data, columns=column_headings)

        units = {}

        for column in self.data.columns:
            units[column] = 'A.U.'

        self.data.attrs['units'] = units

        return self.data

    @helper.post_mpl_plot
    def plot(self, x, y, *, gridsize=200, bins_1d=20, log_hexbin=False, log_hist=False, cmap="viridis", hist_color="gray"):
        """
        Plot a fast hexbin 2D density plot with marginal 1D histograms.

        Parameters
        ----------
        x : array_like
            Data for the horizontal axis.
        y : array_like
            Data for the vertical axis.

        gridsize : int, optional (default: 200)
            Resolution of the hexagonal grid for the 2D histogram.

        bins_1d : int, optional (default: 200)
            Number of bins used for the marginal histograms.

        log_hexbin : bool, optional (default: False)
            If True, color-scale of the hexbin is logarithmic.

        log_hist : bool, optional (default: False)
            If True, marginal histograms are plotted with log-scaled counts.

        cmap : str, optional (default: "viridis")
            Colormap used for the hexbin.

        figsize : tuple, optional (default: (8, 8))
            Overall figure size.

        x_label : str or None
            Label for the x-axis (falls back to no label if None).

        y_label : str or None
            Label for the y-axis (falls back to no label if None).

        title : str or None
            Optional title for the full figure.

        hist_color : str, optional (default: "gray")
            Color used for the marginal histograms.

        Returns
        -------
        fig : matplotlib.figure.Figure
            The created figure object.

        ax_hex : matplotlib.axes.Axes
            Main hexbin plot axis.

        ax_xhist : matplotlib.axes.Axes
            Top marginal histogram axis.

        ax_yhist : matplotlib.axes.Axes
            Right marginal histogram axis.
        """
        # Extract data
        x_values = self.data[x].values
        y_values = self.data[y].values

        fig = plt.figure()
        gs = GridSpec(4, 4, figure=fig, wspace=0.05, hspace=0.05)

        # Main plot
        ax_hex = fig.add_subplot(gs[1:, 0:3])

        # Marginal plots
        ax_xhist = fig.add_subplot(gs[0, 0:3], sharex=ax_hex)
        ax_yhist = fig.add_subplot(gs[1:, 3], sharey=ax_hex)

        # Initial hexbin
        hb = ax_hex.hexbin(
            x_values, y_values,
            gridsize=gridsize,
            mincnt=1,
            bins="log" if log_hexbin else None,
            cmap=cmap,
        )

        # Initial marginal histograms
        ax_xhist.hist(x_values, bins=bins_1d, color=hist_color, log=log_hist)
        ax_yhist.hist(y_values, bins=bins_1d, orientation="horizontal", color=hist_color, log=log_hist)

        # Aesthetic cleanup
        plt.setp(ax_xhist.get_xticklabels(), visible=False)
        plt.setp(ax_yhist.get_yticklabels(), visible=False)
        ax_xhist.tick_params(axis="x", bottom=False)
        ax_yhist.tick_params(axis="y", left=False)

        # Remove scientific notation everywhere
        ax_hex.ticklabel_format(useOffset=False, style='plain', scilimits=[0, 0])
        ax_xhist.ticklabel_format(useOffset=False, style='plain', scilimits=[0, 0])
        ax_yhist.ticklabel_format(useOffset=False, style='plain', scilimits=[0, 0])

        # --------------------------
        # Dynamic update functionality (with recursion guard)
        # --------------------------

        is_updating = False

        def update_plot(event=None):
            nonlocal is_updating, hb

            # Avoid recursive calls
            if is_updating:
                return
            is_updating = True

            # Current visible window
            xmin, xmax = ax_hex.get_xlim()
            ymin, ymax = ax_hex.get_ylim()

            # Mask visible data
            mask = (x_values >= xmin) & (x_values <= xmax) & (y_values >= ymin) & (y_values <= ymax)
            xv = x_values[mask]
            yv = y_values[mask]

            # ----------------------
            # Update hexbin colors
            # ----------------------
            # Remove old hexbin collections
            for col in list(ax_hex.collections):
                try:
                    col.remove()
                except Exception:
                    pass

            hb = ax_hex.hexbin(
                xv, yv,
                gridsize=gridsize,
                mincnt=1,
                bins="log" if log_hexbin else None,
                cmap=cmap,
            )

            # ----------------------
            # Update marginal histograms
            # ----------------------
            ax_xhist.cla()
            ax_yhist.cla()

            ax_xhist.hist(xv, bins=bins_1d, color=hist_color, log=log_hist)
            ax_yhist.hist(yv, bins=bins_1d, orientation="horizontal", color=hist_color, log=log_hist)

            plt.setp(ax_xhist.get_xticklabels(), visible=False)
            plt.setp(ax_yhist.get_yticklabels(), visible=False)
            ax_xhist.tick_params(axis="x", bottom=False)
            ax_yhist.tick_params(axis="y", left=False)

            ax_xhist.set_xlim(xmin, xmax)
            ax_yhist.set_ylim(ymin, ymax)

            # Remove scientific notation again after replot
            ax_hex.ticklabel_format(useOffset=False, style='plain', scilimits=[0, 0])
            ax_xhist.ticklabel_format(useOffset=False, style='plain', scilimits=[0, 0])
            ax_yhist.ticklabel_format(useOffset=False, style='plain', scilimits=[0, 0])

            fig.canvas.draw_idle()
            is_updating = False

        # Connect callbacks
        ax_hex.callbacks.connect("xlim_changed", update_plot)
        ax_hex.callbacks.connect("ylim_changed", update_plot)

        x_units = self.data.attrs['units'].get(x, '')
        y_units = self.data.attrs['units'].get(y, '')

        ax_hex.set_xlabel(f"{x} [{x_units}]" if x_units else x)
        ax_hex.set_ylabel(f"{y} [{y_units}]" if y_units else y)

        # Initial computation
        update_plot()

        return fig