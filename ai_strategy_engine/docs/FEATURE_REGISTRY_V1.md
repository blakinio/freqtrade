# Feature Registry v1

Każda cecha posiada:

- `id`,
- `version`,
- `status`,
- `parameters`,
- `inputs`,
- `warmup`,
- `timestamp_policy`,
- `normalization`,
- `roles`,
- `approved_for_ai`,
- `license_origin`,
- `tests`.

## Statusy

- `experimental`
- `validated`
- `approved`
- `deprecated`
- `blocked`

## Role

- `regime`
- `trigger`
- `confirmation`
- `exit`
- `risk`
- `visualization`
- `ml_feature`

## Zasada AI

Model może użyć cechy tylko, gdy:

```text
approved_for_ai = true
AND status in {validated, approved}
AND timestamp_policy != unsafe
```

Pełna konfiguracja znajduje się w `configs/feature_registry.v1.yaml`.
