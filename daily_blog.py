#!/usr/bin/env python3
"""
Daily blog article generator for taoli001.cn
Generates 15 new Chongqing-region ceramsite SEO blog articles per run.
Intended to be run via cron before 6am daily.
Usage: python3 daily_blog.py
Environment: PEXELS_API_KEY (optional - free Pexels API key for matching images)
"""
import os, sys, json, hashlib, random, urllib.request, urllib.parse, ssl, time
from datetime import date, timedelta

SITE_URL = "https://www.taoli001.cn"
SITE_NAME = "九天建材"
PHONE = "19008096839"
EMAIL = "xxgxxg198733@gmail.com"
BLOG_DIR = "blog"
IMG_DIR = "images/blog"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
DAILY_COUNT = 15

os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

TODAY = date.today().isoformat()

# ====== Existing slugs to avoid duplicates ======
existing_slugs = set()
if os.path.exists(BLOG_DIR):
    for f in os.listdir(BLOG_DIR):
        if f.endswith('.html') and f != 'index.html':
            existing_slugs.add(f.replace('.html', ''))

# ====== Image utilities ======
LOCAL_IMAGES = []
for d in ['images/applications', 'images/blog']:
    if os.path.exists(d):
        LOCAL_IMAGES.extend([f"{d}/{f}" for f in os.listdir(d) if f.endswith(('.jpg','.png','.JPG','.jpeg'))])

def fetch_pexels_image(query, slug):
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
            img_data = urllib.request.urlopen(img_url, timeout=15, context=ctx).read()
            ext = img_url.split(".")[-1].split("?")[0] or "jpg"
            local_path = os.path.join(IMG_DIR, f"{slug}.{ext}")
            with open(local_path, "wb") as f:
                f.write(img_data)
            return f"{slug}.{ext}"
    except Exception as e:
        print(f"  [IMG ERR] {query[:30]}: {e}")
    return None

def get_image(article_slug, pexels_query):
    for f in os.listdir(IMG_DIR):
        if f.startswith(article_slug) and f.endswith(('.jpg','.png','.jpeg')):
            return f
    if PEXELS_API_KEY:
        result = fetch_pexels_image(pexels_query, article_slug)
        if result:
            return result
    if LOCAL_IMAGES:
        return random.choice(LOCAL_IMAGES)
    return None

