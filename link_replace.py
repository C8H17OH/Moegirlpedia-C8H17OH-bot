import pywikibot, pywikibot.site
import argparse
from disambig_basic import find_link, replace_link, bot_save, short_link

def link_replace(
    old_title: str,
    new_title: str,
    keep_no_caption: bool = False,
    show_diff: bool = False,
    auto_submit: bool = False,
    skip_user: bool = True,
    skip_talk: bool = True
):
    site = pywikibot.Site()
    page = pywikibot.Page(site, old_title)
    for backlink in page.backlinks():
        if skip_user and backlink.namespace() == 'User:':
            continue
        if skip_talk and backlink.namespace() % 2 == 1:
            continue
        if find_link(backlink.text, old_title):
            print(backlink.title(), short_link(backlink), sep=' | ')
            if show_diff or auto_submit:
                newtext = replace_link(backlink.text, old_title, new_title, keep_no_caption)
            if show_diff:
                pywikibot.showDiff(backlink.text, newtext)
            if auto_submit:
                backlink.text = newtext
                bot_save(backlink, "链接替换：[[" + old_title + "]]→[[" + new_title + "]]")
    print("OK")

def link_replace_main():
    parser = argparse.ArgumentParser(description='Replace a link to another in the whole site.')
    parser.add_argument('old_title', help='old link\'s title')
    parser.add_argument('new_title', help='new link\'s title')
    parser.add_argument('-k', '--keep-no-caption', action='store_true', help='keep no caption (default: use old full title as new caption)')
    parser.add_argument('-d', '--show-diff',       action='store_true', help='show difference between before and after edit, before submit')
    parser.add_argument('-a', '--auto-submit',     action='store_true', help='auto submit every edit')
    parser.add_argument('-u', '--userpage',        action='store_true', help='deal with userpage')
    parser.add_argument('-t', '--talkpage',        action='store_true', help='deal with talkpage')
    args = parser.parse_args()
    # print(args)
    if args.old_title and args.new_title:
        link_replace(args.old_title, args.new_title, args.keep_no_caption, args.show_diff, args.auto_submit, not args.userpage, not args.talkpage)

if __name__ == "__main__":
    link_replace_main()
