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
    class TestField(object):
        def __init__(self, value):
            self.value = value

    fields = { "file": TestField("foo") }

    @mock.patch('__builtin__._')
    @mock.patch('fileupl.FormAnalyzer.save_uploaded_file')
    @mock.patch('fileupl.FormAnalyzer.delete_saved_files')
    @mock.patch('fileupl.FormAnalyzer.set_page')
    @mock.patch('cgi.FieldStorage')
    def test_run(self, MockClass, set_page, delete_saved_files,
            save_uploaded_file, m_):
        instance = MockClass.return_value
        instance.__getitem__ = lambda s, key: self.fields[key]
        instance.__contains__ = lambda s, key: key in self.fields
        set_page.return_value = 0
        delete_saved_files.return_value = 'dsf'
        save_uploaded_file.return_value = 'suf'
        def _(message): return message
        m_.side_effect = _
        fa = fileupl.FormAnalyzer()
        self.fields["file"] = self.TestField("foo")
        self.fields["author"] = self.TestField("a1")
        self.assertEqual(fa.run(), ('suf', 0, True))
        self.fields.clear()
        self.fields["kill"] = self.TestField("k")
        self.fields["target"] = self.TestField("t")
        self.assertEqual(fa.run(), ('dsf', 0, True))
        self.fields.clear()
        self.fields["page"] = self.TestField("p")
        set_page.return_value = 1
        self.assertEqual(fa.run(), ('', 1, False))
        set_page.return_value = -1
        self.assertEqual(fa.run(), (_('Invalid page number specified.'),
            -1, True))
        self.fields.clear()
        self.fields["file"] = self.TestField("foo")
        self.assertEqual(fa.run(), (_('Invalid form parameter.'),
            0, True))
        self.fields.clear()
        self.assertEqual(fa.run(), ('', 0, False))

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
        self.cc = 'a'
        def chk(a, b):
            self.cc = b
        writedirfile.side_effect = chk
        isfileimage.return_value = True
        remove.return_value = True
        do_upload.return_value = True
        def _(message): return message
        m_.side_effect = _

        mitem = mock.Mock()
        mau = mock.Mock()

        mitem.file = ''
        m1 = dict(file=mitem, author=mau)
        logging.debug('mitem.file')
        logging.debug(mitem.file)
        fa = fileupl.FormAnalyzer()
        self.assertEqual(fa.save_uploaded_file(m1),
                _('No uploading file name specified.'))

        mitem.file = 1
        mitem.filename = '/home/foo/mocktest.txt'
        self.assertEqual(fa.save_uploaded_file(m1),
                _('File extension not allowed.'))

        mitem.filename = '/home/foo/mocktest.jpg'
        self.assertEqual(fa.save_uploaded_file(m1),
                _('File size too large (max %s KB)') \
                        % str(fileupl.up_limit))

        do_upload.return_value = False
        self.assertEqual(fa.save_uploaded_file(m1),
                _('Not an image data.'))

        isfileimage.return_value = False
        self.cc = 'a'
        mau.value = ''
        r = fa.save_uploaded_file(m1)
        self.assertEqual(r,
                _('File successfully uploaded.'))
        self.assertEqual(self.cc, 'a')
        mau.value = '123'
        r = fa.save_uploaded_file(m1)
        self.assertEqual(r,
                _('File successfully uploaded.'))
        self.assertEqual(self.cc, '123')

    @mock.patch('__builtin__._')
    @mock.patch('fileupl.remove')
    @mock.patch('fileupl.readdirfile')
    def test_delete_saved_file(self, readdirfile, remove, m_):
        remove.return_value = True
        def _(message): return message
        m_.side_effect = _

        mpass = mock.Mock()
        mtarget = mock.Mock()
        mtarget.value = '/home/foo/mtgt.txt'
        m1 = dict(target=mtarget)
        m1['pass'] = mpass
        mpass.value = ''
        readdirfile.return_value = ''
        logging.debug('m1[\'pass\'].value')
        logging.debug(m1['pass'].value)
        fa = fileupl.FormAnalyzer()
        self.assertEqual(fa.delete_saved_files(m1),
                _('The file successfully deleted.'))
        mpass.value = ''
        readdirfile.return_value = '123'
        self.assertEqual(fa.delete_saved_files(m1),
                _('Invalid password.'))
        mpass.value = '1234'
        readdirfile.return_value = '1234'
        self.assertEqual(fa.delete_saved_files(m1),
                _('The file successfully deleted.'))

    def test_set_page(self):
        mp = mock.Mock()
        m1 = dict(page=mp)
        mp.value = ''
        fa = fileupl.FormAnalyzer()
        self.assertEqual(fa.set_page(m1), -1)
        mp.value = '0'
        self.assertEqual(fa.set_page(m1), 0)
        mp.value = '43'
        self.assertEqual(fa.set_page(m1), 43)
        mp.value = '-5'
        self.assertEqual(fa.set_page(m1), -1)
        mp.value = '-4.5'
        self.assertEqual(fa.set_page(m1), -1)
        mp.value = 'a'
        self.assertEqual(fa.set_page(m1), -1)



if __name__ == "__main__":
    unittest.main()
