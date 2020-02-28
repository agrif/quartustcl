import argparse
import code

import quartustcl

parser = argparse.ArgumentParser(
    description='Spawn an interactive python shell on top of a Tcl shell.')
parser.add_argument('-d', '--debug', action='store_true',
                    help='display input and output to Tcl shell')
parser.add_argument('-c', '--command', type=str,
                    help='run a command, then exit')
parser.add_argument('subprocess', nargs='*',
                    help='the Tcl shell to use')

args = parser.parse_args()
kwargs = {
    'debug': args.debug,
}
if args.subprocess:
    kwargs['args'] = args.subprocess

quartus = quartustcl.QuartusTcl(**kwargs)

if args.command:
    print(repr(eval(args.command)))
else:
    banner = 'the local variable `quartus` is a running QuartusTcl session'
    code.interact(local=locals(), banner=banner)
