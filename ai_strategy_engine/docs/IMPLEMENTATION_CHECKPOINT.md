
# Checkpoint — AI Strategy Engine foundation

## Zakres pakietu

- niezależne implementacje podstawowych wskaźników;
- mapa wszystkich widocznych komponentów Miyagi;
- Feature Registry i constrained search spaces;
- Strategy DSL i kontrakty sygnałów;
- timestamp/leakage policy;
- position-management guardrails;
- prompt implementacyjny i backlog.

## Bezpieczeństwo

- brak kopiowania kodu LuxAlgo;
- brak zależności od prywatnych skryptów TradingView;
- brak live order path;
- research/shadow only;
- closed-bar i confirmed-HTF jako domyślna polityka.

## Następny etap

Agent ma zintegrować pakiet z istniejącymi kontraktami portalu i WickHunter bez duplikowania już scalonych modułów, zaczynając od inventory/gap analysis oraz jednego syntetycznego vertical slice: market data → features → Strategy DSL → leakage guard → deterministic decision → fail-closed risk → shadow evidence.
