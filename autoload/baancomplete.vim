" File: baancomplete.vim
" Author: Mathias Fussenegger < f.mathias 0x40 zignar.net >
" Description: Omni Completion for baan-c (the Infor ERP LN Scripting language)
" Version: 0.2
" Created: September 18, 2011
" Last Modified: February 11, 2012
"
"

if exists('did_baancomplete') || &cp || version < 700
    finish
endif
let did_baancomplete = 1

if !exists("g:baancomplete_path")
    let g:baancomplete_path = expand("<sfile>:h")
endif

if !has('python')
    echo 'Error: Required vim compiled with +python'
    finish
endif

function! baancomplete#meetsForAcp(context)
    " 3 or more keyword characters are necessary for completion to kick in
    return a:context =~# '\v\k{3,}$'
endfunction


" see :help complete-functions for more details on how baancomplete#Complete works
"
"
"
" example:
"
" column: 123456789
" word  : t dal.s
"
"
" findstart == 1
" We never want to replace anything before the cursor. So we return the current
" column (8)
"
" findstart == 0
" determine the word to lookup (in our example dal.s )

function! baancomplete#Complete(findstart, base)
    if a:findstart == 1
        return col('.')

    else
        let line = getline('.')
        let idx = col('.') - 1

        while idx > 0 && line[idx - 1] =~ '\k'
            let idx -= 1
        endwhile

        let context = line[idx : col('.')]
        execute "python vimcomplete('" . context . "')"
        return g:baancomplete_completions
    endif
endfunction

function! s:DefPython()
python << PYTHONEOF

import vim, os, sqlite3

baancomplete_path = vim.eval("g:baancomplete_path")
api_file = os.path.join(baancomplete_path, 'baancomplete_api.sqlite')
api_file_exists = os.path.isfile(api_file)

if api_file_exists:
    conn = sqlite3.connect(api_file)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

def vimcomplete(context):
    dictstr = '['
    if api_file_exists:
        completions = get_completions(context)
    else:
        vim.command('echom "api file not found"')
        completions = []
    for compl in completions:
        dictstr += '{"word":"%s","abbr":"%s","menu":"%s","info":"%s","icase":0},' % (
            compl['word'], compl['abbr'], compl['menu'], compl['info'])
    dictstr += ']'
    vim.command('silent let g:baancomplete_completions = %s' % dictstr)

def get_completions(context):
    completions = []
    search_term = context + '%'
    cur.execute('select word, menu, info from functions where word like ? limit 20', (search_term,))
    for item in cur:
        word = item['word'][len(context):]
        info = item['info']

        completions.append({
            'menu' : item['menu'],
            'word' : word,
            'abbr' : item['word'],
            'info' : item['info']
        })
    return completions

PYTHONEOF
endfunction

call s:DefPython()
