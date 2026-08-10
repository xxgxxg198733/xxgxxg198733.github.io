#!/usr/bin/env python3
"""
Blog HTML generator for taoli001.cn
Reads blog_data.py, fetches images via Pexels API (or fallback), generates HTML pages.
"""
import os, sys, json, hashlib, random

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

# ====== Image & keyword utilities ======
LOCAL_IMAGES = [f for f in os.listdir("images/applications") if f.endswith(('.jpg','.png','.JPG','.jpeg'))]

# Category-to-image mapping for relevant ceramsite photos
CAT_IMAGE_MAP = {
    "construction": [f for f in LOCAL_IMAGES if "construction" in f.lower()],
    "garden": [f for f in LOCAL_IMAGES if "garden" in f.lower()],
    "water": [f for f in LOCAL_IMAGES if "water" in f.lower()],
    "insulation": [f for f in LOCAL_IMAGES if "insulation" in f.lower()],
}

def get_image(article):
    """Get relevant ceramsite image. Prefer local application photos matching article category."""
    slug = article["slug"]
    cat = article.get("cat", "")
    # Check if already downloaded
    for f in os.listdir(IMG_DIR):
        if f.startswith(slug) and f.endswith(('.jpg','.png','.jpeg')):
            return f

    # 1. Use category-relevant local image (real ceramsite photos)
    cat_images = CAT_IMAGE_MAP.get(cat, [])
    if cat_images:
        picked = random.choice(cat_images)
        return f"../images/applications/{picked}"

    # 2. Fallback to any local image
    if LOCAL_IMAGES:
        picked = random.choice(LOCAL_IMAGES)
        return f"../images/applications/{picked}"

    return None

def find_related(art, all_articles, n=3):
    """Find related articles by shared keyword overlap score. Same category = bonus."""
    my_kws = set(art["keywords"].replace("，", ",").split(","))
    scored = []
    for a in all_articles:
        if a["slug"] == art["slug"]:
            continue
        a_kws = set(a["keywords"].replace("，", ",").split(","))
        score = len(my_kws & a_kws)
        if a["cat"] == art["cat"]:
            score += 2  # same category bonus
        if score > 0:
            scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:n]]

