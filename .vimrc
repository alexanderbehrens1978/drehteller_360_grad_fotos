" Grundlegende Einstellungen für Vi/Vim
syntax on                 " Syntax-Highlighting aktivieren
set background=dark       " Dunkler Hintergrund für bessere Lesbarkeit
set termguicolors         " Echte Farben im Terminal aktivieren (wenn unterstützt)
set number                " Zeilennummern anzeigen
set autoindent            " Automatische Einrückung
set expandtab             " Tabs in Leerzeichen umwandeln
set tabstop=4             " Tab-Breite auf 4 Zeichen setzen
set shiftwidth=4          " Einrückungsbreite auf 4 Zeichen setzen

" Spezielle Hervorhebung für Farbcodes in CSS/HTML/JavaScript-Dateien
" Diese Funktion erkennt Hexadezimal-Farbcodes und färbt sie entsprechend ein
function! HexHighlight()
  let hexColor = matchstr(getline('.'), '#\([0-9A-Fa-f]\{3,6\}\)\>')
  if len(hexColor) > 0
    execute 'hi hexColor' . hexColor . ' guifg=black guibg=' . hexColor
    execute 'match hexColor' . hexColor . ' /' . hexColor . '/'
  else
    execute 'match none'
  endif
endfunction

" Aktiviere automatisches Färben von Hexadezimal-Farbcodes für bestimmte Dateitypen
autocmd BufEnter,BufWritePost *.css,*.html,*.htm,*.js,*.jsx,*.vue call HexHighlight()
autocmd CursorMoved,CursorMovedI *.css,*.html,*.htm,*.js,*.jsx,*.vue call HexHighlight()

" Verbesserte Syntax-Highlighting für CSS-Dateien
augroup css_syntax
  autocmd!
  autocmd FileType css syntax match cssColorProp "#[0-9A-Fa-f]\{3,6\}"
  autocmd FileType css highlight cssColorProp guibg=bg
augroup END

" Plugin-Empfehlungen (wenn Sie Vim-Plug verwenden):
" Fügen Sie diese Zeilen zu Ihrer .vimrc hinzu und installieren Sie vim-plug:
"
" call plug#begin('~/.vim/plugged')
" Plug 'ap/vim-css-color'           " Zeigt Farbcodes direkt an
" Plug 'pangloss/vim-javascript'    " Bessere JS-Syntax
" Plug 'hail2u/vim-css3-syntax'     " CSS3-Syntax
" call plug#end()
