from email.policy import default
import pywikibot as pwb
import urllib.parse as urlp
import asyncio as aio
import itertools as it
import functools as ft
import traceback
import argparse
import typing as tp
from disambig_basic import bot_save


DEBUG = False

def print_before_call(func: tp.Callable):
    if DEBUG:
        @ft.wraps(func)
        def wrapper(*args, **kwargs):
            print(repr(Task(func, *args, **kwargs)))
            return func(*args, **kwargs)
        return wrapper
    else:
        return func


class Task:
    def __init__(self, func: tp.Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @print_before_call
    def call(self):
        return self.func(*self.args, **self.kwargs)

    def __str__(self):
        return self.func.__name__ + '(' + ', '.join(it.chain((repr(a) for a in self.args), (k + '=' + repr(w) for k, w in self.kwargs))) + ')'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self)}>'


class BaseTaskProcess:
    REDO = object()
    QUIT = object()

    async def add(self, func: tp.Callable, *args, **kwargs):
        while True:
            match func(*args, **kwargs):
                case self.REDO:
                    pass
                case self.QUIT:
                    exit(0)
                case _:
                    break

    async def print(self, *args, **kwargs):
        print(*args, **kwargs)

    async def run(self):
        pass

    async def join(self):
        pass


class TaskProcess(BaseTaskProcess):
    @print_before_call
    def __init__(self):
        self.tasks: aio.Queue[Task] = aio.Queue(maxsize=10)

    @print_before_call
    async def add(self, func: tp.Callable, *args, **kwargs):
        await self.tasks.put(Task(func, *args, **kwargs))

    @print_before_call
    async def print(self, *args, **kwargs):
        await self.add(print, *args, **kwargs)

    @print_before_call
    async def run(self):
        while True:
            task = await self.tasks.get()
            match task.call():
                case self.REDO:
                    await self.tasks.put(task)
                case self.QUIT:
                    exit(0)
            self.tasks.task_done()

    @print_before_call
    async def join(self):
        await self.tasks.join()


BILIBILI_DOMAINS = ('bilibili', 'b23.tv')
USERPATH_QUERYARGS = ('from', 'seid', 'spm_id_from', 'from_spmid', 'referfrom', 'bilifrom',
    'share_source', 'share_medium', 'share_plat', 'share_session_id', 'share_tag', 'share_times',
    'timestamp', 'bbid', 'ts', 'from_source', 'broadcast_type', 'is_room_feed', 'vd_source')
USERPATH_QUERYARGS_EQUAL = [s + '=' if len(s) < 4 else s for s in USERPATH_QUERYARGS]

site: pwb.APISite = pwb.Site()
site.login()


def action(page: pwb.Page, auto_submit: bool = False):
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


async def main(
    pages: tp.Iterable[str | pwb.Page] | None = None,
    start_from: str | None = None,
    asynchronous: bool = True,
    auto_submit: bool = False
):
    if pages:
        pages = (page if isinstance(page, pwb.Page) else pwb.Page(site, page) for page in pages)
    else:
        pages = it.chain(
            *(site.exturlusage(url='*.bilibili.com', protocol=prot, namespaces=['', 'Template', 'Category']) for prot in ('http', 'https'))
        )

    process = TaskProcess() if asynchronous else BaseTaskProcess()
    atask = aio.create_task(process.run())

    async def background():
        skipping = bool(start_from)
        try:
            for page in pages:
                page: pwb.Page
                if skipping:
                    if page.title() == start_from:
                        skipping = False
                    else:
                        continue
                await process.add(print, page.title())
                for link in page.extlinks():
                    if any(s in link for s in BILIBILI_DOMAINS) and any(s in link for s in USERPATH_QUERYARGS_EQUAL):
                        await process.add(action, page, auto_submit=auto_submit)
                        break
        except:
            print("Error occurs:")
            traceback.print_exc()
        else:
            print("Program successfully executed.")
            
    btask = aio.create_task(background())
    await btask
    await process.join()
    atask.cancel()
    print("Program Exited.")

    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pages', nargs='*')
    parser.add_argument('-s', '--start')
    parser.add_argument('-c', '--sync', action='store_true')
    parser.add_argument('-a', '--auto', action='store_true')
    args = parser.parse_args()
    print(args)
    aio.run(main(pages=args.pages, start_from=args.start, asynchronous=not args.sync, auto_submit=args.auto))
