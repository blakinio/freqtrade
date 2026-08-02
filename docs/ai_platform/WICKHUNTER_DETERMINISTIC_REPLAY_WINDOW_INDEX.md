# WickHunter deterministic replay window index

WH-02 validates each normalized aggregate-trade partition once per symbol, builds one immutable timestamp index, and passes only the exact entry/deadline slice to the unchanged event-label function.

The slice begins at the first trade eligible for entry and ends after every trade exactly on the label deadline. When no trade occurs exactly at the deadline, it additionally includes the first later trade solely to prove coverage; that trade remains outside the evaluated label window. This preserves entry ordering, TP-before-SL ordering, same-timestamp aggregate-trade ordering, timeout, MFE, MAE, missing-entry and holdout semantics.

The optimization changes no policy, source data, label identity, authority or output format. It removes repeated whole-partition validation from every decision/side and keeps credentials, execution, orders and live capital absent.
