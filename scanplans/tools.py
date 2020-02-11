import numpy as np
import bluesky.plan_stubs as bps

from xpdacq.glbl import glbl
from xpdacq.xpdacq_conf import xpd_configuration
from xpdconf.conf import XPD_SHUTTER_CONF
from typing import Dict, Union

__all__ = [
    "configure_area_det",
    "open_shutter_stub",
    "close_shutter_stub",
    "calc_exposure",
    "shutter_step",
    "calc_delay",
    "inner_shutter_control"
]


def configure_area_det(det, md: Dict[str, Union[int, float]]):
    """
    Yield the message to configure the area detector with time per frame and number of frames per exposure according
    to the required exposure time. Update the metadata.

    Parameters
    ----------
    det
        The area detector.
    md
        A dictionary to configure the area detector. It is the output of calc_exposure.
        It contains the key value pairs:
        {
            'sp_time_per_frame': acq_time (float),
            'sp_num_frames': num_frame (int),
            'sp_requested_exposure': exposure (float),
            'sp_computed_exposure': computed_exposure (float)
        }

    Yields
    ------
    msg
        Message to configure the area detector.
    """
    acq_time = md.get('sp_time_per_frame')
    num_frame = md.get('sp_num_frames')

    yield from bps.abs_set(det.cam.acquire_time, acq_time, wait=True)
    if hasattr(det, "images_per_set"):
        yield from bps.abs_set(det.images_per_set, num_frame, wait=True)


def calc_exposure(det, exposure):
    """
    Calculate the number of frame and exposure time (s) for the detector. Return a dictionary of those information.

    Parameters
    ----------
    det
        The area detector.
    exposure
        The requested exposure time in second.

    Returns
    -------
    md
        A metadata dictionary of configuration for the area detector. The template:
        {
            'sp_time_per_frame': acq_time (float),
            'sp_num_frames': num_frame (int),
            'sp_requested_exposure': exposure (float),
            'sp_computed_exposure': computed_exposure (float)
        }

    """
    acq_time = glbl['frame_acq_time']
    _check_mini_expo(exposure, acq_time)
    if hasattr(det, "images_per_set"):
        # compute number of frames
        num_frame = int(np.ceil(exposure / acq_time))
    else:
        # The dexela detector does not support `images_per_set` so we just
        # use whatever the user asks for as the thing
        num_frame = 1
    computed_exposure = num_frame * acq_time
    print(
        "INFO: requested exposure time = {} - > computed exposure time"
        "= {}".format(exposure, computed_exposure)
    )
    md = {
        'sp_time_per_frame': acq_time,
        'sp_num_frames': num_frame,
        'sp_requested_exposure': exposure,
        'sp_computed_exposure': computed_exposure
    }
    return md


def _check_mini_expo(exposure, acq_time):
    if exposure < acq_time:
        raise ValueError(
            "WARNING: total exposure time: {}s is shorter "
            "than frame acquisition time {}s\n"
            "you have two choices:\n"
            "1) increase your exposure time to be at least"
            "larger than frame acquisition time\n"
            "2) increase the frame rate, if possible\n"
            "    - to increase exposure time, simply resubmit"
            " the ScanPlan with a longer exposure time\n"
            "    - to increase frame-rate/decrease the"
            " frame acquisition time, please use the"
            " following command:\n"
            "    >>> {} \n then rerun your ScanPlan definition"
            " or rerun the xrun.\n"
            "Note: by default, xpdAcq recommends running"
            "the detector at its fastest frame-rate\n"
            "(currently with a frame-acquisition time of"
            "0.1s)\n in which case you cannot set it to a"
            "lower value.".format(
                exposure,
                acq_time,
                ">>> glbl['frame_acq_time'] = 0.5  #set" " to 0.5s",
            )
        )


def shutter_step(detectors, motor, step):
    """ customized step to ensure shutter is open before
    reading at each motor point and close shutter after reading
    """
    yield from bps.checkpoint()
    yield from bps.abs_set(motor, step, wait=True)
    yield from open_shutter_stub()
    yield from bps.sleep(glbl["shutter_sleep"])
    yield from bps.trigger_and_read(list(detectors) + [motor])
    yield from close_shutter_stub()


def open_shutter_stub():
    """simple function to return a generator that yields messages to
    open the shutter"""
    yield from bps.abs_set(
        xpd_configuration["shutter"], XPD_SHUTTER_CONF["open"], wait=True
    )
    yield from bps.sleep(glbl["shutter_sleep"])
    yield from bps.checkpoint()


def close_shutter_stub():
    """simple function to return a generator that yields messages to
    close the shutter"""
    yield from bps.abs_set(
        xpd_configuration["shutter"], XPD_SHUTTER_CONF["close"], wait=True
    )
    yield from bps.checkpoint()


def calc_delay(delay, computed_exposure, num):
    """Calculate the real delay time. Return a dictionary of metadata."""
    real_delay = max(computed_exposure, delay)
    print(
        "INFO: requested delay = {}s  -> computed delay = {}s".format(
            delay, real_delay
        )
    )
    delay_md = {
        "sp_requested_delay": delay,
        "sp_requested_num": num,
        "sp_computed_delay": real_delay,
    }
    return delay_md


def inner_shutter_control(msg):
    """Use plan_mutator(plan, inner_shutter_control) to make to shutter open when a detector is triggered and close
    when the data is saved. """
    if msg.command == "trigger":

        def inner():
            yield from open_shutter_stub()
            yield msg

        return inner(), None
    elif msg.command == "save":
        return None, close_shutter_stub()
    else:
        return None, None
