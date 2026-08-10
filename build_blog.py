#!/usr/bin/env python3
"""
Blog HTML generator for taoli001.cn
Reads blog_data.py, fetches images via Pexels API (or fallback), generates HTML pages.
"""
import os, sys, json, hashlib, time, random, urllib.request, urllib.parse, ssl

SITE_URL = "https://www.taoli001.cn"
SITE_NAME = "九天建材"
PHONE = "19008096839"
EMAIL = "xxgxxg198733@gmail.com"
BLOG_DIR = "blog"
IMG_DIR = "images/blog"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# Load article data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog_data
ARTICLES = blog_data.BLOG_ARTICLES

# ====== Image fetching ======
LOCAL_IMAGES = [f for f in os.listdir("images/applications") if f.endswith(('.jpg','.png','.JPG','.jpeg'))]

def fetch_picsum_image(query, slug):
    """Fetch image from Picsum (free, no API key, seed-based). Returns local filename or None."""
    try:
        seed = slug[:16]
        img_url = f"https://picsum.photos/seed/{seed}/800/450"
        ctx = ssl.create_default_context()
        req = urllib.request.Request(img_url, headers={"User-Agent": "taoli-blog/1.0"})
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        final_url = resp.geturl()
        img_data = urllib.request.urlopen(final_url, timeout=15, context=ctx).read()
        ext = "jpg"
        if ".png" in final_url:
            ext = "png"
        elif ".webp" in final_url:
            ext = "webp"
        local_path = os.path.join(IMG_DIR, f"{slug}.{ext}")
        with open(local_path, "wb") as f:
            f.write(img_data)
        print(f"    [Picsum] seed={seed} -> {slug}.{ext}")
        return f"{slug}.{ext}"
    except Exception as e:
        print(f"    [Picsum ERR] {query}: {e}")
    return None

def fetch_pexels_image(query, slug):
    """Fetch image from Pexels API. Returns URL or None."""
    if not PEXELS_API_KEY:
        return None
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=5&size=medium"
        req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        data = json.loads(resp.read())
        if data.get("photos"):
            img_url = data["photos"][0]["src"]["medium"]
            # Download to local
            img_data = urllib.request.urlopen(img_url, timeout=15, context=ctx).read()
            ext = img_url.split(".")[-1].split("?")[0] or "jpg"
            local_path = os.path.join(IMG_DIR, f"{slug}.{ext}")
            with open(local_path, "wb") as f:
                f.write(img_data)
            print(f"    [Pexels] {query} -> {slug}.{ext}")
            return f"{slug}.{ext}"
    except Exception as e:
        print(f"    [Pexels ERR] {query}: {e}")
    return None

def get_image(article):
    """Get image for article. Try Lorem Flickr, Pexels, then fallback to local images."""
    slug = article["slug"]
    # Check if already downloaded
    for f in os.listdir(IMG_DIR):
        if f.startswith(slug) and f.endswith(('.jpg','.png','.jpeg')):
            return f

    # 1. Try Picsum (free, no API key, seed-based unique images)
    result = fetch_picsum_image(article["pexels_query"], slug)
    if result:
        return result

    # 2. Try Pexels if API key configured (higher quality)
    if PEXELS_API_KEY:
        result = fetch_pexels_image(article["pexels_query"], slug)
        if result:
            return result

    # 3. Fallback to local existing images
    if LOCAL_IMAGES:
        picked = random.choice(LOCAL_IMAGES)
        return f"../images/applications/{picked}"

    return None

