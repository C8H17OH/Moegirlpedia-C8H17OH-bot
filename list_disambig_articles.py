import pywikibot
import re
from typing import Union, Optional
# from disambig_linkshere import disambig_linkshere
from disambig_task_process import TaskProcess
from disambig_basic import NoneProcess


class Link:
    def __init__(self, link_tuple):
        (prefix, core, suffix, section, caption) = link_tuple
        self.prefix = prefix
        self.core = core
        self.suffix = suffix
        self.section = section
        self.caption = caption

    def title(self):
        ret = str()
        if self.prefix:
            ret += self.prefix + ":"
        ret += self.core
        if self.suffix:
            ret += "(" + self.suffix + ")"
        return ret

    def link(self):
        ret = Link.title(self)
        if self.section:
            ret += "#" + self.section
        return ret

    def showed_caption(self):
        return self.caption if self.caption else self.link()


def clean_zero_width_spaces(text):
    return text.replace("\u200e", "")


def findlinks(text):
    link_pattern = r"(?:[\ _]*([^\[\]]*?)\:)([^\[\]]*?)(?:\(([^\[\]]*?)\))?(?:\#([^\[\]]*?)[\ _]*)?(?:\|[\ _]*([^\[\]]*?)[\ _]*)?"
    link_tuple_list = re.findall(r"(?:\[\[|\{\{[\ _]*(?:coloredlink|dl)[\ _]*\|[^\|]*\|)" + link_pattern + r"\]\]", text)
    # (prefix, core, suffix, section, caption):
    # "[[prefix:core(suffix)#section|caption]]"
    # "{{coloredlink|prefix:core(suffix)#section|caption}}"
    # "{{dl|prefix:core(suffix)#section}}"
    return [Link(tuple(map(clean_zero_width_spaces, link_tuple))) for link_tuple in link_tuple_list]


def list_disambig_articles(
        disambig: pywikibot.Page,
        process: Union[TaskProcess, NoneProcess] = NoneProcess(),
        article_except: Optional[list] = None,
        dropout_multi_articles: bool = False,
        dropout_no_keyword: bool = False
        ) -> list:
    # print("list_disambig_articles(" + disambig.title() + ")")
    articles = list()
    process.print("==", disambig.title(), "==")
    process.print(disambig.full_url())
    if len(list(disambig.categories())) > 2:
        process.print(list(disambig.categories()))
    for line in disambig.text.splitlines():
        line_split = line.split("————")
        if len(line_split) < 2:
            line_split = line.split("——")
            if len(line_split) < 2:
                continue
        article_links = findlinks(line_split[0])
        keyword_links = findlinks(line_split[1])
        if not article_links \
            or (dropout_multi_articles and len(article_links) > 1) \
            or (dropout_no_keyword and not keyword_links):
            continue
        process.print(line)
        for article_link in article_links:
            if article_except and article_link.title() in article_except:
                continue
            article = article_link.__dict__
            article["title"] = article_link.title()
            article["link"] = article_link.link()
            keywords = set()
            if article_link.prefix and article_link.prefix not in (
                "Template", "模板", "Category", "分类", "User", "用户", "zhwiki"):
                keywords.add(article_link.prefix)
            elif article_link.suffix:
                keywords.add(article_link.suffix)
            for keyword_link in keyword_links:
                keywords.add(keyword_link.title())
                if keyword_link.caption:
                    keywords.add(keyword_link.caption)
            article["keywords"] = keywords
            articles.append(article)
    # for article in articles:
    #     process.print(article)
    return articles
    # process.print(articles)


def list_disambig_articles_main():
    # list_disambig_articles("Afterglow")
    pass


if __name__ == '__main__':
    list_disambig_articles_main()
