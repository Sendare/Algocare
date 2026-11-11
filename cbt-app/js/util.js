
let calcExpr = '';
function toggleCalculator() { document.getElementById('calcModal').classList.toggle('open'); }
function calcInput(val) {
  const display = document.getElementById('calcDisplay');
  if (val === 'C') { calcExpr = ''; }
  else if (val === '=') { try { calcExpr = String(eval(calcExpr || '0')); } catch { calcExpr = 'Error'; } }
  else { if (calcExpr === 'Error') calcExpr = ''; calcExpr += val; }
  display.textContent = calcExpr || '0';
}
