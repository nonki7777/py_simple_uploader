#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
A simple file uploader using Python
Confirmed workable on version 2.6.6
'''

from __future__ import print_function, unicode_literals

from time import time, localtime, strftime
import commands
import cgi
import os, re
import sys
import gettext

def getcwd():
    return os.getcwd()

gettext.install(
        domain='fileupl',
        localedir=getcwd(),
        names=('ngettext',)
        )

# import cgitb
# cgitb.enable()

up_limit    = 3072  # max. file size (KB)
item_bypage = 10    # max. number of file names displayed on a page
maxfilenum  = 50    # max. number of files to be stored on a server

dir_src = 'src'
dir_db  = 'db'

thiscgifile = os.path.basename(__file__)


def remove(filename):
    if os.path.isfile(filename):
        os.remove(filename)

def listdir(fpath):
    return os.listdir(fpath)

def chmod(fpath):
    os.system('chmod 644 ' + fpath)

def isfileimage(fpath):
    return commands.getoutput('file ' + fpath).find("image") == -1


class FormAnalyzer(object):
    """Receives form parameters and manages save/delete uploaded files"""
    
    def run(self):
        result = ''
        page = 0
        gotoredirect = True
        form = cgi.FieldStorage()
        if form.has_key('file') and form.has_key('author'):
            result = self.save_uploaded_file(form)
        elif form.has_key('kill') and form.has_key('target'):
            result = self.delete_saved_files(form)
        elif form.has_key('page'):
            page = self.set_page(form)
            if page == -1:
                result = _('Invalid page number spacified.')
            else:
                gotoredirect = False
        elif form.has_key('file') or form.has_key('kill'):
            result = _('Invalid form parameter.')
        else:
            gotoredirect = False
        return (result, page, gotoredirect)

    def chkExt(self, ext):
        return re.match('^\.(jpe?g|png|gif)$', ext)
    
    def do_upload(self, rf, wf, fpath):
        upcnt = 0
        while True:
            upcnt += 1
            if upcnt > up_limit:
                reach_max = True
                break
            chunk = rf.read(1024)
            if not chunk:
                reach_max = False
                break
            wf.write(chunk)
        wf.close()
        chmod(fpath)
        return reach_max

    def delete_oldest(self):
        fsrc = os.path.join(getcwd(), dir_src)
        while len(listdir(fsrc)) > maxfilenum:
            oldestfile = sorted(listdir(fsrc))[0]
            base = os.path.splitext(oldestfile)[0]
            src = os.path.join(fsrc, oldestfile)
            db = os.path.join(getcwd(), dir_db, base + '.txt')
            remove(src)
            remove(db)

    def save_uploaded_file(self, form):
        item = form['file']
        author = form['author']
        if not (item.file and item.filename):
            return _('No uploading file name specified.')
        base, ext = os.path.splitext(item.filename)
        if not self.chkExt(ext):
            return _('File extension not allowed.')
        now = int(time())
        fname = str(now) + ext
        fsrc = os.path.join(getcwd(), dir_src)
        fpath = os.path.join(fsrc, fname)
        fout = file(fpath, 'wb')
        reach_max = self.do_upload(item.file, fout, fpath)
        if reach_max:
            remove(fpath)
            return _('File size too large (max %s KB)') \
                % str(up_limit)
        if isfileimage(fpath):
            remove(fpath)
            return _('Not an image data.')
        if author.value:
            fout = file(os.path.join(getcwd(), dir_db, \
                str(now) + '.txt'), 'wa')
            fout.write(author.value)
            fout.close()
        self.delete_oldest()
        return _('File successfully uploaded.')

    def delete_saved_files(self, form):
        if form.has_key('pass'):
            upass = form['pass'].value
        else:
            upass = ''
        opass = ''
        base, ext = os.path.splitext(form['target'].value)
        src = os.path.join(getcwd(), dir_src, form['target'].value)
        db = os.path.join(getcwd(), dir_db, base + '.txt')
        if os.path.isfile(db):
            f = open(db, 'ra')
            opass = f.read()
            f.close()
        if upass == opass:
            remove(src)
            remove(db)
            return _('The file successfully deleted.')
        else:
            return _('Invalid password.')

    def set_page(self, form):
        try:
            page = int(form['page'].value)
            if page < 0:
                page = -1
        except:
            page = -1
        return page


class HTMLBuilder(object):

    def run(self, result, page, gotoredirect):
        self.html_header()
        if gotoredirect:
            self.html_refresh(result)
        else:
            self.html_normal(page)

    def html_header(self):
        print('Content-type: text/html')
        print()
        print('<!DOCTYPE html>')
        print('<html>')
        print('<head>')
        print('<meta http-equiv="cache-control" content="no-cache" />')
        print('<meta http-equiv="Content-Type" content="text/html" charset="UTF-8" />')
        print('<title>uploader</title>')
        print('<style>*{font-size:9pt;color:#404040}a{color:#409060;text-decoration:none;}</style>')

    def html_refresh(self, result):
        print('<META http-equiv="refresh" content="3; url=%s">' % thiscgifile)
        print('</head>')
        print('<body>')
        print(result, '<br>')
        print('<br>')
        print(_('Wait a moment'), \
                ' ... <a href="%s target="_self">' % thiscgifile, \
              _('back'), '</a><br>')
        print('</body></html>')

    def html_normal(self, page):
        print('</head>')
        print('<body>')
        print('<div align="center">')

        print('<table width="830" cellspacing="0" cellpadding="0" style="margin:10px;">')
        print('<td>')
        # print(_('A simple file uploader.'), file=sys.stderr)
        print('<li>', _('A simple file uploader.'))
        print('<li>', _('You can upload an image file up to %s MB.') \
            % str(up_limit / 1024), \
            _('  If the server gets full, older files would be deleted.'))
        print('<li>', \
            _('Read more information at <a href="/" target="_blank">its top page</a>.'))
        print('</td>')
        print('</table>')

        print('<table id="outer" width="830" cellspacing="0" cellpadding="0">')

        print('<tr><td><!-- outer No.1 -->')
        print('<form action="%s" method="post" enctype="multipart/form-data">' % thiscgifile)

        print('<fieldset style="border:2px solid silver">')
        print('<legend>', _('a new post'), '</legend>')
        print(_('file (max %s KB)') % str(up_limit), ': ', \
            '<input type="file" name="file" ', \
            "style=\"height:18px;color:black;background:white;border:1px ", \
            "solid silver\" />")
        print(_('pass code to delete (option)'), ': <input type="text" name="author" style="width:80px;height:18px;color:black;background:white;border:1px solid silver" />')
        print('<input type="submit" value="', _("post"), '" style="width:50px;height:18px;color:black;background:white;border:1px solid silver" />')
        print('<span align="right">', _("max. number of files"), ':' + \
                str(maxfilenum) + ' (', _('up to '), \
                str(maxfilenum*up_limit/1024) + 'MB)</span>')
        print('</fieldset>')

        print('</form>')
        print('</td></tr><!-- outer No.1 -->')
        print('<tr><td>----</td></tr>')

        print('<tr><td><!-- outer No.2 -->')
        print('<form action="%s" method="post">' % thiscgifile)
        print('  <table id="listview" border="1" rules="all"')
        print('    cellpadding="5" style="display:block;">')
        print('  <tr>')
        print('    <td colspan="4">', _('stored files'), '</td>')
        print('  </tr>')
        print('  <tr>')
        print('    <th width="80">', _('select'), '</th>')
        print('    <th width="320">', _('file name'), '</th>')
        print('    <th width="320">', _('date'), '</th>')
        print('    <th width="100">', _('size'), '</th>')
        print('  </tr>')
        cnt = 0
        all_sorted_list = reversed(sorted(listdir(os.path.join(getcwd(),
            dir_src))))
        sorted_list = []
        for item in all_sorted_list:
            if item[0] != '.':
                sorted_list.append(item)
        for file in sorted_list:
            if (cnt >= item_bypage * page) and (cnt < item_bypage * (page + 1)):
                href = os.path.join("./", dir_src, file)
                base, ext = os.path.splitext(file)
                print('  <tr>')
                print('    <td><input type="radio" name="target" value="%s"></td>' % file)
                print('    <td><a href="%s" target="_blank">%s</a></td>' % (href, file))
                print('    <td>%s</td>' %
                    strftime('%Y/%m/%d %H:%M:%S',localtime(int(base))))
                fsize = os.path.getsize(os.path.join("./", dir_src, file))
                if fsize < 1024:
                    fsize = str(fsize)+"Byte"
                elif fsize < 1024 * 1024:
                    fsize = str(fsize/1024)+'KB'
                else:
                    fsize = str(fsize/1024/1024)+'MB'
                print('    <td>%s</td>' % fsize)
                print('  </tr>')
            cnt += 1
        print('  </table><!-- listview -->')
        print('  </td></tr><!-- outer No.2 -->')
        print('  <tr><!-- outer No.3 -->')
        print('    <td align="right">')

        print('    ', _('pass code to delete'), ': <input type="text" name="pass" value="" style="width:120px;height:18px;color:black;background:white;border:1px solid silver">')
        print('    <input type="submit" name="kill" value="', _('delete'), '" style="width:50px;height:18px;color:black;background:white;border:1px solid silver">')

        print('    </td>')
        print('  </tr><!-- outer No.3 -->')
        print('  <tr><!-- outer No.4 -->')
        print('    <td align="center">')

        print('    <<')
        print('      ')
        for i in xrange(int(cnt / item_bypage) + ( 0 if (cnt%item_bypage) == 0 else 1 )):
            if i == page:
                print('[%s] ' % str(page + 1))
            else:
                print('[<a href="%s?page=%s">%s</a>] ' % (thiscgifile, str(i), str(i+1)))
        print('    >>')
        print('    </td>')
        print('  </tr><!-- outer No.4 -->')
        print('</form>')
        print('</table>')
        print('</div>')
        print('</body></html>')


def main():
    fa = FormAnalyzer()
    aresult, apage, agotoredirect = fa.run()
    hb = HTMLBuilder()
    hb.run(aresult, apage, agotoredirect)

main()
