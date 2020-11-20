from bluesky.simulators import summarize_plan

import scanplans.grid_scan as mod


def test_acq_rel_grid_scan():
    plan = mod.acq_rel_grid_scan([], 30, 5, -1, 1, 3, -1, 1, 3)
    summarize_plan(plan)
