#!/usr/bin/env python2

from __future__ import division, absolute_import, print_function, unicode_literals

import re
import sqlite3
import os
import pickle
from BeautifulSoup import BeautifulSoup

class FunctionDesc(object):
    def __init__(self, name, parameters, retval, doc):
        self.name = name
        self.parameters = parameters
        self.retval = retval
        self.doc = doc

    def __str__(self):
        return '%s%s' % (self.name, self.parameters)

class ApiDocParser(object):
    def __init__(self, filepath):
        self._filepath = filepath
        self._function_descriptions = []

    def parse(self):
        with open(self._filepath) as fp:
            contents = fp.read()

        
        desc_pattern = '<p class="FirstPara">(.*)<b>(.*)</b>(.*)</p>'
        rex_desc = re.compile(desc_pattern)

        soup = BeautifulSoup(contents)

        for td in soup.findAll('td', { 'id' : 'FunctionCall' }):
            desc = str(td.p).replace('\n', '').replace('\t', '')
            r_search = rex_desc.search(desc)

            if not r_search:
                print ('Error reading {0}'.format(td.b.renderContents()))
                continue

            f_retval = r_search.group(1)
            f_name = r_search.group(2)
            f_params = r_search.group(3)

            f_doc = td.findParent('table').findNext('pre').renderContents()
            f_doc = f_doc.replace('\r\n', os.linesep)
            f_doc = f_doc.replace('\n', os.linesep)
            f_doc = f_doc.replace('&lt;', '<')
            f_doc = f_doc.replace('&gt;', '>')

            # baancomplete.vim doesn't like double quotes
            f_doc = f_doc.replace('&quot;', "'")   
            f_doc += '%s%s' % (os.linesep, os.path.basename(self._filepath))

            self._function_descriptions.append(
                    FunctionDesc(f_name, f_params, f_retval, f_doc))

    def get_function_descriptions(self):
        for func_desc in self._function_descriptions:
            yield func_desc


class VimOutput(object):
    def __init__(self, output_path):

        if os.path.isfile(output_path):
            os.remove(output_path)

        self._conn = sqlite3.connect(output_path)
        self._c = self._conn.cursor()
        self._c.execute('''
create table functions (
    word text,
    menu text,
    info text
)''')
        self._conn.commit()

    def append(self, function_desc):
        self._c.execute('insert into functions (word, menu, info) values (?, ?, ?)', 
                (function_desc.name,
                function_desc.parameters,
                function_desc.doc))

    def close(self):
        self._conn.commit()
        self._conn.close()

class PickleOutput(object):
    def __init__(self):
        pass
        
#api.append({
#'word' : word,
#'menu' : menu,
#'info' : info
#})

#with open('c:\\temp\\api.pkl', 'wb') as output:
#    pickle.dump(api, output)

class SciteOutput(object):
    def __init__(self, output_path):
        self._fp = open(output_path, 'w')

    def append(self, function_desc):
        self._fp.write('%s%s[Ret: %s]\n' % (
                function_desc.name,
                function_desc.parameters,
                function_desc.retval,
                )
            )

    def close(self):
        self._fp.close()


if __name__ == '__main__':
    path = raw_input('path to baan html documentations: ')
    vimoutput = VimOutput(raw_input('path to vimcomplete output: '))
    for file in os.listdir(path):
        if not os.path.isfile(os.path.join(path, file)):
            continue

        aparser = ApiDocParser(os.path.join(path, file))
        aparser.parse()
        for f in aparser.get_function_descriptions():
            vimoutput.append(f)

    vimoutput.close()
