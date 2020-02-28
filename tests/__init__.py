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
            make_tcl().parse('broken {')
        self.assertRaises(quartustcl.TclParseError, fail)

    def test_parse_nested(self):
        data = make_tcl().parse('{1 2} {3 4} {5 6}', levels=2)
        self.assertEqual(data, [['1', '2'], ['3', '4'], ['5', '6']])


class TestEval(unittest.TestCase):
    def test_eval(self):
        data = make_tcl().eval('expr 1 + 2')
        self.assertEqual(data, '3')

    def test_eval_args(self):
        data = make_tcl().eval('expr {} + {}', 1, 2)
        self.assertEqual(data, '3')

    def test_call(self):
        data = make_tcl().call('expr', 1, '+', 2)
        self.assertEqual(data, '3')

    def test_getattr(self):
        data = make_tcl().expr(1, '+', 2)
        self.assertEqual(data, '3')

    def test_error(self):
        def div_zero():
            make_tcl().expr(1, '/', 0)
        self.assertRaises(quartustcl.TclError, div_zero)

    def test_interact_error(self):
        def unbalanced_braces():
            make_tcl().eval('expr 1 + 2 {')
        self.assertRaises(quartustcl.TclError, unbalanced_braces)


class TestQuote(unittest.TestCase):
    def test_quote_eval(self):
        original = ['x', r'ugly \{} $var [hello]', '$just [vars]']
        q = make_tcl()
        data = q.parse(q.eval('list {} {} {}', *original))
        self.assertEqual(data, original)

    def test_quote_call(self):
        original = ['x', r'ugly \{} $var [hello]', '$just [vars]']
        q = make_tcl()
        data = q.parse(q.call('list', *original))
        self.assertEqual(data, original)
