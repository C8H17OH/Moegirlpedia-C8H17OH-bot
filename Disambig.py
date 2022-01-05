# try to reconstruct the disambig codes with OOP, not finished

import sys
import pywikibot
import typing
import itertools
from list_disambig_articles import Link, findlinks
from disambig_basic import find_word, find_link


class DisambigTerm:
    def __init__(self, link: Link):
        self.termlink: Link = link
        self.keywords: typing.Set[str] = set()
        if self.termlink.prefix and self.termlink.prefix not in (
            "Template", "模板", "Category", "分类", "User", "用户", "zhwiki"):
            self.keywords.add(self.termlink.prefix)
        elif self.termlink.suffix:
            self.keywords.add(self.termlink.suffix)

    def describe(self, dlinks: typing.List[Link]) -> None:
        for dlink in dlinks:
            self.keywords.add(dlink.title())
            if dlink.caption:
                self.keywords.add(dlink.caption)
    
    def __repr__(self) -> str:
        return repr(self.termlink) + ': ' + repr(self.keywords)


class DisambigPage:
    def __init__(self, page: pywikibot.Page):
        self.page: pywikibot.Page = page
        self.terms: typing.List[DisambigTerm] = list()
        for line in page.text.splitlines():
            line_split = line.split("————")
            if len(line_split) < 2:
                line_split = line.split("——")
                if len(line_split) < 2:
                    continue
            termlinks = findlinks(line_split[0])
            dlinks = findlinks(line_split[1])
            for termlink in termlinks:
                term = DisambigTerm(termlink)
                term.describe(dlinks)
                self.terms.append(term)
        print((page, self.terms))

    def check_backlinks(self) -> None:
        class TermRelation:
            def __init__(self, term: DisambigTerm):
                self.term: DisambigTerm = term
                self.title: typing.Optional[str] = None
                self.cats: typing.List[pywikibot.Category] = []
                self.kwlinks: typing.Set[str] = set()
            def __bool__(self) -> bool:
                return bool(self.title or self.cats or self.kwlinks)
            def __repr__(self) -> str:
                return repr({k: v for (k, v) in self.__dict__.items() if v})
        # all_relations: typing.List[(pywikibot.Page, pywikibot.Page, typing.List[TermRelation])] = []
        for redirect in itertools.chain([self.page], self.page.backlinks(filter_redirects=True)):
            for backlink in redirect.backlinks(filter_redirects=False):
                relations: typing.List[TermRelation] = [TermRelation(term) for term in self.terms]
                for relation in relations:
                    for keyword in relation.term.keywords:
                        if find_word(backlink.title(), keyword):
                            relation.title = backlink.title()
                        for category in backlink.categories():
                            if find_word(category.title(), keyword):
                                relation.cats.append(category)
                for line in backlink.text.splitlines():
                    if find_link(line, redirect.title()):
                        for relation in relations:
                            for keyword in relation.term.keywords:
                                if keyword != redirect.title() and find_link(line, keyword):
                                    relation.kwlinks.add(keyword)
                relations = [relation for relation in relations if relation]
                # all_relations.append((redirect, backlink, relations))
                print((redirect, backlink, relations))


if __name__ == '__main__':
    site = pywikibot.Site()
    page = pywikibot.Page(site, title=sys.argv[1] if len(sys.argv) > 1 else 'Afterglow')
    d = DisambigPage(page)
    print(end='...')
    input()
    d.check_backlinks()
