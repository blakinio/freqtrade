# ASE-00 DEFLATE recovery

- original ZIP SHA-256: `e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`
- expected ZIP SHA-256: `73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f`
- `examples/signal_event.json`: compressed offset `266` changed `b1` -> `89`; absolute ZIP offset `5301`
- `src/strategy_engine/features/momentum.py`: compressed offset `500` changed `b9` -> `b7`; absolute ZIP offset `34444`
- `tests/unit/test_squeeze.py`: compressed offset `151` changed `a2` -> `ca`; absolute ZIP offset `43749`
- patched ZIP SHA-256: `73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f`
- all ZIP members valid: `true`
- first invalid member/error: `None`
- exact expected archive recovered: `true`
