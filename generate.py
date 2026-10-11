# -*- coding: utf-8 -*-
"""Generate the static cooperation Site from the latest local Markdown."""
from pathlib import Path
import html
import re
import json
import hashlib

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent.parent / '05-产品与交付/GEO产品代理合作方案_v1.0.md'
if not SOURCE.exists():
    SOURCE = ROOT / 'source-plan.md'
text = SOURCE.read_text()

def number(value):
    return int(value.replace(',', ''))

fee_row = re.search(r'^\| 代理费金额 \| 人民币([\d,]+)元 \| 人民币([\d,]+)元 \|$', text, re.M)
assert fee_row, '代理费表格格式需要核对'
config = {
    'deposit': number(re.search(r'金额为\*\*人民币([\d,]+)元', text).group(1)),
    'feeFirst': number(fee_row.group(1)),
    'feeSecond': number(fee_row.group(2)),
    'refundDays': int(re.search(r'终止结算后(\d+)个工作日内', text).group(1)),
}
for key, name in [('first', '一级合伙人直接成交'), ('second', '二级合伙人直接成交'), ('override', '一级获得二级成交提成'), ('feeReward', '一级获得二级代理费提成')]:
    row = next(line for line in text.splitlines() if line.startswith('| ' + name + ' |'))
    config[key] = int(re.search(r'\| (\d+)% \|', row).group(1))
period_row = next(line for line in text.splitlines() if line.startswith('| 合作期限 |'))
periods = [part.strip() for part in period_row.split('|')[2:4]]
config['periodFirst'], config['periodSecond'] = periods
reward = config['feeSecond'] * config['feeReward'] / 100
assert config['first'] < 100 and config['second'] + config['override'] < 100
assert f'一级合伙人{config["first"]}%，二级合伙人{config["second"]}%' in text, '分成正文与表格不一致'
assert f'二级直接成交的订单总佣金为{config["second"] + config["override"]}%' in text, '总佣金需校正'
assert f'代理费提成为{reward:,.0f}元' in text, '代理费奖励示例需校正'

def inline(s):
    s = html.escape(s)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

