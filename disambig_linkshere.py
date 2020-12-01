import pywikibot
import re
import sys
# from itertools import chain
from list_disambig_articles import list_disambig_articles


def find_link(text, link):
    pattern = r"\[\[" + re.escape(link) + r"(#[^\[\]]*?)?(\|.*?)?\]\]"
    return re.search(pattern, text) != None


def replace_link(text, oldlink, newlink):
    pattern = r"\[\[" + re.escape(oldlink) + r"(#[^\[\]]*?)?(\|[^\[\]]*?)\]\]"
    repl = r"[[" + newlink + r"\1\2]]"
    text = re.sub(pattern, repl, text)
    pattern = r"\[\[" + re.escape(oldlink) + r"(#[^\[\]]*?)?\]\]"
    repl = r"[[" + newlink + r"\1|" + oldlink + r"]]"
    text = re.sub(pattern, repl, text)
    return text


def disambig_linkshere(disambig, articles=None, do_edit=False, show_manual=False, backlink_except=None):
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
                print("Error: lack title and categories, suffix, or prefix in" + article)
                return False
    else:
        articles = list_disambig_articles(disambig, dropout_multi_articles=True, dropout_no_keyword=True)
    
    autos = list()
    manuals = list()
    article_titles = list(article["title"] for article in articles)

    if all((any(("崩坏" in keyword for keyword in article["keywords"])) for article in articles)): # 崩坏学园2 and 崩坏3 # f**k
        return "skip"
    
    # for redirect in chain(iter([disambig]), disambig.backlinks(filter_redirects=True)):
    for redirect in [disambig] + list(disambig.backlinks(filter_redirects=True)):
        print("====", redirect.title(), "====")
        # for linksto in site.search("linksto:" + disambig.title()):
        for backlink in redirect.backlinks(filter_redirects=False):
            if "Talk" in backlink.namespace() or "talk" in backlink.namespace():
                continue
            elif not backlink.namespace() in ("", "Template"):
                manuals.append(backlink)
                continue
            if backlink.title() in article_titles \
                or (backlink_except and backlink.title() in backlink_except) \
                or "Category:消歧义页" in (category.title() for category in backlink.categories()) \
                or not find_link(backlink.text, redirect.title()):
                continue
            raw_relations = dict() # categories and keyword links related to articles
            for article in articles:
                raw_relations[article["title"]] = set()
                for keyword in article["keywords"]:
                    for category in backlink.categories():
                        if category.title().find(keyword) >= 0:
                            raw_relations[article["title"]].add(category.title())
            for line in backlink.text.splitlines():
                if find_link(line, redirect.title()):
                    for article in articles:
                        for keyword in article["keywords"]:
                            if find_link(line, keyword):
                                raw_relations[article["title"]].add(keyword)
            relations = dict()
            for article_title in raw_relations:
                if raw_relations[article_title]:
                   relations[article_title] = raw_relations[article_title]
            print(backlink.title(), relations, backlink.full_url(), sep=", ")
            if len(relations) != 1:
                manuals.append(backlink)
                continue
            article_title = list(relations.keys())[0]
            autos.append((backlink, redirect.title(), article_title, relations[article_title]))
    
    if not autos:
        return "none"
    
    print("====== autos:", disambig.title(), "======")
    index = 0
    for (backlink, redirect_title, article_title, categories) in autos:
        index += 1
        print(index, backlink.title(), redirect_title, article_title, categories, backlink.full_url(), sep=", ")

    passes = list()
    if not do_edit:
        while True:
            print(end="Action? (y[es] / [n]o / [p]ass some / [r]edo / [q]uit): ")
            order = input()
            if not order:
                pass
            elif order[0] == 'y':
                do_edit = True
                break
            elif order[0] == 'n':
                break
            elif order[0] == 'r':
                return "redo"
            elif order[0] == 'q':
                return "quit"
            elif order[0] == 'p':
                print(end="Pass which ones? ")
                passes = input().split()
                break
    
    if do_edit:
        index = 0
        for (backlink, redirect_title, article_title, categories) in autos:
            index += 1
            if index in passes:
                continue
            backlink.text = replace_link(backlink.text, redirect_title, article_title)
            backlink.save(summary="消歧义：[[" + redirect_title + "]]→[[" + article_title + "]]"
                + "。本次编辑由机器人进行，如修改有误，请撤销或更正，并[[User_talk:C8H17OH|联系操作者]]。",
                asynchronous=True, watch="nochange", minor=True, botflag=True)
    
    if show_manual:
        print("====== manuals:", disambig.title(), "======")
        for manual in manuals:
            print(manual.title(), manual.full_url())
    
    return "done" if do_edit else "deny"


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

    if len(sys.argv) == 2:
        site = pywikibot.Site()
        disambig = pywikibot.Page(site, sys.argv[1])
        disambig_linkshere(disambig, do_edit=False, show_manual=False)
    

if __name__ == '__main__':
    disambig_linkshere_main()
