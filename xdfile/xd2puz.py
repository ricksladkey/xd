#!/usr/bin/env python3
# -*- coding: utf-8

import puz
import crossword

import xdfile


def to_puz(xd):

    result = puz.Puzzle()

    result.preamble = b''
    result.width = xd.width()
    result.height = xd.height()
    if 'Author' in xd.headers:
        result.author = xd.headers['Author']
    if 'Copyright' in xd.headers:
        result.copyright = xd.headers['Copyright']
    if 'Title' in xd.headers:
        result.title = xd.headers['Title']

    filled_cells = []
    unfilled_cells = []
    for row in xd.grid:
        for cell in row:
            filled_cells.append('.' if cell == xdfile.BLOCK_CHAR else cell)
            unfilled_cells.append('.' if cell == xdfile.BLOCK_CHAR else ' ')
    result.solution = ''.join(filled_cells)
    result.fill = ''.join(unfilled_cells)

    result.clues = []
    for pos, clue, answer in xd.clues:
        if answer:
            result.clues.append(clue)

    return result


if __name__ == "__main__":
    import sys
    from .utils import get_args, find_files

    args = get_args(desc='convert .xd file to .puz file')
    for fn, contents in find_files(*args.inputs):
        input_xd = xdfile.xdfile(xd_contents=contents.decode("utf-8"), filename=fn)
        output_puz = to_puz(input_xd)
        output_puz.save(fn.replace('.xd', '.puz'))
