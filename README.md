quartustcl
----------

[![PyPI](https://img.shields.io/pypi/v/quartustcl)](https://pypi.org/project/quartustcl/)
[![Travis CI](https://img.shields.io/travis/com/agrif/quartustcl/master)](https://travis-ci.com/agrif/quartustcl)
[![Read the Docs](https://img.shields.io/readthedocs/quartustcl/latest)][docs]

 [docs]: https://quartustcl.readthedocs.io/en/latest/

`quartustcl` is a Python module to interact with Intel Quartus TCL
shells. It opens a single shell in a subprocess, then helps you with
reading and writing data to it, and parsing TCL lists.

## Installation

Install via `pip`:

```bash
pip install quartustcl
```

## Basic Use

Instantiate a `QuartusTcl` object to start a shell. Then, call methods on it to get automatically-parsed TCL lists:

```python
quartus = quartustcl.QuartusTcl()
devnames = quartus.get_device_names(hardware_name="Foo Bar")
```

In the TCL subshell, this runs
```tcl
get_device_names -hardware_name {Foo Bar}
```
and parses the result into a Python list.

For more detailed information, please [read the documentation][docs].
