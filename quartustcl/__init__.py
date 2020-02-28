import functools
import subprocess
import sys
import time
import tkinter


class TclError(Exception):
    """This error is raised whenever the Tcl subprocess encounters an
    error. It exposes four attributes:

    * **message** - the cause of the error, as a human-friendly string

    * **return_code** - the Tcl return code of the command, as an
      integer

    * **error_code** - the cause of the error, as a machine-friendly
      list. This is parsed directly from `$errorCode` inside Tcl.

    * **error_info** - the cause of the error, as a longer
      human-friendly string.  This is parsed directly from
      `$errorInfo` inside Tcl.

    """
    def __init__(self, message, return_code, error_code, error_info):
        super().__init__(message)
        self.message = message
        self.return_code = return_code
        self.error_code = error_code
        self.error_info = error_info

    def __repr__(self):
        return '{}({!r}, {!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.message,
            self.return_code,
            self.error_code,
            self.error_info,
        )


class TclParseError(Exception):
    """This error is raised by `QuartusTcl.parse` when Python attempts to
    parse something as a list that is not actually a list.

    """

    def __init__(self, message):
        super().__init__(message)


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

        # we need to use some special variables to use with catch
        # and detect output phases
        self.var = '_python_val'
        self.retcode = '_python_ret_code'
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
        that TCL error will be raised in Python as a `TclError`.

        """
        # write a single line to our subprocess
        # wrap it in puts to guarantee at least one newline is output
        unique = str(hash(time.time()))
        parts = dict(
            expr=self.quote(line),
            var=self.var,
            retcode=self.retcode,
            sentinel_start=self.sentinel + '_' + unique + '_START',
            sentinel_middle=self.sentinel + '_' + unique + '_MIDDLE',
            sentinel_end=self.sentinel + '_' + unique + '_END',
        )
        cmd = ' '.join("""
        puts "{sentinel_start}";
        if {{[set {retcode} [catch {expr} {var}]]}} {{
            puts [list "{sentinel_middle}" ${retcode} ${var}
                  $errorCode $errorInfo];
        }} else {{
            puts [list "{sentinel_middle}" ${retcode} ${var}];
        }};
        puts "{sentinel_end}";
        """.format(**parts).split())
        if self.debug:
            print('(tcl) <<<', line, file=sys.stderr)
        self.process.stdin.write((cmd + '\n').encode())
        self.process.stdin.flush()

        # read the output, which will be introduced with sentinel_start
        # and ended by sentinel_end
        accum = ""
        accum_end = ""
        error = 0
        state = 0
        while True:
            outline = self.process.stdout.readline().decode()
            if state == 0 and outline.strip() \
                                     .endswith(parts['sentinel_start']):
                state = 1
            elif state == 1 and outline.startswith(parts['sentinel_middle']):
                accum_end += outline
                _, error, extra = outline.split(' ', 2)
                error = int(error)
                state = 2
                if self.debug and extra and not error:
                    print('(tcl) >>>', extra.rstrip(), file=sys.stderr)
            elif state == 1:
                if self.debug and outline:
                    print('(tcl) >>>', outline.rstrip(), file=sys.stderr)
                accum += outline
            elif state == 2 and outline.startswith(parts['sentinel_end']):
                break
            elif state == 2:
                if self.debug and outline and not error:
                    print('(tcl) >>>', outline.rstrip(), file=sys.stderr)
                accum_end += outline

        _, retcode, *data = self.parse(accum_end)
        retcode = int(retcode)
        if retcode > 0:
            message, code, info = data
            raise TclError(message, retcode, self.parse(code), info)
        else:
            # stdout is in accum
            return data[0]

    def parse(self, data):
        """Parse a Tcl-formatted list into a Python list. This only works on
        the top-level of a list -- if you need to parse nested lists,
        you will need to call this multiple times.

        If parsing fails, this will raise `TclParseError`.

        """
        data = data.strip()
        # first, make sure the list is canonically formatted
        try:
            data = '{' + self.tcl.eval('list ' + data) + '}'
        except Exception:
            raise TclParseError('Tcl list could not be parsed: ' + repr(data))
        # what is the length of the list?
        length = int(self.tcl.eval('llength {}'.format(data)))

        # iterate through each item, and add it to our python list
        parsed = []
        for i in range(length):
            # get the i'th element...
            part = self.tcl.eval('lindex {} {}'.format(data, i))
            parsed.append(part)
        return parsed

    def quote(self, data):
        """Wrap a string in the Tcl necessary for it to evaluate to the
        original string. For example:

        ```python
        quartus.run("puts " + quartus.quote("$var [{]"))
        ```

        will result in printing the string "$var [{]" to standard
        out. This is required to work around reserved syntax in the
        Tcl language.

        """
        # https://stackoverflow.com/a/5302213
        if any(c in data for c in '{}'):
            escaped = data.replace('\\', '\\\\') \
                          .replace('{', '\\{')   \
                          .replace('}', '\\}')
            return '[subst -nocommands -novariables {{{}}}]'.format(escaped)
        else:
            return '{{{}}}'.format(data)

    def run(self, cmd, *args):
        """Run a Tcl command, and parse and return the resulting list. If an
        error is raised, it is re-raised in Python as a
        `TclError`.

        **cmd** can be a format string, which will be filled out with the
        remaining arguments. If used this way, the remaining arguments are
        quoted using `quote`. For example:

        ```python
        quartus.run("get_device_names -hardware_name {}", "Foo Bar")
        ```

        is equivalent to running

        ```tcl
        get_device_names -hardware_name {Foo Bar}
        ```

        in the Tcl interpreter subprocess. If you do not want this
        automatic quoting, you can use the usual format() method on
        strings.

        """
        # construct the full command by formatting-in our later arguments
        # but -- quote them first!
        if args:
            cmd = cmd.format(*[self.quote(str(a)) for a in args])

        return self.parse(self.interact(cmd))

    def run_args(self, cmd, *args, **kwargs):
        """Run a Tcl command with the given arguments and optional arguments,
        then parse and return the resulting list. If an error is
        raised, it is re-raised in Python as a `TclError`.

        **cmd** is a bare Tcl command. For example:

        ```python
        quartus.run_args('get_device_names', hardware_name="Foo Bar")
        ```

        is equivalent to running

        ```tcl
        get_device_names -hardware_name {Foo Bar}
        ```

        """
        args = [cmd] + [self.quote(str(a)) for a in args]
        for k, v in kwargs.items():
            args.append('-' + k)
            args.append(self.quote(str(v)))
        return self.run(' '.join(args))

    def __getattr__(self, attr):
        return functools.partial(self.run_args, attr)
