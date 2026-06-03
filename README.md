# Articles Site

A Jekyll-based static site for tech articles and collaborative writing.

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/articles-site.git
   cd articles-site
   ```

2. **Install dependencies** (if running locally)
   ```bash
   bundle install
   ```

3. **Run locally**
   ```bash
   bundle exec jekyll serve
   ```
   Visit `http://localhost:4000/articles-site/`

### GitHub Pages (Production)

1. Push to GitHub
2. Go to **Settings > Pages** in your repository
3. Set source to **Deploy from a branch** → **main** → **/(root)**
4. Site will be available at `https://YOUR_USERNAME.github.io/articles-site/`

## Repository Structure

```
articles-site/
├── _config.yml          # Site configuration
├── _posts/              # Published articles (YYYY-MM-DD-title.md)
├── _drafts/             # Work in progress (not published)
├── assets/images/       # Article images
├── index.md             # Homepage
├── about.md             # About & contribution guide
└── README.md            # This file
```

## Writing Articles

### Create a New Post

1. Create a file in `_posts/` with format: `YYYY-MM-DD-title.md`
2. Add YAML frontmatter:

```yaml
---
layout: post
title: "Your Article Title"
date: 2025-06-03 12:00:00 +0000
tags: [programming, tools]
lang: en  # or ru for Russian
---

Your content here...
```

### Drafts

Files in `_drafts/` are excluded from the site. Use them for work in progress.

### Images

Place images in `assets/images/` and reference with:

```markdown
![Description]({{ '/assets/images/filename.png' | relative_url }})
```

## Contributing

1. **Suggest a topic:** Open an issue with label `topic-idea`
2. **Submit an article:** Fork → create branch → add post → pull request
3. **Fix or improve:** Open a PR with your changes

See [About page](about.md) for detailed guidelines.

## Customization

### Change Theme

Edit `_config.yml`:

```yaml
theme: minima  # Built-in themes: minima, cayman, hacker, etc.
```

Or use a [remote theme](https://github.com/topics/jekyll-theme).

### Update Site Info

Edit the header in `_config.yml`:

```yaml
title: "Your Site Name"
description: "Your description"
author:
  name: "Your Name"
  email: "your@email.com"
```

## Bilingual Support (Future)

Posts can include `lang: en` or `lang: ru` in frontmatter. Navigation and language switching to be implemented as content grows.

## Resources

- [Jekyll Docs](https://jekyllrb.com/docs/)
- [GitHub Pages](https://docs.github.com/en/pages)
- [Markdown Guide](https://www.markdownguide.org/)
- [Minima Theme](https://github.com/jekyll/minima)

---

Built with [Jekyll](https://jekyllrb.com/) and hosted on [GitHub Pages](https://pages.github.com/).
