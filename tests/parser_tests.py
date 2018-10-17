from dadabot.commandparser import *
import unittest


class ParseMatchTest(unittest.TestCase):
    def test_simple(self):
        cmd = 'match\na\nb\nc\n\nd\ne'
        output = {'match': ["a", "b", "c"],
                  'responses': ["d", "e"]}
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_multiline(self):
        cmd = 'match\na\nb/\nc/\nd\n\ne/\nf\ng'
        output = {'match': ["a", "bcd"],
                  'responses': ["ef", "g"]}
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_multiline_empty(self):
        cmd = 'match\na\nb/\n\nc\n\nd/\ne'
        output = {'match': ["a", "b", "c"],
                  'responses': ["de"]}
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_double_empty(self):
        cmd = 'match\na\nb\n\nc\n\nd\ne'
        output = None
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_no_match(self):
        cmd = 'match\n\n\nd\ne'
        output = None
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_no_responses(self):
        cmd = 'match\n\n\nd\ne'
        output = None
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_only_slash(self):
        cmd = 'match\n/\n/\n/\n\n\n/\n/\n\n/\n\n'
        output = {'match': [''],
                  'responses': ['', '']}
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)

    def test_no_separator(self):
        cmd = 'match\na\nb\nc\nd\ne'
        output = None
        r = parse_match(cmd.splitlines())
        self.assertEqual(r, output)


class ParseAddTest(unittest.TestCase):
    def test_simple(self):
        cmd = 'addwords 789\na\nb\nc'
        output = {'id': 789,
                  'words': ['a', 'b', 'c']}
        r = parse_add(cmd.splitlines())
        self.assertEqual(r, output)

    def test_multiline(self):
        cmd = 'addwords 789\na/\nb\nc'
        output = {'id': 789,
                  'words': ['ab', 'c']}
        r = parse_add(cmd.splitlines())
        self.assertEqual(r, output)

    def test_no_id(self):
        cmd = 'addwords \na\nb\nc'
        output = None
        r = parse_add(cmd.splitlines())
        self.assertEqual(r, output)

    def test_no_words(self):
        cmd = 'addwords 545 \n'
        output = None
        r = parse_add(cmd.splitlines())
        self.assertEqual(r, output)


unittest.main()
