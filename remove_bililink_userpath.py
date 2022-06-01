import pywikibot as pwb
import pywikibot.site as pwb_site
import re
import argparse
from disambig_basic import bot_save
from disambig_task_process import TaskProcess, NoneProcess

site: pwb.APISite = pwb.Site()
site.login()

def remove_bililink_userpath_action(page: pwb.Page):
    domain = r'((?:bilibili\.com|b23\.tv)/.*?)'
    userpath = r'from=search|seid=\d+|(spm_id_from|from_spmid)=\d+\.\d+\.[^\s\]\?&<\|#]*'
    pattern = domain + r'\?' + userpath + r'(' + userpath + r')*'
    newtext = re.sub(domain + r'(\?(.*?=.*?)(&.*?=.*?)*)(&' + userpath + r')+', r'\1\2',
        re.sub(pattern + r'&', r'\1?',
        re.sub(pattern + r'(?!&)', r'\1', page.text)))
    print(page.full_url())
    pwb.showDiff(page.text, newtext)
    while True:
        print(end='Save? ([Y]es / [N]o / [Q]uit): ')
        cmd = input()
        if cmd == 'y' or cmd == 'Y':
            page.text = newtext
            bot_save(page, '删除B站链接中的“spm_id_from”等无用GET参数')
            break
        elif cmd == 'n' or cmd == 'N':
            break
        elif cmd == 'q' or cmd == 'Q':
            return "quit"
    re.search()

def remove_bililink_userpath(start: str = '!', namespace: int | pwb_site.Namespace = 0, asynchronous: bool = True):
    process = TaskProcess() if asynchronous else NoneProcess()
    print(process)
    process.start()
    for page in site.allpages(start=start, namespace=namespace, filterredir=False):
        page: pwb.Page
        process.add(print, page.title())
        for link in page.extlinks():
            if any(s in link for s in ('bilibili.com', 'b23.tv')) and any(s in link for s in ('from=search', 'seid', 'spm_id_from')):
                process.add(remove_bililink_userpath_action, page)
                break
    process.wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start')
    parser.add_argument('-n', '--ns')
    parser.add_argument('-c', '--sync', action='store_true')
    args = parser.parse_args()
    print(args)
    remove_bililink_userpath(start=args.start, namespace=args.ns, asynchronous=not args.sync)
