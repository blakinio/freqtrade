# AI Routing and Ranking Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-ai-routing-ranking`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent Regime Routera i Ensemble Rankera.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- immutable experiment, feature registry, validation and protected-holdout contracts.

## Cel

Zamknij tylko realne braki AI routing/ranking przydzielone przez koordynatora. Warstwa ma proponować i oceniać kandydatów, ale nie może promować modelu, zmieniać Risk Core ani posiadać execution authority.

## Potencjalny zakres — tylko zgodnie z child taskiem

- trend/range regime;
- high/low volatility regime;
- liquidation regime;
- drift monitoring;
- ensemble correlation penalties;
- OOS stability;
- drawdown contribution;
- calibration;
- deterministic/fail-closed ranking evidence;
- versioned model/config/data identities and explanation records.

## Wymagania

- Korzystaj wyłącznie z approved registry features i immutable experiment evidence.
- Nie używaj chronionego final holdoutu iteracyjnie.
- Missing/ambiguous regime data musi prowadzić do jawnego unknown/fail-closed state.
- Ranking nie może ukrywać correlation, drawdown ani instability penalties.
- Kandydat nie może automatycznie zastąpić active model ani zmienić `selected_model = null`.
- Metryki muszą być OOS/trading-aware, nie wyłącznie treningowe.
- Nie zmieniaj zamrożonych thresholds `0.006/-0.009`.

## Akceptacja

- wszystkie przydzielone real gaps mają kod, testy i evidence;
- stability/correlation/calibration edge cases przechodzą;
- protected-holdout and no-promotion guards przechodzą;
- wyniki są deterministyczne dla tego samego manifestu;
- wymagane CI jest zielone;
- focused PR jest scalony normalnie;
- checkpoint ma dokładnie jeden następny krok.

Działaj autonomicznie do pełnego zamknięcia bounded tasku.
