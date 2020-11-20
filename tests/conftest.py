from importlib.resources import path

import pytest
from bluesky import RunEngine
from ophyd.sim import hw
from xpdacq.beamtime import Beamtime
from xpdacq.beamtime import xpd_configuration
from xpdacq.beamtimeSetup import load_beamtime
from xpdacq.simulation import xpd_pe1c, shctl1

with path("data", "__init__.py") as p:
    DATA = p.parent

HW = hw()


@pytest.fixture()
def bt() -> Beamtime:
    bt = load_beamtime(str(DATA.joinpath("acqsim/xpdUser/config_base/yml")))
    return bt


@pytest.fixture
def RE():
    return RunEngine()


xpd_configuration.update(
    {
        "area_det": xpd_pe1c,
        "x_controller": HW.motor1,
        "y_controller": HW.motor2,
        "shutter": shctl1
    }
)
