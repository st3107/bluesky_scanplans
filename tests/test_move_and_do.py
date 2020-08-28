import pytest
from bluesky.simulators import summarize_plan

from scanplans.move_and_do import move_and_do_many


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (
            ([(0, 0)], 10), {}
        ),
        (
            ([(0, 0)], 10, True), {}
        ),
        (
            ([(0, 0), (1, 1)], [0, 10]), {}
        )
    ]
)
def test_move_and_do_many(RE, bt, args, kwargs):
    plans = move_and_do_many(bt, *args, **kwargs)
    for plan in plans:
        summarize_plan(plan)
