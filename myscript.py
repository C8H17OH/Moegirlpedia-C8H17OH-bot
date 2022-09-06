import pywikibot, pywikibot.textlib, pywikibot.page
import mwparserfromhell as mw
import re
import difflib
import sys, traceback
import json
import datetime
import pprint
import typing
import itertools
from disambig_basic import find_link, replace_link, bot_save, link_preproc, template_and_redirects_regex, short_url
from list_disambig_articles import findlinks

site: pywikibot.APISite = pywikibot.Site()
site.login()

def list_birthday_celebration_description():
    title = "Template:生日祝福"
    page = pywikibot.Page(site, title)
    # print(len(list(page.backlinks())))
    for embed in page.embeddedin(filter_redirects=False):
        for templateWithParams in embed.templatesWithParams():
            if templateWithParams[0] == page:
                for param in templateWithParams[1]:
                    if re.search(r" *描述 *= *", param) != None:
                        print(embed.title(), param, sep=": ")
                break

def test_bot_save():
    page = pywikibot.Page(site, 'User:C8H17OH-bot')
    page.text += '\n\nAh ah, no'
    bot_save(page, summary='test bot_save')

def modify_Houbunsha_family_template(startfrom: str = ''):
    # oldtext = '{{\s*芳文社(?=\s*(?:\|.*)?}})'
    # newtext = '{{芳文社|漫画网站'
    # text = '{{芳文社top}}\n{{芳文社|xxx}}'
    # print(re.sub(oldtext, newtext, text))
    # return
    category = pywikibot.Category(site, 'Category:芳文社')
    started = not startfrom
    for subcat in category.subcategories():
        if subcat.title().startswith('Category:COMIC'):
            param = '漫画网站'
        elif subcat.title().startswith('Category:Manga'):
            param = '漫画杂志'
        else:
            print('pass')
            continue
        pattern = '{{\s*芳文社(?=\s*(?:\|.*)?}})'
        repl = '{{芳文社|' + param
        for article in subcat.articles():
            print(subcat.title(), article.title(), sep=', ')
            if not started and article.title() == startfrom:
                started = True
            if not started:
                continue
            for templateWithParam in article.templatesWithParams():
                if templateWithParam[0].title() != 'Template:芳文社':
                    continue
                print(templateWithParam)
                if param not in templateWithParam[1]:
                    newtext = re.sub(pattern, repl, article.text)
                    pywikibot.showDiff(article.text, newtext)
                    article.text = newtext
                    bot_save(article, '文本替换："' + pattern + '" → "' + repl + '"')
                break

def modify_Fallout_family_template(do_edit: bool = False):
    subgroup_and_newparams: list[tuple[str, str]] = [('游戏相关', '游戏'), ('人物', '人物'), ('世界观与道具', '道具'), ('登场组织', '组织'), ('重要地点', '地点')]
    template = pywikibot.Page(site, 'Template:辐射')
    invoke = '#(?:' + '|'.join(pywikibot.textlib._ignore_case(mw) for mw in site.getmagicwords('invoke')) + ')'
    for (function, params) in pywikibot.textlib.extract_templates_and_params(text=template.text, remove_disabled_parts=True, strip=True, filter_parser_functions=True):
        if not (re.match('^' + invoke + r':[Nn]av$', function) and params.get('1', '').strip() == 'box' and params.get('2', '').strip() == 'subgroup'):
            continue
        for (subgroup, np) in subgroup_and_newparams:
            if subgroup in params.get('title', ''):
                newparam = np
                break
        else:
            print(params.get('title', None))
            continue
        pattern = r'{{\s*辐射(?=\s*(?:\|.*)?}})'
        repl = r'{{辐射|' + newparam
        for key, value in params.items():
            if not key.startswith('list'):
                continue
            for link in findlinks(value):
                page = pywikibot.Page(site, link.title)
                if not page.exists():
                    continue
                for (tl, p) in pywikibot.textlib.extract_templates_and_params(text=page.text, remove_disabled_parts=True, strip=True):
                    if tl != '辐射' or p.get('1', '').strip() == newparam:
                        continue
                    print(page.title())
                    newtext = re.sub(pattern, repl, page.text)
                    pywikibot.showDiff(page.text, newtext)
                    if do_edit:
                        page.text = newtext
                        bot_save(page, '文本替换："' + pattern + '" → "' + repl + '"')


def test_replace_link(title: str, oldlink: str, newlink: str):
    page = pywikibot.Page(site, title)
    page.text = replace_link(page.text, oldlink, newlink)
    bot_save(page)


