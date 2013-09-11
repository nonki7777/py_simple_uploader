# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import os
import unittest
import mock
import tempfile
import random
import fileupl
import logging


logging.basicConfig(filename='test2.log', level=logging.DEBUG,
        filemode='w')


class TestHTMLBuilder(unittest.TestCase):
    @mock.patch('fileupl.HTMLBuilder.html_header')
    @mock.patch('fileupl.HTMLBuilder.html_refresh')
    @mock.patch('fileupl.HTMLBuilder.html_normal')
    def test_run(self, html_normal, html_refresh, html_header):
        self.normal = False
        self.refresh = False
        self.header = False
        def nrml(a): self.normal = True
        html_normal.side_effect = nrml
        def rfrsh(a): self.refresh = True
        html_refresh.side_effect = rfrsh
        def hdr(): self.header = True
        html_header.side_effect = hdr
        hb = fileupl.HTMLBuilder()
        hb.run(1, 2, True)
        self.assertTrue(self.header)
        self.assertTrue(self.refresh)
        self.assertFalse(self.normal)
        self.refresh = False
        self.header = False
        hb.run(1, 2, False)
        self.assertTrue(self.header)
        self.assertFalse(self.refresh)
        self.assertTrue(self.normal)
