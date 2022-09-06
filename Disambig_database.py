import pywikibot as pwb
import typing as tp
import json
import pprint
import asyncio
import sys, os
import Disambig


filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'disambig_database.json')

async def empty_coroutine():
    pass

async def save_json(db: dict[str, dict[str]]):
    with open(filepath, mode='w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

async def append_json(record: dict[str]):
    with open(filepath, mode='r+', encoding='utf-8') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(size - 3, os.SEEK_SET)
        text = json.dumps({record['title']: record}, indent=4, ensure_ascii=False)
        f.write(',' + text[1:])

async def update_disambig_terms(
    disamb_list: tp.Iterable[tp.Union[str, pwb.Page]] = None,
    force_flush_terms: bool = False
):
    site: pwb.APISite = pwb.Site()
    db: dict[str, dict[str]]
    with open(filepath, mode='r', encoding='utf-8') as f:
        db = json.load(f)
    save_task = asyncio.create_task(empty_coroutine())
    cnt = 0
    for disamb in pwb.Category(site, 'Category:消歧义页').articles() if disamb_list is None else disamb_list:
        if isinstance(disamb, str):
            disamb = pwb.Page(site, disamb)
        disamb: pwb.Page
        record = db.setdefault(disamb.title(), {'title': disamb.title()})
        if force_flush_terms \
            or 'terms' not in record \
            or 'last_revision_time' not in record \
            or pwb.Timestamp.fromISOformat(record['last_revision_time']) < disamb.editTime():
            record['terms'] = {term.termlink.link: list(term.keywords) for term in Disambig.get_disambig_terms(disamb)}
            record['last_revision_time'] = str(disamb.editTime())
        record['update_time'] = str(pwb.Timestamp.now())
        # pprint.pprint(record)
        print(cnt, disamb.title())
        cnt += 1
        await save_task
        save_task = asyncio.create_task(save_json(db) if disamb.title() in db else append_json(record))


async def update_disambig_backlinks(
    disamb_list: tp.Iterable[tp.Union[str, pwb.Page]] = None,
    force_flush_backlinks: bool = False
):
    site = pwb.Site()
    db: dict[str, dict[str]]
    with open(filepath, mode='r', encoding='utf-8') as f:
        db = json.load(f)
    save_task = asyncio.create_task(empty_coroutine())
    cnt = 0
    for disamb_title in db if disamb_list is None else disamb_list:
        disamb: pwb.Page = pwb.Page(site, disamb_title) if isinstance(disamb_title, str) else disamb_title
        record = db[disamb_title]
        record['backlinks'] = {}
        backlinks: dict[str, dict[int, dict[str]]] = record['backlinks']
        cnt1 = 0
        for redirect, backlink, relations in Disambig.get_disambig_relations_for_disambig(disamb):
            bl_dict: dict[str, tp.Union[list[str], dict[str]]] = backlinks.setdefault(backlink.namespace().canonical_name, {}).setdefault(backlink.title(), {})
            bl_dict.setdefault('redirects', []).append(redirect.title())
            rs_dict: dict[str] = bl_dict.setdefault('relations', {})
            for relation in relations:
                r_dict: dict[str, tp.Union[str, list[str]]] = rs_dict.setdefault(relation.term.termlink.link, {})
                if relation.title:
                    r_dict['title'] = relation.title
                if relation.cats:
                    cats = set(r_dict.setdefault('cats', []))
                    cats.update({cat.title() for cat in relation.cats})
                    r_dict['cats'] = list(cats)
                if relation.kwlinks:
                    kwlinks = set(r_dict.setdefault('kwlinks', []))
                    kwlinks.update(relation.kwlinks)
                    r_dict['kwlinks'] = list(kwlinks)
            print(':', cnt1, (redirect, backlink, relations))
            cnt1 += 1
            await save_task
            save_task = asyncio.create_task(save_json(db))
        print(cnt, disamb_title)
        pprint.pprint(record)
        cnt += 1


if __name__ == '__main__':
    asyncio.run(update_disambig_backlinks())