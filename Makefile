.PHONY: check image analyze

check:
	PYTHONDONTWRITEBYTECODE=1 python3 -c "from pathlib import Path; [compile(path.read_text(), str(path), 'exec') for path in Path('tools').rglob('*.py')]"

image:
	docker build --tag repository-analysis-tool:local .

analyze:
	docker compose run --rm analyzer
