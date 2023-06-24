# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME=/opt/poetry
ENV PATH=$POETRY_HOME/bin:$PATH
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get -y clean all \
    && rm -rf /var/lib/apt/lists/*

# Download and install ExifTool from source
RUN curl -sSL https://exiftool.org/Image-ExifTool-12.60.tar.gz -o exiftool.tar.gz \
    && tar -xzf exiftool.tar.gz \
    && rm exiftool.tar.gz \
    && cd Image-ExifTool-12.60 \
    && perl Makefile.PL \
    && make install

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Set work directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY poetry.lock pyproject.toml /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy project
COPY . /app/

# Set the entrypoint to poetry run
ENTRYPOINT ["poetry", "run"]