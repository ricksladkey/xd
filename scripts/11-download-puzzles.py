#!/usr/bin/env python3

# Usage:
#  $0 -o <output-zip> -r <recent-downloads.tsv>
#
#  Examines <input> filenames for each source and most recent date; downloads more recent puzzles and saves them to <output-zip>.
#

import urllib.request, urllib.error, urllib.parse
import datetime
import re

from xdfile import utils, metadatabase as metadb
from xdfile.utils import get_args, log, error, warn, summary, debug, open_output, datestr_to_datetime, args_parser
from xdfile.metadatabase import xd_sources_header, xd_sources_row, xd_puzzle_sources, xd_recent_download, xd_recents_header


def construct_xdid(pubabbr, dt):
    return pubabbr + dt.strftime("%Y-%m-%d")


def get_dates_between(before_date, after_date, days_to_advance=1):
    if before_date > after_date:
        before_date, after_date = after_date, before_date

    days_diff = (after_date - before_date).days
    return [before_date + datetime.timedelta(days=x) for x in range(days_to_advance, days_diff, days_to_advance)]


def main():
    p = args_parser('download recent puzzles')
    args = get_args(parser=p)

    outf = open_output()

    today = datetime.date.today()
    todaystr = today.strftime("%Y-%m-%d")

    sources_tsv = ''

    puzzle_sources = xd_puzzle_sources()

    new_recents_tsv = []

    # some downloads may fail, track the last successful ones
    most_recent = {}

    # download new puzzles since most recent download
    for row in metadb.xd_recent_downloads().values():
        pubid = row.pubid
        latest_date = datestr_to_datetime(row.date)

        # by default, keep the previous one
        most_recent[pubid] = row.date

        if pubid not in puzzle_sources:
            warn("unknown puzzle source for '%s', skipping" % pubid)
            continue

        puzsrc = puzzle_sources[pubid]

        if not puzsrc.urlfmt or puzsrc.urlfmt.startswith("#"):
            warn("no source url for '%s', skipping" % pubid)
            continue

        from_date = latest_date
        to_date = today
        dates_to_get = get_dates_between(from_date, to_date, int(puzsrc.freq))
        if not dates_to_get:
            warn("*** %s: nothing to get since %s" % (pubid, from_date))
            continue

        summary("*** %s: downloading %d puzzles from %s to %s" % (pubid, len(dates_to_get), from_date, to_date))

        for dt in sorted(dates_to_get):
            try:
                xdid = construct_xdid(pubid, dt)
                url = dt.strftime(puzsrc.urlfmt)
                fn = "%s.%s" % (xdid, puzsrc.ext)

                debug("downloading '%s' from '%s'" % (fn, url))

                response = urllib.request.urlopen(url)
                content = response.read()

                outf.write_file(fn, content)

                most_recent[pubid] = todaystr
            except (urllib.error.HTTPError, urllib.error.URLError) as err:
                error('%s [%s] %s: %s' % (xdid, err.code, err.reason, url))
            except Exception as e:
                error(str(e))

            sources_tsv += xd_sources_row(fn, url, todaystr)

    for k, v in most_recent.items():
        new_recents_tsv.append(xd_recent_download(k, v))

    if sources_tsv:
        outf.write_file("sources.tsv", xd_sources_header + sources_tsv)

    if new_recents_tsv:
        # on filesystem
        open(metadb.RECENT_DOWNLOADS_TSV, "w").write(xd_recents_header + "".join(sorted(new_recents_tsv)))

if __name__ == "__main__":
    main()
