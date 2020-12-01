import pywikibot
import json
import sys
from disambig_linkshere import disambig_linkshere
from list_disambig_articles import list_disambig_articles


def traverse_all_disambigs(startfrom=None):
    site = pywikibot.Site()
    disambig_category = pywikibot.Category(site, "Category:消歧义页")
    except_file = open("scripts/userscripts/disambig_except.json")
    excepts = json.load(except_file)
    started = False if startfrom else True
    for disambig in disambig_category.members():
        if not started and disambig.title() != startfrom:
            continue
        started = True
        if disambig.title() in excepts["DISAMBIG_EXCEPT"]:
            continue
        ret = disambig_linkshere(disambig, do_edit=False, show_manual=False,
            backlink_except=(excepts["BACKLINK_EXCEPT"].get(disambig.title()) or list()) + (excepts["BACKLINK_EXCEPT"].get("") or list()))
        while ret == "redo":
            except_file = open("scripts/userscripts/disambig_except.json")
            excepts = json.load(except_file)
            if disambig.title() in excepts["DISAMBIG_EXCEPT"]:
                continue
            ret = disambig_linkshere(disambig, do_edit=False, show_manual=False,
                backlink_except=(excepts["BACKLINK_EXCEPT"].get(disambig.title()) or list()) + (excepts["BACKLINK_EXCEPT"].get("") or list()))
        if ret == "quit":
            break


def traverse_all_disambigs_main():
    if len(sys.argv) == 1:
        traverse_all_disambigs()
    elif len(sys.argv) == 2:
        traverse_all_disambigs(sys.argv[1])
    # next time from 家庭教师


if __name__ == '__main__':
    traverse_all_disambigs_main()
