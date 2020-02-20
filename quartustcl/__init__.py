import functools
import subprocess
import sys
import time
import tkinter


class QuartusTcl:
    """A class for managing a Quartus Tcl interpreter as a subprocess.

    #### Arguments

    * **args** - the Quartus TCL subshell to launch, in a format
      suitable for `subprocess.Popen`. This defaults to launching
      `quartus_stp`.

    * **debug** - if True, write input and output of the subshell to
      stderr.

    #### Usage

    Communication with the subshell is done via methods. Some simple
    methods are provided, but methods not documented here are turned
    directly into TCL commands. For example:

    ```python
    quartus.get_device_names(hardware_name="Foo Bar")
    ```

    will result in running

    ```tcl
    get_device_names -hardware_name {Foo Bar}
    ```

    All methods (except `interact`) will automatically parse their
    result as a TCL list into a Python list. If the TCL result is a
    single value, this means you will get a Python list with one
    element.

    Nested lists are not parsed, only the top level. If you need to
    parse the components of a nested list, use the `parse` method.

    """
    def __init__(self, args=['quartus_stp', '-s'], debug=False):
        self.debug = debug

        # we need to use some special variables to store and detect errors
        self.errvar = '_python_err_val'
        self.sentinel = '_PYTHON_SENTINEL'

        # we use python's built-in Tcl interpreter to help us parse Tcl lists
        self.tcl = tkinter.Tcl()

        # we launch a single instance of the quartus tcl shell, and then
        # talk to it line by line
        self.process = subprocess.Popen(args,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)

    def interact(self, line):
        """Write one line to the Tcl interpreter, and read the result
        out. This method bypasses the automatic list parsing, so the
        result will always be a string. If the line raises an error,
        that TCL error will be raised in Python as a `RuntimeError`.

        """
        # write a single line to our subprocess
        # wrap it in puts to guarantee at least one newline is output
        unique = str(hash(time.time()))
        parts = dict(
            expr=line,
            errvar=self.errvar,
            sentinel_start=self.sentinel + '_' + unique + '_START',
            sentinel_end=self.sentinel + '_' + unique + '_END',
        )
        cmd = ' '.join("""
        puts "{sentinel_start}";
        if {{[catch {{puts [{expr}]}} {errvar}]}} {{
            puts -nonewline "{sentinel_end} 1 ";
            puts ${errvar};
        }} else {{
            puts "{sentinel_end} 0 success";
        }}
        """.format(**parts).split())
        if self.debug:
            print('(tcl) <<<', line, file=sys.stderr)
        self.process.stdin.write((cmd + '\n').encode())
        self.process.stdin.flush()

        # read the output, which will be introduced with sentinel_start
        # and ended by sentinel_end
        accum = ""
        after_prompt = False
        while True:
            outline = self.process.stdout.readline().decode()
            if not after_prompt and outline.strip() \
                                           .endswith(parts['sentinel_start']):
                after_prompt = True
            elif after_prompt and outline.startswith(parts['sentinel_end']):
                _, err, msg = outline.split(' ', 2)
                if int(err) > 0:
                    raise RuntimeError(msg)
                break
            elif after_prompt:
                if self.debug and outline:
                    print('(tcl) >>>', outline.rstrip(), file=sys.stderr)
                accum += outline
        accum = accum.strip()
        return accum

    def parse(self, data):
        """Parse a Tcl-formatted list into a Python list. This only works on
        the top-level of a list -- if you need to parse nested lists,
        you will need to call this multiple times.

        """
        data = data.strip()
        # first, make sure the list is canonically formatted
        try:
            data = '{' + self.tcl.eval('list ' + data) + '}'
        except Exception:
            raise RuntimeError('Tcl list could not be parsed: ' + repr(data))
        # what is the length of the list?
        length = int(self.tcl.eval('llength {}'.format(data)))

        # iterate through each item, and add it to our python list
        parsed = []
        for i in range(length):
            # get the i'th element...
            part = self.tcl.eval('lindex {} {}'.format(data, i))
            parsed.append(part)
        return parsed

    def run(self, cmd, *args):
        """Run a Tcl command, and parse and return the resulting list. If an
        error is raised, it is re-raised in Python as a
        `RuntimeError`.

        **cmd** can be a format string, which will be filled out with the
        remaining arguments. If used this way, the remaining arguments are
        quoted in Tcl using {...}. For example:

        ```python
        quartus.run("get_device_names -hardware_name {}", "Foo Bar")
        ```

        will result in running

        ```tcl
        get_device_names -hardware_name {Foo Bar}
        ```

        in the Tcl interpreter subprocess. If you do not want this
        automatic quoting, you can use the usual format() method on
        strings.

        """
        # construct the full command by formatting-in our later arguments
        # but -- quote them in braces first!
        if args:
            cmd = cmd.format(*['{' + str(a) + '}' for a in args])

        return self.parse(self.interact(cmd))

    def run_args(self, cmd, *args, **kwargs):
        """Run a Tcl command with the given arguments and optional arguments,
        then parse and return the resulting list. If an error is
        raised, it is re-raised in Python as a `RuntimeError`.

        **cmd** is a bare Tcl command. For example:

        ```python
        quartus.run_args('get_device_names', hardware_name="Foo Bar")
        ```

        will result in running

        ```tcl
        get_device_names -hardware_name {Foo Bar}
        ```

        """
        args = [cmd] + ['{' + str(a) + '}' for a in args]
        for k, v in kwargs.items():
            args.append('-' + k)
            args.append('{' + str(v) + '}')
        return self.run(' '.join(args))

    def __getattr__(self, attr):
        return functools.partial(self.run_args, attr)
