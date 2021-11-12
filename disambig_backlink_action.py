import pywikibot
import json
from disambig_basic import bot_save
from disambig_linkshere import replace_link


def disambig_backlink_action():
    site = pywikibot.Site()
    result_file = open("scripts/userscripts/disambig_result.json", mode="r", encoding="UTF-8")
    result_json = json.load(result_file)
    result_file.close()
    for disambig_title in result_json:
        for (backlink_title, redirect_title, article_title, article_relations) in result_json[disambig_title]:
            backlink = pywikibot.Page(site, backlink_title)
            backlink.text = replace_link(backlink.text, redirect_title, article_title)
            bot_save(backlink, summary="消歧义：[[" + redirect_title + "]]→[[" + article_title + "]]")
    result_file = open("scripts/userscripts/disambig_result.json", mode="w", encoding="UTF-8")
    json.dump(dict(), result_file)
    result_file.close()


def disambig_backlink_action_main():
    disambig_backlink_action()


if __name__ == '__main__':
    disambig_backlink_action_main()
