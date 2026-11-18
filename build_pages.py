"""Build the blog from posts/*.md after installing requirements.txt."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import escape
from itertools import groupby
from collections import defaultdict
from pathlib import Path
from hashlib import sha256
from urllib.parse import quote, urlsplit, urlunsplit
import unicodedata
import re
import subprocess

import yaml
from markdown_it import MarkdownIt

SITE = Path(__file__).resolve().parent
ROUTES = [('notes','手记'), ('tags','标签'), ('archives','归档'), ('links','友链'), ('about','关于')]
PALETTES = [('linen','Linen','#f2f1eb'), ('glacier','Glacier','#eaf0f6'),
            ('graphite','Graphite','#2e3440'), ('white','Pure White','#ffffff')]
parser = MarkdownIt('commonmark', {'html':False}).enable(['table','strikethrough'])

@dataclass
class Post:
    slug: str
    title: str
    category: str
    content: str
    headings: list
    updated: datetime | None
    has_clock: bool
    tags: list[str]
    summary: str

def tag_key(name):
    return unicodedata.normalize('NFKC', name).strip().casefold()

def tag_folder(name):
    key = tag_key(name)
    label = re.sub(r'[^\w-]+', '-', key).strip('-')[:36]
    return f't-{label}-{sha256(key.encode()).hexdigest()[:10]}'

def tag_list(raw, path):
    if raw is None:
        return []
    if isinstance(raw,str):
        raw = re.split('[,，]', raw)
    if not isinstance(raw,list) or not all(isinstance(tag,str) for tag in raw):
        raise ValueError(f'{path.name}: tags must be a list of tag names')
    names = {}
    for tag in raw:
        if tag.strip():
            names.setdefault(tag_key(tag),tag.strip())
    return list(names.values())

def post_meta(post, prefix):
    parts = []
    if post.updated:
        stamp = post.updated
        fmt = '%Y-%m-%d %H:%M' if post.has_clock else '%Y-%m-%d'
        parts.append(f'<time datetime="{stamp.isoformat(timespec="minutes")}">{stamp.strftime(fmt)}</time>')
    parts.extend(f'<a href="{prefix}tags/{quote(tag_folder(t))}/index.html"># {escape(t)}</a>' for t in post.tags)
    return '<div class="post-meta">'+''.join(parts)+'</div>' if parts else ''

def post_row(post,prefix):
    return (f'<div class="post-row"><a class="post-name" href="{prefix}posts/{quote(post.slug)}/index.html">{escape(post.title)}</a>'
            +post_meta(post,prefix)+f'<p class="post-summary">{escape(post.summary)}</p></div>')

def archive_date(metadata, path):
    value = (metadata.get('updated', '').strip() or metadata.get('date', '').strip()).strip('"\'')
    if not value:
        return None, False
    for pattern in ('%Y-%m-%d', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(value, pattern), '%H' in pattern
        except ValueError:
            continue
    raise ValueError(f'{path.name}: expected updated/date as YYYY-MM-DD or YYYY-MM-DD HH:MM')

def post_sort_key(post):
    stamp = post.updated or datetime.min
    if not post.updated or post.has_clock:
        return stamp, 0
    # Date-only posts can share a day with precisely timed posts.
    try:
        result = subprocess.run(
            ['git','--literal-pathspecs','log','--follow','--diff-filter=A','--format=%ct',
             '--',f'posts/{post.slug}.md'],
            cwd=SITE, capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return stamp, 0
    history = result.stdout.splitlines()
    if not history:
        return stamp, 0
    first_commit = int(history[-1])
    published = datetime.fromtimestamp(first_commit, timezone(timedelta(hours=8))).replace(tzinfo=None)
    if published.date() == stamp.date():
        return published, first_commit
    return stamp, first_commit

def timeline(posts):
    if not posts:
        return '<p>还没有可归档的手记。</p>'
    years = []
    months = '一 二 三 四 五 六 七 八 九 十 十一 十二'.split()
    for year, group in groupby(posts,key=lambda p:p.updated.year if p.updated else None):
        entries = list(group)
        blocks = []
        for month, items in groupby(entries,key=lambda p:p.updated.month if p.updated else None):
            rows = list(items)
            month_name = months[month-1]+'月' if month else '未注明'
            blocks.append(f'<div class="month-block"><h3>{month_name} <sup>{len(rows)}</sup></h3><div>'
                          +''.join(post_row(post,'../') for post in rows)+'</div></div>')
        years.append(f'<section class="archive-year"><h2>{year or "日期待补"} <sup>{len(entries)}</sup></h2>'
                     +''.join(blocks)+'</section>')
    return '<p class="eyeline">按最后更新，由近到远</p><div class="timeline">' + ''.join(years) + '</div>'

def read_post(path):
    text = path.read_text(encoding='utf-8-sig').rstrip()+'\n'
    front = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if text.startswith('---\n') and not front:
        raise ValueError(f'{path.name}: unclosed metadata block')
    metadata = (yaml.load(front[1], Loader=yaml.BaseLoader) or {}) if front else {}
    if not isinstance(metadata,dict):
        raise ValueError(f'{path.name}: metadata must contain named fields')
    for field in ('title','category','date','updated','summary'):
        if field in metadata and not isinstance(metadata[field],str):
            raise ValueError(f'{path.name}: {field} must be plain text')
    tokens = parser.parse(text[front.end():] if front else text)
    title = metadata.get('title','').strip()
    if tokens and tokens[0].type=='heading_open' and tokens[0].tag=='h1':
        if not title or title==tokens[1].content:
            title=tokens[1].content
            tokens=tokens[3:]
    title=title or path.stem
    headings = []
    for index, token in enumerate(tokens):
        for inline in token.children or []:
            if inline.type not in ('link_open','image'):
                continue
            attr = 'src' if inline.type == 'image' else 'href'
            url = urlsplit(inline.attrGet(attr))
            if url.scheme or url.netloc:
                continue
            location = url.path.removeprefix('./')
            if location.startswith('../assets/'):
                location = '../' + location
            elif inline.type == 'link_open' and '/' not in location and location.endswith('.md'):
                location = '../' + location[:-3] + '/index.html'
            else:
                continue
            inline.attrSet(attr,urlunsplit(('', '', location, url.query, url.fragment)))
        if token.type == 'heading_open' and token.tag in ('h2','h3'):
            anchor = f'section-{len(headings)+1}'
            token.attrSet('id', anchor)
            headings.append((anchor,tokens[index+1].content))
    summary = metadata.get('summary','').strip()
    if not summary:
        for index, token in enumerate(tokens):
            if token.type=='paragraph_open':
                words=''.join(t.content for t in tokens[index+1].children or [] if t.type in ('text','code_inline')).strip()
                if words:
                    summary=words if len(words)<=85 else words[:84]+'…'
                    break
    stamp, has_clock = archive_date(metadata,path)
    return Post(path.stem,title,metadata.get('category','手记').strip(),
                parser.renderer.render(tokens,parser.options,{}),headings,stamp,has_clock,
                tag_list(metadata.get('tags'),path),summary)

def controls():
    choices = ''.join(
        f'<label><input type="radio" name="palette" value="{key}"><span class="swatch" style="--swatch:{color}" aria-hidden="true"></span>{name}<span class="tick" aria-hidden="true"></span></label>'
        for key,name,color in PALETTES)
    return f'''<details class="palette"><summary aria-label="阅读配色" title="阅读配色">
<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7">
<path d="M12 3a9 9 0 1 0 0 18h1a2.2 2.2 0 0 0 1.4-3.8c-.85-.78-.34-2.2.9-2.2H17a4 4 0 0 0 4-4c0-4.4-4-8-9-8Z"/>
<g fill="currentColor" stroke="none"><circle cx="7.4" cy="11.5" r="1.1"/><circle cx="10.1" cy="7.6" r="1.1"/><circle cx="14.8" cy="7.7" r="1.1"/><circle cx="17.4" cy="11.3" r="1.1"/></g></svg></summary><fieldset aria-label="阅读配色">{choices}</fieldset></details>'''

def build_page(dest, title, section, main, toc=''):
    prefix = '../' * len(dest.parent.relative_to(SITE).parts)
    links = []
    for slug,name in ROUTES:
        current = ' aria-current="page"' if section==slug else ''
        arrow = '<span class="nav-arrow" aria-hidden="true">↗</span>' if slug=='about' else ''
        links.append(f'<a href="{prefix}{slug}/index.html"{current}>{name}{arrow}</a>')
    html = f'''<!doctype html>
<!-- Stellar_src generated page -->
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f2f1eb"><title>{escape(title)} · Stellar_src</title>
<script src="{prefix}assets/reading.js"></script>
<link rel="stylesheet" href="{prefix}assets/site.css"><link rel="stylesheet" href="{prefix}assets/reading.css"></head>
<body><div id="og-journal" class="inner"><div class="inner-shell"><a class="skip" href="#main">跳到正文</a>
<header class="nav" id="top"><a class="brand" href="{prefix}index.html"><span class="mark" aria-hidden="true"></span>Stellar_src</a>
<div class="inner-top"><nav class="navlinks" aria-label="主导航">{''.join(links)}</nav>{controls()}</div></header>
<div class="page-grid"><main id="main" class="main-column">{main}</main><aside class="rail" aria-label="页侧栏"><div class="forest-orb" aria-hidden="true"></div>{toc}</aside></div></div></div></body></html>'''
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(html,encoding='utf-8')

def friend_links():
    path = SITE/'content'/'links.yml'
    sites = yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    if sites is None or sites == []:
        return '<p class="eyeline">暂无友链。</p>'
    if not isinstance(sites, list):
        raise ValueError('content/links.yml 应为站点列表')
    rows = []
    for index, item in enumerate(sites, 1):
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ('name','url')):
            raise ValueError(f'content/links.yml 第 {index} 项需要名称 name 和网址 url')
        url = item['url'].strip()
        parsed = urlsplit(url)
        if parsed.scheme not in ('https','http') or not parsed.hostname or any(c.isspace() for c in url):
            raise ValueError(f'content/links.yml 第 {index} 项需要完整的 http 或 https 网址')
        rows.append(f'<li><a href="{escape(url)}"><strong>{escape(item["name"].strip())}</strong>'
                    f'<span>{escape(url)}</span></a></li>')
    return '<ul class="friend-list">'+''.join(rows)+'</ul>'

def build():
    posts = [read_post(path) for path in sorted((SITE/'posts').glob('*.md'))]
    posts.sort(key=post_sort_key,reverse=True)
    for post in posts:
        main = f'''<a class="backlink" href="../../notes/index.html">← 手记</a>
<article><header><h1 class="page-title">{escape(post.title)}</h1>{post_meta(post,'../../')}<p class="reader-summary">{escape(post.summary)}</p></header>
<div class="prose">{post.content}</div></article>'''
        items=''.join(f'<li><a href="#{anchor}">{escape(label)}</a></li>' for anchor,label in post.headings)
        toc=f'<nav class="toc" aria-label="文章目录"><h2>目录</h2><ul>{items}</ul><a class="toc-top" href="#top">↑ 返回顶部</a></nav>'
        build_page(SITE/'posts'/post.slug/'index.html',post.title,'notes',main,toc)
    listing=''.join(post_row(post,'../') for post in posts) or '<p>还没有手记。</p>'
    tags=build_tags(posts)
    about = parser.render((SITE/'content'/'about.md').read_text(encoding='utf-8-sig'))
    sections = {'notes':listing,'archives':timeline(posts),'tags':tags,'links':friend_links(),'about':f'<div class="about-copy">{about}</div>'}
    for slug,name in ROUTES:
        content=sections[slug]
        build_page(SITE/slug/'index.html', name, slug,f'<a class="backlink" href="../index.html">← 首页</a><h1 class="page-title">{name}</h1>{content}')
    home = SITE/'index.html'
    html = home.read_text(encoding='utf-8')
    entries = '\n'.join(
        f'<article class="recent-note"><a class="entry" href="posts/{quote(p.slug)}/index.html">'
        f'<small>{escape(p.category)}</small><strong>{escape(p.title)}</strong><span class="arr" aria-hidden="true">↗</span></a>'
        f'{post_meta(p,"")}<p class="post-summary">{escape(p.summary)}</p></article>' for p in posts[:5]
    ) or '<p>还没有手记。</p>'
    if len(posts) > 5:
        entries += '\n<a class="all-notes" href="notes/index.html">查看全部手记 →</a>'
    html, count = re.subn(r'(<!-- recent-notes:start -->).*?(<!-- recent-notes:end -->)',lambda m:m[1]+'\n'+entries+'\n'+m[2],html,flags=re.S)
    if count != 1:
        raise ValueError('index.html must contain one recent-notes section')
    html = re.sub(r'<dialog\b.*?</dialog>', '', html, flags=re.S)
    home.write_text(html,encoding='utf-8')

def build_tags(posts):
    groups=defaultdict(list)
    names={}
    for post in posts:
        for tag in post.tags:
            key=tag_key(tag)
            names.setdefault(key,tag)
            groups[key].append(post)
    images={}
    for image in sorted((SITE/'assets'/'tags').glob('*')):
        if image.is_file() and image.suffix.lower() in ('.jpg','.jpeg','.png','.webp','.avif'):
            images.setdefault(tag_key(image.stem),image)
    cards=[]
    generated=set()
    for key,group in sorted(groups.items()):
        name=names[key]
        dest=SITE/'tags'/tag_folder(key)/'index.html'
        generated.add(dest)
        title=f'标签：{name}'
        main=(f'<a class="backlink" href="../index.html">← 全部标签</a><h1 class="page-title">{escape(title)}</h1>'
              f'<p class="eyeline">{len(group)} 篇手记</p>'+''.join(post_row(p,'../../') for p in group))
        build_page(dest,title,'tags',main)
        image=images.get(key,SITE/'assets'/'forest.jpg')
        src=quote(image.relative_to(SITE).as_posix())
        cards.append(f'<a class="tag-card" href="{quote(dest.parent.name)}/index.html"><img src="../{src}" alt="" loading="lazy">'
                     f'<span><strong># {escape(name)}</strong><small>{len(group)} 篇</small></span></a>')
    for old in (SITE/'tags').glob('t-*/index.html'):
        if old not in generated and '<!-- Stellar_src generated page -->' in old.read_text(encoding='utf8')[:100]:
            old.unlink()
            if not any(old.parent.iterdir()):
                old.parent.rmdir()
    return '<div class="tag-gallery">'+''.join(cards)+'</div>' if cards else '<p>还没有标签。</p>'

if __name__=='__main__':
    build()
