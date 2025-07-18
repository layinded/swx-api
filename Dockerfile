## Use a lightweight Python base image
#FROM python:3.10-slim AS builder
#
#WORKDIR /app/
#
## Install uv (Fast dependency management)
#COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/
#ENV PATH="/app/.venv/bin:$PATH"
#
## Set environment variables
#ENV PYTHONUNBUFFERED=1
#ENV UV_COMPILE_BYTECODE=1
#ENV UV_LINK_MODE=copy
#
## Step 1️⃣: Create Virtual Environment & Install pip
#RUN python -m venv .venv && \
#    /app/.venv/bin/python -m ensurepip --default-pip && \
#    /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel
#
## Step 2️⃣: Copy Dependencies
#COPY pyproject.toml uv.lock /app/
#
## Step 3️⃣: Install Dependencies with `uv`
#RUN --mount=type=cache,target=/root/.cache/uv \
#    uv venv .venv && uv sync --frozen --no-install-project
#
## Step 4️⃣: Reinstall pip AFTER uv (because uv wipes pip)
#RUN /app/.venv/bin/python -m ensurepip --default-pip && \
#    /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel
#
## Step 5️⃣: Install SwX-API as a Package
#RUN /app/.venv/bin/python -m pip install .
#
## Stage 2: Final lightweight image
#FROM python:3.10-slim
#
#WORKDIR /app/
#
## Copy virtual environment from builder
#COPY --from=builder /app/.venv /app/.venv
#
## Ensure `.venv` activation
#ENV PATH="/app/.venv/bin:$PATH"
#
## Copy application files & dependencies to the final stage
#COPY  swx_api /app/swx_api
#COPY  alembic.ini /app/alembic.ini
#COPY  migrations /app/migrations
#
#COPY  scripts /app/scripts
#
#
#
#COPY .env /app/.env
#
#
#COPY pyproject.toml /app/
#
#
#RUN /app/.venv/bin/python -m pip install .
#
## Expose FastAPI port
#EXPOSE 8000
#
#
## Default command (Users can override this in Docker Compose)
#CMD ["/app/.venv/bin/uvicorn", "swx_api.core.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Stage 1: Build environment
FROM python:3.10-slim AS builder

WORKDIR /app/

# Use uv (ultra-fast dependency resolver)
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Create virtualenv and install pip
RUN python -m venv .venv && \
    /app/.venv/bin/python -m ensurepip --default-pip && \
    /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel

# Copy project dependencies
COPY pyproject.toml /app/
# Optional: If you have a lock file
# COPY uv.lock /app/

# Install dependencies with uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv .venv && uv sync --no-install-project

# Reinstall pip (uv sometimes overwrites it)
RUN /app/.venv/bin/python -m ensurepip --default-pip && \
    /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel

# Install your project itself (editable mode)
RUN /app/.venv/bin/python -m pip install .

# Stage 2: Final runtime image
FROM python:3.10-slim

WORKDIR /app/

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy all source code
COPY . /app/

# (Optional) Make any prestart scripts executable
# RUN chmod +x /app/scripts/prestart.sh

# Expose FastAPI port
EXPOSE 8000

# Default startup command
CMD ["/app/.venv/bin/uvicorn", "swx_api.core.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
