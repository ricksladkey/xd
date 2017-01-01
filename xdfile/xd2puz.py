#!/usr/bin/env python3
# -*- coding: utf-8

import xdfile
import puz


def to_puz(xd):

    # Create a blank puzzle.
    result = puz.Puzzle()
    result.preamble = b'' # workaround for new puzzle

    # Fill in the main puzzle fields.
    result.width = xd.width()
    result.height = xd.height()
    if 'Author' in xd.headers:
        if 'Editor' in xd.headers:
            result.author = xd.headers['Author'] + ' / ' + xd.headers['Editor']
        else:
            result.author = xd.headers['Author']
    if 'Copyright' in xd.headers:
        result.copyright = xd.headers['Copyright']
    if 'Title' in xd.headers:
        result.title = xd.headers['Title']
    if 'Notes' in xd.headers:
        result.notes = xd.header['Notes']
    else:
        result.notes = xd.notes.replace('{*Notepad:*}', '').strip()
    result.notes = result.notes.replace('\n', '\r\n')

    # Populate the solved puzzle and the unsolved puzzle.
    filled_cells = []
    unfilled_cells = []
    for row in xd.grid:
        for cell in row:
            is_block = cell == xdfile.BLOCK_CHAR
            filled_cells.append('.' if is_block else cell.upper())
            unfilled_cells.append('.' if is_block else '-')
    result.solution = ''.join(filled_cells)
    result.fill = ''.join(unfilled_cells)

    # Populate the clues which are sorted by number (across first if both).
    result.clues = []
    clues = [(pos[1], clue) for pos, clue, answer in xd.clues if answer]
    clues = sorted(clues, key=lambda item: item[0])
    for index, clue in clues:
        result.clues.append(clue)

    # Handle shaded/circled squares.
    # Example: nyt-2008-09-11
    if 'Special' in xd.headers:
        markup = []
        for row in xd.grid:
            for cell in row:
                value = puz.GridMarkup.Default
                if cell.isalpha() and cell == cell.lower():
                    value = puz.GridMarkup.Circled
                markup.append(value)
        result.markup().markup = markup

    # Handle rebus.
    # Example: nyt-2008-09-11
    # Example: nyt-2008-09-14
    if 'Rebus' in xd.headers:
        result.extensions[puz.Extensions.Rebus] = b'' # workaround for new puzzle
        mapping = {
            value: key
            for key, value in enumerate(sorted(xd.rebus().keys()))
        }
        table = []
        for row in xd.grid:
            for cell in row:
                value = 0
                if cell in mapping:
                    value = mapping[cell] + 1 # plus one because zero is valid
                table.append(value)
        result.rebus().table = table
        result.rebus().solutions = {
            mapping[cellchar]: replstr
            for cellchar, replstr in xd.rebus().items()
        }

    return result


if __name__ == "__main__":
    import sys
    from .utils import get_args, find_files

    args = get_args(desc='convert .xd file to .puz file')
    for fn, contents in find_files(*args.inputs):
        input_xd = xdfile.xdfile(xd_contents=contents.decode("utf-8"), filename=fn)
        output_puz = to_puz(input_xd)
        output_puz.save(fn.replace('.xd', '.puz'))
