/**
 * Vercel serverless function: blog comment handler.
 * Receives comments and sends email via Gmail SMTP.
 * Purchase-intent comments get flagged in the subject line.
 */
const nodemailer = require('nodemailer');

const ADMIN_EMAIL = 'xxgxxg198733@gmail.com';
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

async function sendEmail(to, subject, body) {
  if (!SMTP_PASS) {
    console.log('[COMMENT] SMTP_PASS not set, email skipped');
    return false;
  }

  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: SMTP_USER,
      pass: SMTP_PASS,
    },
  });

  try {
    await transporter.sendMail({
      from: `"taoli001.cn 评论系统" <${SMTP_USER}>`,
      to: to,
      subject: subject,
      text: body,
    });
    console.log(`[COMMENT] Email sent: ${subject}`);
    return true;
  } catch (e) {
    console.error(`[COMMENT] Email failed: ${e.message}`);
    return false;
  }
}

module.exports = async function handler(req, res) {
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
类型: ${purchase ? '采购意向' : '普通评论'}
评论内容:
${text}
---
来源: taoli001.cn 博客评论系统
`;

    await sendEmail(
      ADMIN_EMAIL,
      `${subjectPrefix} ${name} - ${(article_title || slug).slice(0, 30)}`,
      body
    );

    return res.status(200).json({
      ok: true,
      msg: purchase ? '感谢您的采购意向！我们会尽快与您联系。' : '感谢您的评论！',
    });
  } catch (e) {
    console.error('[COMMENT] Error:', e);
    return res.status(200).json({ ok: false, msg: '提交失败，请稍后重试' });
  }
};
