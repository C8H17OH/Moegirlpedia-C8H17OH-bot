import json
import typing
import pywikibot
# import re
# import asyncio
# import json
import sys
# from itertools import chain
from disambig_basic import *
from disambig_task_process import TaskProcess
from list_disambig_articles import list_disambig_articles


def disambig_linkshere(
    disambig: pywikibot.Page,
    articles: typing.List[typing.Dict[str, typing.Union[str, typing.Set[str]]]] = [],
    process: typing.Union[TaskProcess, NoneProcess] = NoneProcess(),
    print_procedure: bool = True,
    do_edit: bool = False,
    show_manual: bool = False,
    excepts: typing.Dict[str, typing.Union[typing.List[str], typing.Dict[str, typing.List[str]]]] = {}
) -> typing.Union[str, bool]:
    # print("disambig_linkshere(" + disambig.title() + ")")
    if excepts:
        backlink_except = (excepts["BACKLINK_EXCEPT"].get(disambig.title()) or list()) + (excepts["BACKLINK_EXCEPT"].get("") or list())
        article_except = (excepts["ARTICLE_EXCEPT"].get(disambig.title()) or list()) + (excepts["ARTICLE_EXCEPT"].get("") or list())
    else:
        backlink_except = article_except = list()
    
    if articles:
        for article in articles:
            if article.get("title") and article.get("keywords"):
                continue
            if not article.get("keywords"):
                article["keywords"] = set()
            if article.get("prefix"):
                article["title"] = article["prefix"] + ':' + disambig.title()
                if article.get("suffix"):
                    article["title"] += '(' + article["suffix"] + ')'
                article["keywords"].add(article["prefix"])
            elif article.get("suffix"):
                article["title"] = disambig.title() + '(' + article["suffix"] + ')'
                article["keywords"].add(article["suffix"])
            else:
                process.print("Error: lack title and categories, suffix, or prefix in" + article)
                return False
    else:
        articles = list_disambig_articles(disambig, process=process, article_except=article_except, dropout_multi_articles=True, dropout_no_keyword=True)
        if not articles:
            return "none"
    
    # print("articles =", articles)
    
    autos = list()
    manuals = list()
    article_titles = list(article["title"] for article in articles)

    # if all((any(("崩坏" in keyword for keyword in article["keywords"])) for article in articles)): # 崩坏学园2 and 崩坏3 # f**k
    #     return "skip"
    
    # print([disambig] + list(disambig.backlinks(filter_redirects=True)))
    # for redirect in chain(iter([disambig]), disambig.backlinks(filter_redirects=True)):
    for redirect in [disambig] + list(disambig.backlinks(filter_redirects=True)):
        # print("redirect = " + redirect.title())
        if print_procedure:
            process.print("====", redirect.title(), "(" + str(len(list(redirect.backlinks(filter_redirects=False)))) + ") ====")
        # for linksto in site.search("linksto:" + disambig.title()):
        for backlink in redirect.backlinks(follow_redirects=False, filter_redirects=False):
            backlink: pywikibot.Page
            # print("backlink = " + backlink.title())
            if "Talk" in backlink.namespace() or "talk" in backlink.namespace():
                continue
            elif not backlink.namespace() in ("", "Template"):
                manuals.append(backlink)
                continue
            backlink_redirect_titles = [backlink.title()] + list(backlink_redirect.title() for backlink_redirect in backlink.backlinks(filter_redirects=True))
            # backlink_redirect_titles += list(map(capitalize, backlink_redirect_titles)) + list(map(minusculize, backlink_redirect_titles))
            # backlink_redirect_titles += list(map(s2t.convert, backlink_redirect_titles)) + list(map(t2s.convert, backlink_redirect_titles))
            # print(backlink_redirect_titles)
            if (set(map(link_preproc, backlink_redirect_titles)) & set(map(link_preproc, article_titles + backlink_except))) \
                or backlink.isDisambig() \
                or not find_link(backlink.text, redirect.title()):
                continue
            relations = dict() # categories and keyword links related to articles
            for article in articles:
                relation = set()
                for keyword in article["keywords"]:
                    for category in backlink.categories():
                        if find_word(category.title(), keyword):
                            relation.add(category.title())
                    if find_word(backlink.title(), keyword):
                        relation.add(backlink.title())
                if relation:
                    relations[article["link"]] = relation
            if not relations:
                for line in backlink.text.splitlines():
                    if find_link(line, redirect.title()):
                        for article in articles:
                            for keyword in article["keywords"]:
                                if keyword != redirect.title() and find_link(line, keyword):
                                    if article["link"] not in relations:
                                        relations[article["link"]] = set()
                                    relations[article["link"]].add("keyword=" + keyword)
            if print_procedure:
                process.print(backlink.title(), relations, backlink.full_url(), sep=", ")
            if len(relations) != 1:
                manuals.append(backlink)
                continue
            article_link = list(relations.keys())[0]
            autos.append((backlink, redirect.title(), article_link, relations[article_link]))
    
    if not autos:
        return "none"
    
    process.print("====== autos:", disambig.title(), "======")
    index = 0
    for (backlink, redirect_title, article_link, article_relations) in autos:
        index += 1
        process.print(index, backlink.title(), redirect_title, article_link, article_relations, backlink.full_url(), sep=", ")
        newtext = replace_link(backlink.text, redirect_title, article_link)
        process.add(pywikibot.showDiff, backlink.text, newtext)

    # if asynchronous:
        # result_file = open("scripts/userscripts/disambig_result.json", mode="r", encoding="UTF-8")
        # result_json = json.load(result_file)
        # result_file.close()
        # result_json[disambig.title()] = list((backlink.title(), redirect_title, article_link, tuple(article_relations))
        #     for (backlink, redirect_title, article_link, article_relations) in autos)
        # result_file = open("scripts/userscripts/disambig_result.json", mode="w", encoding="UTF-8")
        # json.dump(result_json, result_file, ensure_ascii=False, indent=4)
        # result_file.close()
    # else:
    return process.action(disambig, autos, manuals, do_edit=do_edit, show_manual=show_manual)


