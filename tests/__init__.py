import unittest

import quartustcl


quartus = None


def make_tcl():
    global quartus
    if quartus is None:
        quartus = quartustcl.QuartusTcl(args=['tclsh'])
    return quartus


class TestParse(unittest.TestCase):
    def test_parse(self):
        data = make_tcl().parse('1 2 3')
        self.assertEqual(data, ['1', '2', '3'])

    def test_parse_quotes(self):
        data = make_tcl().parse('"hello world" 2 3')
        self.assertEqual(data, ['hello world', '2', '3'])

    def test_parse_fail(self):
        def fail():
            print(make_tcl().parse('broken {'))
        self.assertRaises(quartustcl.TclParseError, fail)


class TestEval(unittest.TestCase):
    def test_interact(self):
        data = make_tcl().interact('expr 1 + 2')
        self.assertEqual(data, '3')

    def test_run(self):
        data = make_tcl().run('expr {} + {}', 1, 2)
        self.assertEqual(data, ['3'])

    def test_run_args(self):
        data = make_tcl().run_args('expr', 1, '+', 2)
        self.assertEqual(data, ['3'])

    def test_getattr(self):
        data = make_tcl().expr(1, '+', 2)
        self.assertEqual(data, ['3'])

    def test_error(self):
        def div_zero():
            make_tcl().expr(1, '/', 0)
        self.assertRaises(quartustcl.TclError, div_zero)
