# AI Strategy Engine source bundle manifest

## Zawartość

Pełny starter źródłowy jest przechowywany w tekstowych fragmentach Base64 pod:

```text
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part*
```

Bundle zawiera 67 plików źródłowych i dokumentacyjnych, w tym:

- JSON Schema kontraktów;
- Feature Registry i constrained search spaces;
- mapę parametrów Miyagi;
- Strategy DSL i przykłady strategii;
- niezależne implementacje wskaźników i polityk;
- guardrails czasu, leakage i position management;
- unit oraz contract E2E tests;
- dokumentację architektury, audytu i licencji.

## Integralność

Oczekiwany SHA-256 zrekonstruowanego archiwum ZIP:

```text
73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f
```

`materialize_starter.py` weryfikuje ten hash przed rozpakowaniem oraz blokuje ścieżki wychodzące poza katalog pakietu.

## Materializacja

Z katalogu głównego repozytorium uruchom:

```bash
python ai_strategy_engine/materialize_starter.py
```

Następnie:

```bash
cd ai_strategy_engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src/strategy_engine
```

## Weryfikacja wykonana przed zapisem

- `pytest -q`: 20 testów zakończonych powodzeniem;
- `python -m compileall -q src tests`: powodzenie;
- parsowanie JSON/YAML: powodzenie;
- lokalna rekonstrukcja fragmentów Base64: identyczny SHA-256 jak bundle źródłowy.

Ruff i mypy nie były dostępne w lokalnym sandboxie, dlatego muszą zostać uruchomione w CI lub środowisku agenta po instalacji zależności developerskich.

## Status

To foundation/research package. Nie zawiera produkcyjnej ścieżki live order. Po materializacji agent ma wykonać inventory istniejącego repo, dopasować ownership paths i dostarczyć osobny ASE-00 vertical slice bez duplikowania portalu, WickHunter, liquidation data layer ani execution.
