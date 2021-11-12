from hashlib import new
import pywikibot
import pywikibot.textlib
import re
from disambig_basic import find_link, replace_link, bot_save

def list_birthday_celebration_description():
    title = "Template:生日祝福"
    site = pywikibot.Site()
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
    site = pywikibot.Site()
    page = pywikibot.Page(site, 'User:C8H17OH-bot')
    page.text += '\n\nAh ah, no'
    bot_save(page, summary='test bot_save')

def modify_houbunsha_family_template(startfrom: str = ''):
    # oldtext = '{{\s*芳文社(?=\s*(?:\|.*)?}})'
    # newtext = '{{芳文社|漫画网站'
    # text = '{{芳文社top}}\n{{芳文社|xxx}}'
    # print(re.sub(oldtext, newtext, text))
    # return
    site = pywikibot.Site()
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

if __name__ == "__main__":
    modify_houbunsha_family_template()
