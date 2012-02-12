" File: baan.vim
" Author: Mathias Fussenegger < f.mathias 0x40 zignar.net >
" Description: Omni Completion for baan-c (the Infor ERP LN Scripting language)
" Version: 0.2
" Created: September 18, 2011
" Last Modified: February 11, 2012

set omnifunc=baancomplete#Complete
set completefunc=syntaxcomplete#Complete

" Configure Acp (if installed)
" (http://www.vim.org/scripts/script.php?script_id=1879)
" First regular keyword completion will be attempted
" Then syntax- and finally omnicompletion

if exists("g:acp_behavior")
    if !exists("g:acp_behavior_set")
        let g:acp_behavior_set = 1
        let g:acp_behavior = { 'baan' : [] }


        call add(g:acp_behavior['baan'], {
                    \   'command' : "\<C-x>\<C-p>",
                    \   'meets'   : 'acp#meetsForKeyword',
                    \   'repeat'  : 0,
                    \ })
        call add(g:acp_behavior['baan'], {
                    \   'command'      : "\<C-x>\<C-u>",
                    \   'completefunc' : 'syntaxcomplete#Complete',
                    \   'meets'        : 'baancomplete#meetsForAcp',
                    \   'repeat'       : 0,
                    \ })
        call add(g:acp_behavior['baan'], {
                    \   'command'      : "\<C-x>\<C-o>",
                    \   'completefunc' : 'baancomplete#Complete',
                    \   'meets'        : 'baancomplete#meetsForAcp',
                    \   'repeat'       : 0,
                    \ })
    endif
endif
