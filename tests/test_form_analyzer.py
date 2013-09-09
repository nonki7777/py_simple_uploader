# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import unittest
from mock import patch
import tempfile
from fileupl import FormAnalyzer, up_limit


def open_temp_file(size=128):
    """Makes a temporary file with specified size and returns a handle.
    Note: the temporary files will NOT be deleted automatically.
    """
    fh = tempfile.NamedTemporaryFile(delete=False)
    fname = fh.name
    fh.write('a' * size)
    fh.close()
    return open(fname, 'rb')


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

    def test_do_upload(self):

        def file_maxsize(size):
            wb = open_temp_file()
            fpath = wb.name
            wb.close()
            os.remove(wb.name)
            uplb = open_temp_file(size)
            reachmax = fa.do_upload(uplb, fpath)
            uplb.close()
            os.remove(uplb.name)
            os.remove(fpath)
            return reachmax

        fa = FormAnalyzer()
        self.assertRaises(TypeError, lambda: fa.do_upload(None, None))
            # 2nd arg must be str

        self.assertFalse(file_maxsize(0))
        self.assertFalse(file_maxsize(3))
        self.assertFalse(file_maxsize(1024 + 1))
        self.assertFalse(file_maxsize(1024 * (up_limit - 1)))
        self.assertTrue(file_maxsize(1024 * (up_limit - 1) + 1))
        

if __name__ == "__main__":
    unittest.main()
