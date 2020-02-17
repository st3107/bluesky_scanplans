"""A class to print sample information and generate bluesky plan to target samples."""
from xpdacq.beamtime import Beamtime
from xpdacq.xpdacq_conf import xpd_configuration
from bluesky.plan_stubs import mv, null
from pprint import pprint
from typing import Union, Tuple

__all__ = [
    "BeamtimeHelper"
]
POS_KEYS = (
    "position_x",
    "position_y"
)


class BeamtimeHelper:
    """
    A class helping to tackle with tasks related to samples on a rack during the beam time.

    Attributes
    ----------
    _bt
        The instance storing meta data of the sample and plan.
    _pos_key
        The key for the position of samples. Default is the global variable POS_KEYS.
    """
    def __init__(self, bt: Beamtime, pos_key: Tuple[str, str] = POS_KEYS):
        """
        Initiate the class instance.

        Parameters
        ----------
        bt
            The instance storing meta data of the sample and plan.
        pos_key

        """
        self._bt = bt
        self._pos_key = pos_key

    def get_sample_meta(self, sample: Union[int, str]) -> dict:
        """
        Get metadata of a sample.

        Parameters
        ----------
        sample
            The sample index or sample name key.

        Returns
        -------
        sample_meta
            the meta data of a sample
        """
        if isinstance(sample, str):
            sample_cls = self._bt.samples[sample]
        elif isinstance(sample, int):
            sample_cls = list(self._bt.samples.values())[sample]
        else:
            raise ValueError(f"{sample} is not int or str. It is {type(sample)}.")
        sample_meta = dict(sample_cls.items())
        return sample_meta

    def print_sample(self, *samples: Union[int, str]):
        """
        Print the sample information.

        Parameters
        ----------
        samples
            The sample index or sample name key.
        """
        for sample in samples:
            sample_meta = self.get_sample_meta(sample)
            pprint(sample_meta)

    def aim_at_sample(self, sample):
        """
        Target the beam at the sample according to sample position metadata.

        Parameters
        ----------
        sample
            The sample index or sample name key.
        """
        posx_controller = xpd_configuration["posx_controller"]
        posy_controller = xpd_configuration["posy_controller"]
        sample_meta = self.get_sample_meta(sample)
        name = sample_meta.get("sample_name")
        print(f"INFO: Target sample {name}")
        pos_x_key, pos_y_key = self._pos_key
        pos_x = sample_meta.get(pos_x_key)
        pos_y = sample_meta.get(pos_y_key)
        if pos_x is None:
            print(f"Warning: No {pos_x_key} in sample {sample} -> Do nothing")
        else:
            print(f"INFO: Move to x = {pos_x}")
            yield from mv(posx_controller, float(pos_x))
        if pos_y is None:
            print(f"Warning: No {pos_y_key} in sample {sample} -> Do nothing")
        else:
            print(f"INFO: Move to y = {pos_y}")
            yield from mv(posy_controller, float(pos_y))
        yield null()
