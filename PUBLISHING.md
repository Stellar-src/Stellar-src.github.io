# 在 GitHub 发布手记

把这个站点目录内的文件放在仓库根目录，同时保留 `.github/workflows/pages.yml`。在仓库的 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。随项目提供的工作流监听 `main` 分支。

## 写第一篇文章

在仓库的 **Add file → Create new file** 输入 `posts/forest-walk.md`，也可以把已有的 Markdown 文件上传到 `posts/`。文件名会成为文章网址的一部分。下面的内容可以直接复制。

```markdown
---
title: 雨后的山路
date: 2026-11-16
updated: 2026-11-18 19:30
category: 山野手记
tags: [摄影, 徒步]
summary: 雨停以后，山腰的雾散开了十分钟。
---

走到半山腰时，第一束光刚好落在石阶上。

## 沿途所见

在这里写正文。
```

提交到 `main`（或把分支合并到 `main`）后，在 **Actions → Build and publish Stellar_src** 查看进度。部署完成后，首页、手记、归档、标签索引和各标签的文章列表都会更新。访问地址可在 **Settings → Pages** 查看。

## 哪些字段影响页面

| 字段 | 用途 |
| --- | --- |
| `title` | 文章标题。省略时取正文开头的一级标题，再回退到文件名。 |
| `summary` | 列表中的一句备注。省略时自动摘录正文中的首个文字段落。 |
| `tags` | 可填写多个标签，支持示例中的方括号或 YAML 的多行列表。每个新标签都会生成独立入口。 |
| `category` | 首页文章条目的栏目名，默认「手记」。 |
| `updated`、`date` | 优先使用 `updated` 排序和显示，其次使用 `date`。两项都省略时，文章进入「日期待补」。 |

改错字时保留原日期，文章就留在时间轴原处。希望一次修订排到新位置时，手动更新 `updated`，可以精确到分钟。GitHub 的提交时间不会覆盖这里的值。

## 在 GitHub 编辑友链和关于

打开仓库的 **Code**，进入相应文件，点铅笔 **Edit this file**。保存到 `main` 后，Pages 工作流会重新发布。

- **友链**使用 `content/links.yml`。每项包含名称和完整网址，按文件中的顺序展示。复制下面这一组即可增加一条。
- **关于**使用 `content/about.md`。直接写文字，空一行分段，也可以使用 Markdown 小标题、列表和链接。

```yaml
- name: 朋友的博客
  url: https://example.com/
```

首页「最近手记」取自 `posts/`，沿用手记页的排序、时间、标签和备注。更新文章后两个入口会一起刷新。

## 添加图片和文章链接

- **标签封面**：例如新增了「徒步」，把图上传为 `assets/tags/徒步.webp`。支持 JPG、JPEG、PNG、WebP 和 AVIF，推荐横图，主体放在中间。没有同名图片时会自动使用首页森林图，之后随时可以补图。
- **正文配图**：把图放在 `assets/photos/`，在文章中写 `![雨后的石阶](../assets/photos/steps.jpg)`，在仓库预览和发布后的文章里都可以看见。
- **引用另一篇手记**：同在 `posts/` 目录里的文章可写成 `[林梢留下的两种温度](forest.md)`，构建时会自动指向它的阅读页。

本地预览可在站点目录内依次运行 `python -m pip install -r requirements.txt` 和 `python build_pages.py`，然后打开 `index.html`。使用 Python 3.12 可与 GitHub 的构建环境保持一致。
