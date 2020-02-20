# Introduction

`quartustcl` is a Python module to interact with Intel Quartus TCL
shells. It opens a single shell in a subprocess, then helps you with
reading and writing data to it, and parsing TCL lists.

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
on it to get automatically-parsed TCL lists:

```python
quartus = quartustcl.QuartusTcl()
devnames = quartus.get_device_names(hardware_name="Foo Bar")
```

In the TCL subshell, this runs
```tcl
get_device_names -hardware_name {Foo Bar}
```
and parses the result into a Python list.

Since *quartustcl* assumes all results will be lists, you will instead
receive a list of one item if the result is a single value. This
decision to automatically parse results as lists was a usability
trade-off.

Note that only top-level lists are automatically parsed. If your
result contains nested lists, you will need to parse them manually
with the `parse` method:

```python
for element in quartus.parse(data_from_tcl):
    ...
```

For more information, including more ways to interact with the TCL
subprocess, see [the reference documentation](reference).
