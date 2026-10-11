(() => {
  'use strict';
  const terms = JSON.parse(document.getElementById('terms-data').textContent);
  const form = document.getElementById('calculator');
  const amountField = document.getElementById('amount');
  const scenarioField = document.getElementById('scenario');
  const money = value => new Intl.NumberFormat('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}).format(value);
  const set = (id, value) => document.getElementById(id).textContent = value;
  function update() {
    const amount = Number(amountField.value);
    const valid = amountField.value.trim() !== '' && Number.isFinite(amount) && amount >= 0 && amount <= 1000000000 && amountField.validity.valid;
    set('calc-error', valid ? '' : '请输入0至1,000,000,000元的有效金额，最多两位小数。');
    if (!valid) {
      ['total-commission','l1-income','l2-income','company-income'].forEach(id => set(id, '—'));
      set('commission-label', '输入有效金额后显示测算结果');
      return;
    }
    const second = scenarioField.value === 'second';
    const l1rate = second ? terms.override : terms.first;
    const l2rate = second ? terms.second : 0;
    const l1 = Math.round(amount * l1rate) / 100;
    const l2 = Math.round(amount * l2rate) / 100;
    const commission = Math.round((l1 + l2) * 100) / 100;
    const company = Math.round((amount - commission) * 100) / 100;
    set('total-commission', '¥ ' + money(commission));
    set('commission-label', '订单总佣金 ' + (l1rate + l2rate) + '% · 按实际回款计提');
    set('l1-income', '¥ ' + money(l1));
    set('l2-income', '¥ ' + money(l2));
    set('company-income', '¥ ' + money(company));
    set('l1-rate', '一级收益 · ' + l1rate + '%');
    set('l2-rate', '二级收益 · ' + l2rate + '%');
    set('company-rate', '我方收入 · ' + (100 - l1rate - l2rate) + '%');
    document.getElementById('bar-l1').style.width = l1rate + '%';
    document.getElementById('bar-l2').style.width = l2rate + '%';
    document.getElementById('bar-company').style.width = (100 - l1rate - l2rate) + '%';
  }
  form.addEventListener('submit', event => event.preventDefault());
  amountField.addEventListener('input', update);
  scenarioField.addEventListener('change', update);
  update();
  const sections = [...document.querySelectorAll('#full-terms details')];
  document.getElementById('expand-all').addEventListener('click', () => sections.forEach(section => section.open = true));
  document.getElementById('collapse-all').addEventListener('click', () => sections.forEach(section => section.open = false));
  let beforePrint = [];
  window.addEventListener('beforeprint', () => {beforePrint = sections.map(section => section.open); sections.forEach(section => section.open = true);});
  window.addEventListener('afterprint', () => sections.forEach((section, i) => section.open = beforePrint[i]));
})();
