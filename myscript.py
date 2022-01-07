import pywikibot, pywikibot.textlib
import re
import sys, traceback
import typing, itertools
from disambig_basic import find_link, replace_link, bot_save, link_preproc

site = pywikibot.Site()

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

def modify_houbunsha_family_template(startfrom: str = ''):
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

def test_replace_link(title: str, oldlink: str, newlink: str):
    page = pywikibot.Page(site, title)
    page.text = replace_link(page.text, oldlink, newlink)
    bot_save(page)

def search_template_with_parameter(title: str, parameter: str):
    page = pywikibot.Page(site, title, ns='Template')
    redirects = link_preproc(title) + ''.join(('|' + link_preproc(redirect.title(with_ns=False))) for redirect in page.backlinks(filter_redirects=True))
    results = []
    for embed in page.embeddedin():
        for (template, params) in pywikibot.textlib.extract_templates_and_params(text=embed.text, remove_disabled_parts=True, strip=True):
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
                        print((embed.title(), template, False))
                        break
                result = (embed.title(), template, key, value)
                results.append(result)
                print(result)
        else:
            print((embed.title(), False))
    print('========')
    for result in results:
        print(result)
            

def test():
    tl = pywikibot.Page(site, 'LoveLive人物信息', ns='Template')
    while tl.isRedirectPage():
        tl = tl.getRedirectTarget()
    print(tl)
    # print(pywikibot.textlib.extract_templates_and_params(page.text, True, True))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        eval(sys.argv[1])