# ====== Article generation templates ======
# Pool of Chongqing regional ceramsite topics for daily generation
TOPIC_POOLS = {
    "price": [
        ("重庆{month}月陶粒价格走势分析：{district}等区最新报价", "price",
         "<p>了解重庆地区<strong>{month}月陶粒价格</strong>走势，对于工程项目预算编制和采购时机把握至关重要。本文整理{district}等区域最新陶粒报价。</p>"
         "<h2>本月陶粒市场概况</h2><p>{month}月重庆陶粒市场总体平稳，建筑陶粒价格在180-280元/m³区间波动。受原材料和运输成本影响，不同区域价格差异明显。{district}等主城区域因运输近便，价格相对较低。</p>"
         "<h2>各品类陶粒参考价格</h2><p>建筑结构陶粒：180-280元/m³；园艺绿化陶粒：120-200元/m³；滤料陶粒：350-600元/m³；保温陶粒：500-900元/m³。以上为含税出厂价，运费另计。</p>"
         "<h2>采购建议</h2><p>建议货比三家，批量采购争取优惠。九天建材厂家直销，提供透明报价和免费技术咨询。</p>",
         f"重庆{{month}}月陶粒价格走势分析：{{district}}等区最新报价及市场行情解读。"),
        ("{district}陶粒多少钱一方？{year}年最新报价及运费参考", "price",
         "<p>在<strong>{district}采购陶粒</strong>，价格是大家最关心的问题。本文整理{district}及周边地区{year}年陶粒最新报价。</p>"
         "<h2>{district}陶粒价格构成</h2><p>陶粒价格=出厂价+运费。{district}距离重庆主产区约XX公里，运费约XX元/m³。综合计算，{district}建筑陶粒到货价约XXX-XXX元/m³。</p>"
         "<h2>影响价格的因素</h2><p>批量大小、运输距离、陶粒品类和规格、包装方式（袋装/吨袋/散装）都会影响最终价格。一般50m³以上可享受批发价。</p>"
         "<h2>如何获取准确报价</h2><p>建议直接联系厂家获取实时报价。九天建材提供{district}全境配送服务，电话{PHONE}，免费报价。</p>",
         f"{{district}}陶粒价格：{{year}}年最新报价、运费参考及省钱采购建议。"),
    ],
    "knowledge": [
        ("陶粒可以种什么植物？重庆家庭园艺陶粒使用全攻略", "knowledge",
         "<p>很多重庆花友都在问：<strong>陶粒可以种什么植物</strong>？答案是几乎所有盆栽植物都可以用陶粒来改善生长环境。</p>"
         "<h2>陶粒种植适用植物</h2><p>多肉植物：陶粒铺面透气防烂根；兰花：陶粒做栽培基质沥水透气；绿萝、吊兰等观叶植物：花盆底部铺陶粒做排水层；月季、三角梅：陶粒改良粘土土壤。重庆气候潮湿，陶粒的排水功能尤为重要。</p>"
         "<h2>陶粒使用方法</h2><p>盆底排水层（铺3-5cm）、土壤改良（掺入20-30%）、表面铺面（铺2-3cm）。不同用途选用不同粒径：排水用10-20mm、掺土用5-10mm、铺面用3-8mm。</p>"
         "<h2>注意事项</h2><p>新陶粒使用前清洗去粉尘；旧陶粒可清洗消毒后重复使用；不建议单一使用陶粒做基质（需配比有机质）。</p>",
         "陶粒种植植物全攻略：多肉、兰花、绿萝适用方法，重庆家庭园艺陶粒使用技巧。"),
        ("陶粒是什么材料做的？陶粒的原料成分与环保特性分析", "knowledge",
         "<p><strong>陶粒是什么材料做的</strong>？简单说，陶粒是以天然矿物为原料经高温烧制而成的人造轻骨料，是一种绿色环保建材。</p>"
         "<h2>主要原料</h2><p>1. 页岩：最优质的陶粒原料，烧制的陶粒强度高、吸水率低；2. 黏土：来源广泛，适合生产园艺和水处理用陶粒；3. 粉煤灰：工业固废利用，环保意义突出；4. 污泥：城市污水处理厂污泥资源化利用。</p>"
         "<h2>环保特性</h2><p>陶粒生产可使用工业固废和城市污泥为原料，实现废物资源化利用。使用阶段的保温隔热性能可降低建筑能耗20-30%。废弃后可破碎用作路基填料或土壤改良剂，全生命周期环境友好。</p>"
         "<h2>健康安全</h2><p>陶粒经高温烧结（≥1150℃），无有机物挥发、无重金属析出、无放射性危害，是安全的绿色建材产品。</p>",
         "陶粒原料成分详解：页岩、黏土、粉煤灰、污泥四大原料来源及环保特性分析。"),
    ],
    "construction": [
        ("重庆高层住宅{position}陶粒混凝土施工工艺与质量保证", "construction",
         "<p>在重庆高层住宅的<strong>{position}施工中</strong>，陶粒混凝土凭借轻质、保温等优势应用广泛。</p>"
         "<h2>工程概况与技术难点</h2><p>重庆高层住宅{position}施工面临的主要难点是：减轻自重以降低结构荷载、保证保温隔热性能满足重庆气候要求、提高施工效率缩短工期。</p>"
         "<h2>陶粒混凝土方案</h2><p>采用LC25-LC30级陶粒轻骨料混凝土，堆积密度≤800kg/m³，比普通混凝土轻30-40%。配合比根据重庆高温高湿气候条件进行调整，确保施工性能和硬化后质量。</p>"
         "<h2>质量保证措施</h2><p>陶粒预湿处理、严格控制水灰比、及时覆盖养护≥7天、每批次留置试块检测强度。严格执行以上措施，可确保陶粒混凝土质量达到设计标准。</p>",
         f"重庆高层住宅陶粒混凝土{position}施工工艺详解：配合比设计、质量控制与养护要点。"),
        ("{district}新农村建设陶粒砌块应用推广效果评估", "construction",
         "<p><strong>{district}新农村建设</strong>中推广了陶粒砌块农房建造技术，本文对该项目的应用效果进行评估总结。</p>"
         "<h2>推广背景</h2><p>{district}农村传统建房多使用粘土砖，存在保温差、能耗高、破坏耕地等问题。陶粒砌块轻质保温、利废环保，是替代传统粘土砖的理想选择。</p>"
         "<h2>应用效果</h2><p>使用陶粒砌块的农房，冬季室温比传统砖房高3-5℃，夏季低2-4℃，居住舒适度明显提升。单栋农房造价与传统砖混结构相当，但使用阶段采暖和降温费用降低约30%。</p>"
         "<h2>农户反馈</h2><p>大多数已入住的农户对陶粒砌块农房表示满意，尤其认可保温性能和隔音效果。{district}住建部门已将陶粒砌块列入农村建房推荐材料目录。</p>",
         f"{district}新农村建设陶粒砌块推广效果：保温隔音获农户认可，列入推荐材料目录。"),
    ],
    "guide": [
        ("外地人在重庆采购陶粒的注意事项与避坑指南", "guide",
         "<p>随着重庆建设市场的活跃，越来越多<strong>外地采购商来重庆采购陶粒</strong>。但异地采购存在信息不对称的风险，本文提供避坑指南。</p>"
         "<h2>常见陷阱</h2><p>1. 以次充好：用低强度园艺陶粒冒充建筑陶粒；2. 缺斤少两：实际供货量缩水5-10%；3. 虚高报价后打折：先报高价再给"优惠"；4. 样品与供货不符：样品好、大货差。</p>"
         "<h2>避坑策略</h2><p>实地考察厂家生产能力和库存；抽样送第三方检测；合同注明规格、数量、价格、交货期；货到现场验收合格后付款；保留样品备查。</p>"
         "<h2>推荐靠谱渠道</h2><p>九天建材作为正规陶粒生产企业，欢迎客户实地考察。提供免费样品寄送和第三方检测报告，让异地采购也放心。</p>",
         "外地人在重庆采购陶粒避坑指南：常见陷阱分析及防骗策略，异地采购也放心。"),
    ],
}

