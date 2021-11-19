import typing
import pywikibot
import re
import opencc

s2t = opencc.OpenCC("s2t.json")
t2s = opencc.OpenCC("t2s.json")


class NoneProcess:
    def print(self, *args, **kwargs):
        return print(*args, **kwargs)
    
    def action(self, *args, **kwargs):
        return disambig_linkshere_action(*args, **kwargs)


def bot_save(page: pywikibot.Page, summary: str = "") -> None:
    if summary:
        summary += "。"
    summary += "本次编辑由机器人进行，如修改有误，请撤销或更正，并[[User_talk:C8H17OH|联系操作者]]。"
    page.save(summary=summary, asynchronous=True, watch="nochange", minor=True, botflag=True, tags=["Bot"])


def short_link(page: pywikibot.Page) -> str:
    return page.site.base_url(page.site.article_path + '_?curid=' + str(page.pageid))


def link_preproc(link: str) -> str:
    link = link.strip() # 去除首尾空格
    link = re.escape(link) # 正则表达式化
    link = re.sub(r"(?:\\ |_)", r"(?:\\ |_)", link) # 空格和下划线互通
    if link[0].lower() != link[0].upper():
        link = r"[" + link[0].lower() + link[0].upper() + r"]" + link[1:] # 首字母大小写互通
    ret = ""
    for char in link:
        if s2t.convert(char) != t2s.convert(char):
            ret += r"[" + s2t.convert(char) + t2s.convert(char) + r"]" # 繁简互通
        else:
            ret += char
    return ret


def find_link(text: str, link: str) -> bool:
    pattern = r"\[\[[\ _]*" + link_preproc(link) + r"[\ _]*(\#[^\[\]]*?[\ _]*)?(\|.*?[\ _]*)?[\ _]*\]\]"
    return re.search(pattern, text) != None


def replace_link(text: str, oldlink: str, newlink: str, keep_no_caption: bool = False) -> str:
    oldlink = link_preproc(oldlink)

    # replace "[[oldlink#section|caption]]" to "[[newlink#section|caption]]"
    pattern = r"\[\[[ _]*" + oldlink + r"[ _]*(\#[^\[\]]*?[ _]*)?(\|[^\[\]]*?[ _]*)[ _]*\]\]"
    repl = r"[[" + newlink + r"\1\2]]" # \1 is "#section", \2 is "|caption"
    text = re.sub(pattern, repl, text)

    # if keep_no_caption, then replace "[[oldlink#section]]" to "[[newlink#section]]"
    # else, use old full title as caption, i.e. replace "[[oldlink#section]]" to "[[newlink#section|oldlink#section]]";
    pattern = r"\[\[[ _]*(" + oldlink + r"[ _]*(\#[^\[\]]*?)?)[ _]*\]\]"
    if keep_no_caption:
        repl = r"[[" + newlink + r"\2]]" # \2 is "#section"
    else:
        repl = r"[[" + newlink + r"\2|\1]]" # \1 is "oldlink#section", \2 is "#section"
    text = re.sub(pattern, repl, text)

    # replace "[[File:...|link=<oldlink>]]" (and also "[[Image:...]]") to "[[File:...|link=<newlink>]]"
    pattern = r"\[\[[ _]*((?:[Ff][Ii][Ll][Ee]|[Ii][Mm][Aa][Gg][Ee])[ _]*:.*?\| *link=)[ _]*" + oldlink + r"[ _]*(\|.*?)?\]\]"
    repl = r"[[\1" + newlink + r"\2]]"
    text = re.sub(pattern, repl, text)

    return text


# def original(s):
#     return s

# def capitalize(s):
#     return s.capitalize()

# def minusculize(s):
#     return s[0].lower() + s[1:]


# def text_preproc_func(func, targ, tval, *args, **kwargs):
#     kwargs[targ] = tval
#     ret = func(*args, **kwargs)
#     for convert in (s2t.convert, t2s.convert):
#         for initial in (capitalize, minusculize):
#             proced = convert(initial(tval))
#             if proced != tval:
#                 kwargs[targ] = proced
#                 ret = ret or func(*args, **kwargs)
#     return ret


# def find_link(text, link):
#     ret = find_link_once(text, link)
#     for convert in (s2t.convert, t2s.convert):
#         for initial in (capitalize, minusculize):
#             proced = convert(initial(link))
#             if proced != link:
#                 ret = ret or find_link_once(text, proced)
#     return ret


# def replace_link(text, oldlink, newlink):
#     text = replace_link_once(text, oldlink, newlink)
#     for convert in (s2t.convert, t2s.convert):
#         for initial in (capitalize, minusculize):
#             proced = convert(initial(oldlink))
#             if proced != oldlink:
#                 text = replace_link_once(text, proced, newlink)
#     return text


def find_word(text: str, word: str) -> bool:
    return re.search(link_preproc(word), text) != None


# def find_word(text, word):
#     ret = (text.find(word) >= 0)
#     for convert in (s2t.convert, t2s.convert):
#         for initial in (capitalize, minusculize):
#             proced = convert(initial(word))
#             if proced != word:
#                 ret = ret or (text.find(word) >= 0)
#     return ret


def disambig_linkshere_action(
    disambig: pywikibot.Page,
    autos: typing.List[typing.Tuple[pywikibot.Page, str, pywikibot.Page, typing.Set[str]]],
    manuals: typing.List[typing.Tuple[pywikibot.Page, str, pywikibot.Page, typing.Set[str]]],
    do_edit: bool = False,
    show_manual: bool = False
) -> str:
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
                passes = order.split()[1:]
                if not passes:
                    print(end="Pass which ones? ")
                    passes = input().split()    
                break
    if do_edit:
        index = 0
        for (backlink, redirect_title, article_link, article_relations) in autos:
            index += 1
            if index in passes:
                continue
            backlink.text = replace_link(backlink.text, redirect_title, article_link)
            bot_save(backlink, summary="消歧义：[[" + redirect_title + "]]→[[" + article_link + "]]")
    if show_manual:
        print("====== manuals:", disambig.title(), "======")
        for manual in manuals:
            print(manual.title(), manual.full_url())
    return "done" if do_edit else "deny"


def disambig_basic_test():
    text = "隨故事发展逐渐展現对[[ I am_大老师_yes_]]的好感，曾在遊樂設施上要求[[I_am 大老師_yes ]]拯救她。"
    link = " I_am_大老师 yes"
    word = "大老師"
    repl = "比企谷八幡"
    print(replace_link(text, link, repl))
    print(find_word(text, word))


if __name__ == "__main__":
    disambig_basic_test()
