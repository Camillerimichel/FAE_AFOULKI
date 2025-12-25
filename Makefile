VENV ?= .venv
PYTHON ?= python3
HOST ?= 0.0.0.0
PORT ?= 8000
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

.PHONY: install dev run clean

install: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

dev: install
	$(UVICORN) app.main:app --reload --host $(HOST) --port $(PORT)

run: install
	$(UVICORN) app.main:app --host $(HOST) --port $(PORT)

clean:
	rm -rf $(VENV)
