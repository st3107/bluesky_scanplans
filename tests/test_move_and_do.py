import pytest
from scanplans.move_and_do import move_and_do_many


@pytest.mark.parametrize(
    "sps,kwargs",
    [
        (
                [(0, 0)], {"wait_times": 10}
        ),
        (
                [(0, 0)], {"wait_times": 10, "wait_at_first": True}
        ),
        (
                [(0, 0), (1, 1)], {"wait_times": 10}
        )
    ]
)
def test_move_and_do_many(bt, sps, kwargs):
    #TODO: set up xpdconfig
    move_and_do_many(bt, sps, **kwargs)
