# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml README.rst LICENSE MANIFEST.in ./
COPY RosettaX ./RosettaX

# The build context excludes Git metadata; use the checked-in package version.
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ROSETTAX="$(python -c 'import runpy; print(runpy.run_path("RosettaX/_version.py")["__version__"])')" \
    python -m pip wheel --only-binary=:all: --wheel-dir /wheels .

FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    ROSETTAX_CALIBRATION_DIRECTORY=/home/rosettax/.rosettax/calibrations \
    ROSETTAX_USAGE_METRICS_PATH=/home/rosettax/.rosettax/usage_metrics.json \
    ROSETTAX_VISIT_LOG_PATH=/home/rosettax/.rosettax/visit_log.jsonl \
    GUNICORN_CMD_ARGS="--bind=0.0.0.0:8050 --workers=1 --threads=4 --timeout=300 --access-logfile=- --error-logfile=-"

RUN apt-get update \
    && apt-get install --no-install-recommends --yes libgomp1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-index --find-links=/wheels RosettaX \
    && rm -rf /wheels \
    && useradd --create-home --uid 10001 --user-group rosettax \
    && mkdir -p /home/rosettax/.rosettax/uploads/staged \
        /home/rosettax/.rosettax/calibrations/fluorescence \
        /home/rosettax/.rosettax/calibrations/scattering \
    && chown -R rosettax:rosettax /home/rosettax

WORKDIR /home/rosettax
USER rosettax
EXPOSE 8050

HEALTHCHECK --interval=10s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; response = urlopen('http://127.0.0.1:8050/', timeout=3); assert response.status == 200"]

CMD ["gunicorn", "RosettaX.application.wsgi:server"]
