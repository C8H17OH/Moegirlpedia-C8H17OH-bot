import pywikibot as pwb
import pywikibot.site as pwb_site
import urllib.parse as urlp
import traceback
import argparse
from disambig_basic import bot_save
from disambig_task_process import TaskProcess, NoneProcess

site: pwb.APISite = pwb.Site()
site.login()

BILIBILI_DOMAINS = ('bilibili', 'b23.tv')
USERPATH_QUERYARGS = ('from', 'seid', 'spm_id_from', 'from_spmid', 'referfrom', 'bilifrom',
    'share_source', 'share_medium', 'share_plat', 'share_session_id', 'share_tag', 'share_times',
    'timestamp', 'bbid', 'ts', 'from_source', 'broadcast_type', 'is_room_feed')
USERPATH_QUERYARGS_EQUAL = [s + '=' if len(s) < 4 else s for s in USERPATH_QUERYARGS]

def remove_bililink_userpath_action(page: pwb.Page):
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
    pwb.showDiff(page.text, newtext)
    print(removed_queryargs)
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
    pages: list[str] | None = None,
    start: str = '!',
    namespace: int | str | pwb_site.Namespace = 0,
    asynchronous: bool = True
):
    try:
        process = TaskProcess() if asynchronous else NoneProcess()
        print(process)
        process.start()
        for page in (pwb.Page(site, p) for p in pages) if pages else site.allpages(start=start, namespace=namespace, filterredir=False):
            page: pwb.Page
            process.add(print, page.title())
            for link in page.extlinks():
                if any(s in link for s in BILIBILI_DOMAINS) and any(s in link for s in USERPATH_QUERYARGS_EQUAL):
                    process.add(remove_bililink_userpath_action, page)
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
    parser.add_argument('-n', '--ns')
    parser.add_argument('-c', '--sync', action='store_true')
    args = parser.parse_args()
    print(args)
    remove_bililink_userpath(pages=args.pages, start=args.start, namespace=args.ns, asynchronous=not args.sync)