# ====== HTML Templates ======
HEADER_TMPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{meta}
<title>{title} | {site_name}博客</title>
<script type="application/ld+json">{ld_json}</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Zhi+Mang+Xing&display=swap');
  *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}
  :root{{--primary:#2d5a27;--primary-light:#4a7c3f;--accent:#c8924b;--accent-light:#e8c07a;--bg:#fafaf8;--bg-warm:#f5f0e8;--text:#2c2c2c;--text-light:#6b6b6b;--white:#fff;--border:#e8e3da;--shadow:0 4px 24px rgba(0,0,0,.06);--shadow-lg:0 12px 48px rgba(0,0,0,.08);--radius:16px;--transition:.35s cubic-bezier(.25,.46,.45,.94);}}
  html{{scroll-behavior:smooth;}}
  body{{font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;color:var(--text);background:var(--bg);line-height:1.85;-webkit-font-smoothing:antialiased;}}
  .nav{{position:fixed;top:0;left:0;right:0;z-index:100;padding:0 40px;height:90px;display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.92);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);box-shadow:0 1px 0 rgba(0,0,0,.05);}}
  .nav-logo{{font-family:'Zhi Mang Xing','STXingkai',cursive;font-size:52px;color:var(--primary);letter-spacing:6px;text-decoration:none;line-height:1;}}
  .nav-phone{{font-family:'STKaiti','KaiTi',serif;font-size:52px;font-weight:900;color:#e74c3c;text-decoration:none;margin-left:24px;letter-spacing:2px;line-height:1;}}
  .nav-links{{display:flex;gap:36px;list-style:none;}}
  .nav-links a{{text-decoration:none;color:var(--text);font-size:15px;font-weight:500;transition:var(--transition);position:relative;}}
  .nav-links a::after{{content:'';position:absolute;bottom:-4px;left:0;width:0;height:2px;background:var(--accent);transition:var(--transition);}}
  .nav-links a:hover{{color:var(--primary);}}
  .nav-links a:hover::after,.nav-links a.active::after{{width:100%;}}
  .nav-links a.active{{color:var(--primary);font-weight:700;}}
  .nav-cta{{padding:8px 24px;background:var(--primary);color:#fff!important;border-radius:50px;font-weight:600;font-size:14px!important;}}
  .nav-cta:hover{{background:var(--primary-light);transform:translateY(-1px);}}
  .nav-cta::after{{display:none!important;}}
  .page-header{{padding:140px 40px 60px;text-align:center;background:linear-gradient(165deg,#f5f0e8 0%,#e8e0d3 40%,#dce8d5 100%);}}
  .page-header h1{{font-size:38px;font-weight:900;color:#1a1a1a;margin-bottom:12px;line-height:1.3;}}
  .page-header p{{color:var(--text-light);font-size:17px;max-width:650px;margin:0 auto;}}
  .breadcrumb{{max-width:900px;margin:0 auto;padding:20px 40px 0;font-size:14px;color:var(--text-light);}}
  .breadcrumb a{{color:var(--primary);text-decoration:none;}}
  .breadcrumb a:hover{{text-decoration:underline;}}
  .article-container{{max-width:900px;margin:0 auto;padding:0 40px 60px;}}
  .article-meta{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px;font-size:14px;color:var(--text-light);align-items:center;}}
  .article-cat{{display:inline-block;padding:4px 14px;background:rgba(45,90,39,.1);color:var(--primary);border-radius:50px;font-weight:600;font-size:13px;}}
  .article-content{{font-size:16px;line-height:1.9;}}
  .article-content h2{{font-size:26px;font-weight:700;margin:36px 0 16px;color:#1a1a1a;}}
  .article-content p{{margin-bottom:16px;}}
  .article-content strong{{color:var(--primary);}}
  .article-tags{{display:flex;gap:10px;flex-wrap:wrap;margin-top:36px;padding-top:24px;border-top:1px solid var(--border);}}
  .article-tag{{padding:6px 16px;background:var(--bg-warm);border-radius:50px;font-size:13px;color:var(--primary);font-weight:500;}}
  .related-section{{background:var(--bg-warm);padding:60px 40px;}}
  .related-section h2{{text-align:center;font-size:28px;font-weight:700;margin-bottom:32px;}}
  .related-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;max-width:1100px;margin:0 auto;}}
  .related-card{{background:var(--white);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:var(--transition);text-decoration:none;color:var(--text);display:block;}}
  .related-card:hover{{transform:translateY(-4px);box-shadow:var(--shadow-lg);}}
  .related-card-body{{padding:18px 20px 22px;}}
  .related-card-body h3{{font-size:16px;font-weight:700;margin-bottom:6px;line-height:1.4;}}
  .related-card-body p{{font-size:13px;color:var(--text-light);}}
  .cta{{text-align:center;padding:80px 40px;background:linear-gradient(165deg,var(--primary) 0%,#1e3d1a 100%);color:#fff;}}
  .cta h2{{font-size:36px;font-weight:700;margin-bottom:12px;}}
  .cta p{{font-size:17px;opacity:.8;margin-bottom:32px;}}
  .btn{{display:inline-flex;align-items:center;gap:8px;padding:14px 36px;border-radius:50px;font-size:16px;font-weight:600;text-decoration:none;border:none;transition:var(--transition);font-family:inherit;}}
  .btn-primary{{background:var(--accent);color:#fff;}}
  .btn-primary:hover{{background:var(--accent-light);box-shadow:0 8px 24px rgba(200,146,75,.4);transform:translateY(-2px);}}
  .btn-outline{{background:transparent;color:#fff;border:2px solid rgba(255,255,255,.3);}}
  .btn-outline:hover{{border-color:#fff;transform:translateY(-2px);}}
  .footer{{padding:48px 40px 32px;background:#1a1a1a;color:rgba(255,255,255,.65);}}
  .footer-grid{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;max-width:1120px;margin:0 auto;gap:40px;}}
  .footer h4{{color:#fff;font-size:15px;font-weight:700;margin-bottom:16px;}}
  .footer a{{color:rgba(255,255,255,.5);text-decoration:none;font-size:14px;display:block;margin-bottom:8px;transition:var(--transition);}}
  .footer a:hover{{color:var(--accent-light);}}
  .footer-brand p{{font-size:14px;margin-top:12px;max-width:280px;}}
  .footer-bottom{{max-width:1120px;margin:40px auto 0;padding-top:24px;border-top:1px solid rgba(255,255,255,.08);text-align:center;font-size:13px;}}
  .float-phone{{position:fixed;bottom:32px;right:32px;z-index:999;width:60px;height:60px;border-radius:50%;background:#e74c3c;color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 6px 24px rgba(231,76,60,.4);animation:pulse 2s infinite;transition:var(--transition);}}
  .float-phone:hover{{transform:scale(1.1);}}
  .float-phone .icon{{font-size:28px;animation:ring 1.5s ease-in-out infinite;}}
  @keyframes pulse{{0%,100%{{box-shadow:0 6px 24px rgba(231,76,60,.4);}}50%{{box-shadow:0 6px 40px rgba(231,76,60,.7);}}}}
  @keyframes ring{{0%,100%{{transform:rotate(0);}}10%{{transform:rotate(15deg);}}20%{{transform:rotate(-15deg);}}30%{{transform:rotate(10deg);}}40%{{transform:rotate(-10deg);}}50%{{transform:rotate(0);}}}}
  @media(max-width:1024px){{.nav{{padding:0 24px;height:72px;}}.nav-logo{{font-size:40px;letter-spacing:4px;}}.nav-phone{{font-size:30px;}}.related-grid{{grid-template-columns:repeat(2,1fr);}}.footer-grid{{grid-template-columns:repeat(2,1fr);}}}}
  @media(max-width:768px){{.nav{{padding:0 16px;height:64px;}}.nav-logo{{font-size:28px;}}.nav-phone{{font-size:16px;margin-left:8px;}}.nav-links{{display:none;}}.page-header{{padding:120px 20px 40px;}}.page-header h1{{font-size:24px;}}.article-container{{padding:0 20px 40px;}}.related-grid{{grid-template-columns:1fr;}}.footer-grid{{grid-template-columns:1fr;}}}}
  .comment-section{{max-width:900px;margin:0 auto;padding:0 40px 40px;}}
  .comment-section h2{{font-size:24px;font-weight:700;margin-bottom:24px;color:#1a1a1a;}}
  .comment-form{{display:flex;flex-direction:column;gap:16px;margin-bottom:20px;}}
  .comment-form input,.comment-form textarea{{width:100%;padding:14px 18px;border:2px solid #e8e3da;border-radius:12px;font-size:15px;font-family:inherit;transition:border-color .3s;outline:none;background:#fff;}}
  .comment-form input:focus,.comment-form textarea:focus{{border-color:var(--primary);}}
  .comment-form textarea{{min-height:120px;resize:vertical;}}
  .comment-form .btn-submit{{padding:12px 32px;background:var(--primary);color:#fff;border:none;border-radius:50px;font-size:15px;font-weight:600;cursor:pointer;transition:var(--transition);align-self:flex-start;font-family:inherit;}}
  .comment-form .btn-submit:hover{{background:var(--primary-light);transform:translateY(-2px);}}
  .comment-form .btn-submit:disabled{{opacity:.6;cursor:not-allowed;}}
  .comment-msg{{padding:14px 20px;border-radius:12px;margin-bottom:16px;font-size:15px;display:none;}}
  .comment-msg.success{{display:block;background:#e8f5e9;color:#2d5a27;border:1px solid #a5d6a7;}}
  .comment-msg.error{{display:block;background:#fbe9e7;color:#c62828;border:1px solid #ef9a9a;}}
</style>
<script>var _hmt=_hmt||[];(function(){{var hm=document.createElement("script");hm.src="https://hm.baidu.com/hm.js?50d17ca69efc1a95abaf2e673fdabebf";var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(hm,s);}})();</script>
</head>
<body>
<nav class="nav">
  <a href="{site_url}/" class="nav-logo">九天建材</a><a href="tel:{phone}" class="nav-phone">&#9742; {phone}</a>
  <ul class="nav-links">
    <li><a href="{site_url}/#products">产品展示</a></li>
    <li><a href="{site_url}/#scenes">应用场景</a></li>
    <li><a href="{site_url}/applications/">陶粒应用</a></li>
    <li><a href="{site_url}/blog/" class="active">陶粒博客</a></li>
    <li><a href="{site_url}/#contact" class="nav-cta">立即咨询</a></li>
  </ul>
</nav>
'''

FOOTER_TMPL = '''
<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand"><h4 style="font-size:20px;">&#9679; 九天建材</h4><p>专注于高品质陶粒研发、生产与销售，致力于为客户提供绿色建材整体解决方案。</p></div>
    <div><h4>产品中心</h4><a href="{site_url}/#products">建筑结构陶粒</a><a href="{site_url}/#products">园艺绿化陶粒</a><a href="{site_url}/#products">水处理滤料陶粒</a><a href="{site_url}/#products">耐火保温陶粒</a></div>
    <div><h4>内容导航</h4><a href="{site_url}/applications/">陶粒应用案例</a><a href="{site_url}/blog/">陶粒博客</a><a href="{site_url}/#scenes">应用场景</a><a href="{site_url}/#features">核心优势</a></div>
    <div><h4>联系方式</h4><a href="tel:{phone}">电话：{phone}</a><a href="mailto:{email}">邮箱：{email}</a><a href="#">地址：四川成都高新区海洋路</a></div>
  </div>
  <div class="footer-bottom">&copy; 2026 九天建材 · 绿色建材品质之选. All rights reserved.</div>
</footer>
<script>
function submitComment(e){{
  e.preventDefault();
  var btn=document.getElementById('submitBtn');
  var msg=document.getElementById('commentMsg');
  var name=document.getElementById('commentName').value.trim();
  var email=document.getElementById('commentEmail').value.trim();
  var text=document.getElementById('commentText').value.trim();
  if(!name||!text){{msg.className='comment-msg error';msg.textContent='请填写昵称和评论内容';return false;}}
  btn.disabled=true;btn.textContent='提交中...';
  msg.className='comment-msg';msg.textContent='';
  var slug=window.location.pathname.split('/').pop().replace('.html','');
  var title=document.querySelector('.page-header h1')?document.querySelector('.page-header h1').textContent:'';
  fetch('/api/comment',{{
    method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{slug:slug,name:name,email:email,text:text,article_title:title}})
  }})
  .then(function(r){{return r.json();}})
  .then(function(d){{
    msg.className='comment-msg '+(d.ok?'success':'error');
    msg.textContent=d.msg;
    if(d.ok){{document.getElementById('commentForm').reset();}}
  }})
  .catch(function(err){{
    msg.className='comment-msg error';msg.textContent='提交失败，请稍后重试';
  }})
  .finally(function(){{btn.disabled=false;btn.textContent='发表评论';}});
  return false;
}}
</script>
<script>(function(){{var bp=document.createElement('script');var curProtocol=window.location.protocol.split(':')[0];if(curProtocol==='https'){{bp.src='https://zz.bdstatic.com/linksubmit/push.js';}}else{{bp.src='http://push.zhanzhang.baidu.com/push.js';}}var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(bp,s);}})();</script>
<a href="tel:{phone}" class="float-phone" title="立即电话咨询"><span class="icon">&#9742;</span></a>
</body>
</html>
'''

CAT_NAMES = {
    "construction": "施工技巧", "garden": "园艺绿化", "knowledge": "陶粒知识",
    "district": "区域采购", "price": "价格行情", "water": "水处理", "insulation": "工业保温"
}

def gen_article(art, all_articles):
    slug = art["slug"]
    canonical = f"{SITE_URL}/blog/{slug}.html"
    img_file = get_image(art)
    img_path = img_file if img_file and img_file.startswith("http") else (f"{SITE_URL}/{IMG_DIR}/{img_file}" if img_file else "")
    if img_path and not img_path.startswith("http"):
        img_path = f"{SITE_URL}/{IMG_DIR}/{img_file}" if "/" not in img_file else f"{SITE_URL}/images/applications/{os.path.basename(img_file)}"

    meta = f'''<meta name="description" content="{art['meta_desc']}">
<meta name="keywords" content="{art['keywords']}">
<meta name="author" content="{SITE_NAME}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{art['title']} | {SITE_NAME}博客">
<meta property="og:description" content="{art['meta_desc']}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{SITE_NAME}">'''

    ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": art["title"], "description": art["meta_desc"],
        "datePublished": art["date"], "dateModified": art["date"],
        "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "articleSection": CAT_NAMES.get(art["cat"], art["cat"])
    }, ensure_ascii=False)

    header = HEADER_TMPL.format(meta=meta, title=art["title"], ld_json=ld, site_url=SITE_URL, phone=PHONE, site_name=SITE_NAME)

    img_html = f'<img src="{img_path}" alt="{art["title"]}" style="width:100%;max-height:420px;object-fit:cover;border-radius:var(--radius);margin-bottom:32px;box-shadow:var(--shadow);" onerror="this.style.display=\'none\'">' if img_path else ""

    breadcrumb = f'''<div class="breadcrumb"><a href="{SITE_URL}/">首页</a> &raquo; <a href="{SITE_URL}/blog/">陶粒博客</a> &raquo; <span>{art["title"]}</span></div>'''

    tags = " ".join(f'<span class="article-tag">{t.strip()}</span>' for t in art["keywords"].split(",")[:6])

    # Related articles
    related = random.sample([a for a in all_articles if a["slug"] != slug], min(3, len(all_articles)-1))
    related_html = ""
    for ra in related:
        rimg = get_image(ra)
        rimg_path = f"{SITE_URL}/{IMG_DIR}/{rimg}" if rimg else ""
        related_html += f'<a href="{SITE_URL}/blog/{ra["slug"]}.html" class="related-card"><div class="related-card-body"><h3>{ra["title"]}</h3><p>{ra["meta_desc"][:80]}...</p></div></a>\n'

    article_html = f'''
<section class="page-header"><h1>{art["title"]}</h1><p>{art["meta_desc"]}</p></section>
{breadcrumb}
<div class="article-container">
  <div class="article-meta"><span class="article-cat">{CAT_NAMES.get(art["cat"], art["cat"])}</span><span>发布日期: {art["date"]}</span><span>来源: {SITE_NAME}</span></div>
  {img_html}
  <div class="article-content">{art["content"]}</div>
  <div class="article-tags">{tags}</div>
</div>
<section class="comment-section">
  <h2>文章评论</h2>
  <div class="comment-msg" id="commentMsg"></div>
  <form class="comment-form" id="commentForm" onsubmit="return submitComment(event)">
    <input type="text" id="commentName" placeholder="您的昵称 *" required maxlength="50">
    <input type="email" id="commentEmail" placeholder="您的邮箱（选填，方便我们回复您）" maxlength="100">
    <textarea id="commentText" placeholder="写下您的评论或采购意向..." required maxlength="2000"></textarea>
    <button type="submit" class="btn-submit" id="submitBtn">发表评论</button>
  </form>
</section>
<section class="related-section"><h2>相关文章</h2><div class="related-grid">{related_html}</div></section>
<section class="cta"><h2>需要陶粒产品？立即联系我们</h2><p>{SITE_NAME}提供全品类优质陶粒，全国配送，价格优惠</p><div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;"><a href="tel:{PHONE}" class="btn btn-primary">&#9742; {PHONE}</a><a href="mailto:{EMAIL}" class="btn btn-outline">&#9993; 发送邮件咨询</a></div></section>
'''

    footer = FOOTER_TMPL.format(site_url=SITE_URL, phone=PHONE, email=EMAIL)
    return header + article_html + footer

def gen_listing(all_articles):
    """Generate blog index page."""
    cat_counts = {}
    for a in all_articles:
        cat_counts[a["cat"]] = cat_counts.get(a["cat"], 0) + 1
    sq = "'"

    cards = ""
    for art in sorted(all_articles, key=lambda x: x["date"], reverse=True):
        cards += f'''<a href="{SITE_URL}/blog/{art["slug"]}.html" class="blog-card" data-category="{art["cat"]}">
  <h3>{art["title"]}</h3>
  <p>{art["meta_desc"][:120]}...</p>
  <div class="blog-card-meta"><span class="article-cat" style="font-size:12px;">{CAT_NAMES.get(art["cat"], art["cat"])}</span><span>{art["date"]}</span></div>
</a>'''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{SITE_NAME}陶粒博客 - 重庆陶粒选购指南、施工技巧、价格行情、产品知识分享，覆盖重庆各区县陶粒采购攻略。">
<meta name="keywords" content="陶粒博客,重庆陶粒,陶粒知识,陶粒选购,陶粒施工,陶粒价格,重庆建材博客">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_URL}/blog/">
<meta property="og:title" content="陶粒博客 | {SITE_NAME}">
<meta property="og:description" content="{SITE_NAME}陶粒博客 - 陶粒选购、施工、价格、知识分享">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}/blog/">
<title>陶粒博客 | 重庆陶粒选购·施工·价格·知识 | {SITE_NAME}</title>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Blog","name":"九天建材陶粒博客","description":"陶粒选购、施工、价格、知识分享","url":"{SITE_URL}/blog/"}}</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Zhi+Mang+Xing&display=swap');
  *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}
  :root{{--primary:#2d5a27;--primary-light:#4a7c3f;--accent:#c8924b;--accent-light:#e8c07a;--bg:#fafaf8;--bg-warm:#f5f0e8;--text:#2c2c2c;--text-light:#6b6b6b;--white:#fff;--border:#e8e3da;--shadow:0 4px 24px rgba(0,0,0,.06);--shadow-lg:0 12px 48px rgba(0,0,0,.08);--radius:16px;--transition:.35s cubic-bezier(.25,.46,.45,.94);}}
  html{{scroll-behavior:smooth;}}
  body{{font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;color:var(--text);background:var(--bg);line-height:1.85;-webkit-font-smoothing:antialiased;}}
  .nav{{position:fixed;top:0;left:0;right:0;z-index:100;padding:0 40px;height:90px;display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.92);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);box-shadow:0 1px 0 rgba(0,0,0,.05);}}
  .nav-logo{{font-family:'Zhi Mang Xing','STXingkai',cursive;font-size:52px;color:var(--primary);letter-spacing:6px;text-decoration:none;line-height:1;}}
  .nav-phone{{font-family:'STKaiti','KaiTi',serif;font-size:52px;font-weight:900;color:#e74c3c;text-decoration:none;margin-left:24px;letter-spacing:2px;line-height:1;}}
  .nav-links{{display:flex;gap:36px;list-style:none;}}
  .nav-links a{{text-decoration:none;color:var(--text);font-size:15px;font-weight:500;transition:var(--transition);position:relative;}}
  .nav-links a::after{{content:'';position:absolute;bottom:-4px;left:0;width:0;height:2px;background:var(--accent);transition:var(--transition);}}
  .nav-links a:hover{{color:var(--primary);}}
  .nav-links a:hover::after,.nav-links a.active::after{{width:100%;}}
  .nav-links a.active{{color:var(--primary);font-weight:700;}}
  .nav-cta{{padding:8px 24px;background:var(--primary);color:#fff!important;border-radius:50px;font-weight:600;font-size:14px!important;}}
  .nav-cta:hover{{background:var(--primary-light);transform:translateY(-1px);}}
  .nav-cta::after{{display:none!important;}}
  .page-header{{padding:140px 40px 60px;text-align:center;background:linear-gradient(165deg,#f5f0e8 0%,#e8e0d3 40%,#dce8d5 100%);}}
  .page-header h1{{font-size:44px;font-weight:900;color:#1a1a1a;margin-bottom:12px;}}
  .page-header h1 span{{color:var(--primary);}}
  .page-header p{{color:var(--text-light);font-size:17px;max-width:650px;margin:0 auto;}}
  .breadcrumb{{max-width:1100px;margin:0 auto;padding:20px 40px 0;font-size:14px;color:var(--text-light);}}
  .breadcrumb a{{color:var(--primary);text-decoration:none;}}
  .cat-nav{{display:flex;justify-content:center;gap:12px;padding:30px 40px;flex-wrap:wrap;}}
  .cat-btn{{padding:8px 22px;border-radius:50px;text-decoration:none;font-weight:600;font-size:15px;transition:var(--transition);background:var(--white);color:var(--text);box-shadow:var(--shadow);border:none;cursor:pointer;font-family:inherit;}}
  .cat-btn:hover{{background:var(--primary);color:#fff;}}
  .cat-btn.active{{background:var(--primary);color:#fff;}}
  .cat-count{{font-weight:400;opacity:.7;font-size:13px;}}
  .blog-card.hidden{{display:none;}}
  .no-results{{display:none;text-align:center;padding:40px 20px 60px;color:var(--text-light);font-size:16px;grid-column:1/-1;}}
  .blog-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px;max-width:1100px;margin:0 auto;padding:30px 40px 60px;}}
  .blog-card{{background:var(--white);border-radius:var(--radius);padding:28px 32px;box-shadow:var(--shadow);transition:var(--transition);text-decoration:none;color:var(--text);display:flex;flex-direction:column;}}
  .blog-card:hover{{transform:translateY(-4px);box-shadow:var(--shadow-lg);}}
  .blog-card h3{{font-size:18px;font-weight:700;margin-bottom:8px;line-height:1.5;color:#1a1a1a;}}
  .blog-card p{{font-size:14px;color:var(--text-light);flex:1;margin-bottom:12px;}}
  .blog-card-meta{{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--text-light);}}
  .footer{{padding:48px 40px 32px;background:#1a1a1a;color:rgba(255,255,255,.65);}}
  .footer-grid{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;max-width:1120px;margin:0 auto;gap:40px;}}
  .footer h4{{color:#fff;font-size:15px;font-weight:700;margin-bottom:16px;}}
  .footer a{{color:rgba(255,255,255,.5);text-decoration:none;font-size:14px;display:block;margin-bottom:8px;transition:var(--transition);}}
  .footer a:hover{{color:var(--accent-light);}}
  .footer-brand p{{font-size:14px;margin-top:12px;max-width:280px;}}
  .footer-bottom{{max-width:1120px;margin:40px auto 0;padding-top:24px;border-top:1px solid rgba(255,255,255,.08);text-align:center;font-size:13px;}}
  .float-phone{{position:fixed;bottom:32px;right:32px;z-index:999;width:60px;height:60px;border-radius:50%;background:#e74c3c;color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 6px 24px rgba(231,76,60,.4);animation:pulse 2s infinite;transition:var(--transition);}}
  .float-phone:hover{{transform:scale(1.1);}} .float-phone .icon{{font-size:28px;animation:ring 1.5s ease-in-out infinite;}}
  @keyframes pulse{{0%,100%{{box-shadow:0 6px 24px rgba(231,76,60,.4);}}50%{{box-shadow:0 6px 40px rgba(231,76,60,.7);}}}}
  @keyframes ring{{0%,100%{{transform:rotate(0);}}10%{{transform:rotate(15deg);}}20%{{transform:rotate(-15deg);}}30%{{transform:rotate(10deg);}}40%{{transform:rotate(-10deg);}}50%{{transform:rotate(0);}}}}
  @media(max-width:1024px){{.nav{{padding:0 24px;height:72px;}}.nav-logo{{font-size:40px;}}.nav-phone{{font-size:30px;}}.blog-grid{{grid-template-columns:1fr;}}.footer-grid{{grid-template-columns:repeat(2,1fr);}}}}
  @media(max-width:768px){{.nav{{padding:0 16px;height:64px;}}.nav-logo{{font-size:28px;}}.nav-phone{{font-size:16px;margin-left:8px;}}.nav-links{{display:none;}}.page-header{{padding:120px 20px 40px;}}.page-header h1{{font-size:30px;}}.blog-grid{{padding:20px;}}.footer-grid{{grid-template-columns:1fr;}}}}
</style>
<script>var _hmt=_hmt||[];(function(){{var hm=document.createElement("script");hm.src="https://hm.baidu.com/hm.js?50d17ca69efc1a95abaf2e673fdabebf";var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(hm,s);}})();</script>
</head>
<body>
<nav class="nav">
  <a href="{SITE_URL}/" class="nav-logo">九天建材</a><a href="tel:{PHONE}" class="nav-phone">&#9742; {PHONE}</a>
  <ul class="nav-links">
    <li><a href="{SITE_URL}/#products">产品展示</a></li>
    <li><a href="{SITE_URL}/#scenes">应用场景</a></li>
    <li><a href="{SITE_URL}/applications/">陶粒应用</a></li>
    <li><a href="{SITE_URL}/blog/" class="active">陶粒博客</a></li>
    <li><a href="{SITE_URL}/#contact" class="nav-cta">立即咨询</a></li>
  </ul>
</nav>
<section class="page-header"><h1><span>陶粒博客</span></h1><p>重庆陶粒选购指南 · 施工技巧 · 价格行情 · 产品知识 — 分享陶粒行业实用干货</p></section>
<div class="breadcrumb"><a href="{SITE_URL}/">首页</a> &raquo; <span>陶粒博客</span></div>
<div class="cat-nav"><button class="cat-btn active" data-filter="all" onclick="filterCategory('all',this)">全部 <span class="cat-count">({len(all_articles)})</span></button>{" ".join(f'<button class="cat-btn" data-filter="{c}" onclick="filterCategory({sq}{c}{sq},this)">{CAT_NAMES.get(c,c)} <span class="cat-count">({n})</span></button>' for c,n in cat_counts.items())}</div>
<div class="blog-grid" id="blogGrid">{cards}</div>
<div class="no-results" id="noResults">该分类下暂无文章</div>
<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand"><h4 style="font-size:20px;">&#9679; 九天建材</h4><p>专注于高品质陶粒研发、生产与销售。</p></div>
    <div><h4>产品中心</h4><a href="{SITE_URL}/#products">建筑结构陶粒</a><a href="{SITE_URL}/#products">园艺绿化陶粒</a><a href="{SITE_URL}/#products">水处理滤料陶粒</a><a href="{SITE_URL}/#products">耐火保温陶粒</a></div>
    <div><h4>内容导航</h4><a href="{SITE_URL}/applications/">陶粒应用案例</a><a href="{SITE_URL}/blog/">陶粒博客</a><a href="{SITE_URL}/#scenes">应用场景</a></div>
    <div><h4>联系方式</h4><a href="tel:{PHONE}">电话：{PHONE}</a><a href="mailto:{EMAIL}">邮箱：{EMAIL}</a></div>
  </div>
  <div class="footer-bottom">&copy; 2026 九天建材. All rights reserved.</div>
</footer>
<script>
function submitComment(e){{
  e.preventDefault();
  var btn=document.getElementById('submitBtn');
  var msg=document.getElementById('commentMsg');
  var name=document.getElementById('commentName').value.trim();
  var email=document.getElementById('commentEmail').value.trim();
  var text=document.getElementById('commentText').value.trim();
  if(!name||!text){{msg.className='comment-msg error';msg.textContent='请填写昵称和评论内容';return false;}}
  btn.disabled=true;btn.textContent='提交中...';
  msg.className='comment-msg';msg.textContent='';
  var slug=window.location.pathname.split('/').pop().replace('.html','');
  var title=document.querySelector('.page-header h1')?document.querySelector('.page-header h1').textContent:'';
  fetch('/api/comment',{{
    method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{slug:slug,name:name,email:email,text:text,article_title:title}})
  }})
  .then(function(r){{return r.json();}})
  .then(function(d){{
    msg.className='comment-msg '+(d.ok?'success':'error');
    msg.textContent=d.msg;
    if(d.ok){{document.getElementById('commentForm').reset();}}
  }})
  .catch(function(err){{
    msg.className='comment-msg error';msg.textContent='提交失败，请稍后重试';
  }})
  .finally(function(){{btn.disabled=false;btn.textContent='发表评论';}});
  return false;
}}
</script>
<script>
function filterCategory(cat,btn){{
  document.querySelectorAll('.cat-btn').forEach(function(b){{b.classList.remove('active');}});
  btn.classList.add('active');
  var visible=0;
  document.querySelectorAll('.blog-card').forEach(function(card){{
    if(cat==='all'||card.getAttribute('data-category')===cat){{card.classList.remove('hidden');visible++;}}
    else{{card.classList.add('hidden');}}
  }});
  document.getElementById('noResults').style.display=visible?'none':'block';
}}
</script>
<script>(function(){{var bp=document.createElement('script');var curProtocol=window.location.protocol.split(':')[0];if(curProtocol==='https'){{bp.src='https://zz.bdstatic.com/linksubmit/push.js';}}else{{bp.src='http://push.zhanzhang.baidu.com/push.js';}}var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(bp,s);}})();</script>
<a href="tel:{PHONE}" class="float-phone"><span class="icon">&#9742;</span></a>
</body>
</html>'''

# ====== MAIN ======
print(f"Generating {len(ARTICLES)} blog articles...")
print(f"Pexels API: {'configured' if PEXELS_API_KEY else 'not configured (using local images)'}")

for i, art in enumerate(ARTICLES):
    html = gen_article(art, ARTICLES)
    path = os.path.join(BLOG_DIR, f"{art['slug']}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    if (i+1) % 10 == 0:
        print(f"  {i+1}/{len(ARTICLES)} done")

# Listing page
listing = gen_listing(ARTICLES)
with open(os.path.join(BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(listing)

print(f"All {len(ARTICLES)} blog articles + listing page generated.")
print(f"Files: blog/*.html ({len(ARTICLES)+1} files)")
