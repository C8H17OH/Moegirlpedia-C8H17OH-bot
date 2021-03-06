import pywikibot
import re
import opencc

s2t = opencc.OpenCC("s2t.json")
t2s = opencc.OpenCC("t2s.json")


class NoneProcess():
    def print(self, *args, **kwargs):
        return print(*args, **kwargs)
    
    def action(self, *args, **kwargs):
        return disambig_linkshere_action(*args, **kwargs)


def bot_save(page: pywikibot.Page, summary: str = ""):
    if summary:
        summary += "。"
    summary += "本次编辑由机器人进行，如修改有误，请撤销或更正，并[[User_talk:C8H17OH|联系操作者]]。"
    page.save(summary=summary, asynchronous=True, watch="nochange", minor=True, botflag=True)


def link_preproc(link):
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


def find_link(text, link):
    pattern = r"\[\[[\ _]*" + link_preproc(link) + r"[\ _]*(\#[^\[\]]*?[\ _]*)?(\|.*?[\ _]*)?[\ _]*\]\]"
    return re.search(pattern, text) != None


def replace_link(text, oldlink, newlink):
    pattern = r"\[\[[\ _]*" + link_preproc(oldlink) + r"[\ _]*(\#[^\[\]]*?[\ _]*)?(\|[^\[\]]*?[\ _]*)[\ _]*\]\]"
    repl = r"[[" + newlink + r"\1\2]]"
    text = re.sub(pattern, repl, text)
    pattern = r"\[\[[\ _]*(" + link_preproc(oldlink) + r")[\ _]*(\#[^\[\]]*?)?[\ _]*\]\]"
    repl = r"[[" + newlink + r"\2|\1]]"
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


def find_word(text, word):
    return re.search(link_preproc(word), text) != None


# def find_word(text, word):
#     ret = (text.find(word) >= 0)
#     for convert in (s2t.convert, t2s.convert):
#         for initial in (capitalize, minusculize):
#             proced = convert(initial(word))
#             if proced != word:
#                 ret = ret or (text.find(word) >= 0)
#     return ret


def disambig_linkshere_action(disambig, autos, manuals, do_edit=False, show_manual=False):
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
            backlink.save(summary="消歧义：[[" + redirect_title + "]]→[[" + article_link + "]]"
                + "。本次编辑由机器人进行，如修改有误，请撤销或更正，并[[User_talk:C8H17OH|联系操作者]]。",
                asynchronous=True, watch="nochange", minor=True, botflag=True)
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
