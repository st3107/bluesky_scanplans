from typing import Generator

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import sleep
from ophyd.sim import SynAxis
from xpdacq.beamtime import Beamtime, Sample, ScanPlan
from xpdacq.xpdacq_conf import xpd_configuration

from scanplans.beamtimehelper import BeamtimeHelper


@pytest.mark.skip(reason="Yaml not found in CI.")
def test_beamtimehelper():
    RE = RunEngine()
    motor0 = SynAxis(name="motor0")
    motor1 = SynAxis(name="moror1")
    xpd_configuration["posx_controller"] = motor0
    xpd_configuration["posy_controller"] = motor1
    xpd_configuration["area_det"] = None
    bt = Beamtime("Billinge", 300000, ["Billinge"])

    sample_md = {"sample_name": "Ni", "sample_composition": {"Ni": 1}}
    Sample(bt, sample_md)

    def plan(dets, sleep_time):
        yield from sleep(sleep_time)

    ScanPlan(bt, plan, 10)
    bthelper = BeamtimeHelper(bt)
    output_sample_md = bthelper.get_sample(0)

    assert output_sample_md.get("sample_name") == "Ni"
    assert output_sample_md.get("sample_composition") == {"Ni": 1}
    assert isinstance(bthelper.get_plan(0), Generator)
    assert bthelper.print_sample(0) is None
    assert bthelper.print_plan(0) is None

    x0, y0 = float(motor0.position), float(motor1.position)

    RE(bthelper.aim_at_sample(0))
    assert motor0.position == x0
    assert motor1.position == y0
    sample_md.update({
        "position_x": x0 + 1,
        "position_y": y0 + 1
    })
    Sample(bt, sample_md)
    RE(bthelper.aim_at_sample(0))
    assert motor0.position == x0 + 1
    assert motor1.position == y0 + 1