def search_template_with_parameter(title: str, parameter: str):
    page = pywikibot.Page(site, title, ns='Template')
    redirects = link_preproc(title) + ''.join(('|' + link_preproc(redirect.title(with_ns=False))) for redirect in page.backlinks(filter_redirects=True))
    results = []
    for embed in page.embeddedin():
        embed: pywikibot.Page
        result = []
        print(embed.title(), end=': [', flush=True)
        for (template, params) in pywikibot.textlib.extract_templates_and_params(text=embed.text, remove_disabled_parts=True, strip=True):
            template: str
            params: pywikibot.textlib.OrderedDict
            if re.fullmatch(redirects, template):
                key, value = parameter, params.get(parameter)
                if not value:
                    for param in params:
                        try:
                            if site.expand_text(param, title=embed.title()) == parameter:
                                key, value = param, params[param]
                                break
                        except Exception:
                            traceback.print_exc()
                    else:
                        print((template, False), end=', ', flush=True)
                        continue
                res = (template, key, value)
                result.append(res)
                print(res, end=', ', flush=True)
        print(']')
        if result:
            results.append((embed.title(), result))
    print('========')
    count = 0
    for title_res in results:
        print(title_res)
        count += len(title_res[1])
    print('Total:', len(results), 'pages,', count, 'uses')

