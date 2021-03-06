#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import string
# import os.path
import re

from lxml import html
from xdfile.utils import info, debug, error
import xdfile

SPLIT_REBUS_TITLES = "CRYPTOCROSSWORD TIC-TAC-TOE".split()


def stringify_children(node):
    for br in node.cssselect("br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    s = node.text_content()
    if s is None:
        s = ''
    # for child in node:
    #     s += etree.tostring(child, encoding='unicode')
    return s


# content is unicode()
def parse_xwordinfo(content, filename):
    content = content.decode('utf-8')

    REBUS_LONG_HANDS = {'NINE': '9',
                        'EIGHT': '8',
                        'SEVEN': '7',
                        'SIX': '6',
                        'FIVE': '5',
                        'FOUR': '4',
                        'THREE': '3',
                        'TWO': '2',
                        'ONE': '1',
                        'ZERO': '0',
                        'AUGHT': '0',
                        'AMPERSAND': '&',
                        'AND': '&',
                        'ASTERISK': '*',
                        'PERCENT': '%',
                        'STAR': '*',
                        'AT': '@',
                        'DOLLAR': '$',
                        'PLUS': '+',
                        'CENT': 'c',
                        # 'DASH': '-',
                        # 'DOT': '●'
                        }
    rsh = 'zyxwvutsrqponmlkjihgfedcba♚♛♜♝♞♟⚅⚄⚃⚂⚁⚀♣♦♥♠Фθиλπφя+&%$@?*0987654321'
    REBUS_SHORT_HANDS = list(rsh)

    content = content.replace("<b>", "{*")
    content = content.replace("</b>", "*}")
    content = content.replace("<i>", "{/")
    content = content.replace("</i>", "/}")
    content = content.replace("<em>", "{/")
    content = content.replace("</em>", "/}")
    content = content.replace("<u>", "{_")
    content = content.replace("</u>", "_}")
    content = content.replace("<strike>", "{-")
    content = content.replace("</strike>", "-}")
    content = content.replace("’", "'")
    content = content.replace('“', '"')
    # content = content.replace('–', '-')

    if "CPHContent_" in content:
        xwiprefix = '#CPHContent_'
    else:
        xwiprefix = '#'

    root = html.fromstring(content)

    ## debug("ROOT: %s" % root)

    special_type = ''
    rebus = {}
    rebus_order = []

    xd = xdfile.xdfile('', filename)

    # get crossword info
    title = root.cssselect(xwiprefix + 'toppanel #PuzTitle')[0].text.strip()
    subtitles = root.cssselect(xwiprefix + 'SubTitleH3')
    if subtitles:
        subtitle = subtitles[0].text.strip()
        subtitle = ' [%s]' % subtitle
    else:
        subtitle = ""

    notepads = root.cssselect('#notepad')
    if notepads:
        xd.notes = stringify_children(notepads[0])
    else:
        xd.notes = ""

    xd.set_header("Title", '%s%s' % (title, subtitle))
    xd.set_header("Copyright", root.cssselect(xwiprefix + 'Copyright')[0].text.strip())
    xd.set_header("Author", root.cssselect(xwiprefix + 'aetable tr td')[1].text.strip())
    xd.set_header("Editor", root.cssselect(xwiprefix + 'aetable tr td')[3].text.strip())

    xd.notes = xd.notes.replace("<br/>", "\n")
    xd.notes = xd.notes.replace("{*Notepad:*}", "\n")
    xd.notes = xd.notes.replace("&#13;", "\n")
    xd.notes = xd.notes.strip()

    puzzle_table = root.cssselect('#PuzTable tr')

    for row in puzzle_table:
        row_data = ""
        for cell in row.cssselect('td'):
            # check if the cell is special - with a shade or a circle
            cell_class = cell.get('class')
            cell_type = ''
            if cell_class == 'bigshade':
                cell_type = 'shaded'
            elif cell_class == 'bigcircle':
                cell_type = 'circle'

            letter = cell.cssselect('div.letter')
            letter = (len(letter) and letter[0].text) or xdfile.BLOCK_CHAR

            # handle rebuses
            if letter == xdfile.BLOCK_CHAR:
                subst = cell.cssselect('div.subst2')
                subst = (len(subst) and subst[0].text) or ''
                if not subst:
                    subst = cell.cssselect('div.subst')
                    if subst:
                        if title in SPLIT_REBUS_TITLES:
                            subst = "/".join(list(subst[0].text))
                        else:
                            subst = subst[0].text
                    else:
                        subst = ''

                if subst:
                    if subst not in rebus:
                        if subst in REBUS_LONG_HANDS:
                            rebus_val = REBUS_LONG_HANDS[subst]
                            if rebus_val in REBUS_SHORT_HANDS:
                                REBUS_SHORT_HANDS.remove(rebus_val)
                        else:
                            rebus_val = REBUS_SHORT_HANDS.pop()
                        rebus[subst] = rebus_val
                        rebus_order.append(subst)
                    letter = rebus[subst]

            if cell_type:
                # the special cell's letter should be represented in lower case
                letter = letter.lower()
                if not special_type:
                    # hopefully there shouldn't be both shades and circles in
                    # the same puzzle - if that is the case, only the last value
                    # will be put up in the header
                    special_type = cell_type

            row_data += letter
        xd.grid.append(row_data)

    if len(rebus):
        rebus = ["%s=%s" % (rebus[x], x.upper()) for x in rebus_order]
        xd.set_header("Rebus", xdfile.REBUS_SEP.join(rebus))
    if special_type:
        xd.set_header("Special", special_type)

    # add clues
    across_clues = _fetch_clues(xd, 'A', root, xwiprefix + 'tdAcrossClues', rebus)
    down_clues = _fetch_clues(xd, 'D', root, xwiprefix + 'tdDownClues', rebus)

    return xd


def _fetch_clues(xd, clueprefix, root, css_identifier, rebus):
    PT_CLUE = re.compile(r'(\d+)\. ?(.*)')
    text = number = solution = None
    answer_next = False
    cluespan = root.cssselect(css_identifier)
    if not cluespan:
        return
    for content in cluespan[0].itertext():
        content = content.strip()
        if answer_next:
            assert not solution
            solution = content

            # replace rebuses with appropriate identifiers (numbers)
            for item in rebus:
                if item in content:
                    pass
                    # TODO: where is 'index'???
                    # content = content.replace(item, str(index + 1))

            solution = content
            xd.clues.append(((clueprefix, number), text, solution))
            text = number = solution = None
            answer_next = False
        else:
            if content[-2:] == " :":
                answer_next = True
                content = content[:-2]

            match = re.match(PT_CLUE, content)
            if match:
                number = int(match.group(1))
                text = match.group(2)
            else:
                if text is None:  # a special one
                    number = content
                    text = ""
                else:
                    text += " " + content

if __name__ == "__main__":
    import sys
    from .utils import find_files, get_args
    args = get_args(desc='convert xwordinfo HTML to xd format')
    for fn, contents in find_files(*args.inputs):
        xd = parse_xwordinfo(contents, fn)
        print("--- %s ---" % fn)
        print(xd.to_unicode())