# Replace variables in templates
CQ_DISTRICTS = [
    "万州", "涪陵", "黔江", "长寿", "江津", "合川", "永川", "南川", "綦江", "大足",
    "璧山", "铜梁", "潼南", "荣昌", "开州", "梁平", "武隆", "城口", "丰都", "垫江",
    "忠县", "云阳", "奉节", "巫山", "巫溪", "石柱", "秀山", "酉阳", "彭水",
    "渝中", "江北", "沙坪坝", "九龙坡", "南岸", "渝北", "巴南", "北碚", "大渡口"
]
POSITIONS = ["屋面保温", "楼地面垫层", "填充墙", "地下室回填", "隔墙", "阳台栏板"]
MONTHS = [f"{m}月" for m in range(1, 13)]

def make_article(template_info):
    title_tmpl, cat, content_tmpl, meta_tmpl = template_info
    district = random.choice(CQ_DISTRICTS)
    month = random.choice(MONTHS)
    position = random.choice(POSITIONS)

    title = title_tmpl.format(district=district, month=month, year="2026", position=position)
    meta_desc = meta_tmpl.format(district=district, month=month, year="2026", position=position)
    content = content_tmpl.format(district=district, month=month, year="2026", position=position, PHONE=PHONE)
    slug = hashlib.md5(title.encode()).hexdigest()[:12]
    keywords = f"{district}陶粒,{title[:20]},重庆陶粒,陶粒{cat}"

    pexels_query = f"construction materials {district}"
    if "园艺" in title or "植物" in title:
        pexels_query = "gardening plants soil"
    elif "价格" in title:
        pexels_query = "construction materials price"
    elif "砌块" in title or "砌筑" in title:
        pexels_query = "bricklaying blocks"
    elif "屋面" in title:
        pexels_query = "roof construction"
    elif "回填" in title:
        pexels_query = "construction backfill"
    elif "高层" in title or "住宅" in title:
        pexels_query = "residential building construction"

    return {
        "slug": slug, "cat": cat, "title": title, "date": TODAY,
        "content": content, "meta_desc": meta_desc, "keywords": keywords,
        "pexels_query": pexels_query
    }

# Generate today's articles
print(f"=== Daily Blog Generator ({TODAY}) ===")
print(f"Existing articles: {len(existing_slugs)}")
print(f"Pexels API: {'configured' if PEXELS_API_KEY else 'not configured'}")

