#!/usr/bin/env python3
"""Regenerate the Habr-ready copy from the Russian post.

Habr takes Markdown but not Liquid, so site-relative links are resolved to absolute
URLs here. Edit the post, not the generated file.
"""
import re
import sys
from pathlib import Path

SITE = "https://laconicman.github.io/articles"
POST = Path("_posts/2026-08-24-yandex-delivery-express-api.ru.md")
OUT = Path("notes/2026-08-24-habr-version.ru.md")
CUT_BEFORE = "\n\n## Откуда это всё"

HEADER = """<!--
ВЕРСИЯ ДЛЯ HABR. Генерируется скриптом notes/build-habr-copy.py из
_posts/2026-08-24-yandex-delivery-express-api.ru.md — правьте пост, а не этот файл.
На сайт не публикуется: папка notes/ исключена в _config.yml.

Заполнить в форме редактора Habr, не в тексте:

  Хабы:   Яндекс API · API · Проектирование и рефакторинг · IT-стандарты
  Теги:   OpenAPI, Яндекс Доставка, API design, contract-first, коды ошибок,
          документация, интеграция, RFC 3339
  Формат: Аналитика (в прошлый раз стоял «Мнение»)

  Для сравнения, прошлая публикация (habr.com/ru/articles/1044340/) шла в хабах
  macOS · iOS · Android · Linux · Windows с тегами OpenAPI, REST, кодогенерация, swift.
  Здесь текст не платформенный, поэтому хабы предложены другие — решать вам.

Кат (<cut/>) стоит после врезки «Короткая суть»: до ката видны заголовок и врезка.
После публикации: добавить в конец статьи ссылку на копию у себя, а в оба поста на
GitHub Pages — строку «Опубликовано на Habr» со ссылкой.
-->

"""

def main() -> int:
    body = POST.read_text(encoding="utf-8").split("---\n", 2)[2]
    body = "\n".join(l for l in body.split("\n") if "Read in English" not in l).lstrip("\n")
    if body.startswith("---\n"):
        body = body[4:].lstrip("\n")

    # Liquid → absolute URLs, in both spellings the posts use.
    body = re.sub(r"\{\{ '(/[^']+)' \| relative_url \}\}", lambda m: SITE + m.group(1), body)
    body = re.sub(r"\{\{ site\.baseurl \}\}(/\S*)", lambda m: SITE + m.group(1), body)

    if CUT_BEFORE not in body:
        print("cut anchor not found; the section heading must have been renamed", file=sys.stderr)
        return 1
    body = body.replace(CUT_BEFORE, "\n\n<cut />" + CUT_BEFORE, 1)

    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", body)
    if leftover:
        print(f"unresolved Liquid left in the output: {leftover}", file=sys.stderr)
        return 1

    OUT.write_text(HEADER + body, encoding="utf-8")
    print(f"wrote {OUT} ({len(body.split())} words)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
