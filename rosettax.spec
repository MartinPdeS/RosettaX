# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules


dash_datas, dash_binaries, dash_hiddenimports = collect_all("dash")
plotly_datas, plotly_binaries, plotly_hiddenimports = collect_all("plotly")
dbc_datas, dbc_binaries, dbc_hiddenimports = collect_all(
    "dash_bootstrap_components"
)
pymiesim_datas, pymiesim_binaries, pymiesim_hiddenimports = collect_all("PyMieSim")

rosettax_datas = collect_data_files(
    "RosettaX",
    includes=[
        "assets/*",
        "profiles/**/*.json",
        "calibrations/**/*.json",
        "data/**/*",
        "workflow/detector/presets/*.json",
    ],
)

a = Analysis(
    ["RosettaX/__main__.py"],
    pathex=[],
    binaries=dash_binaries + plotly_binaries + dbc_binaries + pymiesim_binaries,
    datas=dash_datas + plotly_datas + dbc_datas + pymiesim_datas + rosettax_datas,
    hiddenimports=(
        collect_submodules("RosettaX.pages")
        + dash_hiddenimports
        + plotly_hiddenimports
        + dbc_hiddenimports
        + pymiesim_hiddenimports
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rosettax",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="rosettax",
)