def traverse_template_usages(title: str):
    # json format: {
    #   embed_page_1: [
    #       (used_template_name, {
    #           key1: value1,
    #           key2: value2,
    #           ...
    #       }),
    #       (used_template_name, {
    #           key1: value1,
    #           key2: value2,
    #           ...
    #       }),
    #       ...
    #   ],
    #   embed_page_2: [...],
    #   ...
    # }
    filename = 'Usages of Template ' + title + '.json'
    results = {}
    # try:
    #     with open(filename, mode='r', encoding='utf-8') as f:
    #         results = json.load(f)
    # except:
    #     pass
    page = pywikibot.Page(site, title, ns='Template')
    redirects = link_preproc(title) + ''.join(('|' + link_preproc(redirect.title(with_ns=False))) for redirect in page.backlinks(filter_redirects=True))
    count = 0
    for embed in page.embeddedin():
        embed: pywikibot.Page
        result = []
        print(count, embed.title())
        for (template, params) in pywikibot.textlib.extract_templates_and_params(text=embed.text, remove_disabled_parts=True, strip=True):
            template: str
            params: pywikibot.textlib.OrderedDict
            if re.fullmatch(redirects, template):
                print((template, params))
                result.append((template, params))
        if result:
            results[embed.title()] = result
        count += 1
    print('========')
    count = 0
    for title_res in results:
        print(title_res)
        count += len(results[title_res])
    print('Total:', len(results), 'pages,', count, 'uses')
    result['_'] = {'template': title, 'pages': len(results), 'uses': count, 'access_time': datetime.datetime.now().isoformat()}
    with open(filename, mode='w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


def search_in_revisions(title: str, keyword: str = '', skipSameUser: bool = True):
    page = pywikibot.Page(site, title)
    rev: pywikibot.page.Revision = None
    for oldrev in page.revisions(content=True):
        oldrev: pywikibot.page.Revision
        if not rev:
            rev = oldrev
            continue
        if skipSameUser and oldrev.userid == rev.userid:
            continue
        print((rev.revid, oldrev.revid, rev.user, rev.timestamp, site.base_url('_?diff={}&oldid={}'.format(rev.revid, oldrev.revid))))
        a: str = oldrev.text
        b: str = rev.text
        s = difflib.SequenceMatcher(None, a, b)
        for tag, alo, ahi, blo, bhi in s.get_opcodes():
            if (tag == 'insert' and keyword in b[blo:bhi]) \
                or (tag == 'delete' and keyword in a[alo:ahi]) \
                or (tag == 'replace' and (keyword in a[alo:ahi] or keyword in b[blo:bhi])):
                pywikibot.showDiff(a, b)
                input()
                break
        rev = oldrev


def upload_and_replace_img_tags(title: str):
    def check_wikicode(code: mw.wikicode.Wikicode | None):
        if code is None:
            return
        for node in code.nodes:
            node: mw.nodes.Node
            if isinstance(node, mw.nodes.Text):
                continue
            elif isinstance(node, mw.nodes.Argument):
                # yield from check_wikicode(node.name)
                yield from check_wikicode(node.default)
            elif isinstance(node, mw.nodes.Comment):
                continue
            elif isinstance(node, mw.nodes.ExternalLink):
                # yield from check_wikicode(node.url)
                yield from check_wikicode(node.title)
            elif isinstance(node, mw.nodes.Heading):
                yield from check_wikicode(node.title)
            elif isinstance(node, mw.nodes.HTMLEntity):
                continue
            elif isinstance(node, mw.nodes.Tag):
                if str(node.tag).lower() == 'img':
                    # print(node)
                    yield node
                # yield from check_wikicode(node.tag)
                yield from check_wikicode(node.contents)
            elif isinstance(node, mw.nodes.Template):
                # yield from check_wikicode(node.name)
                for param in node.params:
                    param: mw.nodes.extras.Parameter
                    # yield from check_wikicode(param.name)
                    yield from check_wikicode(param.value)
            elif isinstance(node, mw.nodes.Wikilink):
                # yield from check_wikicode(node.title)
                yield from check_wikicode(node.text)

    page = pywikibot.Page(site, title)
    for node in check_wikicode(mw.parse(page.text)):
        for attr in node.attributes:
            attr: mw.nodes.extras.Attribute
            if str(attr.name).lower() != 'src':
                continue
            src = attr.value.nodes[0]
            if not isinstance(src, mw.nodes.Text):
                continue
            print(src.value)


def fix_taiwan_isbn_group(start: str = '!'):
    PAIRS = (('978-9-57', '978-957'), ('978-9-86', '978-986'), ('978-6-26', '978-626'))
    for page in set(itertools.chain(*(site.search(s[0]) for s in PAIRS))):
        page: pywikibot.Page
        if page.isTalkPage():
            continue
        repl = [s for s in PAIRS if s[0] in page.text]
        print((page.title(), short_url(page), repl))
        if not repl:
            continue
        newtext = page.text
        for s in repl:
            newtext = newtext.replace(s[0] + '-', s[1] + '-').replace(s[0], s[1] + '-')
        # pywikibot.showDiff(page.text, newtext)
        page.text = newtext
        bot_save(page, '修正ISBN区域代码分段：' + '，'.join(s[0] + '→' + s[1] for s in repl))


def bot_delete(page: pywikibot.Page, reason: str, requested: bool = False):
    if requested:
        reason = '讨论版申请：' + reason
    page.text = '{{即将删除|1=' + reason + '}}'
    summary = '挂删：' + reason
    bot_save(page, summary)

def PanzerGirls_delete_files(text: str):
    commons = pywikibot.APISite('commons')
    for line in text.splitlines():
        files, reason = line.split('，原因：')
        files = [file.lstrip('*[cm:').rstrip(']') for file in files.split('、')]
        reason = reason.rstrip('。')
        for file in files:
            bot_delete(pywikibot.FilePage(commons, file), reason, True)

def search_and_delete_files(query: str, reason: str, requested: bool = False):
    commons = pywikibot.APISite('commons')
    for page in commons.search(query, namespaces=['File']):
        page: pywikibot.FilePage
        print(page.title())
        bot_delete(page, reason, requested)

def delete_files_uploaded_by_user(username: str, reason: str, requested: bool = False, start: pywikibot.Timestamp = None, end: pywikibot.Timestamp = None):
    commons = pywikibot.APISite('commons')
    user = pywikibot.User(commons, 'User:' + username)
    for page, _, _, _ in user.contributions(namespaces=['File'], start=start, end=end):
        page: pywikibot.FilePage
        print(page.title())
        bot_delete(page, reason, requested)

def delete_files(files: str, reason: str = '不再使用', requested: bool = False):
    commons = pywikibot.APISite('commons')
    for file in files.splitlines():
        page = pywikibot.FilePage(commons, file)
        print(page.title())
        bot_delete(page, reason, requested)


def test():
    tl = pywikibot.Page(site, 'LoveLive人物信息', ns='Template')
    while tl.isRedirectPage():
        tl = tl.getRedirectTarget()
    print(tl)
    # print(pywikibot.textlib.extract_templates_and_params(page.text, True, True))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        eval(sys.argv[1])

# 多行lj清理
# python pwb.py replace -cat:'文豪与炼金术师' -regex -exceptinsidetag:poem
# '\{\{(?:[Ll]ang\|ja|[Ll]j)\|(.*?(?<!\}\})(?:\n\n.*)+)\}\}' '{{ljd|\1}}'
# -summary:'多行lj清理：[[T:lang]]或[[T:lj]]→[[T:ljd]]。本次编辑由机器人进行，如修改有误，请撤销或更正，并[[User_talk:C8H17OH|联系操作者]]。'