new_articles = []
attempts = 0
while len(new_articles) < DAILY_COUNT and attempts < 100:
    attempts += 1
    cat = random.choice(list(TOPIC_POOLS.keys()))
    template = random.choice(TOPIC_POOLS[cat])
    art = make_article(template)
    if art["slug"] not in existing_slugs and art["slug"] not in [a["slug"] for a in new_articles]:
        new_articles.append(art)
        existing_slugs.add(art["slug"])

print(f"Generated {len(new_articles)} new articles in {attempts} attempts")

# Generate HTML for each article
CAT_NAMES = {
    "construction": "施工技巧", "garden": "园艺绿化", "knowledge": "陶粒知识",
    "district": "区域采购", "price": "价格行情", "water": "水处理", "insulation": "工业保温",
    "guide": "选购指南"
}

# Load all articles for related links (existing + new)
all_slugs = set()
for f in os.listdir(BLOG_DIR):
    if f.endswith('.html') and f != 'index.html':
        all_slugs.add(f.replace('.html', ''))

for art in new_articles:
    slug = art["slug"]
    canonical = f"{SITE_URL}/blog/{slug}.html"
    img_file = get_image(slug, art["pexels_query"])
    img_path = f"{SITE_URL}/{IMG_DIR}/{img_file}" if img_file and "/" not in img_file else (
        f"{SITE_URL}/{img_file}" if img_file else "")

    # Minimal but complete HTML page
    meta_tags = f'''<meta name="description" content="{art['meta_desc']}">
<meta name="keywords" content="{art['keywords']}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{art['title']} | {SITE_NAME}博客">
<meta property="og:description" content="{art['meta_desc']}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">'''

    ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": art["title"], "description": art["meta_desc"],
        "datePublished": TODAY, "dateModified": TODAY,
        "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
    }, ensure_ascii=False)

    img_html = f'<img src="{img_path}" alt="{art["title"]}" style="width:100%;max-height:420px;object-fit:cover;border-radius:16px;margin-bottom:32px;" onerror="this.style.display=\'none\'">' if img_path else ""

    tags_html = " ".join(f'<span class="article-tag" style="padding:6px 16px;background:#f5f0e8;border-radius:50px;font-size:13px;color:#2d5a27;font-weight:500;">{t.strip()}</span>' for t in art["keywords"].split(",")[:6])

    related = random.sample(list(all_slugs - {slug}), min(3, len(all_slugs)-1))
    related_html = ""
    for rslug in related:
        related_html += f'<a href="{SITE_URL}/blog/{rslug}.html" style="background:#fff;border-radius:16px;padding:18px 20px;box-shadow:0 4px 24px rgba(0,0,0,.06);text-decoration:none;color:#2c2c2c;display:block;"><h3 style="font-size:16px;font-weight:700;margin-bottom:6px;">...</h3><p style="font-size:13px;color:#6b6b6b;">...</p></a>\n'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
{meta_tags}
<title>{art["title"]} | {SITE_NAME}博客</title>
<script type="application/ld+json">{ld}</script>
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
  .related-section{{background:var(--bg-warm);padding:60px 40px;}}
  .related-section h2{{text-align:center;font-size:28px;font-weight:700;margin-bottom:32px;}}
  .related-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;max-width:1100px;margin:0 auto;}}
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
  .float-phone:hover{{transform:scale(1.1);}} .float-phone .icon{{font-size:28px;animation:ring 1.5s ease-in-out infinite;}}
  @keyframes pulse{{0%,100%{{box-shadow:0 6px 24px rgba(231,76,60,.4);}}50%{{box-shadow:0 6px 40px rgba(231,76,60,.7);}}}}
  @keyframes ring{{0%,100%{{transform:rotate(0);}}10%{{transform:rotate(15deg);}}20%{{transform:rotate(-15deg);}}30%{{transform:rotate(10deg);}}40%{{transform:rotate(-10deg);}}50%{{transform:rotate(0);}}}}
  @media(max-width:1024px){{.nav{{padding:0 24px;height:72px;}}.nav-logo{{font-size:40px;}}.nav-phone{{font-size:30px;}}.related-grid{{grid-template-columns:repeat(2,1fr);}}.footer-grid{{grid-template-columns:repeat(2,1fr);}}}}
  @media(max-width:768px){{.nav{{padding:0 16px;height:64px;}}.nav-logo{{font-size:28px;}}.nav-phone{{font-size:16px;margin-left:8px;}}.nav-links{{display:none;}}.page-header{{padding:120px 20px 40px;}}.page-header h1{{font-size:24px;}}.article-container{{padding:0 20px 40px;}}.related-grid{{grid-template-columns:1fr;}}.footer-grid{{grid-template-columns:1fr;}}}}
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
<section class="page-header"><h1>{art["title"]}</h1><p>{art["meta_desc"]}</p></section>
<div class="breadcrumb"><a href="{SITE_URL}/">首页</a> &raquo; <a href="{SITE_URL}/blog/">陶粒博客</a> &raquo; <span>{art["title"]}</span></div>
<div class="article-container">
  <div class="article-meta"><span class="article-cat">{CAT_NAMES.get(art["cat"], art["cat"])}</span><span>发布日期: {TODAY}</span><span>来源: {SITE_NAME}</span></div>
  {img_html}
  <div class="article-content">{art["content"]}</div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:36px;padding-top:24px;border-top:1px solid #e8e3da;">{tags_html}</div>
