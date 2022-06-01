# try to reconstruct the disambig codes with OOP, not finished

import pywikibot as pwb
import sys
import typing as tp
import pprint
import itertools
from list_disambig_articles import Link, findlinks
from disambig_basic import find_word, find_link, link_preproc


def get_page_and_redirects(page: pwb.Page) -> tp.List[pwb.Page]:
    return [page] + list(page.backlinks(filter_redirects=True))


class DisambigTerm:
    def __init__(self, link: Link, dlinks: tp.Sequence[Link] = ()):
        self.termlink: Link = link
        self.keywords: tp.Set[str] = set()
        if self.termlink.prefix and self.termlink.prefix not in (
            "Template", "模板", "Category", "分类", "User", "用户", "zhwiki"):
            self.keywords.add(self.termlink.prefix)
        elif self.termlink.suffix:
            self.keywords.add(self.termlink.suffix)
        for dlink in dlinks:
            self.keywords.add(dlink.title)
            if dlink.caption:
                self.keywords.add(dlink.caption)
    
    def __repr__(self) -> str:
        return repr((self.termlink, self.keywords))

def get_disambig_terms(disambig: pwb.Page) -> tp.List[DisambigTerm]:
    terms: tp.List[DisambigTerm] = list()
    for line in disambig.text.splitlines():
        line_split = line.split("————")
        if len(line_split) < 2:
            line_split = line.split("——")
            if len(line_split) < 2:
                continue
        termlinks = findlinks(line_split[0])
        dlinks = findlinks(line_split[1])
        for termlink in termlinks:
            terms.append(DisambigTerm(termlink, dlinks))
    # print((disambig, terms))
    return terms


class TermRelation:
    def __init__(self, term: DisambigTerm):
        self.term: DisambigTerm = term
        self.title: tp.Optional[str] = None
        self.cats: tp.List[pwb.Category] = []
        self.kwlinks: tp.Set[str] = set()

    def __bool__(self) -> bool:
        return bool(self.title or self.cats or self.kwlinks)

    def __repr__(self) -> str:
        return repr({k: v for (k, v) in self.__dict__.items() if v})

def get_disambig_relations(
    disambig: pwb.Page,
    backlink: pwb.Page,
    disambig_terms: tp.Optional[tp.Sequence[DisambigTerm]] = None,
    disambig_redirects: tp.Optional[tp.Sequence[str]] = None,
):
    """
    For given disambig page and its backlink, return the relation between the backlink and each terms in the disambig page.
    
    :param disambig: The disambig page.
    :param backlink: The backlink page.
    :param disambig_terms: The terms of `disambig`. Automatically generated if not provided.
    :param disambig_redirects: The redirect pages of `disambig`. Automatically generated if not provided.
    """
    if disambig_terms is None:
        disambig_terms = get_disambig_terms(disambig)
    if disambig_redirects is None:
        disambig_redirects = get_page_and_redirects(page)
    relations: tp.List[TermRelation] = [TermRelation(term) for term in disambig_terms]
    for relation in relations:
        for keyword in relation.term.keywords:
            if find_word(backlink.title(), keyword):
                relation.title = backlink.title()
            for category in backlink.categories():
                category: pwb.Category
                if find_word(category.title(), keyword):
                    relation.cats.append(category)
    for line in backlink.text.splitlines():
        for redirect in disambig_redirects:
            if find_link(line, redirect.title()):
                for relation in relations:
                    for keyword in relation.term.keywords:
                        if keyword != redirect.title() and find_link(line, keyword):
                            relation.kwlinks.add(keyword)
    relations = [relation for relation in relations if relation]
    # print((disambig, backlink, relations))
    return relations


def get_disambig_relations_for_disambig(
    disambig: pwb.Page,
    skip_ns: list = [],
    skip_term_backlinks: bool = True,
):
    """
    For given disambig page, iterate its backlinks (all pages that links to it), and yield relations between them.
    
    :param disambig: The disambig page.
    :param skip_ns: Skip which namespaces. Default empty.
    :param skip_term_backlinks: Whether skip every backlink that is a term. Default True.
    """
    terms = get_disambig_terms(disambig)
    term_titles = [term.termlink.title for term in terms]
    redirects = get_page_and_redirects(disambig)
    for redirect in redirects:
        for backlink in redirect.backlinks(follow_redirects=False, filter_redirects=False):
            backlink: pwb.Page
            if skip_term_backlinks:
                backlink_redirect_titles = [backlink.title()] + [backlink_redirect.title() for backlink_redirect in backlink.backlinks(filter_redirects=True)]
                if set(map(link_preproc, backlink_redirect_titles)) & set(map(link_preproc, term_titles)):
                    continue
            if backlink.namespace() in skip_ns:
                continue
            yield (redirect, backlink, get_disambig_relations(disambig, backlink, terms, redirects))


def get_linked_disambigs_relations(page: pwb.Page):
    """
    For given page, iterate all disambig pages that it links to, and yield relations between them.
    
    :param page: The page to be checked.
    """
    for linkedPage in page.linkedPages():
        linkedPage: pwb.Page
        # yield (linkedPage,)
        if linkedPage.isDisambig():
            yield (linkedPage, get_disambig_relations(linkedPage, page))


if __name__ == '__main__':
    site = pwb.Site()
    page = pwb.Page(site, title=sys.argv[1] if len(sys.argv) > 1 else 'Afterglow')
    for relation in get_disambig_relations_for_disambig(page, skip_ns=['User']):
        pprint.pprint(relation)
    print(end='...')
    input()
    page = pwb.Page(site, title=sys.argv[2] if len(sys.argv) > 2 else 'Overidea')
    for relation in get_linked_disambigs_relations(page):
        print(relation)
    print('OK')
