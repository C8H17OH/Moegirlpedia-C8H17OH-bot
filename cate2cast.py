import copy
import re

import mwparserfromhell as mw
import pywikibot as pwb
from pywikibot import site as pwb_site

from disambig_basic import link_preproc, bot_save


def replace_cate_with_cast(site: pwb_site.APISite, page: pwb.Page) -> bool:
    """
    Replace usage of Template:Cate with Template:声优
    
    :param page: The page to be processed
    :type page: pwb.Page
    :return: True if the replacement was made, False otherwise
    :rtype: bool
    """
    processed = False
    ignored = 0
    wikicode = mw.parse(page.text)

    while templates := wikicode.filter_templates(
        recursive=True,
        matches=lambda t: t.name.capitalize() == "Cate" and all(param.endswith("配音角色") for param in t.params[1:])
    )[ignored:]:
        template = templates[0]
        content = copy.deepcopy(template.params[0].value)
        success = True

        for param in template.params[1:]:
            name = param.value[:-4]
            name_pattern = link_preproc(name) + "|" + link_preproc(fr"{name}\(声优\)")
            before, title, text, color, dead = None, None, None, None, None

            if links := content.filter_wikilinks(
                recursive=mw.wikicode.Wikicode.RECURSE_OTHERS,
                matches=lambda link: re.match(name_pattern, str(link.title)) is not None
            ):
                # [[name]] -> {{声优|name}}; [[name|text]] -> {{声优|name|text}}
                before = links[0]
                title = before.title
                text = before.text

            elif links := content.filter_wikilinks(
                recursive=mw.wikicode.Wikicode.RECURSE_OTHERS,
                matches=lambda link:
                    re.match(":(Category|category|CAT|分类|分類):" + link_preproc(str(param.value)), str(link.title)) is not None
                    and re.match(name_pattern, str(link.text)) is not None
            ):
                # [[:Category:param|text]] -> {{声优|@|text}}
                before = links[0]
                title = "@"
                text = before.text

            elif coloredlinks := content.filter_templates(
                recursive=mw.wikicode.Wikicode.RECURSE_OTHERS,
                matches=lambda t: t.name.capitalize() == "Coloredlink" and re.match(name_pattern, str(t.get("2").value)) is not None
            ):
                # {{Coloredlink|color|name}} -> {{声优|name|color=color}}; {{Coloredlink|color|name|text}} -> {{声优|name|text|color=color}}
                before = coloredlinks[0]
                color = before.get("1").value
                title = before.get("2").value
                if before.has("3"):
                    text = before.get("3").value

            elif dead_templates := content.filter_templates(
                recursive=mw.wikicode.Wikicode.RECURSE_OTHERS,
                matches=lambda t: t.name.capitalize() == "Dead" and re.match(name_pattern, str(t.get("1").value)) is not None
            ):
                # {{Dead|name}} -> {{声优|name|dead=1}}; {{Dead|name|text}} -> {{声优|name|text|dead=1}}
                before = dead_templates[0]
                dead = True
                title = before.get("1").value
                if before.has("2"):
                    text = before.get("2").value

            if before is not None:
                new_params = [mw.nodes.extras.Parameter("1", title, showkey=False)]
                if text and text != re.sub(r"\(.*?\)", "", str(title)):
                    new_params.append(mw.nodes.extras.Parameter("2", text, showkey=False))
                if re.match(r".*\(.*?\)", name):
                    new_params.append(mw.nodes.extras.Parameter("分类", param.value, showkey=True))
                if color:
                    new_params.append(mw.nodes.extras.Parameter("color", color, showkey=True))
                if dead:
                    new_params.append(mw.nodes.extras.Parameter("dead", "1", showkey=True))
                new_template = mw.nodes.Template("声优", new_params)
                # print(f"{before} -> {new_template}")
                content.replace(before, new_template)
                continue

            if texts := content.filter_text(matches=lambda text: re.match(link_preproc(name), text.value) is not None):
                # name -> {{声优||name}}
                before = texts[0]
                new_params = [
                    mw.nodes.extras.Parameter("1", "", showkey=False),
                    mw.nodes.extras.Parameter("2", name, showkey=False)
                ]
                if re.match(r"\(.*?\)", name):
                    new_params.append(mw.nodes.extras.Parameter("分类", param, showkey=True))
                new_template = mw.nodes.Template("声优", new_params)
                new_text = before.replace(name, new_template)
                # print(f"{text} -> {new_text}")
                content.replace(before, new_text)
                continue

            # default: add [[Category:param]]
            # category_link = mw.nodes.Wikilink(f"Category:{param.value}")
            # print(f"+{category_link}")
            # content.append(category_link)
            # continue

            print(f"=== Page {page.title()} ===")
            print(f"Failed to replace parameter {param} in template {template}")
            success = False
            ignored += 1
            break
        
        if success:
            print(f"=== Page {page.title()} ===")
            print(f"* Before: {template}")
            print(f"* After: {content}")
            wikicode.replace(template, content)
            processed = True

    if processed:
        page.text = str(wikicode)
        # bot_save(page, "替换模板：[[Template:Cate]]→[[Template:声优]]")
    else:
        print(f"=== Page {page.title()} ===")
        print(f"No changes made.")

    return processed


if __name__ == "__main__":
    site = pwb.Site()
    if not isinstance(site, pwb_site.APISite):
        print("This script requires an API-enabled site.")
        exit(-1)
    site.login()

    # page = pwb.Page(site, "蓝那祈")
    # replace_cate_with_cast(site, page)

    template = pwb.Page(site, "Template:Cate")
    for page in template.embeddedin(namespaces=[0], total=100, content=True):
        replace_cate_with_cast(site, page)