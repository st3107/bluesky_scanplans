import os
import pyFAI

def calib_map_gen(calib_file_dir, ext='.poni'):
    """helper function to generate a calib map dict
    with key as the file sequence and name as the calib info

    Note: the file sequence will respect nature ``sort`` function
    """
    fns = [x for x in os.listdir(calib_file_dir) if x.endswith(ext)]
    rv = {}
    for i, fn in enumerate(fns):
        print('{} --> {}'.format(i, fn))
        rv[i] = dict(pyFAI.load(fn).getPyFAI())
    return rv
