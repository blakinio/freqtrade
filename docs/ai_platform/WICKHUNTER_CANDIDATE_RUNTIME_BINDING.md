# WickHunter candidate runtime binding

The candidate runtime binding is the fail-closed seam between an independently verified WH-04 candidate package, its immutable WH-09 activation request, and the read-only WH-07 runtime.

It reconstructs the exact candidate model, selected parameters, PAPER/SHADOW window, dataset identity, code identity and validation policy. A shadow decision request is accepted only when its bot, mode, parameters, frozen bounds, dataset, code and timestamps match the activation. The seam then installs the verified WH-04 scorer and enables only `candidate_paper_validation_authorized` for that request.

The binding cannot authorize `LIVE_BLOCKED`, cannot accept pre-authorized requests, and does not contain credentials, private exchange access, an order adapter, order submission, execution authority, automatic promotion or live-capital authority. All remaining risk vetoes continue to execute unchanged.