def disambig_linkshere_main():
    # disambig_linkshere("艾拉", [
    #     {"suffix": "暗夜协奏曲"},
    #     {"suffix": "可塑性记忆"},
    #     {"prefix": "战舰少女"},
    #     {"suffix": "崩坏系列", "keywords": ["崩坏"]},
    #     {"prefix": "战双帕弥什"},
    #     {"title": "Isla(海底囚人)", "keywords": ["海底囚人"]},
    # ], False, False)

    # disambig_linkshere("安娜", [
    #     {"suffix": "冰雪奇缘"},
    #     {"prefix": "火焰之纹章"},
    #     {"suffix": "杀戮公主"},
    #     {"suffix": "月光嘉年华"},
    #     {"suffix": "独角兽", "keywords": ["高达"]},
    #     {"suffix": "血族手游", "keywords": ["血族"]},
    #     {"suffix": "安娜"},
    #     {"title": "美杜莎(Fate)", "keywords": ["Fate"]},
    #     {"suffix": "封印者"},
    # ], do_edit=False, show_manual=True)

    site = pywikibot.Site()
    if len(sys.argv) == 2:
        excepts_file = open("disambig_except.json", mode="r", encoding="UTF-8")
        excepts = json.load(excepts_file)
        disambig = pywikibot.Page(site, sys.argv[1])
        disambig_linkshere(disambig, excepts=excepts, do_edit=False, show_manual=True)
        excepts_file.close()
    else:
        disambig = pywikibot.Page(site, "芭芭拉")
        disambig_linkshere(disambig, [
            {"suffix": "原神"}
        ], do_edit=False, show_manual=True)
    

if __name__ == '__main__':
    disambig_linkshere_main()
