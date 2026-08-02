# WickHunter production volatility metric

`volatility_ratio` is the population standard deviation of completed-candle
simple returns over the frozen lookback. It is dimensionless and remains on the
same decimal return-ratio scale as `minimum_volatility` and
`maximum_volatility` in `WickHunterParameters`.

It must not be divided by mean absolute return. That alternative is a
coefficient-like statistic commonly near one and is incompatible with the
frozen research ceiling of `0.50`.

The formula correction changes immutable feature identities. Existing WH-01
production datasets and every downstream replay/model artifact remain valid as
historical evidence but must not be reused for candidate fitting. A new WH-01
dataset, replay price-path binding, WH-02 replay package, and candidate package
must be materialized after the corrected code merges.

This boundary changes no holdout, credential, execution, order, promotion, or
live-capital authority.