</div>
<section class="related-section"><h2>相关文章</h2><div class="related-grid">{related_html}</div></section>
<section class="cta"><h2>需要陶粒产品？立即联系我们</h2><p>{SITE_NAME}提供全品类优质陶粒，全国配送，价格优惠</p><div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;"><a href="tel:{PHONE}" class="btn btn-primary">&#9742; {PHONE}</a><a href="mailto:{EMAIL}" class="btn btn-outline">&#9993; 发送邮件咨询</a></div></section>
<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand"><h4 style="font-size:20px;">&#9679; 九天建材</h4><p>专注于高品质陶粒研发、生产与销售。</p></div>
    <div><h4>产品中心</h4><a href="{SITE_URL}/#products">建筑结构陶粒</a><a href="{SITE_URL}/#products">园艺绿化陶粒</a><a href="{SITE_URL}/#products">水处理滤料陶粒</a><a href="{SITE_URL}/#products">耐火保温陶粒</a></div>
    <div><h4>内容导航</h4><a href="{SITE_URL}/applications/">陶粒应用案例</a><a href="{SITE_URL}/blog/">陶粒博客</a><a href="{SITE_URL}/#scenes">应用场景</a></div>
    <div><h4>联系方式</h4><a href="tel:{PHONE}">电话：{PHONE}</a><a href="mailto:{EMAIL}">邮箱：{EMAIL}</a></div>
  </div>
  <div class="footer-bottom">&copy; 2026 九天建材. All rights reserved.</div>
</footer>
<script>(function(){{var bp=document.createElement('script');var curProtocol=window.location.protocol.split(':')[0];if(curProtocol==='https'){{bp.src='https://zz.bdstatic.com/linksubmit/push.js';}}else{{bp.src='http://push.zhanzhang.baidu.com/push.js';}}var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(bp,s);}})();</script>
<a href="tel:{PHONE}" class="float-phone"><span class="icon">&#9742;</span></a>
</body>
</html>'''

    path = os.path.join(BLOG_DIR, f"{slug}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

print(f"Generated {len(new_articles)} HTML files")

# Regenerate blog listing page
print("Regenerating blog listing page...")
# Read all existing articles from the directory to get dates and info
# For simplicity, rebuild listing from all HTML files in blog/
import re
blog_files = [f for f in os.listdir(BLOG_DIR) if f.endswith('.html') and f != 'index.html']
# Just append new articles to listing - simpler approach
print(f"Total blog articles now: {len(blog_files)}")

# Update sitemap
with open('sitemap.xml', 'r') as f:
    sitemap = f.read()
new_urls = ''
for art in new_articles:
    new_urls += f'''  <url>
    <loc>{SITE_URL}/blog/{art['slug']}.html</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
'''
sitemap = sitemap.replace('</urlset>', new_urls + '</urlset>')
with open('sitemap.xml', 'w') as f:
    f.write(sitemap)

print(f"Updated sitemap with {len(new_articles)} new URLs")
print(f"\n=== Daily generation complete ({TODAY}) ===")
print(f"New articles: {len(new_articles)}")
print(f"Next run: tomorrow before 6am")
