"""The functions to get metadata related to the samples and plans from the Beamtime object."""
from typing import Union, List

from bluesky.preprocessors import msg_mutator
from xpdacq.beamtime import Beamtime, ScanPlan, Sample
from xpdacq.xpdacq import _sample_injector_factory

__all__ = [
    "translate_to_sample",
    "translate_to_plan",
    "get_from_sample"
]


def translate_to_sample(beamtime: Beamtime, sample: Union[int, List[int], dict]):
    """Translate a sample into a list of dict

    Parameters
    ----------
    beamtime : Beamtime
        The BeamTime instance.

    sample : list of int or dict-like
        Sample metadata. If a beamtime object is linked,
        an integer will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding metadata will be passed.
        A customized dict can also be passed as the sample
        metadata.

    Returns
    -------
    sample_md : Union[List[dict], dict]
        The sample info loaded
    """
    if isinstance(sample, list):
        sample_md = [translate_to_sample(beamtime, s) for s in sample]
    elif isinstance(sample, int):
        try:
            sample_md = list(beamtime.samples.values())[sample]
        except IndexError:
            print(
                "WARNING: hmm, there is no sample with index `{}`"
                ", please do `bt.list()` to check if it exists yet".format(
                    sample
                )
            )
            return
    else:
        raise TypeError(f"The type of sample is {type(sample)}. Expect list, int or dict-like.")
    return sample_md


def translate_to_plan(beamtime, plan, sample_md):
    """Translate a plan input into a generator

    Parameters
    ----------
    beamtime : Beamtime
        The BeamTime instance.
    sample_md : list of dict-like
        Sample metadata. If a beamtime object is linked,
        an integer will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding metadata will be passed.
        A customized dict can also be passed as the sample
        metadata.
    plan : list of int or generator
        Scan plan. If a beamtime object is linked, an integer
        will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding scan plan will be
        A generator or that yields ``Msg`` objects (or an iterable
        that returns such a generator) can also be passed.

    Returns
    -------
    plan : generator
        The generator of messages for the plan

    """
    if isinstance(plan, list):
        plan = [translate_to_plan(beamtime, p, s) for p, s in zip(plan, sample_md)]
    # If a plan is given as a int, look in up in the global registry.
    else:
        if isinstance(plan, int):
            try:
                plan = list(beamtime.scanplans.values())[plan]
            except IndexError:
                print(
                    "WARNING: hmm, there is no scanplan with index `{}`"
                    ", please do `bt.list()` to check if it exists yet".format(
                        plan
                    )
                )
                return
        # If the plan is an xpdAcq 'ScanPlan', make the actual plan.
        if isinstance(plan, ScanPlan):
            plan = plan.factory()
        mm = _sample_injector_factory(sample_md)
        plan = msg_mutator(plan, mm)
    return plan


def get_from_sample(sample, key):
    """
    Get the value of the key in a Sample instance. If fail to access, print out the message.

    Parameters
    ----------
    sample
        A Sample object.

    key : basestring
        The name of the key.

    Returns
    -------
    value
        The result of sample.get(key).
    """
    value = sample.get(key)
    if not value:
        print(
            "INFO: The sample '{}' does not have key '{}'.".format(sample.get('sample_name'), key)
        )
    return value
