PYTHON ?= python3.13
BUILD_DIR ?= build
ROOT_DIR := $(CURDIR)
PYBIND11_DIR := $(shell $(PYTHON) -m pybind11 --cmakedir)
DIST_DIR ?= dist
BUNDLE_DIR ?= $(DIST_DIR)/rosettax

UNAME_S := $(shell uname -s 2>/dev/null || echo Unknown)

ifeq ($(OS),Windows_NT)
DETECTED_PLATFORM := windows
else ifeq ($(UNAME_S),Darwin)
DETECTED_PLATFORM := macos
else ifeq ($(UNAME_S),Linux)
DETECTED_PLATFORM := linux
else
DETECTED_PLATFORM := unknown
endif

.PHONY: configure build install quick rebuild editable bundle \
	mac-bundle windows-bundle linux-bundle bundle-zip \
	mac-release windows-release linux-release clean

configure:
	cmake -S . -B $(BUILD_DIR) \
		-Dpybind11_DIR="$(PYBIND11_DIR)" \
		-DPython_EXECUTABLE="$$(which $(PYTHON))" \
		-DCMAKE_INSTALL_PREFIX="$(ROOT_DIR)"

build:
	cmake --build $(BUILD_DIR) -j

install:
	cmake --install $(BUILD_DIR)

uninstall:
	$(PYTHON) -m pip uninstall -y PyMieSim

quick: configure build install

rebuild: configure build install

editable:
	$(PYTHON) -m pip install --no-build-isolation -Cbuild-dir=build -Ceditable.rebuild=false -Ceditable.mode=inplace -e .

bundle:
	$(PYTHON) -m pip install -e .[bundling]
	$(PYTHON) -m PyInstaller rosettax.spec --clean

mac-bundle:
	@if [ "$(DETECTED_PLATFORM)" != "macos" ]; then \
		echo "mac-bundle must be run on macOS. Detected platform: $(DETECTED_PLATFORM)"; \
		exit 1; \
	fi
	$(MAKE) bundle

windows-bundle:
	@if [ "$(DETECTED_PLATFORM)" != "windows" ]; then \
		echo "windows-bundle must be run on Windows. Detected platform: $(DETECTED_PLATFORM)"; \
		exit 1; \
	fi
	$(MAKE) bundle

linux-bundle:
	@if [ "$(DETECTED_PLATFORM)" != "linux" ]; then \
		echo "linux-bundle must be run on Linux. Detected platform: $(DETECTED_PLATFORM)"; \
		exit 1; \
	fi
	$(MAKE) bundle

bundle-zip:
	@if [ ! -d "$(BUNDLE_DIR)" ]; then \
		echo "Bundle directory $(BUNDLE_DIR) does not exist. Run a bundle target first."; \
		exit 1; \
	fi
	$(PYTHON) -c "from pathlib import Path; import shutil; source = Path(r'$(BUNDLE_DIR)'); archive = shutil.make_archive(str(source), 'zip', root_dir=str(source.parent), base_dir=source.name); print(f'Created {archive}')"

mac-release: mac-bundle bundle-zip

windows-release: windows-bundle bundle-zip

linux-release: linux-bundle bundle-zip

clean:
	rm -rf $(BUILD_DIR)