def add_internal_links(content, related_articles):
    """Append contextual 'read more' links pointing to related articles at end of content."""
    if not related_articles:
        return content
    links_html = '<div style="margin-top:28px;padding:20px 24px;background:#f5f0e8;border-radius:12px;border-left:4px solid var(--primary);"><p style="font-weight:700;color:var(--primary);margin-bottom:12px;">延伸阅读：</p><ul style="list-style:none;padding:0;">'
    for ra in related_articles[:3]:
        links_html += f'<li style="margin-bottom:8px;">&raquo; <a href="{SITE_URL}/blog/{ra["slug"]}.html" style="color:var(--primary);text-decoration:underline;font-weight:500;">{ra["title"]}</a></li>'
    links_html += '</ul></div>'
    # Insert before last </p> tag
    last_p = content.rfind('</p>')
    if last_p > 0:
        return content[:last_p + 4] + links_html + content[last_p + 4:]
    return content + links_html

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
  .nav-brand{{display:flex;align-items:center;flex-shrink:0;}}
  .nav-logo{{font-family:'Zhi Mang Xing','STXingkai',cursive;font-size:52px;color:var(--primary);letter-spacing:6px;text-decoration:none;line-height:1;white-space:nowrap;}}
  .nav-phone{{font-family:'STKaiti','KaiTi',serif;font-size:52px;font-weight:900;color:#e74c3c;text-decoration:none;margin-left:24px;letter-spacing:2px;line-height:1;white-space:nowrap;}}
  .nav-links{{display:flex;gap:28px;list-style:none;flex-shrink:0;flex-wrap:nowrap;}}
  .nav-links a{{text-decoration:none;color:var(--text);font-size:15px;font-weight:500;transition:var(--transition);position:relative;white-space:nowrap;}}
  .nav-links a::after{{content:'';position:absolute;bottom:-4px;left:0;width:0;height:2px;background:var(--accent);transition:var(--transition);}}
  .nav-links a:hover{{color:var(--primary);}}
  .nav-links a:hover::after,.nav-links a.active::after{{width:100%;}}
  .nav-links a.active{{color:var(--primary);font-weight:700;}}
  .nav-toggle{{display:none;flex-direction:column;gap:5px;cursor:pointer;background:none;border:none;padding:8px;z-index:101;flex-shrink:0;}}
  .nav-toggle span{{display:block;width:26px;height:2.5px;background:var(--text);border-radius:2px;transition:var(--transition);}}
  .nav-toggle.active span:nth-child(1){{transform:rotate(45deg)translate(5px,5px);}}
  .nav-toggle.active span:nth-child(2){{opacity:0;}}
  .nav-toggle.active span:nth-child(3){{transform:rotate(-45deg)translate(5px,-5px);}}
  .nav-drawer{{display:none;position:fixed;top:0;right:-100%;width:280px;height:100vh;background:#fff;z-index:99;padding:100px 32px 40px;box-shadow:-4px 0 24px rgba(0,0,0,.1);transition:right .35s cubic-bezier(.25,.46,.45,.94);flex-direction:column;gap:8px;}}
  .nav-drawer.open{{right:0;}}
  .nav-drawer a{{display:block;padding:14px 0;text-decoration:none;color:var(--text);font-size:17px;font-weight:500;border-bottom:1px solid var(--border);transition:var(--transition);}}
  .nav-drawer a:hover{{color:var(--primary);padding-left:8px;}}
  .nav-drawer .nav-cta-mobile{{margin-top:12px;padding:14px 32px;background:var(--primary);color:#fff!important;border-radius:50px;text-align:center;font-weight:600;border-bottom:none;}}
  .nav-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:98;}}
  .nav-overlay.show{{display:block;}}
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
  @media(max-width:1200px){{.nav{{padding:0 28px;}}.nav-links{{gap:20px;}}}}
  @media(max-width:1024px){{.nav{{padding:0 24px;height:80px;}}.nav-links{{display:none;}}.nav-toggle{{display:flex;}}.nav-drawer{{display:flex;}}.related-grid{{grid-template-columns:repeat(2,1fr);}}.footer-grid{{grid-template-columns:repeat(2,1fr);}}}}
  @media(max-width:768px){{.nav{{padding:0 16px;height:68px;}}.nav-logo{{font-size:36px;letter-spacing:2px;}}.nav-phone{{font-size:22px;margin-left:10px;letter-spacing:1px;}}.page-header{{padding:120px 20px 40px;}}.page-header h1{{font-size:24px;}}.page-header p{{font-size:15px;max-width:90%;}}.article-container{{padding:0 20px 40px;}}.article-content h2{{font-size:22px;margin:28px 0 12px;}}.article-content{{font-size:15px;}}.article-meta{{gap:12px;font-size:13px;}}.related-section{{padding:40px 20px;}}.related-section h2{{font-size:24px;}}.related-grid{{grid-template-columns:1fr;}}.cta{{padding:60px 20px;}}.cta h2{{font-size:28px;}}.cta p{{font-size:15px;}}.footer{{padding:40px 20px 24px;}}.footer-grid{{grid-template-columns:1fr;gap:24px;}}.comment-section{{padding:0 20px 40px;}}.comment-section h2{{font-size:20px;}}.breadcrumb{{padding:16px 20px 0;font-size:13px;}}}}
  @media(max-width:480px){{.nav{{padding:0 12px;height:60px;}}.nav-logo{{font-size:28px;letter-spacing:1px;}}.nav-phone{{font-size:17px;margin-left:6px;letter-spacing:0;}}.page-header{{padding:100px 16px 32px;}}.page-header h1{{font-size:20px;}}.page-header p{{font-size:14px;}}.article-container{{padding:0 16px 32px;}}.article-content h2{{font-size:20px;margin:24px 0 10px;}}.article-content{{font-size:14px;}}.btn{{padding:12px 24px;font-size:14px;}}.cta h2{{font-size:24px;}}.cta p{{font-size:14px;}}.footer{{padding:32px 16px 20px;}}.footer h4{{font-size:14px;}}.comment-section{{padding:0 16px 32px;}}.breadcrumb{{padding:12px 16px 0;font-size:12px;}}.nav-drawer{{width:260px;}}}}
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
  <div class="nav-brand">
    <a href="{site_url}/" class="nav-logo">九天建材</a><a href="tel:{phone}" class="nav-phone">&#9742; {phone}</a>
  </div>
  <ul class="nav-links">
    <li><a href="{site_url}/#products">产品展示</a></li>
    <li><a href="{site_url}/#scenes">应用场景</a></li>
    <li><a href="{site_url}/applications/">陶粒应用</a></li>
    <li><a href="{site_url}/blog/" class="active">陶粒博客</a></li>
    <li><a href="{site_url}/#contact" class="nav-cta">立即咨询</a></li>
  </ul>
  <button class="nav-toggle" id="navToggle" aria-label="菜单"><span></span><span></span><span></span></button>
</nav>
<div class="nav-overlay" id="navOverlay"></div>
<div class="nav-drawer" id="navDrawer">
  <a href="{site_url}/#products">产品展示</a>
  <a href="{site_url}/#scenes">应用场景</a>
  <a href="{site_url}/applications/">陶粒应用</a>
  <a href="{site_url}/blog/">陶粒博客</a>
  <a href="{site_url}/#contact" class="nav-cta-mobile">立即咨询</a>
</div>
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
<script>
// Hamburger menu
(function(){{
  var toggle=document.getElementById('navToggle');
  var drawer=document.getElementById('navDrawer');
  var overlay=document.getElementById('navOverlay');
  function open(){{toggle.classList.add('active');drawer.classList.add('open');overlay.classList.add('show');document.body.style.overflow='hidden';}}
  function close(){{toggle.classList.remove('active');drawer.classList.remove('open');overlay.classList.remove('show');document.body.style.overflow='';}}
  toggle.addEventListener('click',function(){{toggle.classList.contains('active')?close():open();}});
  overlay.addEventListener('click',close);
  drawer.querySelectorAll('a').forEach(function(a){{a.addEventListener('click',close);}});
}})();
</script>
</body>
</html>
'''

CAT_NAMES = {
    "construction": "施工技巧", "garden": "园艺绿化", "knowledge": "陶粒知识",
    "district": "区域采购", "price": "价格行情", "news": "行业新闻", "water": "水处理", "insulation": "工业保温"
}

def gen_article(art, all_articles):
    slug = art["slug"]
    canonical = f"{SITE_URL}/blog/{slug}.html"
    img_file = get_image(art)
    img_path = ""
    if img_file:
        if img_file.startswith("http"):
            img_path = img_file
        elif img_file.startswith("../images/"):
            img_path = f"{SITE_URL}/images/{'/'.join(img_file.split('/')[2:])}"
        elif "/" not in img_file:
            img_path = f"{SITE_URL}/{IMG_DIR}/{img_file}"
        else:
            img_path = f"{SITE_URL}/{img_file}"

    # Long-tail keyword optimization: merge primary keywords into meta
    cat_name = CAT_NAMES.get(art["cat"], art["cat"])
    primary_kw = art["keywords"].split(",")[0].strip()

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

    # Build schemas: Article + BreadcrumbList + optional FAQPage
    schemas = [{
        "@context": "https://schema.org", "@type": "Article",
        "headline": art["title"], "description": art["meta_desc"],
        "datePublished": art["date"], "dateModified": art["date"],
        "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "articleSection": cat_name
    }, {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "首页", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": "陶粒博客", "item": f"{SITE_URL}/blog/"},
            {"@type": "ListItem", "position": 3, "name": cat_name, "item": f"{SITE_URL}/blog/{art['cat']}.html"},
            {"@type": "ListItem", "position": 4, "name": art["title"]}
        ]
    }]

    # FAQPage schema for question-style titles (contains "？" or starts with Q-words)
    is_question = "？" in art["title"] or any(art["title"].startswith(w) for w in ["什么", "如何", "怎么", "为什么", "哪", "多少"])
    if is_question:
        faq_text = art["content"].replace("<p>", "").replace("</p>", "\n").replace("<h2>", "").replace("</h2>", "").replace("<strong>", "").replace("</strong>", "")
        # Extract first 300 chars as answer snippet
        answer_snippet = faq_text[:300].strip().replace('"', '\\"')
        schemas.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question", "name": art["title"],
                "acceptedAnswer": {"@type": "Answer", "text": answer_snippet}
            }]
        })

    ld = json.dumps(schemas if len(schemas) > 1 else schemas[0], ensure_ascii=False)

    header = HEADER_TMPL.format(meta=meta, title=art["title"], ld_json=ld, site_url=SITE_URL, phone=PHONE, site_name=SITE_NAME)

    img_alt = f"{primary_kw} - {art['title']}" if primary_kw else art["title"]
    img_html = f'<img src="{img_path}" alt="{img_alt}" style="width:100%;max-height:420px;object-fit:cover;border-radius:var(--radius);margin-bottom:32px;box-shadow:var(--shadow);" onerror="this.style.display=\'none\'">' if img_path else ""

    breadcrumb = f'''<div class="breadcrumb"><a href="{SITE_URL}/">首页</a> &raquo; <a href="{SITE_URL}/blog/">陶粒博客</a> &raquo; <a href="{SITE_URL}/blog/{art['cat']}.html">{cat_name}</a> &raquo; <span>{art["title"]}</span></div>'''

    tags = " ".join(f'<span class="article-tag">{t.strip()}</span>' for t in art["keywords"].split(",")[:6])

    # Smart related articles by keyword overlap
    related = find_related(art, all_articles, n=3)
    if len(related) < 3:
        # fallback: same category articles
        same_cat = [a for a in all_articles if a["cat"] == art["cat"] and a["slug"] != slug]
        for a in same_cat:
            if a not in related:
                related.append(a)
            if len(related) >= 3:
                break
    if len(related) < 3:
        extra = random.sample([a for a in all_articles if a["slug"] != slug and a not in related], min(3 - len(related), len(all_articles) - 1 - len(related)))
        related.extend(extra)

    related_html = ""
    for ra in related[:3]:
        ra_kw = ra["keywords"].split(",")[0].strip() if ra["keywords"] else ra["title"]
        related_html += f'<a href="{SITE_URL}/blog/{ra["slug"]}.html" class="related-card"><div class="related-card-body"><h3>{ra["title"]}</h3><p>{ra["meta_desc"][:80]}...</p></div></a>\n'

    # Add internal links to content (link to related articles)
    linked_content = add_internal_links(art["content"], related)

    article_html = f'''
<section class="page-header"><h1>{art["title"]}</h1><p>{art["meta_desc"]}</p></section>
{breadcrumb}
<div class="article-container">
  <div class="article-meta"><span class="article-cat">{cat_name}</span><span>发布日期: {art["date"]}</span><span>来源: {SITE_NAME}</span></div>
  {img_html}
  <div class="article-content">{linked_content}</div>
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
  .nav-brand{{display:flex;align-items:center;flex-shrink:0;}}
  .nav-logo{{font-family:'Zhi Mang Xing','STXingkai',cursive;font-size:52px;color:var(--primary);letter-spacing:6px;text-decoration:none;line-height:1;white-space:nowrap;}}
  .nav-phone{{font-family:'STKaiti','KaiTi',serif;font-size:52px;font-weight:900;color:#e74c3c;text-decoration:none;margin-left:24px;letter-spacing:2px;line-height:1;white-space:nowrap;}}
  .nav-links{{display:flex;gap:28px;list-style:none;flex-shrink:0;flex-wrap:nowrap;}}
  .nav-links a{{text-decoration:none;color:var(--text);font-size:15px;font-weight:500;transition:var(--transition);position:relative;white-space:nowrap;}}
  .nav-links a::after{{content:'';position:absolute;bottom:-4px;left:0;width:0;height:2px;background:var(--accent);transition:var(--transition);}}
  .nav-links a:hover{{color:var(--primary);}}
  .nav-links a:hover::after,.nav-links a.active::after{{width:100%;}}
  .nav-links a.active{{color:var(--primary);font-weight:700;}}
  .nav-toggle{{display:none;flex-direction:column;gap:5px;cursor:pointer;background:none;border:none;padding:8px;z-index:101;flex-shrink:0;}}
  .nav-toggle span{{display:block;width:26px;height:2.5px;background:var(--text);border-radius:2px;transition:var(--transition);}}
  .nav-toggle.active span:nth-child(1){{transform:rotate(45deg)translate(5px,5px);}}
  .nav-toggle.active span:nth-child(2){{opacity:0;}}
  .nav-toggle.active span:nth-child(3){{transform:rotate(-45deg)translate(5px,-5px);}}
  .nav-drawer{{display:none;position:fixed;top:0;right:-100%;width:280px;height:100vh;background:#fff;z-index:99;padding:100px 32px 40px;box-shadow:-4px 0 24px rgba(0,0,0,.1);transition:right .35s cubic-bezier(.25,.46,.45,.94);flex-direction:column;gap:8px;}}
  .nav-drawer.open{{right:0;}}
  .nav-drawer a{{display:block;padding:14px 0;text-decoration:none;color:var(--text);font-size:17px;font-weight:500;border-bottom:1px solid var(--border);transition:var(--transition);}}
  .nav-drawer a:hover{{color:var(--primary);padding-left:8px;}}
  .nav-drawer .nav-cta-mobile{{margin-top:12px;padding:14px 32px;background:var(--primary);color:#fff!important;border-radius:50px;text-align:center;font-weight:600;border-bottom:none;}}
  .nav-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:98;}}
  .nav-overlay.show{{display:block;}}
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
  @media(max-width:1200px){{.nav{{padding:0 28px;}}.nav-links{{gap:20px;}}}}
  @media(max-width:1024px){{.nav{{padding:0 24px;height:80px;}}.nav-links{{display:none;}}.nav-toggle{{display:flex;}}.nav-drawer{{display:flex;}}.blog-grid{{grid-template-columns:1fr;}}.footer-grid{{grid-template-columns:repeat(2,1fr);}}}}
  @media(max-width:768px){{.nav{{padding:0 16px;height:68px;}}.nav-logo{{font-size:36px;letter-spacing:2px;}}.nav-phone{{font-size:22px;margin-left:10px;letter-spacing:1px;}}.page-header{{padding:120px 20px 40px;}}.page-header h1{{font-size:26px;}}.page-header p{{font-size:15px;max-width:90%;}}.blog-grid{{padding:20px 20px 40px;}}.blog-card-body{{padding:16px;}}.blog-card-body h3{{font-size:15px;}}.cta{{padding:60px 20px;}}.cta h2{{font-size:28px;}}.cta p{{font-size:15px;}}.footer{{padding:40px 20px 24px;}}.footer-grid{{grid-template-columns:1fr;gap:24px;}}.breadcrumb{{padding:16px 20px 0;font-size:13px;}}.btn{{padding:12px 24px;font-size:14px;}}.cat-nav{{gap:8px;padding:16px 20px;overflow-x:auto;flex-wrap:nowrap;}}.cat-nav a{{font-size:13px;padding:8px 16px;white-space:nowrap;}}}}
  @media(max-width:480px){{.nav{{padding:0 12px;height:60px;}}.nav-logo{{font-size:28px;letter-spacing:1px;}}.nav-phone{{font-size:17px;margin-left:6px;letter-spacing:0;}}.page-header{{padding:100px 16px 32px;}}.page-header h1{{font-size:20px;}}.page-header p{{font-size:14px;}}.article-container{{padding:0 16px 32px;}}.article-content h2{{font-size:20px;margin:24px 0 10px;}}.article-content{{font-size:14px;}}.btn{{padding:12px 24px;font-size:14px;}}.cta h2{{font-size:24px;}}.cta p{{font-size:14px;}}.footer{{padding:32px 16px 20px;}}.footer h4{{font-size:14px;}}.comment-section{{padding:0 16px 32px;}}.breadcrumb{{padding:12px 16px 0;font-size:12px;}}.nav-drawer{{width:260px;}}}}
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
<script>
// Hamburger menu
(function(){{
  var toggle=document.getElementById('navToggle');
  var drawer=document.getElementById('navDrawer');
  var overlay=document.getElementById('navOverlay');
  function open(){{toggle.classList.add('active');drawer.classList.add('open');overlay.classList.add('show');document.body.style.overflow='hidden';}}
  function close(){{toggle.classList.remove('active');drawer.classList.remove('open');overlay.classList.remove('show');document.body.style.overflow='';}}
  toggle.addEventListener('click',function(){{toggle.classList.contains('active')?close():open();}});
  overlay.addEventListener('click',close);
  drawer.querySelectorAll('a').forEach(function(a){{a.addEventListener('click',close);}});
}})();
</script>
</body>
</html>'''

def gen_category_page(cat_key, articles):
    """Generate a category hub page with its own SEO metadata."""
    cat_name = CAT_NAMES.get(cat_key, cat_key)
    cat_articles = sorted([a for a in articles if a["cat"] == cat_key], key=lambda x: x["date"], reverse=True)
    n = len(cat_articles)

    cat_descriptions = {
        "construction": "陶粒施工技巧专题 — 回填、找坡、混凝土搅拌、屋顶防水等陶粒施工全流程详解，专业施工团队经验分享。",
        "price": "陶粒价格行情专题 — 重庆及周边各区县陶粒实时报价、价格走势分析、采购成本对比，助您买到实惠好陶粒。",
        "knowledge": "陶粒知识百科专题 — 陶粒生产工艺、性能参数、选购技巧、产品对比，全面了解陶粒材料特性。",
        "district": "区域采购指南专题 — 重庆各区县陶粒采购攻略，本地厂家推荐、运输成本分析、就近采购建议。",
        "garden": "园艺绿化陶粒专题 — 屋顶花园、阳台菜园、多肉盆栽、草坪排水等园艺陶粒应用技巧与实践分享。",
        "news": "陶粒行业新闻专题 — 最新陶粒建材行业动态、市场走势、政策解读、企业快讯，紧跟陶粒行业前沿资讯。",
    }

    cards = ""
    for art in cat_articles:
        cards += f'''<a href="{SITE_URL}/blog/{art["slug"]}.html" class="blog-card" data-category="{art['cat']}">
  <h3>{art["title"]}</h3>
  <p>{art["meta_desc"][:120]}...</p>
  <div class="blog-card-meta"><span>{art["date"]}</span></div>
</a>'''

    # Precompute LD+JSON to avoid f-string backslash issues
    part_items = []
    for a in cat_articles[:10]:
        safe_title = a['title'].replace('"', '\\"')
        part_items.append('{"@type":"Article","headline":"' + safe_title + '"}')
    ld_json = '{"@context":"https://schema.org","@type":"CollectionPage","name":"' + cat_name + ' - 陶粒博客专题","description":"' + cat_descriptions.get(cat_key, '') + '","url":"' + SITE_URL + '/blog/' + cat_key + '.html","hasPart":[' + ','.join(part_items) + ']}'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{cat_descriptions.get(cat_key, f'{cat_name} - {SITE_NAME}陶粒博客专题')}">
<meta name="keywords" content="{cat_name},陶粒{cat_name},重庆陶粒{cat_name},{cat_name}陶粒,{SITE_NAME}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_URL}/blog/{cat_key}.html">
<meta property="og:title" content="{cat_name} | 陶粒博客 | {SITE_NAME}">
<meta property="og:description" content="{cat_descriptions.get(cat_key, '')}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}/blog/{cat_key}.html">
<title>{cat_name} | 陶粒博客专题 | {SITE_NAME}</title>
<script type="application/ld+json">{ld_json}</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Zhi+Mang+Xing&display=swap');
  *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}
  :root{{--primary:#2d5a27;--primary-light:#4a7c3f;--accent:#c8924b;--accent-light:#e8c07a;--bg:#fafaf8;--bg-warm:#f5f0e8;--text:#2c2c2c;--text-light:#6b6b6b;--white:#fff;--border:#e8e3da;--shadow:0 4px 24px rgba(0,0,0,.06);--shadow-lg:0 12px 48px rgba(0,0,0,.08);--radius:16px;--transition:.35s cubic-bezier(.25,.46,.45,.94);}}
  html{{scroll-behavior:smooth;}}
  body{{font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;color:var(--text);background:var(--bg);line-height:1.85;}}
  .nav{{position:fixed;top:0;left:0;right:0;z-index:100;padding:0 40px;height:90px;display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.92);backdrop-filter:blur(20px);box-shadow:0 1px 0 rgba(0,0,0,.05);}}
  .nav-logo{{font-family:'Zhi Mang Xing','STXingkai',cursive;font-size:52px;color:var(--primary);letter-spacing:6px;text-decoration:none;line-height:1;}}
  .nav-phone{{font-family:'STKaiti','KaiTi',serif;font-size:52px;font-weight:900;color:#e74c3c;text-decoration:none;margin-left:24px;letter-spacing:2px;line-height:1;}}
  .nav-links{{display:flex;gap:36px;list-style:none;}}
  .nav-links a{{text-decoration:none;color:var(--text);font-size:15px;font-weight:500;transition:var(--transition);position:relative;}}
  .nav-links a.active{{color:var(--primary);font-weight:700;}}
  .nav-cta{{padding:8px 24px;background:var(--primary);color:#fff!important;border-radius:50px;font-weight:600;font-size:14px!important;}}
  .page-header{{padding:140px 40px 60px;text-align:center;background:linear-gradient(165deg,#f5f0e8 0%,#e8e0d3 40%,#dce8d5 100%);}}
  .page-header h1{{font-size:44px;font-weight:900;color:#1a1a1a;margin-bottom:12px;}}
  .page-header p{{color:var(--text-light);font-size:17px;max-width:650px;margin:0 auto;}}
  .breadcrumb{{max-width:1100px;margin:0 auto;padding:20px 40px 0;font-size:14px;color:var(--text-light);}}
  .breadcrumb a{{color:var(--primary);text-decoration:none;}}
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
  .footer-bottom{{max-width:1120px;margin:40px auto 0;padding-top:24px;border-top:1px solid rgba(255,255,255,.08);text-align:center;font-size:13px;}}
  .float-phone{{position:fixed;bottom:32px;right:32px;z-index:999;width:60px;height:60px;border-radius:50%;background:#e74c3c;color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 6px 24px rgba(231,76,60,.4);animation:pulse 2s infinite;}}
  .float-phone:hover{{transform:scale(1.1);}} .float-phone .icon{{font-size:28px;animation:ring 1.5s ease-in-out infinite;}}
  @keyframes pulse{{0%,100%{{box-shadow:0 6px 24px rgba(231,76,60,.4);}}50%{{box-shadow:0 6px 40px rgba(231,76,60,.7);}}}}
  @keyframes ring{{0%,100%{{transform:rotate(0);}}10%{{transform:rotate(15deg);}}20%{{transform:rotate(-15deg);}}30%{{transform:rotate(10deg);}}40%{{transform:rotate(-10deg);}}50%{{transform:rotate(0);}}}}
  @media(max-width:1200px){{.nav{{padding:0 28px;}}.nav-links{{gap:20px;}}}}
  @media(max-width:1024px){{.nav{{padding:0 24px;height:80px;}}.nav-links{{display:none;}}.nav-toggle{{display:flex;}}.nav-drawer{{display:flex;}}.blog-grid{{grid-template-columns:1fr;}}.footer-grid{{grid-template-columns:repeat(2,1fr);}}}}
  @media(max-width:768px){{.nav{{padding:0 16px;height:68px;}}.nav-logo{{font-size:36px;letter-spacing:2px;}}.nav-phone{{font-size:22px;margin-left:10px;letter-spacing:1px;}}.page-header{{padding:120px 20px 40px;}}.page-header h1{{font-size:26px;}}.page-header p{{font-size:15px;max-width:90%;}}.blog-grid{{padding:20px 20px 40px;}}.blog-card-body{{padding:16px;}}.blog-card-body h3{{font-size:15px;}}.cta{{padding:60px 20px;}}.cta h2{{font-size:28px;}}.cta p{{font-size:15px;}}.footer{{padding:40px 20px 24px;}}.footer-grid{{grid-template-columns:1fr;gap:24px;}}.breadcrumb{{padding:16px 20px 0;font-size:13px;}}.btn{{padding:12px 24px;font-size:14px;}}.cat-nav{{gap:8px;padding:16px 20px;overflow-x:auto;flex-wrap:nowrap;}}.cat-nav a{{font-size:13px;padding:8px 16px;white-space:nowrap;}}}}
  @media(max-width:480px){{.nav{{padding:0 12px;height:60px;}}.nav-logo{{font-size:28px;letter-spacing:1px;}}.nav-phone{{font-size:17px;margin-left:6px;letter-spacing:0;}}.page-header{{padding:100px 16px 32px;}}.page-header h1{{font-size:20px;}}.page-header p{{font-size:14px;}}.article-container{{padding:0 16px 32px;}}.article-content h2{{font-size:20px;margin:24px 0 10px;}}.article-content{{font-size:14px;}}.btn{{padding:12px 24px;font-size:14px;}}.cta h2{{font-size:24px;}}.cta p{{font-size:14px;}}.footer{{padding:32px 16px 20px;}}.footer h4{{font-size:14px;}}.comment-section{{padding:0 16px 32px;}}.breadcrumb{{padding:12px 16px 0;font-size:12px;}}.nav-drawer{{width:260px;}}}}
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
<section class="page-header"><h1>{cat_name}</h1><p>{cat_descriptions.get(cat_key, '')}</p></section>
<div class="breadcrumb"><a href="{SITE_URL}/">首页</a> &raquo; <a href="{SITE_URL}/blog/">陶粒博客</a> &raquo; <span>{cat_name}</span></div>
<div class="blog-grid">{cards}</div>
<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand"><h4 style="font-size:20px;">&#9679; 九天建材</h4><p>专注于高品质陶粒研发、生产与销售。</p></div>
    <div><h4>产品中心</h4><a href="{SITE_URL}/#products">建筑结构陶粒</a><a href="{SITE_URL}/#products">园艺绿化陶粒</a><a href="{SITE_URL}/#products">水处理滤料陶粒</a><a href="{SITE_URL}/#products">耐火保温陶粒</a></div>
    <div><h4>博客分类</h4>{"".join(f'<a href="{SITE_URL}/blog/{k}.html">{v}</a>' for k,v in CAT_NAMES.items() if k in ["construction","price","knowledge","district","garden","news"])}</div>
    <div><h4>联系方式</h4><a href="tel:{PHONE}">电话：{PHONE}</a><a href="mailto:{EMAIL}">邮箱：{EMAIL}</a></div>
  </div>
  <div class="footer-bottom">&copy; 2026 九天建材. All rights reserved.</div>
</footer>
<script>(function(){{var bp=document.createElement('script');var curProtocol=window.location.protocol.split(':')[0];if(curProtocol==='https'){{bp.src='https://zz.bdstatic.com/linksubmit/push.js';}}else{{bp.src='http://push.zhanzhang.baidu.com/push.js';}}var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(bp,s);}})();</script>
<a href="tel:{PHONE}" class="float-phone"><span class="icon">&#9742;</span></a>
<script>
// Hamburger menu
(function(){{
  var toggle=document.getElementById('navToggle');
  var drawer=document.getElementById('navDrawer');
  var overlay=document.getElementById('navOverlay');
  function open(){{toggle.classList.add('active');drawer.classList.add('open');overlay.classList.add('show');document.body.style.overflow='hidden';}}
  function close(){{toggle.classList.remove('active');drawer.classList.remove('open');overlay.classList.remove('show');document.body.style.overflow='';}}
  toggle.addEventListener('click',function(){{toggle.classList.contains('active')?close():open();}});
  overlay.addEventListener('click',close);
  drawer.querySelectorAll('a').forEach(function(a){{a.addEventListener('click',close);}});
}})();
</script>
</body>
</html>'''

# ====== MAIN ======
print(f"Generating {len(ARTICLES)} blog articles...")
print(f"Using local ceramsite images from images/applications/")

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
print("  listing page done")

# Category hub pages
for cat_key in ["construction", "price", "knowledge", "district", "garden", "news"]:
    cat_html = gen_category_page(cat_key, ARTICLES)
    with open(os.path.join(BLOG_DIR, f"{cat_key}.html"), "w", encoding="utf-8") as f:
        f.write(cat_html)
    print(f"  category: {cat_key}")

print(f"All {len(ARTICLES)} blog articles + listing + {6} category pages generated.")
print(f"Files: blog/*.html ({len(ARTICLES)+1+6} files)")
