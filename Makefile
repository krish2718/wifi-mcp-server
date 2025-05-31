.PHONY: install test test-standalone test-mcp clean

install:
	pip install -r requirements.txt
	pip install -e .

test: test-standalone test-mcp

test-standalone:
	python3 standalone_test.py

test-mcp:
	python3 test_wifi_server.py ./wifi_mcp_server.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev-setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	./venv/bin/pip install -r requirements-dev.txt
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

lint:
	python3 -m flake8 --max-line-length 100 wifi_mcp_server.py
	python3 -m ruff check wifi_mcp_server.py
