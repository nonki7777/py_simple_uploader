# -*- coding: utf-8 -*-

from __future__ import print_function

import unittest
from fileupl import FormAnalyzer


class TestFormAnalyzer(unittest.TestCase):

    def test_chkExt(self):
        fa = FormAnalyzer()
        goodlist = (".jpg", ".jpeg", ".png", ".gif")
        badlist = ("jpg", ".txt", ".gif2", "a.gif")
        for a in goodlist:
            t = fa.chkExt(a)
            self.assertTrue(t)
        for b in badlist:
            f = fa.chkExt(b)
            self.assertTrue(not f)
    

if __name__ == "__main__":
    unittest.main()
