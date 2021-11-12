import pywikibot
import sys
from disambig_basic import find_link, replace_link

def link_replace(old_title: str, new_title: str):
    site = pywikibot.Site()
    page = pywikibot.Page(site, old_title)
    for backlink in page.backlinks():
        if find_link(backlink.text, old_title):
            print(backlink.title(), backlink.full_url())
            # backlink.text = replace_link(backlink.text, old_title, new_title)
            # backlink.save(summary="链接替换：[[" + old_title + "]]→[[" + new_title + "]]"
            #     + "。本次编辑由机器人进行，如修改有误，请撤销或更正，并[[User_talk:C8H17OH|联系操作者]]。",
            #     asynchronous=True, watch="nochange", minor=True, botflag=True)
    print("OK")

def link_replace_main():
    if len(sys.argv) == 3:
        link_replace(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    link_replace_main()
