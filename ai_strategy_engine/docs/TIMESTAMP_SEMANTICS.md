# Semantyka czasu i ochrona przed leakage

## Pola obowiązkowe

- `event_time`: czas, którego dotyczy zdarzenie.
- `detected_at`: pierwszy czas, w którym system mógł wykryć zdarzenie.
- `available_at`: czas, w którym zdarzenie było dostępne dla strategii.
- `decision_time`: czas decyzji.
- `sent_at`: czas wysłania zlecenia.
- `exchange_at`: czas odbioru/potwierdzenia przez giełdę.

## Inwariant

```text
event_time <= detected_at <= available_at <= decision_time <= sent_at <= exchange_at
```

Wyjątek: `event_time` może być historycznym czasem pivotu znanego później. Nigdy nie oznacza to, że strategia mogła użyć pivotu w `event_time`.

## Pivot

Dla `right_bars = 15` pivot na świecy `t` staje się znany dopiero po zamknięciu świecy `t+15`.

## HTF

Wartość 1h używana na 5m jest potwierdzona dopiero po zamknięciu pełnej świecy 1h.

## Replay test

1. Oblicz sygnały na danych do czasu `T`.
2. Zapisz snapshot.
3. Dołącz dane po `T`.
4. Oblicz ponownie.
5. Sygnały z `available_at <= T` muszą być identyczne.
