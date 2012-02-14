#!/usr/bin/env python2

from __future__ import division, absolute_import, print_function, unicode_literals

import re
import sqlite3
import os
from getpass import getpass
from clint import args
from clint.textui import puts, colored, indent

from BeautifulSoup import BeautifulSoup

class Function(object):
    def __init__(self, name, parameters, retval='', doc=''):
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
                    Function(f_name, f_params, f_retval, f_doc))

    def get_function_descriptions(self):
        for func_desc in self._function_descriptions:
            yield func_desc


class SqliteOutput(object):
    def __init__(self, path):
        self.conn = None
        self.cur = None
        self.create_db(path)

    def create_db(self, path):
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()
        self.cur.execute("select name from sqlite_master where type='table' and name='functions'")

        if not self.cur.fetchone():
            self.cur.execute('create table functions (word text, menu text, info text)')
            self.cur.execute('create index pk_functions on functions (word)')
            self.conn.commit()

    def append(self, function):
        self.cur.execute('select word from functions where word = ?', (function.name,))
        if not self.cur.fetchone():
            self.cur.execute('insert into functions (word, menu, info) values (?, ?, ?)',
                    (function.name,
                    function.parameters,
                    function.doc)
            )

    def close(self):
        self.conn.commit()
        self.conn.close()

def read_write_tablefields(conn, out):
    sql = '''
select
	distinct
	word = convert(nvarchar, t_cpac + t_cmod + t_flno + '.' + t_fdnm)
	,menu = convert(nvarchar, isnull((case t_clab when ''
				then
					(select	top 1
						t_desc
					from
						tttadv140000 labels
					where
						labels.t_clan = 2
						and labels.t_lhgt = 1
						and labels.t_cpac = tablefields.t_cpac
						and labels.t_clab = tablefields.t_cpac + tablefields.t_cmod + tablefields.t_flno + '.' + tablefields.t_fdnm
					order by
						labels.t_leng desc
					)
				else
					(select top 1
						t_desc
					from
						tttadv140000 labels
					where
						labels.t_clan = 2
						and labels.t_cpac = tablefields.t_cpac
						and labels.t_clab = tablefields.t_clab
						and labels.t_lhgt = 1
						--and labels.t_vers = tablefields.t_vers
						--and labels.t_rele = tablefields.t_rele
						--and labels.t_cust = tablefields.t_cust
					order by
						labels.t_leng desc
					)

				end), ''))

from
	tttadv422000 tablefields
order by
	convert(nvarchar, t_cpac + t_cmod + t_flno + '.' + t_fdnm)
'''
    cur = conn.cursor()
    cur.execute(sql)
    for row in cur.fetchall():
        f = Function(row['word'], row['menu'].decode('latin1'))
        out.append(f)

def from_doc():
    files = args.files
    output = args.grouped['--out'][0]
    files = [x for x in files if x.endswith('.html')]

    out = SqliteOutput(output)
    for fi in files:
        parser = ApiDocParser(fi)
        parser.parse()
        for fun in parser.get_function_descriptions():
            out.append(fun)

    out.close()

def from_db():
    db = args.grouped['--db'][0]
    output = args.grouped['--out'][0]
    out = SqliteOutput(output)

    if db == 'mssql':
        import pymssql as db

    host = raw_input('sql server: ')
    user = raw_input('username: ')
    database = raw_input('database name: ')
    password = getpass()

    conn = db.connect(host=host,
                      user=user,
                      password=password,
                      database=database,
                      as_dict=True)
    read_write_tablefields(conn, out)
    out.close()


def print_help():
    puts('Baancomplete gen_api.py')
    puts('Use this python script to generate a baancomplete_api.sqlite file')
    puts('')
    puts('Either from library documentation generated with ttstpbaandoc')
    with indent(2):
        puts('{0} {1} {2} {3}'.format(
            colored.green('--doc'),
            colored.yellow('[file or directory (subfolders are searched too)]'),
            colored.green('--out'),
            colored.yellow('[file]'))
        )
    puts('Or from table definitions (database credentials required)')
    with indent(2):
        puts('{0} {1} {2} {3}'.format(
            colored.green('--db'),
            colored.yellow('[mssql]'),
            colored.green('--out'),
            colored.yellow('[file]')
        ))

    puts(colored.red('''
The output file is a sqlite3 database.
Copy it into the baancomplete autoload folder and name it baancomplete_api.sqlite
You can change the path to the folder where baancomplete will look for the api file by setting
g:baancomplete_path in .vimrc
But you cannot change the filename itself.
'''))


def main():
    if '--out' in args.flags:
        if '--doc' in args.flags:
            return from_doc()
        elif '--db' in args.flags:
            return from_db()
    print_help()

if __name__ == '__main__':
    main()
