import pywikibot
import json
import sys
from disambig_linkshere import disambig_linkshere, NoneProcess
# from list_disambig_articles import list_disambig_articles
from disambig_task_process import TaskProcess


def traverse_all_disambigs_redo(site, disambig, process):
    disambig = pywikibot.Page(site, disambig.title())
    except_file = open("scripts/userscripts/disambig_except.json", mode="r", encoding="UTF-8")
    excepts = json.load(except_file)
    if disambig.title() in excepts["DISAMBIG_EXCEPT"]:
        return
    return disambig_linkshere(disambig, process=process, print_procedure=False, do_edit=False, show_manual=False, excepts=excepts)


def traverse_all_disambigs(startfrom=None):
    site = pywikibot.Site()
    disambig_category = pywikibot.Category(site, "Category:消歧义页")
    except_file = open("scripts/userscripts/disambig_except.json", mode="r", encoding="UTF-8")
    excepts = json.load(except_file)
    started = False if startfrom else True
    try:
        process = TaskProcess()
        process.start()
        for disambig in disambig_category.members():
            # print("disambig.title() = " + disambig.title())
            if not started and disambig.title() != startfrom:
                continue
            started = True
            if disambig.title() in excepts["DISAMBIG_EXCEPT"]:
                continue
            ret = disambig_linkshere(disambig, process=process, print_procedure=False, do_edit=False, show_manual=False, excepts=excepts)
            while ret == "redo":
                return traverse_all_disambigs_redo(site, disambig, process)
            if ret == "quit":
                break
            while not process.no_redo():
                for disambig in process.gen_redo():
                    traverse_all_disambigs_redo(site, disambig, process)
            if not process.running:
                print("Process No Longer Running.")
                break
        process.wait()
    except Exception as e:
        print("Erorr occurs:", repr(e))
        process.wait()
    print("Program Exited.")
    except_file.close()


def traverse_all_disambigs_main():
    if len(sys.argv) == 1:
        traverse_all_disambigs()
    elif len(sys.argv) == 2:
        traverse_all_disambigs(sys.argv[1])
    # next time from 黑


if __name__ == '__main__':
    traverse_all_disambigs_main()