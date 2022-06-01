import pywikibot, pywikibot.textlib
import re
import sys, traceback
import pprint
import typing, itertools
from disambig_basic import find_link, replace_link, bot_save, link_preproc
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
        print(repr(embed.title()), end=': [', flush=True)
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

def remove_spm_id_in_bililink(start: str = '!'):
    for page in site.allpages(start=start, filterredir=False):
        page: pywikibot.Page
        print(page.title())
        for link in page.extlinks():
            if any(s in link for s in ('bilibili.com', 'b23.tv')) and any(s in link for s in ('from=search', 'seid', 'spm_id_from')):
                newtext = re.sub(r'((?:bilibili\.com|b23\.tv)/.*?)([\?&](from=search|seid=\d+|(spm_id_from|from_spmid)=\d+\.\d+\.[^\s\]\?&<\|]*))+', r'\1', page.text)
                print(page.full_url())
                pywikibot.showDiff(page.text, newtext)
                while True:
                    print(end='Save? ([Y]es / [N]o / [Q]uit): ')
                    cmd = input()
                    if cmd == 'y' or cmd == 'Y':
                        page.text = newtext
                        bot_save(page, '删除B站链接中的“spm_id_from”等无用GET参数')
                        break
                    elif cmd == 'n' or cmd == 'N':
                        break
                    elif cmd == 'q' or cmd == 'Q':
                        return "quit"
                break

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
