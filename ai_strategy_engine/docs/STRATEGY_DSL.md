# Strategy DSL

## Założenie

DSL reprezentuje strategię jako dane. Nie dopuszcza dowolnego kodu.

## Operatory

- `eq`, `ne`
- `gt`, `gte`
- `lt`, `lte`
- `crosses_above`, `crosses_below`
- `in_range`
- `bars_since_lte`
- `event`
- grupy `all`, `any`, `none`

## Warstwy strategii

1. Universe
2. Features
3. Regime
4. Entry
5. Exit
6. Risk
7. Execution
8. Provenance

## Bezpieczeństwo

Validator odrzuca:

- nieznaną cechę,
- niezatwierdzoną wersję,
- niezakończony HTF w trybie `confirmed`,
- pivot używany przed `available_at`,
- leverage poza limitem,
- DCA bez limitu ekspozycji,
- brak execution cost model.
