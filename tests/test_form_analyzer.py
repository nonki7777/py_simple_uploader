# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import os
import unittest
import mock
import tempfile
import random
import fileupl
import logging


logging.basicConfig(filename='test.log', level=logging.DEBUG,
        filemode='w')


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
        fa = fileupl.FormAnalyzer()
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

        fa = fileupl.FormAnalyzer()
        self.assertRaises(TypeError, lambda: fa.do_upload(None, None))
            # 2nd arg must be str

        self.assertFalse(file_maxsize(0))
        self.assertFalse(file_maxsize(3))
        self.assertFalse(file_maxsize(1024 + 1))
        self.assertFalse(file_maxsize(1024 * (fileupl.up_limit - 1)))
        self.assertTrue(file_maxsize(1024 * (fileupl.up_limit - 1) + 1))

    @mock.patch('fileupl.remove')
    @mock.patch('fileupl.listdir')
    def test_delete_oldest(self, listdir, remove):

        list_dirs = []

        def make_list(num):
            LIST_DIRS = []
            for i in xrange(num):
                s = str(random.randint(1, 100000))
                if s not in LIST_DIRS:
                    LIST_DIRS.append(s)
            return LIST_DIRS

        def mremove(x):
            base, ext = os.path.splitext(x)
            if ext == '.txt':
                logging.debug('mremove: 1 deleted.')
                listdir.return_value = list_dirs.pop()

        list_dirs = make_list(fileupl.maxfilenum)
        listdir.return_value = list_dirs
        remove.side_effect = mremove
        fa = fileupl.FormAnalyzer()
        logging.debug('before delete_oldest')
        logging.debug(list_dirs)
        logging.debug('len = %d' % len(list_dirs))
        fa.delete_oldest()
        logging.debug('after delete_oldest')
        logging.debug(list_dirs)
        logging.debug('len = %d' % len(list_dirs))
        self.assertTrue(len(list_dirs) == fileupl.maxfilenum)

        list_dirs = make_list(fileupl.maxfilenum + 1)
        listdir.return_value = list_dirs
        remove.side_effect = mremove
        fa = fileupl.FormAnalyzer()
        rs = fileupl.listdir('.')
        logging.debug('fileupl.listdir')
        logging.debug(rs)
        logging.debug('before delete_oldest')
        logging.debug(list_dirs)
        logging.debug('len = %d' % len(list_dirs))
        fa.delete_oldest()
        logging.debug('after delete_oldest')
        logging.debug(list_dirs)
        logging.debug('len = %d' % len(list_dirs))
        self.assertTrue(len(list_dirs) == fileupl.maxfilenum)

    @mock.patch('__builtin__._')
    @mock.patch('fileupl.FormAnalyzer.do_upload')
    @mock.patch('fileupl.remove')
    @mock.patch('fileupl.isfileimage')
    @mock.patch('fileupl.writedirfile')
    @mock.patch('fileupl.FormAnalyzer.delete_oldest')
    def test_save_uploaded_file(self, delete_oldest, writedirfile,
            isfileimage, remove, do_upload, m_):
        delete_oldest.return_value = True
        writedirfile.return_value = True
        isfileimage.return_value = True
        remove.return_value = True
        do_upload.return_value = True
        def _(message): return message
        m_.side_effect = _

        mitem = mock.Mock()

        mitem.file = ''
        m1 = dict(file=mitem, author=None)
        logging.debug('mitem.file')
        logging.debug(mitem.file)
        fa = fileupl.FormAnalyzer()
        self.assertEqual(fa.save_uploaded_file(m1),
                _('No uploading file name specified.'))

        mitem.file = 1
        mitem.filename = '/home/foo/mocktest.txt'
        self.assertEqual(fa.save_uploaded_file(m1),
                _('File extension not allowed.'))
        # mitem = mock.Mock()
        # mitem.file = 1
        # mitem.filename = '/home/foo/mocktest.jpg'
        # mform = mock.Mock()
        # mform


if __name__ == "__main__":
    unittest.main()
