======
zardoz
======


.. image:: https://img.shields.io/pypi/v/zardoz.svg
        :target: https://pypi.python.org/pypi/zardoz

.. image:: https://img.shields.io/travis/camillescott/zardoz.svg
        :target: https://travis-ci.com/camillescott/zardoz

.. image:: https://readthedocs.org/projects/zardoz/badge/?version=latest
        :target: https://zardoz.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Another dice bot for discord.

* Free software: MIT license
* Documentation: https://zardoz.readthedocs.io.


Features
--------

* Complex roll options provided via `python-dice <https://github.com/borntyping/python-dice#notation>`_
* Multiple game types to provide fast default dice rolls (ie, `1d100` represented by `r` in Rogue
  Trader mode)
* Reports degrees of success or failure when in RT mode, or success or failure otherwise, when using
  comparison operators
* Stores roll history for server

Examples
--------

For a basic roll, ``/z 1d100``::

    Request:
    1d100
    Rolled out:
    {1d100 ⤳ 53}
    Result:
    [53]

Multiple dice, ``/z 3d100``::

    Request:
    3d100
    Rolled out:
    {3d100 ⤳ [27, 83, 73]}
    Result:
    [27, 83, 73]

Distributed addition and subtraction, ``/z 3d100 + 10``::

    Request:
    3d100 + 10
    Rolled out:
    {3d100 ⤳ [47, 30, 19]} + 10
    Result:
    [57, 40, 29]

Comparisons::

    Request:
    4d6 <= 4
    Rolled out:
    {4d6 ⤳ [6, 2, 4, 2]} <= 4
    Result:
    6 ⤳ failed by 2
    2 ⤳ succeeded by 2
    4 ⤳ succeeded by 0
    2 ⤳ succeeded by 2

DoF/Dos, ``/z 3d100 <= 50``::

    Request:
    3d100 <= 50
    Rolled out:
    {3d100 ⤳ [57, 11, 88]} <= 50
    Result:
    57 ⤳ failure
    11 ⤳ 3 DoS
    88 ⤳ 3 DoF

Order of operations, ``/z 3d100 <= 50 + 5``::

    Request:
    3d100 <= 50 + 5
    Rolled out:
    {3d100 ⤳ [75, 87, 55]} <= 50 + 5
    Result:
    75 ⤳ 2 DoF
    87 ⤳ 3 DoF
    55 ⤳ success

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
