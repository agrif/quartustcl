import unittest

import quartustcl


def make_tcl():
    return quartustcl.QuartusTcl(args=['tclsh'])


class TestParse(unittest.TestCase):
    def test_parse(self):
        data = make_tcl().parse('1 2 3')
        self.assertEqual(data, ['1', '2', '3'])

    def test_parse_quotes(self):
        data = make_tcl().parse('"hello world" 2 3')
        self.assertEqual(data, ['hello world', '2', '3'])

    def test_parse_fail(self):
        with self.assertRaises(quartustcl.TclParseError):
            make_tcl().parse('broken {')

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
        with self.assertRaises(quartustcl.TclEvalError):
            make_tcl().expr(1, '/', 0)

    def test_interact_error(self):
        with self.assertRaises(quartustcl.TclEvalError):
            make_tcl().eval('expr 1 + 2 {')


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


class TestClose(unittest.TestCase):
    def test_close(self):
        q = make_tcl()
        self.assertEqual(q.expr('1 + 2'), '3')
        q.close()
        with self.assertRaises(ValueError):
            q.expr('1 + 2')
        q.close()

    def test_with(self):
        tcl = make_tcl()
        with tcl as q:
            self.assertEqual(q.expr('1 + 2'), '3')
        with self.assertRaises(ValueError):
            tcl.expr('1 + 2')
