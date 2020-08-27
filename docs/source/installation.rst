============
Installation
============

For users
---------

At the command line::

    $ conda config --append channels nsls2forge
    $ conda config --append channels conda-forge
    $ conda create -n use_scanplans --file requirements/build.txt --file requirements/run.txt
    $ conda activate use_scanplans
    $ pip install scanplans

For developers
--------------

At the command line::

    $ conda config --append channels nsls2forge
    $ conda config --append channels conda-forge
    $ conda create -n use_scanplans --file requirements/build.txt --file requirements/run.txt --file requirements/test.txt --file requirements/docs.txt
    $ conda activate use_scanplans
    $ git clone git@github.com:<your_account>/bluesky_scanplans.git
    $ python -m pip install -e bluesky_scanplans

