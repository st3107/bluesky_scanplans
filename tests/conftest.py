import pytest
from importlib.resources import path
from pathlib import Path
from xpdacq.beamtimeSetup import load_beamtime
from xpdacq.beamtime import Beamtime
from bluesky import RunEngine
from ophyd.sim import hw
from xpdacq.beamtime import xpd_configuration
from xpdacq.simulation import xpd_pe1c

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
        "y_controller": HW.motor2
    }
)
