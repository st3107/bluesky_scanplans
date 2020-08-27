import os
import uuid

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import numpy as np
import pandas as pd
from bluesky.callbacks import LiveTable
from xpdacq.beamtime import _configure_area_det
from xpdacq.tools import xpdAcqException
from xpdacq.utils import ExceltoYaml

gridScan_sample = {}


def gridScan(dets, exp_spreadsheet_fn, glbl, xpd_configuration,
             XPD_SHUTTER_CONF, *,
             crossed=False, dx=None, dy=None, wait_time=5):
    """
    Scan plan for the multi-sample grid scan.

    This function takes in a templated excel spreadsheet and constructs a
    spatial scan plan. Single-shot  with total exposure specified in
    the ``Exposure time`` columns will be executed at the spatial
    points specified in the ``X-position`` and ``Y-position`` columns.
    A set of optional arguments ``crossed``, ``dx`` and ``dy``  can be
    passed so that 4 extra data will be collected with respect at each
    spatial point. An optional wait time between spatial points data can
    also be set to avoid residuals (ghost image). Please see
    ``Examples`` below.

    Parameters
    ----------
    dets : list
        A list of detectors will be triggered in the experiment.
        Note the first three detectors in the list must be in the order
        as "area detector, x-motor, y-motor".
    exp_spreadsheet_fn : str
        filename of the spreadsheet contains sample metadata in each
        well, locations, exposure times and all additional metadata.
        This spread MUST be placed inside ``xpdUser/Import``.
    crossed : bool, optional
        option if to perform a crossed scan in each well. If it's true,
        then at each well (x0, y0), 4 additional data will be collected
        at (x0-dx, y0), (x0+dx, y0), (x0, dy+y0), (x0, y0-dy). Default
        to False.
    dx : float, optional
        offset in x-direction for crossed scan per well. Must be
        a float if ``crossed`` is set to True. Default to None.
    dy : float, optional
        offset in y-direction for crossed scan per well. Must be
        a float if ``crossed`` is set to True. Default to None.
    wait_time : float, optional
        Wait time between each count, default is 5s

    Examples
    --------
    # define a list of detectors will be triggered in the spatial scan
    # plan. The first 3 detectors should be in the sequence of
    # "area_det, x-motor,  y-motor" used in the scan.
    dets = [pe1c, diff_x, diff_y, shctl1]

    # case 1
    # define a plan based on the information entered in the
    # spreadsheet ``wandaHY1_sample.xlsx``.
    # Note, this spreadsheet MUST be placed in the ``Import`` directory
    grid_plan = gridScan(dets,  'wandaHY1_sample.xlsx', wait_time=5)

    # preview the plan to check.
    summarize_plan(grid_plan)

    # redefine the scan plan again then execute the plan.
    grid_plan = gridScan(dets,  'wandaHY1_sample.xlsx', wait_time=5)
    uids = xrun(gridScan_sample, grid_plan)

    # case 2
    # define a grid scan that collects 4 extra points at each spatial
    # point to account for potential inhomogeneity
    grid_plan = gridScan(dets, 'wandaHY1_sample.xlsx', crossed=True,
                         dx=0.2, dy=0.1, wai_time=5)

    # preview the plan to check.
    summarize_plan(grid_plan)

    # redefine the scan plan again then execute the plan.
    grid_plan = gridScan(dets,  'wandaHY1_sample.xlsx', wait_time=5)
    uids = xrun(gridScan_sample, grid_plan)

    # finally, retrieve event information as a dataframe
    hdrs = db[-len(uids):]
    df = db.get_table(hdrs)
    # visualize the dataframe
    df
    # save the dataframe as a csv
    df.to_csv('wandaHY1_spatial_scan_df.csv')

    Notes
    -----
    1. ``gridScan_sample`` used in the example is in fact an empty
      dictionary (and it has been defined in this script as well).
      Sample metadata is handled inside the plan, therefore it's
      simply an auxiliary object.

    2. ``gridScan`` yields a generator so you would need to construct
      it every time after using it. As demonstrated in the Example,
      we redefine the ``grid_plan`` again after printing the summary.
      Similarly, if you wish to execute the same scan plan, you would
      have to repeat the syntax.
    """

    def count_dets(_dets, _full_md):
        _count_plan = bp.count(_dets, md=_full_md)
        _count_plan = bpp.subs_wrapper(_count_plan, LiveTable(_dets))
        _count_plan = bpp.finalize_wrapper(_count_plan,
                                           bps.abs_set(xpd_configuration['shutter'],
                                                       XPD_SHUTTER_CONF['close'],
                                                       wait=True))
        yield from bps.abs_set(xpd_configuration['shutter'], XPD_SHUTTER_CONF['open'], wait=True)
        yield from _count_plan

    # read exp spreadsheet
    spreadsheet_parser = ExceltoYaml(glbl['import_dir'])
    fp = os.path.join(spreadsheet_parser.src_dir, exp_spreadsheet_fn)
    spreadsheet_parser.pd_df = pd.read_excel(fp, skiprows=[1])
    spreadsheet_parser.parse_sample_md()
    # get detectors
    area_det = xpd_configuration['area_det']
    x_motor, y_motor = list(dets)[:2]
    dets = [area_det] + dets
    # compute Nsteps
    _md = {'sp_time_per_frame': None,
           'sp_num_frames': None,
           'sp_requested_exposure': None,
           'sp_computed_exposure': None,
           'sp_type': 'gridScan',
           'sp_uid': str(uuid.uuid4())[:4],
           'sp_plan_name': 'gridScan'}
    # first validate through sa_md list
    for md_dict in spreadsheet_parser.parsed_sa_md_list:
        if not ('x-position' in md_dict and 'y-position' in md_dict and 'exposure_time(s)' in md_dict):
            raise xpdAcqException(
                "either X-position, Y-position "
                "or Exposure time column in {} "
                "row is missing. Please fill it "
                "and rerun".format(md_dict['sample_name'])
            )
    # validate crossed scan
    if crossed and (not dx or not dy):
        raise xpdAcqException("dx and dy must both be provided if crossed is set to True")
    # construct scan plan
    for md_dict in spreadsheet_parser.parsed_sa_md_list:
        expo = float(md_dict['exposure_time(s)'])
        # setting up area_detector
        yield from _configure_area_det(expo)
        expo_md = calc_expo_md(dets[0], expo)
        # inject md for each sample
        full_md = dict(_md)
        full_md.update(expo_md)
        full_md.update(md_dict)
        # Manually open shutter before collecting. See the reason
        # stated below.
        # main plan
        x_center = float(md_dict['x-position'])
        y_center = float(md_dict['y-position'])
        yield from bps.mv(x_motor, x_center)
        yield from bps.mv(y_motor, y_center)
        yield from count_dets(dets, full_md)  # no crossed
        if crossed:
            x_traj = [-dx + x_center, x_center + dx, x_center, x_center]
            y_traj = [y_center, y_center, y_center + dy, y_center - dy]
            for x_setpoint, y_setpoint in zip(x_traj, y_traj):
                yield from bps.mv(x_motor, x_setpoint)
                yield from bps.mv(y_motor, y_setpoint)
                full_md['x-position'] = x_setpoint
                full_md['y-position'] = y_setpoint
                yield from count_dets(dets, full_md)
        # use specified sleep time -> avoid residual from the calibrant
        yield from bps.sleep(wait_time)


def calc_expo_md(det, exposure):
    acq_time = det.cam.acquire_time.get()
    if hasattr(det, "images_per_set"):
        # compute number of frames
        num_frame = np.ceil(exposure / acq_time)
    else:
        # The dexela detector does not support `images_per_set` so we just
        # use whatever the user asks for as the thing
        num_frame = 1
    computed_exposure = num_frame * acq_time
    md = {
        'sp_time_per_frame': acq_time,
        'sp_num_frames': num_frame,
        'sp_requested_exposure': exposure,
        'sp_computed_exposure': computed_exposure
    }
    return md


if __name__ == '__main__':
    print(__doc__)
