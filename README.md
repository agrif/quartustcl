quartustcl
----------

[![PyPI](https://img.shields.io/pypi/v/quartustcl)](https://pypi.org/project/quartustcl/)
[![Travis CI](https://img.shields.io/travis/com/agrif/quartustcl/master)](https://travis-ci.com/agrif/quartustcl)
[![Read the Docs](https://img.shields.io/readthedocs/quartustcl/latest)][docs]

 [docs]: https://quartustcl.readthedocs.io/en/latest/

`quartustcl` is a Python module to interact with Intel Quartus Tcl
shells. It opens a single shell in a subprocess, then helps you with
reading and writing data to it, and parsing Tcl lists.

## Installation

Install via `pip`:

```bash
pip install quartustcl
```

## Demo

You can start a demo Python REPL by running the package as a script:
```bash
python3 -m quartustcl
```

The *quartustcl* subshell is exposed in a variable named `quartus`.

## Basic Use

Instantiate a `QuartusTcl` object to start a shell. Then, call methods
on it.

```python
quartus = quartustcl.QuartusTcl()
three = quartus.expr('1 + 2')
assert three == '3'
```

If you are expecting a list as a result, use `parse` to turn Tcl lists
into Python lists.

```python
devnames = quartus.parse(quartus.get_device_names(hardware_name="Foo Bar"))
```

In the Tcl subshell, this runs
```tcl
get_device_names -hardware_name {Foo Bar}
```
and parses the result into a Python list.

For more detailed information, please [read the documentation][docs].
