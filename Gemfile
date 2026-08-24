source "https://rubygems.org"

gem "github-pages", group: :jekyll_plugins
# NB: jekyll-polyglot does NOT load in production. Deployment runs
# actions/jekyll-build-pages, which builds in safe mode against the GitHub Pages
# plugin allowlist, and polyglot is not on it. A local `bundle exec jekyll build`
# DOES load it (this group is auto-required), so local URLs get an /en/ prefix that
# the live site does not have. Post URLs and cross-language links follow production.
# Options for resolving the split: notes/2026-08-24-yandex-delivery-api-research.md
gem "jekyll-polyglot", group: :jekyll_plugins
