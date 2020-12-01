import pywikibot
import re
# from disambig_linkshere import disambig_linkshere


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
        ret = self.title()
        if self.section:
            ret += "#" + self.section
        return ret
    
    def showed_caption(self):
        return self.caption if self.caption else self.link()


def findlinks(text):
    link_tuple_list = re.findall(r"\[\[(?:([^\[\]]*?)\:)?([^\[\]]*?)(?:\(([^\[\]]*?)\))?(?:#([^\[\]]*?))?(?:\|([^\[\]]*?))?\]\]", text)
    # (prefix, core, suffix, section, caption): "[[prefix:core(suffix)#section|caption]]"
    return [Link(link_tuple) for link_tuple in link_tuple_list]


def list_disambig_articles(disambig, dropout_multi_articles=False, dropout_no_keyword=False):
    articles = list()
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
        for article_link in article_links:
            article = article_link.__dict__
            article["title"] = article_link.title()
            # article["link"] = article_link.link()
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
    print("==", disambig.title(), "==")
    print(disambig.full_url())
    for article in articles:
        print(article)
    return articles
    # print(articles)


def list_disambig_articles_main():
    list_disambig_articles("Afterglow")


if __name__ == '__main__':
    list_disambig_articles_main()
