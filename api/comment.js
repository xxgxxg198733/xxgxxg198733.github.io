/**
 * Vercel serverless function: blog comment handler.
 * Receives comments and sends email notifications.
 * Purchase-intent comments get flagged in the subject line.
 */
const https = require('https');
const http = require('http');

const ADMIN_EMAIL = 'xxgxxg198733@gmail.com';
const SMTP_HOST = process.env.SMTP_HOST || 'smtp.gmail.com';
const SMTP_PORT = parseInt(process.env.SMTP_PORT || '587');
const SMTP_USER = process.env.SMTP_USER || ADMIN_EMAIL;
const SMTP_PASS = process.env.SMTP_PASS || '';

const PURCHASE_KEYWORDS = [
  '采购', '购买', '报价', '价格', '多少钱', '批发', '大量',
  '询价', '进货', '订货', '需要', '供货', '样品', '合作',
  '工程', '项目', '施工方', '工地', '装修', '建房',
];

function isPurchaseIntent(text) {
  return PURCHASE_KEYWORDS.some(kw => text.includes(kw));
}

function sendWithMailgun(to, subject, body) {
  // Simple HTTP-based email via a free relay or directly using SMTP-like approach
  // Using Gmail SMTP requires OAuth or app password, use a simpler relay approach
  return new Promise((resolve, reject) => {
    if (!SMTP_PASS) {
      console.log('[COMMENT] SMTP not configured, email skipped');
      return resolve(false);
    }

    // Encode email content
    const payload = JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: SMTP_USER, name: 'taoli001.cn 评论系统' },
      subject: subject,
      content: [{ type: 'text/plain', value: body }]
    });

    const req = https.request({
      hostname: 'api.sendgrid.com',
      path: '/v3/mail/send',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SMTP_PASS}`,
        'Content-Type': 'application/json',
      }
    }, (res) => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        console.log('[COMMENT] Email sent via SendGrid');
        resolve(true);
      } else {
        console.log(`[COMMENT] Email failed: ${res.statusCode}`);
        resolve(false);
      }
    });
    req.on('error', (e) => { console.log(`[COMMENT] Email err: ${e.message}`); resolve(false); });
    req.write(payload);
    req.end();
  });
}

module.exports = async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, msg: 'Method not allowed' });
  }

  try {
    const { slug, name, email, text, article_title } = req.body || {};

    if (!slug || !name || !text) {
      return res.status(200).json({ ok: false, msg: '请填写昵称和评论内容' });
    }
    if (name.length > 50) {
      return res.status(200).json({ ok: false, msg: '昵称过长' });
    }
    if (text.length > 2000) {
      return res.status(200).json({ ok: false, msg: '评论内容过长' });
    }
    if (/https?:\/\/|<[^>]+>|\[url/.test(text)) {
      return res.status(200).json({ ok: false, msg: '评论内容包含非法字符' });
    }

    const purchase = isPurchaseIntent(text);
    const subjectPrefix = purchase ? '[采购意向]' : '[博客评论]';
    const articleUrl = `https://www.taoli001.cn/blog/${slug}.html`;

    const body = `博客新评论:

文章: ${article_title || slug}
链接: ${articleUrl}
评论者: ${name}
邮箱: ${email || '未填写'}
类型: ${purchase ? '采购意向 ⚠️' : '普通评论'}
评论内容:
${text}
---
来源: taoli001.cn 博客评论系统
`;

    const sent = await sendWithMailgun(ADMIN_EMAIL, `${subjectPrefix} ${name} - ${(article_title || slug).slice(0, 30)}`, body);

    return res.status(200).json({
      ok: true,
      msg: purchase ? '感谢您的采购意向！我们会尽快与您联系。' : '感谢您的评论！我们会尽快回复。',
    });
  } catch (e) {
    console.error('[COMMENT] Error:', e);
    return res.status(200).json({ ok: false, msg: '提交失败，请稍后重试' });
  }
};