def markdown(s):
    lines = s.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('### '):
            out.append('<h3>' + inline(line[4:]) + '</h3>')
            i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            assert rows and all(len(r) == len(rows[0]) for r in rows), '表格列数不一致'
            heading = '<thead><tr>' + ''.join('<th scope="col">' + inline(c) + '</th>' for c in rows[0]) + '</tr></thead>'
            body = '<tbody>' + ''.join('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in r) + '</tr>' for r in rows[1:]) + '</tbody>'
            out.append('<div class="table-wrap"><table>' + heading + body + '</table></div>')
        elif re.match(r'^(- |\d+\. )', line):
            ordered = bool(re.match(r'^\d+\. ', line))
            pattern = r'^\d+\. ' if ordered else r'^- '
            items = []
            while i < len(lines) and re.match(pattern, lines[i].strip()):
                items.append('<li>' + inline(re.sub(pattern, '', lines[i].strip())) + '</li>')
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append('<' + tag + '>' + ''.join(items) + '</' + tag + '>')
        else:
            out.append('<p>' + inline(line) + '</p>')
            i += 1
    return '\n'.join(out)

sections = re.split(r'^## (.+)$', text, flags=re.M)
assert len(sections) == 19, '完整方案应包含9个章节'
full_terms = ''.join('<details><summary>' + html.escape(sections[i]) + '</summary><div class="terms-body">' + markdown(sections[i+1]) + '</div></details>' for i in range(1, len(sections), 2))
intro = '本方案用于合作洽谈，正式权利义务以签署的合作协议及附件为准。标注“建议”的规则供双方确认，标注“待定”的参数须在签约前补齐。'
c = config

# Compare the complete 100% revenue composition on a shared zero-based scale.
def composition_chart():
    colors = ['var(--brand-600)', 'var(--brand-300)', 'var(--ink-muted)']
    rows = [("一级直接成交", c['first'], 0), ("二级直接成交", c['override'], c['second'])]
    parts = [f'<figure class="comparison"><figcaption>产品订单回款分配结构</figcaption><p class="chart-meta">占可计提回款的比例（%） · 根据本方案分成表计算 · 不含代理费奖励</p><svg viewBox="0 0 1000 230" role="img" aria-label="一级直接成交：一级{c["first"]}%、我方{100-c["first"]}%；二级直接成交：一级{c["override"]}%、二级{c["second"]}%、我方{100-c["override"]-c["second"]}%" class="composition-svg">']
    for tick in [0,25,50,75,100]:
        x = 160 + tick * 8
        parts.append(f'<line x1="{x}" y1="25" x2="{x}" y2="160" class="chart-grid"/><text x="{x}" y="188" text-anchor="middle" class="axis-label">{tick}%</text>')
    for index, (name, first, second) in enumerate(rows):
        y = 48 + index * 67
        parts.append(f'<text x="0" y="{y+22}" class="row-label">{name}</text>')
        x = 160
        for j, value in enumerate([first,second,100-first-second]):
            if not value: continue
            width = value * 8
            parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="32" fill="{colors[j]}"/>')
            if value >= 10:
                labelcolor = 'var(--on-surface)' if j == 1 else 'var(--on-primary)'
                parts.append(f'<text x="{x+width/2}" y="{y+21}" text-anchor="middle" fill="{labelcolor}" class="value-label">{value}%</text>')
            else:
                parts.append(f'<text x="{x+width/2}" y="{y-7}" text-anchor="middle" fill="var(--on-surface)" class="value-label">{value}%</text>')
            x += width
    for j, name in enumerate(['一级合伙人收益','二级合伙人收益','我方扣除佣金后收入']):
        x = 160 + j * 235
        parts.append(f'<rect x="{x}" y="211" width="11" height="11" fill="{colors[j]}"/><text x="{x+18}" y="221" class="axis-label">{name}</text>')
    parts.append(f'</svg><p class="note">二级成交的佣金占比比一级直销高{c["second"]+c["override"]-c["first"]}个百分点。一级{c["override"]}%从同一笔回款计提，二级{c["second"]}%不被扣减；剩余{100-c["second"]-c["override"]}%由我方承担交付及其他成本。</p></figure>')
    return ''.join(parts)
commission_chart = composition_chart()

page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#fbfbfb"><title>GEO产品代理合作方案 · DeepFocus</title><meta name="description" content="了解DeepFocus品牌代理商、一级合伙人与二级合伙人合作模式，比较品牌授权、费用、销售分成及交付支持。"><link rel="icon" href="assets/mark.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css"><script defer src="app.js"></script></head>
<body><a href="#main" class="skip">跳至主要内容</a>
<header class="top"><div class="wrap top-inner"><a class="brand" href="#" aria-label="DeepFocus合作方案首页"><img class="brand-mark" src="assets/mark.svg" width="32" height="32" alt="">DeepFocus<small>合作方案</small></a><nav aria-label="主导航"><a href="#modes">合作模式</a><a href="#earnings">收益测算</a><a href="#support">合作支持</a><a href="#full-terms">完整方案</a></nav><span class="version">V1.1 / 2026.10.11</span></div></header>
<main id="main" class="wrap">
<section class="hero"><div><div class="eyebrow">GEO PARTNERSHIP PROGRAM</div><h1><span>GEO产品</span><br><span>代理合作方案。</span></h1><p class="hero-copy">品牌代理商可自建品牌、自主定价；个人合伙人使用我方品牌、执行统一售价。我方提供交付，两种模式均支持销售、技术与获客培训。</p><div class="actions"><a class="btn primary" href="#modes">比较合作模式 <span aria-hidden="true">↘</span></a><a class="btn" href="cooperation-plan.md" download>下载方案 <span aria-hidden="true">↓</span></a></div><div class="hero-meta"><span>讨论稿 · 2026年10月11日</span><span>两种模式 / 三级合作身份</span></div></div>
<aside class="hero-board" aria-label="合作费用概览"><div class="board-title"><span>合作门槛一览</span><span>COOPERATION / 01</span></div><div class="board-row"><div><h3>品牌代理商</h3><p>适合团队与规模化销售主体</p></div><div class="board-num">¥ {c['deposit']:,}<small>可退代理保证金</small></div></div><div class="board-row"><div><h3>品牌一级合伙人</h3><p>独立销售 · 可发展二级合伙人</p></div><div class="board-num">¥ {c['feeFirst']:,}<small>代理费 / 合作期限{c['periodFirst']}</small></div></div><div class="board-row"><div><h3>品牌二级合伙人</h3><p>独立销售 · 专注获客与成交</p></div><div class="board-num">¥ {c['feeSecond']:,}<small>代理费 / 合作期限{c['periodSecond']}</small></div></div><p class="board-note">保证金与代理费分别核算；代理费不套用保证金退款规则。</p></aside></section>
<div class="ribbon"><span><i></i>销售培训</span><span><i></i>技术支持</span><span><i></i>获客培训</span><span>我方提供约定的GEO产品交付</span></div>
<section id="modes" class="section"><div class="section-head"><div><div class="sec-num">01 / COOPERATION MODELS</div><h2>按销售能力与经营权限选择模式。</h2></div><p>品牌代理商自主经营与定价；品牌合伙人使用我方品牌及统一售价，与我方协作完成销售。</p></div>
<div class="modes"><article class="mode"><div class="tag">模式一 / 团队主体</div><h3>品牌代理商</h3><p class="desc">具备团队或规模化销售能力，自主承担客户售前与经营。</p><div class="fee"><span>¥</span>{c['deposit']:,}</div><p class="fee-label">代理保证金 · 合作终止后可退款</p><dl><div><dt>品牌</dt><dd>自建品牌 / 授权使用我方品牌</dd></div><div><dt>定价</dt><dd>自主定价</dd></div><div><dt>采购</dt><dd>独家授权采购价</dd></div><div><dt>售前</dt><dd>代理商独立负责</dd></div><div><dt>交付</dt><dd>我方负责约定模块</dd></div><div><dt>收益</dt><dd>销售与采购价差</dd></div></dl><p class="mode-end">建议终止结算后{c['refundDays']}个工作日退款，<br>无应扣款项时全额退还。</p></article>
<article class="mode featured"><div class="tag">模式二 / 个人销售</div><h3>品牌一级合伙人</h3><p class="desc">独立获客与销售，可发展二级合伙人，并获得约定奖励。</p><div class="fee"><span>¥</span>{c['feeFirst']:,}</div><p class="fee-label">代理费 · 合作期限{c['periodFirst']}</p><dl><div><dt>品牌</dt><dd>仅使用我方品牌</dd></div><div><dt>定价</dt><dd>执行我方统一售价</dd></div><div><dt>直销分成</dt><dd>{c['first']}%</dd></div><div><dt>二级成交提成</dt><dd>订单可计提回款的{c['override']}%</dd></div><div><dt>二级代理费提成</dt><dd>净实收代理费的{c['feeReward']}%</dd></div><div><dt>售前 / 交付</dt><dd>我方介入售前并负责交付</dd></div></dl><p class="mode-end">二级准入由我方确认。<br>代理费退款及续约规则由协议明确。</p></article>
<article class="mode"><div class="tag">模式二 / 个人销售</div><h3>品牌二级合伙人</h3><p class="desc">专注客户拓展与成交推进，使用统一品牌、资料及销售支持。</p><div class="fee"><span>¥</span>{c['feeSecond']:,}</div><p class="fee-label">代理费 · 合作期限{c['periodSecond']}</p><dl><div><dt>品牌</dt><dd>仅使用我方品牌</dd></div><div><dt>定价</dt><dd>执行我方统一售价</dd></div><div><dt>直销分成</dt><dd>{c['second']}%</dd></div><div><dt>售前</dt><dd>我方介入</dd></div><div><dt>交付</dt><dd>我方负责</dd></div><div><dt>下级发展</dt><dd>不设置发展下级权限</dd></div></dl><p class="mode-end">仅设置一级与二级合伙关系，<br>不设置更深层级的发展提成。</p></article></div><p class="note">独家授权价为约定的专属采购价；区域、行业及客户范围的独家经营权需另行书面约定。</p></section>
<section id="earnings" class="section"><div class="section-head"><div><div class="sec-num">02 / REVENUE CALCULATOR</div><h2>一级直销佣金{c['first']}%，二级成交佣金{c['second']+c['override']}%。</h2></div><p>一级直接成交总佣金{c['first']}%；二级直接成交总佣金{c['second']+c['override']}%，分别由二级获得{c['second']}%、所属一级获得{c['override']}%。</p></div>{commission_chart}<div class="calc"><form id="calculator"><div class="field"><label for="amount">订单可计提回款（元）</label><div class="input-box"><span aria-hidden="true">¥</span><input id="amount" name="amount" type="number" min="0" max="1000000000" step="0.01" value="100000" inputmode="decimal" aria-describedby="calc-help calc-error"></div></div><div class="field"><label for="scenario">成交方式</label><select id="scenario" name="scenario"><option value="first">一级直接成交</option><option value="second" selected>二级直接成交</option></select></div><p id="calc-error" class="error" role="alert"></p><p id="calc-help" class="calc-note">按含税实际到账服务款，扣除已退款金额后测算。分期款分别计提；未到账款不计佣。</p></form><div aria-live="polite" aria-atomic="true"><h3>该订单合伙人总佣金</h3><p id="total-commission" class="total"></p><p id="commission-label" class="total-label"></p><div class="bar" aria-hidden="true"><span id="bar-l1" class="bar-l1"></span><span id="bar-l2" class="bar-l2"></span><span id="bar-company" class="bar-company"></span></div><div class="breakdown"><div><small><i class="dot bar-l1"></i><span id="l1-rate"></span></small><strong id="l1-income"></strong></div><div><small><i class="dot bar-l2"></i><span id="l2-rate"></span></small><strong id="l2-income"></strong></div><div><small><i class="dot bar-company"></i><span id="company-rate"></span></small><strong id="company-income"></strong></div></div><div class="secondary-reward"><div>一级发展二级的代理费奖励<br><span class="calc-note">¥ {c['feeSecond']:,} × {c['feeReward']}% · 与产品成交分成分别核算</span></div><strong>¥ {reward:,.0f}</strong></div></div></div><p class="note">我方扣除佣金后收入还需承担交付、渠道、运营和税费等成本，不等于利润。二级代理费退款时，发展奖励按原比例冲减。</p></section>
<section id="support" class="section"><div class="section-head"><div><div class="sec-num">03 / PARTNER ENABLEMENT</div><h2>销售、技术与获客支持覆盖两种模式。</h2></div><p>两种模式均获得销售培训、技术支持和获客培训。具体频次、响应时间及定制辅导范围在附件中明确。</p></div><div class="supports"><article class="support"><b>01 / SALES</b><h3>销售培训</h3><p>产品知识、客户需求识别、方案讲解、异议处理、报价及成交方法。</p><p class="format">入驻培训 · 定期复训 · 案例讨论</p></article><article class="support"><b>02 / TECHNOLOGY</b><h3>技术支持</h3><p>产品能力、服务边界、系统使用与交付问题答疑，设置问题对接与跟进机制。</p><p class="format">指定窗口 · 技术答疑 · 问题跟进</p></article><article class="support"><b>03 / ACQUISITION</b><h3>获客培训</h3><p>目标客户画像、渠道拓展、内容获客、线索筛选和销售跟进。</p><p class="format">主题培训 · 方法资料 · 实践辅导</p></article></div><p class="note">另提供统一销售资料及项目协作流程。获客培训属于方法指导，不承诺分配线索或保证成交数量。</p></section>
<section id="workflow" class="section"><div class="section-head"><div><div class="sec-num">04 / WORKING TOGETHER</div><h2>合作分工，贯穿每个节点。</h2></div></div><div class="flows"><article class="flow"><h3>品牌代理商 / 自主经营</h3><ol><li>完成审核、签约、保证金缴纳与培训</li><li>自主获客、售前、定价及客户签约</li><li>提交采购订单，完成付款及资料交接</li><li>我方确认范围、排期并执行交付模块</li><li>代理商组织客户验收与持续维护</li></ol><p class="responsibility">代理商负责客户售前；我方负责约定交付。面向代理商的培训和技术答疑属于合作支持。</p></article><article class="flow"><h3>品牌合伙人 / 协作销售</h3><ol><li>完成审核、签约、代理费缴纳与培训</li><li>合伙人获客、报备并推进销售沟通</li><li>我方介入售前，确认正式方案及报价</li><li>按约定签约、收款，由我方启动交付</li><li>按实际回款对账分佣，配合客户维护</li></ol><p class="responsibility">合伙人负责线索与成交推进；我方介入售前并负责交付。客户归属与分佣在成交前确认。</p></article></div></section>
<section id="full-terms" class="section"><div class="section-head"><div><div class="sec-num">05 / COMPLETE PLAN</div><h2>完整合作方案。</h2></div><div class="terms-header"><button type="button" class="text-btn" id="expand-all">全部展开 ＋</button><button type="button" class="text-btn" id="collapse-all">全部收起 −</button></div></div><p class="note" style="margin:0 0 26px">{intro}</p>{full_terms}</section>
<div class="closing"><div><h3>签约前，确认剩余商务条款。</h3><p>签约前还需确认采购价、佣金结算日、客户保护期、代理费退款与续约规则等事项，详见完整方案第九章。</p></div><a class="btn primary" href="cooperation-plan.md" download>下载完整方案 <span aria-hidden="true">↓</span></a></div>
<footer><span>DeepFocus / GEO产品代理合作方案</span><span>讨论稿 V1.1 · 2026.10.11 · 以双方签署协议为准</span></footer></main><script type="application/json" id="terms-data">{json.dumps(config, ensure_ascii=False)}</script></body></html>'''
page = page.replace('两种模式 / 三级合作身份', '两种模式 / 三类合作身份')
(ROOT/'dist/index.html').write_text(page)
(ROOT/'dist/cooperation-plan.md').write_text(text)
(ROOT/'source-plan.md').write_text(text)
(ROOT/'terms.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n')
(ROOT/'source.sha256').write_text(hashlib.sha256(text.encode()).hexdigest()+'\n')
print('已生成网页与完整方案，关键参数：'+json.dumps(config, ensure_ascii=False))
