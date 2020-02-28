# Example: In-System Memory Editing

As a working example, we will use *quartustcl* together with the [mif
Python package][mif] to read and write editable memories on a
connected FPGA.

 [mif]: https://mif.readthedocs.io/en/latest/

To work through this example, you will need to install both of these
packages with `pip` on the command line.
```bash
pip install --upgrade mif quartustcl
```

Then, in any Python program or session where you use these packages:
```python
import mif
import quartustcl
```

## Finding Your Hardware

The documentation for the [Quartus memory editing package][memedit]
tells us that [`begin_memory_edit`][bme] needs a hardware and device name,
which can be obtained using [the Quartus JTAG package][jtag]. Both of
these packages are available in `quartus_stp`, which happens to be the
default Tcl shell for *quartustcl*.
```python
quartus = quartustcl.QuartusTcl()
```

 [memedit]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_insystem_memory_edit_ver_1.0.htm
 [jtag]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_jtag_ver_1.0.htm
 [bme]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_insystem_memory_edit_ver_1.0_cmd_begin_memory_edit.htm

The documentation says [`get_hardware_names`][ghn] returns a
list. Normally, *quartustcl* returns only strings. To parse lists, we
need to use `parse`. So, calling [`get_hardware_names`][ghn] in Python
looks like this:
```python
hwnames = quartus.parse(quartus.get_hardware_names())
hwname = hwnames[0]
```

 [ghn]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_jtag_ver_1.0_cmd_get_hardware_names.htm

Normally, you would want some way to decide which connected hardware
to use, but for the example we will just use the first one.

Next, we can use [`get_device_names`][gdn] to get the devices connected to a
given piece of hardware. The documentation tells us that the Tcl
syntax for this command is `get_device_names -hardware_name <name>`,
and it returns a list. In Python, that looks like this:
```python
devnames = quartus.parse(quartus.get_device_names(hardware_name=hwname))
devname = devnames[0]
```

 [gdn]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_jtag_ver_1.0_cmd_get_device_names.htm

## Finding Editable Memories

Now we can use [`get_editable_mem_instances`][gemi] to find the
editable memories on our chosen device. The documentation for this
command tells us that it returns a list of memory instance
descriptions, which are themselves lists. This "list of lists" can be
parsed at once with the `levels` argument to `parse`.
```python
memories_raw = quartus.get_editable_mem_instances(
    hardware_name=hwname, device_name=devname)

memories = quartus.parse(memories_raw, levels=2)
```

 [gemi]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_insystem_memory_edit_ver_1.0_cmd_get_editable_mem_instances.htm

Now we can search through these memories to find the ID of one we
want. For example, to find the memory named `CTRL`:
```python
found_memid = None
for memid, depth, width, rw, type, name in memories:
    if name == 'CTRL':
        found_memid = memid

if found_memid is None:
    raise RuntimeError('could not find memory CTRL')
```

Note that `parse` only parses Tcl lists, and makes no attempt to parse
values into integers or other types. This means `memid` and the other
variables are all strings. This will not matter for this example, but
it can for other tasks.

## Reading and Writing Memories

Now we can finally start the memory edit:
```python
quartus.begin_memory_edit(hardware_name=hwname, device_name=devname)
```

We can read the current contents into a MIF file named *contents.mif*
with [`save_content_from_memory_to_file`][scfmtf].
```python
quartus.save_content_from_memory_to_file(
    instance_index=found_memid,
    mem_file_path='contents.mif',
    mem_file_type='mif',
)
```

 [scfmtf]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_insystem_memory_edit_ver_1.0_cmd_save_content_from_memory_to_file.htm

Using the [mif package][mif], we can load that data into a Python
array, and modify it.
```python
with open('contents.mif') as f:
    data = mif.load(f)

# set least-significant bit of address 0x01 to 1
data[0x01][0] = 1
```

Now that it's modified, we can write it out and upload it to the
device using [`update_content_to_memory_from_file`][uctmff].
```python
with open('contents.mif', 'w') as f:
    mif.dump(data, f)

quartus.update_content_to_memory_from_file(
    instance_index=found_memid,
    mem_file_path='contents.mif',
    mem_file_type='mif',
)
```

 [uctmff]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_insystem_memory_edit_ver_1.0_cmd_update_content_to_memory_from_file.htm

Finally, we end the transaction with [`end_memory_edit`][emm].
```python
quartus.end_memory_edit()
```

 [emm]: https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/tafs/tafs/tcl_pkg_insystem_memory_edit_ver_1.0_cmd_end_memory_edit.htm
