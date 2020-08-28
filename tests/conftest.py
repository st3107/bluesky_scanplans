import pytest
from importlib.resources import path
from pathlib import Path
from xpdacq.beamtimeSetup import load_beamtime
from xpdacq.beamtime import Beamtime
from bluesky import RunEngine

with path("data", "__init__.py") as p:
    DATA = p.parent


@pytest.fixture(scope="session")
def bt() -> Beamtime:
    bt = load_beamtime(str(DATA.joinpath("acqsim/xpdUser/config_base/yml")))
    return bt


@pytest.fixture
def RE():
    return RunEngine()
