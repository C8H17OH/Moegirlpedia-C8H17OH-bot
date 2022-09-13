import pywikibot as pwb
import pywikibot.site
pwb.site = pywikibot.site
import urllib.parse as urlp
import itertools
import traceback
import argparse
import typing
from disambig_basic import bot_save
from disambig_task_process import TaskProcess, NoneProcess

site: pwb.APISite = pwb.Site()
site.login()

BILIBILI_DOMAINS = ('bilibili', 'b23.tv')
USERPATH_QUERYARGS = ('from', 'seid', 'spm_id_from', 'from_spmid', 'referfrom', 'bilifrom',
    'share_source', 'share_medium', 'share_plat', 'share_session_id', 'share_tag', 'share_times',
    'timestamp', 'bbid', 'ts', 'from_source', 'broadcast_type', 'is_room_feed', 'vd_source',
    'unique_k')
USERPATH_QUERYARGS_EQUAL = [s + '=' if len(s) < 4 else s for s in USERPATH_QUERYARGS]

def remove_bililink_userpath_action(page: pwb.Page, auto_submit: bool = False):
    newtext = page.text
    removed_queryargs = set()
    for link in page.extlinks():
        res = urlp.urlparse(link)
        if any(s in res.netloc for s in BILIBILI_DOMAINS):
            query_pairs = [e.split('=') for e in res.query.split('&')]
            new_query_pairs = []
            removed = False
            for pair in query_pairs:
                if pair[0] in USERPATH_QUERYARGS:
                    removed = True
                    removed_queryargs.add(pair[0])
                else:
                    new_query_pairs.append(pair)
            if removed:
                newquery = '&'.join('='.join(p) for p in new_query_pairs)
                newlink = urlp.urlunparse((res.scheme, res.netloc, res.path, res.params, newquery, res.fragment))
                newtext = newtext.replace(link, newlink).replace(urlp.unquote(link), newlink)
    print(page.full_url())
    if page.text == newtext:
        return
    pwb.showDiff(page.text, newtext)
    print(removed_queryargs)
    if auto_submit:
        page.text = newtext
        bot_save(page, '清理B站链接参数：' + '，'.join(a for a in removed_queryargs))
        return
    while True:
        print(end='Save? ([Y]es / [N]o / [Q]uit): ')
        cmd = input()
        if cmd == 'y' or cmd == 'Y':
            page.text = newtext
            bot_save(page, '清理B站链接参数：' + '，'.join(a for a in removed_queryargs))
            break
        elif cmd == 'n' or cmd == 'N':
            break
        elif cmd == 'q' or cmd == 'Q':
            return "quit"

def remove_bililink_userpath(
    pages: typing.Iterable[str | pwb.Page] | None = None,
    start_from: str | None = None,
    asynchronous: bool = True,
    auto_submit: bool = False,
    namespaces: typing.Iterable[int | str | pwb.site.Namespace] | None = None
):
    if namespaces is None:
        namespaces = ('Template', '', 'Category')
    skipping = bool(start_from)
    if pages:
        pages = (page if isinstance(page, pwb.Page) else pwb.Page(site, page) for page in pages)
    else:
        pages = itertools.chain(*(
            site.exturlusage(url='*.bilibili.com', protocol=prot, namespaces=ns)
            for prot in ('http', 'https')
            for ns in namespaces
        ))
    try:
        process = TaskProcess() if asynchronous else NoneProcess()
        print(process)
        process.start()
        for page in pages:
            page: pwb.Page
            if skipping:
                if page.title() == start_from:
                    skipping = False
                else:
                    print('skip', page.title())
                    continue
            process.add(print, page.title())
            for link in page.extlinks():
                if any(s in link for s in BILIBILI_DOMAINS) and any(s in link for s in USERPATH_QUERYARGS_EQUAL):
                    # print('(debug) link:', link)
                    process.add(remove_bililink_userpath_action, page, auto_submit=auto_submit)
                    break
        process.wait()
    except:
        print("Error occurs:")
        traceback.print_exc()
        process.wait()
    else:
        print("Program successfully executed.")
    print("Program Exited.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pages', nargs='*')
    parser.add_argument('-s', '--start')
    parser.add_argument('-n', '--ns', nargs='*')
    parser.add_argument('-c', '--sync', action='store_true')
    parser.add_argument('-a', '--auto', action='store_true')
    args = parser.parse_args()
    print(args)
    remove_bililink_userpath(
        pages=args.pages,
        start_from=args.start,
        asynchronous=not args.sync,
        auto_submit=args.auto,
        namespaces=args.ns
    )
