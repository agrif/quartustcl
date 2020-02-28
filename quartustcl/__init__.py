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

    def __init__(self, value):
        super().__init__(value)


class QuartusTcl:
    """A class for managing a Quartus Tcl interpreter as a subprocess.

    #### Arguments

    * **args** - the Quartus Tcl subshell to launch, in a format
      suitable for `subprocess.Popen`. This defaults to launching
      `quartus_stp`.

    * **debug** - if True, write input and output of the subshell to
      stderr.

    #### Usage

    Communication with the subshell is done via methods. Some simple
    methods are provided, but methods not documented here are turned
    directly into Tcl commands. For example:

    ```python
    quartus.get_device_names(hardware_name="Foo Bar")
    ```

    will result in running

    ```tcl
    get_device_names -hardware_name {Foo Bar}
    ```

    All methods will return their result as a string. If the Tcl
    result is a list, you will need to use `parse` to turn it into a
    Python list.

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

    def eval(self, script, *args):
        """Write a script to the Tcl interpreter, and read the result out as a
        string. If the script raises an error, that Tcl error will be
        raised in Python as a `TclError`.

        **script** can be a format string, which will be filled out with the
        remaining arguments. If used this way, the remaining arguments are
        quoted using `quote`. For example:

        ```python
        quartus.eval("get_device_names -hardware_name {}", "Foo Bar")
        ```

        is equivalent to running

        ```tcl
        get_device_names -hardware_name {Foo Bar}
        ```

        in the Tcl interpreter subprocess. If you do not want this
        automatic quoting, you can use the usual format() method on
        strings.

        """

        # if we have any extra args, do the formatting and try again
        if args:
            return self.eval(script.format(
                *[self.quote(str(a)) for a in args]))

        # write a single line to our subprocess
        # wrap it in some code to detect and report errors and results
        unique = str(hash(time.time()))
        parts = dict(
            expr=self.quote(script),
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
            print('(tcl) <<<', script, file=sys.stderr)
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

    def parse(self, data, levels=1):
        """Parse a Tcl-formatted list into a Python list.

        If **levels** is specified, this sets how many levels of the
        list to convert. If you know you are dealing with nested lists
        two levels deep, use `levels=2` to parse both in one call.

        If parsing fails, this will raise `TclParseError`.

        """
        if levels <= 0:
            return data

        parsed = []
        try:
            parts = self.tcl.call('lrange', data, 0, 'end')
        except Exception:
            raise TclParseError(data) from None

        for part in parts:
            if levels > 1:
                part = self.parse(part, levels=levels - 1)
            parsed.append(part)

        return parsed

    def quote(self, data):
        """Wrap a string in the Tcl necessary for it to evaluate to the
        original string. For example:

        ```python
        quartus.eval("puts " + quartus.quote("$var [{]"))
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

    def call(self, cmd, *args, **kwargs):
        """Run a Tcl command with the given arguments and optional arguments,
        then return the resulting string. If an error is raised, it is
        re-raised in Python as a `TclError`.

        **cmd** is a bare Tcl command. For example:

        ```python
        quartus.call('get_device_names', hardware_name="Foo Bar")
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
        return self.eval(' '.join(args))

    def __getattr__(self, attr):
        return functools.partial(self.call, attr)
