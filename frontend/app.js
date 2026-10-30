const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];

const state = {
  userName: localStorage.getItem('aquamind_user_name') || '',
  theme: localStorage.getItem('aquamind_theme') || 'light',
  plantId: localStorage.getItem('aquamind_plant_id') || 'RO-TRAIN-01',
  dataset: localStorage.getItem('aquamind_dataset') || '',
  datasets: [],
  datasetSummary: null,
  lastResult: null,
  periodDays: Number(localStorage.getItem('aquamind_period_days') || '7'),
  currentTaskId: null,
  lastRelatedCases: [],
  lastSources: [],
};

document.documentElement.dataset.theme = state.theme;

function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'OP';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
function esc(v) {
  return String(v ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}
function fmt(v, d = 1) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
  const n = Number(v);
  return Math.abs(n) >= 1000 ? n.toLocaleString(undefined, {maximumFractionDigits: 0}) : n.toFixed(d);
}
function toast(msg) {
  const t = $('#toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => t.classList.remove('show'), 2600);
}
function setUser(name) {
  state.userName = String(name || '').trim() || 'Operator';
  localStorage.setItem('aquamind_user_name', state.userName);
  $('#userName').textContent = state.userName;
  $('#avatar').textContent = initials(state.userName);
  $('#chatUserAvatar').textContent = initials(state.userName);
  $('#settingsName').value = state.userName;
}
function openApp() {
  setUser(state.userName);
  $('#nameGate').classList.add('hidden');
  $('#app').classList.remove('hidden');
  requestAnimationFrame(() => state.datasetSummary && renderChart(state.datasetSummary));
}

async function api(url, opts = {}) {
  const request = {...opts};
  const headers = {...(opts.headers || {})};
  if (!(opts.body instanceof FormData) && opts.body !== undefined) headers['Content-Type'] = 'application/json';
  request.headers = headers;
  const res = await fetch(url, request);
  let body = {};
  try { body = await res.json(); } catch { /* no-op */ }
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
  return body;
}

function sparkSVG(values, bad = true) {
  const vals = (values || []).map(Number).filter(Number.isFinite);
  if (vals.length < 2) return '<svg class="spark" viewBox="0 0 110 38"><line x1="5" y1="29" x2="106" y2="29" stroke="#b6c5d6" stroke-dasharray="3 3"/></svg>';
  const lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
  const pts = vals.map((v, i) => `${5 + i * (100 / (vals.length - 1))},${32 - (v - lo) / span * 25}`).join(' ');
  const color = bad ? '#ff3b3b' : '#0fb981';
  return `<svg class="spark" viewBox="0 0 110 38"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

const metricMeta = {
  feed_pressure: {icon:'◴', badUp:true, decimals:1},
  differential_pressure: {icon:'↔', badUp:true, decimals:1},
  permeate_flow: {icon:'●', badUp:false, decimals:0},
  recovery: {icon:'↻', badUp:false, decimals:1},
  salt_rejection: {icon:'⬟', badUp:false, decimals:1},
  sec: {icon:'ϟ', badUp:true, decimals:1},
};

function renderKPIs(summary) {
  const grid = $('#kpiGrid');
  grid.innerHTML = '';
  Object.entries(summary.metrics || {}).forEach(([key, m]) => {
    const meta = metricMeta[key] || {icon:'•', badUp:true, decimals:1};
    const delta = m.delta_pct;
    const bad = delta === null ? null : (meta.badUp ? delta > 0 : delta < 0);
    const arrow = delta === null ? '' : delta >= 0 ? '↑' : '↓';
    const cls = delta === null ? 'neutral' : bad ? 'bad' : 'good';
    const div = document.createElement('div');
    div.className = 'kpi-card';
    div.tabIndex = 0;
    div.title = `${m.label}: ${fmt(m.value, meta.decimals)} ${m.unit}`;
    div.innerHTML = `<div class="kpi-icon">${meta.icon}</div><div><div class="kpi-label">${esc(m.label)}</div><div class="kpi-value">${fmt(m.value, meta.decimals)} <small>${esc(m.unit)}</small></div><div class="delta ${cls}">${delta === null ? '—' : `${arrow} ${Math.abs(delta).toFixed(1)}%`}</div></div><div>${sparkSVG(m.spark, bad !== false)}</div>`;
    grid.appendChild(div);
  });
  const fp = summary.metrics?.feed_pressure?.value;
  $('#pumpPressure').textContent = `${fmt(fp, 1)} bar`;
  const pf = summary.metrics?.permeate_flow?.value;
  $('#permeateFlow').textContent = `${fmt(pf, 0)} m³/h`;
}

function chartColors() {
  const dark = document.documentElement.dataset.theme === 'dark';
  return {
    text: dark ? '#8ca3bb' : '#6d83a2',
    grid: dark ? '#1c3448' : '#d9e4ef',
    blue: '#1688f3',
    baseline: '#6c89ae',
    surface: dark ? '#0d1d2a' : '#ffffff',
  };
}

function renderChart(summary) {
  const canvas = $('#trendChart');
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const width = Math.max(300, Math.floor(rect.width));
  const height = Math.max(140, Math.floor(rect.height));
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const trend = summary?.trend || {};
  const allValues = (trend.values || []).map(Number).filter(Number.isFinite);
  const allLabels = trend.labels || [];
  if (allValues.length < 2) return;
  const approxPerDay = Math.max(1, Math.ceil(allValues.length / 30));
  const keep = Math.min(allValues.length, Math.max(14, state.periodDays * approxPerDay));
  const values = allValues.slice(-keep);
  const labels = allLabels.slice(-keep);
  const baseline = Number.isFinite(Number(trend.baseline)) ? Number(trend.baseline) : values.reduce((a,b) => a+b, 0) / values.length;
  const valsForScale = [...values, baseline];
  let min = Math.min(...valsForScale), max = Math.max(...valsForScale);
  const span = max - min || Math.abs(max) * 0.1 || 1;
  min -= span * 0.12;
  max += span * 0.12;

  const colors = chartColors();
  const pad = {left:48, right:12, top:14, bottom:28};
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const x = i => pad.left + (i / Math.max(1, values.length - 1)) * plotW;
  const y = v => pad.top + (1 - (v - min) / (max - min)) * plotH;

  ctx.fillStyle = colors.surface;
  ctx.fillRect(0, 0, width, height);
  ctx.font = '9px Segoe UI, Arial';
  ctx.textBaseline = 'middle';
  for (let i = 0; i <= 4; i++) {
    const yy = pad.top + i * plotH / 4;
    const val = max - i * (max - min) / 4;
    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke();
    ctx.fillStyle = colors.text;
    ctx.textAlign = 'right';
    ctx.fillText(fmt(val, Math.abs(val) >= 100 ? 0 : 1), pad.left - 7, yy);
  }
  const ticks = Math.min(7, values.length);
  for (let i = 0; i < ticks; i++) {
    const idx = Math.round(i * (values.length - 1) / Math.max(1, ticks - 1));
    const xx = x(idx);
    ctx.strokeStyle = colors.grid;
    ctx.beginPath(); ctx.moveTo(xx, pad.top); ctx.lineTo(xx, pad.top + plotH); ctx.stroke();
    ctx.fillStyle = colors.text;
    ctx.textAlign = 'center';
    ctx.fillText(labels[idx] || String(idx + 1), xx, height - 10);
  }

  ctx.strokeStyle = colors.baseline;
  ctx.setLineDash([6, 5]);
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(x(0), y(baseline)); ctx.lineTo(x(values.length - 1), y(baseline)); ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = colors.blue;
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.beginPath();
  values.forEach((v, i) => i === 0 ? ctx.moveTo(x(i), y(v)) : ctx.lineTo(x(i), y(v)));
  ctx.stroke();
  ctx.fillStyle = colors.blue;
  values.forEach((v, i) => { ctx.beginPath(); ctx.arc(x(i), y(v), 2.2, 0, Math.PI * 2); ctx.fill(); });
}

function renderDataset(summary) {
  state.datasetSummary = summary;
  renderKPIs(summary);
  renderChart(summary);
  renderOverview();
}

async function loadDataset(name) {
  state.dataset = name;
  localStorage.setItem('aquamind_dataset', name);
  try {
    const s = await api(`/api/dataset/${encodeURIComponent(name)}`);
    renderDataset(s);
    toast(`Loaded ${name}`);
  } catch (e) { toast(e.message); }
}

function addChat(role, text) {
  const area = $('#chatArea');
  const row = document.createElement('div');
  row.className = `chat-row ${role === 'user' ? 'user-row' : 'agent-row'}`;
  const av = role === 'user' ? `<div class="chat-avatar user-avatar">${initials(state.userName)}</div>` : `<div class="chat-avatar agent-avatar"><div class="mini-wave"><i></i><i></i><i></i></div></div>`;
  const now = new Date().toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
  row.innerHTML = `${av}<div class="bubble-wrap"><div class="chat-bubble ${role === 'user' ? 'user-bubble' : 'agent-bubble'}">${esc(text)}</div><span class="timestamp">${now}</span></div>`;
  area.appendChild(row);
  area.scrollTop = area.scrollHeight;
}


function renderSuggestions(items = []) {
  const host = $('#suggestionChips');
  if (!host) return;
  host.innerHTML = '';
  (items || []).slice(0, 3).forEach(text => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'suggestion-chip';
    b.textContent = text;
    b.onclick = () => askAgent(text);
    host.appendChild(b);
  });
}

function showWorkingActivity() {
  const steps = [
    ['Understand the request','Classifying the request and selecting the safest workflow'],
    ['Gather evidence','Checking plant context, operational data and grounded knowledge'],
    ['Use approved tools','Running only the tools required for this request'],
    ['Synthesize findings','Combining evidence into an audit-safe conclusion'],
    ['Propose next step','Preparing verification-oriented follow-up actions'],
  ];
  $('#activityStatus').textContent = 'Agent working…';
  $('#activityTimeline').innerHTML = steps.map(([a,b],i) => `<div class="timeline-step ${i===0?'working':''}"><span class="step-dot"></span><div><strong>${a}</strong><small>${b}</small></div><time></time></div>`).join('');
}

function exportCurrentInvestigation() {
  if (!state.lastResult) { toast('Run an investigation first'); return; }
  const payload = JSON.stringify(state.lastResult, null, 2);
  const blob = new Blob([payload], {type:'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `AquaMind-${state.lastResult.task_id || 'investigation'}.json`;
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  toast('Investigation exported');
}

function showRelatedCases() {
  const cases = state.lastRelatedCases || [];
  if (!cases.length) { toast('No related cases are available yet'); return; }
  openModal('Related Cases', `<div class="case-library">${cases.map(c => `<div class="case-row"><div><strong>${esc(c.title || c.case_id || 'Case')}</strong><small>${esc(c.category || c.domain || '')}</small></div><span>${esc(c.expected_label || '')}</span></div>`).join('')}</div>`);
}

function resetInvestigation() {
  state.lastResult = null;
  state.currentTaskId = null;
  state.lastRelatedCases = [];
  state.lastSources = [];
  renderSuggestions([]);
  const area = $('#chatArea');
  area.innerHTML = '';
  addChat('agent', `Hello ${state.userName}. Select plant data and describe the operating issue you want me to investigate.`);
  $('#activityStatus').textContent = 'Ready ○';
  $('#activityTimeline').innerHTML = [
    ['Understand the issue','Waiting for an operator request'],
    ['Gather and analyze data','Plant data will be validated and compared with baseline'],
    ['Evaluate possible causes','Evidence will be matched against source-grounded patterns'],
    ['Synthesize findings','A defensible hypothesis will be assembled'],
    ['Recommend actions','Verification-oriented next steps will be prepared'],
  ].map(([a,b]) => `<div class="timeline-step"><span class="step-dot"></span><div><strong>${a}</strong><small>${b}</small></div><time></time></div>`).join('');
  $('#hypothesisTitle').textContent = 'Awaiting investigation';
  $('#hypothesisCopy').textContent = 'Run an investigation to generate a source-grounded diagnostic hypothesis.';
  $('#evidenceList').innerHTML = '<li>Supporting evidence will appear after the investigation.</li>';
  $('#recommendationsList').innerHTML = '<li>Verification recommendations will appear after the investigation.</li>';
  $('#investigationInput').value = '';
  showView('investigations');
  $('#investigationInput').focus();
}

function renderActivity(result) {
  const timeline = $('#activityTimeline');
  const serverActivity = Array.isArray(result.activity) ? result.activity : [];
  const defaultSteps = [
    ['Understand the issue','Parsed the operator request and identified relevant operating context'],
    ['Gather and analyze data','Validated operational data and evaluated current RO performance'],
    ['Evaluate possible causes','Compared observed evidence with source-grounded troubleshooting patterns'],
    ['Synthesize findings','Synthesized the most defensible supported hypothesis'],
    ['Recommend actions','Prepared verification-oriented next steps'],
  ];
  const rows = defaultSteps.map((fallback, i) => {
    const a = serverActivity[i];
    if (a && typeof a === 'object') return [a.title || a.action || fallback[0], a.summary || a.detail || fallback[1]];
    if (typeof a === 'string') return [fallback[0], a];
    return fallback;
  });
  const now = new Date().toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
  timeline.innerHTML = rows.map(([s, sub], i) => `<div class="timeline-step done"><span class="step-dot"></span><div><strong>${esc(s)}</strong><small>${esc(sub)}</small></div><time>${i < 3 ? now : ''}</time></div>`).join('');
  $('#activityStatus').textContent = 'Complete ✓';
}

function evidenceText(item) {
  if (typeof item === 'string') return item;
  if (!item || typeof item !== 'object') return String(item ?? '');
  return item.description || item.statement || item.metric || item.reason || item.evidence || JSON.stringify(item);
}

function renderResult(result) {
  state.lastResult = result;
  state.currentTaskId = result.task_id || state.currentTaskId;
  state.lastRelatedCases = result.related_cases || state.lastRelatedCases || [];
  renderDataset(result.dataset);
  renderActivity(result);
  const d = result.diagnosis || {};
  $('#hypothesisTitle').textContent = d.id && d.id !== 'Awaiting investigation' ? String(d.id).replaceAll('_', ' ') : 'No actionable diagnosis';
  $('#hypothesisCopy').textContent = d.conclusion || result.final_answer || 'Investigation completed.';
  const ev = $('#evidenceList');
  ev.innerHTML = '';
  const evidence = d.evidence || [];
  if (evidence.length) {
    evidence.slice(0, 5).forEach((x, i) => {
      const li = document.createElement('li');
      li.innerHTML = `${esc(evidenceText(x))}${d.source_ids?.[i] ? ` <span class="source-tag">${esc(d.source_ids[i])}</span>` : ''}`;
      ev.appendChild(li);
    });
  } else ev.innerHTML = '<li>No additional structured evidence was returned.</li>';
  const rec = $('#recommendationsList');
  rec.innerHTML = '';
  const rs = d.verification_steps || [];
  if (rs.length) rs.slice(0, 5).forEach(x => { const li = document.createElement('li'); li.textContent = typeof x === 'string' ? x : JSON.stringify(x); rec.appendChild(li); });
  else rec.innerHTML = '<li>No additional verification steps were returned.</li>';
  addChat('agent', result.final_answer || 'Investigation completed.');
}

async function askAgent(text) {
  const message = String(text || '').trim();
  if (!message) return;
  addChat('user', message);
  showWorkingActivity();
  renderSuggestions([]);
  $('#sendInvestigation').disabled = true;
  try {
    const response = await api('/api/agent', {
      method:'POST',
      body:JSON.stringify({
        message,
        dataset:state.dataset || null,
        plant_id:state.plantId,
        user_name:state.userName,
        task_id:state.currentTaskId,
      })
    });

    const route = response.route || 'investigation';
    if (route === 'investigation') {
      state.currentTaskId = response.task_id || null;
      state.lastRelatedCases = response.related_cases || [];
      renderResult(response);
      if (response.data_quality_notice) {
        addChat('agent', `Data-quality note: ${response.data_quality_notice}`);
      }
      if (Array.isArray(response.proactive_insights) && response.proactive_insights.length) {
        addChat('agent', `I also noticed: ${response.proactive_insights.join(' ')}`);
      }
      toast('Investigation complete');
    } else if (route === 'knowledge' || route === 'followup') {
      state.lastSources = response.sources || [];
      addChat('agent', response.answer || 'Answer ready.');
      $('#activityStatus').textContent = route === 'knowledge' ? 'Knowledge answer ✓' : 'Follow-up complete ✓';
      $('#activityTimeline').innerHTML = `<div class="timeline-step done"><span class="step-dot"></span><div><strong>${route === 'knowledge' ? 'Search grounded knowledge' : 'Use investigation context'}</strong><small>${route === 'knowledge' ? 'Answered without running an unnecessary plant-data workflow' : 'Reused the current investigation, evidence and sources'}</small></div><time></time></div>`;
      if (response.related_cases) state.lastRelatedCases = response.related_cases;
    } else if (route === 'clarify') {
      addChat('agent', response.answer || 'Tell me what you would like to do.');
      $('#activityStatus').textContent = 'Clarification needed';
      $('#activityTimeline').innerHTML = `<div class="timeline-step current"><span class="step-dot"></span><div><strong>Understand the request</strong><small>I paused before running tools because the request was too broad to investigate responsibly.</small></div><time></time></div>`;
    } else if (route === 'degraded') {
      addChat('agent', response.answer || 'The full analytical runtime is temporarily unavailable.');
      $('#activityStatus').textContent = 'Safe fallback active';
      $('#activityTimeline').innerHTML = `<div class="timeline-step done"><span class="step-dot"></span><div><strong>Stop safely</strong><small>No diagnosis was fabricated. You can retry or continue with grounded knowledge.</small></div><time></time></div>`;
      if (response.reference) console.warn('AquaMind runtime reference:', response.reference);
    } else if (route === 'safety_block') {
      addChat('agent', response.answer || 'The requested action is outside AquaMind\'s safety boundary.');
      $('#activityStatus').textContent = 'Safety boundary ✓';
      $('#activityTimeline').innerHTML = `<div class="timeline-step done"><span class="step-dot"></span><div><strong>Request blocked safely</strong><small>No physical plant-control action was executed.</small></div><time></time></div>`;
    } else if (route === 'needs_data') {
      addChat('agent', response.answer || 'Select plant data to continue.');
      $('#activityStatus').textContent = 'Plant data required';
    }
    renderSuggestions(response.suggestions || []);
  } catch (e) {
    addChat('agent', `I could not complete that request. ${e.message}`);
    toast(e.message);
    $('#activityStatus').textContent = 'Attention required';
  } finally {
    $('#sendInvestigation').disabled = false;
  }
}

async function investigate(text) { return askAgent(text); }

async function refreshDatasets() {
  const data = await api('/api/datasets');
  state.datasets = data.datasets || [];
  const select = $('#datasetSelect');
  const list = $('#datasetList');
  select.innerHTML = '';
  list.innerHTML = '';
  state.datasets.forEach(d => {
    const opt = document.createElement('option'); opt.value = d.name; opt.textContent = d.name; select.appendChild(opt);
    const row = document.createElement('button'); row.type = 'button'; row.className = 'dataset-row'; row.innerHTML = `<strong>${esc(d.name)}</strong><small>Project dataset</small>`;
    row.onclick = () => { loadDataset(d.name); $('#datasetDrawer').classList.remove('open'); select.value = d.name; };
    list.appendChild(row);
  });
  if (!state.dataset && state.datasets.length) state.dataset = state.datasets.find(x => x.name === 'scaling_colloidal_fouling.csv')?.name || state.datasets[0].name;
  if (state.dataset && state.datasets.some(x => x.name === state.dataset)) { select.value = state.dataset; await loadDataset(state.dataset); }
  else if (state.datasets.length) { state.dataset = state.datasets[0].name; select.value = state.dataset; await loadDataset(state.dataset); }
}

async function uploadFile(file) {
  if (!file) return;
  const fd = new FormData(); fd.append('file', file);
  try {
    const res = await fetch('/api/upload', {method:'POST', body:fd});
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || 'Upload failed');
    state.dataset = body.name;
    localStorage.setItem('aquamind_dataset', body.name);
    renderDataset(body.summary);
    await refreshDatasets();
    toast(`Loaded ${file.name}`);
  } catch (e) { toast(e.message); }
}

function showView(name) {
  $$('.view').forEach(v => v.classList.remove('active-view'));
  const target = $(`#${name}View`);
  if (!target) return;
  target.classList.add('active-view');
  $$('.nav-item').forEach(b => b.classList.toggle('active', b.dataset.view === name));
  if (name === 'traces') loadTraces();
  if (name === 'knowledge') loadKnowledge();
  if (name === 'cases') loadCases();
  if (name === 'overview') renderOverview();
}

async function loadTraces() {
  try {
    const data = await api('/api/traces');
    $('#traceList').innerHTML = (data.traces || []).map(t => `<button class="trace-row interactive-row" data-trace="${esc(t.name)}"><strong>${esc(t.name)}</strong><span>${(t.size / 1024).toFixed(1)} KB</span></button>`).join('') || '<p>No validation traces found.</p>';
    $$('.trace-row[data-trace]').forEach(row => row.onclick = async () => {
      try { const d = await api(`/api/trace/${encodeURIComponent(row.dataset.trace)}`); openModal(row.dataset.trace, `<pre class="modal-pre">${esc(d.preview || 'No preview available.')}</pre>`); }
      catch (e) { toast(e.message); }
    });
  } catch (e) { toast(e.message); }
}

async function loadKnowledge() {
  try {
    const d = await api('/api/system-info');
    const labels = [['Authoritative Sources',d.sources],['Canonical Cases',d.cases],['Diagnostic Rules',d.rules],['Evidence Terms',d.evidence_terms]];
    $('#knowledgeStats').innerHTML = labels.map(x => `<div class="overview-stat"><small>${x[0]}</small><strong>${x[1] ?? '—'}</strong></div>`).join('');
  } catch (e) { toast(e.message); }
}

async function loadCases() {
  try {
    const d = await api('/api/cases?limit=50');
    const host = $('#caseLibraryContent');
    if (!host) return;
    host.innerHTML = (d.cases || []).map(c => `<button class="case-row interactive-row"><div><strong>${esc(c.title || c.case_id || 'Case')}</strong><small>${esc(c.category || c.domain || '')}</small></div><span>${esc(c.expected_label || 'View')}</span></button>`).join('') || '<div class="empty-state"><strong>No cases found</strong></div>';
  } catch (e) { toast(e.message); }
}

function renderOverview() {
  const d = state.datasetSummary;
  const m = d?.metrics || {};
  const cards = [['Plant','RO Train 1'],['Dataset',d?.filename || '—'],['Permeate Flow',m.permeate_flow?.value ? `${fmt(m.permeate_flow.value,0)} m³/h` : '—'],['Last Investigation',state.lastResult ? 'Completed' : 'Not run']];
  $('#overviewCards').innerHTML = cards.map(x => `<div class="overview-stat"><small>${x[0]}</small><strong>${esc(x[1])}</strong></div>`).join('');
}

function openModal(title, htmlContent) {
  $('#modalTitle').textContent = title;
  $('#modalBody').innerHTML = htmlContent;
  $('#modalBackdrop').classList.remove('hidden');
}
function closeModal() { $('#modalBackdrop').classList.add('hidden'); }

function showResultTab(name) {
  $$('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  if (name === 'results') { $('.results-body').scrollTo({top:0, behavior:'smooth'}); return; }
  if (name === 'charts') { $('.chart-card').scrollIntoView({behavior:'smooth', block:'center'}); return; }
  if (name === 'system') { $('.system-card').scrollIntoView({behavior:'smooth', block:'center'}); return; }
  if (name === 'cases') { if (state.lastRelatedCases?.length) showRelatedCases(); else loadCases().then(() => showView('cases')); }
}

function cyclePeriod() {
  const values = [7, 30, 90];
  const idx = values.indexOf(state.periodDays);
  state.periodDays = values[(idx + 1) % values.length];
  localStorage.setItem('aquamind_period_days', String(state.periodDays));
  $('#periodButton').textContent = `▣ Last ${state.periodDays} days ⌄`;
  if (state.datasetSummary) renderChart(state.datasetSummary);
}

async function saveCurrentIncident() {
  if (!state.lastResult?.task_id) { toast('Run an investigation first'); return; }
  try {
    const saved = await api('/api/save-incident', {method:'POST', body:JSON.stringify({task_id:state.lastResult.task_id})});
    toast(saved.success === false ? (saved.error || 'Incident was not saved') : 'Incident saved');
  } catch (e) { toast(e.message); }
}

async function checkHealth() {
  try {
    await api('/api/health');
    $('#systemStatusText').textContent = 'System Ready';
    $('#systemStatusSubtext').textContent = 'AI agent online';
  } catch {
    $('#systemStatusText').textContent = 'System Attention';
    $('#systemStatusSubtext').textContent = 'Backend unavailable';
  }
}

function bind() {
  $('#openWorkspace').onclick = () => { const name = $('#nameInput').value.trim(); if (!name) { toast('Enter your name'); return; } state.userName = name; openApp(); };
  $('#nameInput').addEventListener('keydown', e => { if (e.key === 'Enter') $('#openWorkspace').click(); });
  $('#themeToggle').onclick = () => { state.theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'; document.documentElement.dataset.theme = state.theme; localStorage.setItem('aquamind_theme', state.theme); if (state.datasetSummary) renderChart(state.datasetSummary); };
  $$('.nav-item').forEach(b => b.onclick = () => showView(b.dataset.view));
  $('#newInvestigation').onclick = resetInvestigation;
  $('#investorDemo').onclick = async () => { try { const d = await api('/api/demo-scenario'); if (d.dataset) { await loadDataset(d.dataset); $('#datasetSelect').value = d.dataset; } resetInvestigation(); $('#investigationTitle').textContent = d.title || 'Investor Demo'; await askAgent(d.prompt); } catch (e) { toast(e.message); } };
  $('#overviewNewInvestigation').onclick = resetInvestigation;
  $('#sendInvestigation').onclick = () => { const x = $('#investigationInput'); const text = x.value; x.value = ''; investigate(text); };
  $('#investigationInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#sendInvestigation').click(); } });
  $('#globalSearch').addEventListener('keydown', e => { if (e.key === 'Enter') { showView('investigations'); const text = e.target.value; e.target.value = ''; investigate(text); } });
  $('#plantDataButton').onclick = () => $('#datasetDrawer').classList.add('open');
  $('#closeDrawer').onclick = () => $('#datasetDrawer').classList.remove('open');
  $('#uploadFile').onchange = e => uploadFile(e.target.files[0]);
  $('#attachFile').onchange = e => uploadFile(e.target.files[0]);
  $('#saveSettings').onclick = () => { state.plantId = $('#plantIdInput').value.trim() || 'RO-TRAIN-01'; localStorage.setItem('aquamind_plant_id', state.plantId); $('#plantCardId').textContent = state.plantId; const name = $('#settingsName').value.trim(); if (name) setUser(name); const ds = $('#datasetSelect').value; if (ds) loadDataset(ds); toast('Workspace settings saved'); };
  $('#helpButton').onclick = () => openModal('How to use AquaMindAI-Agent', '<p>Select or upload plant CSV data, describe the operating issue, then review the evidence-grounded hypothesis and verification steps. AquaMind does not authorize physical plant action.</p>');
  $('#plantCardButton').onclick = () => showView('settings');
  $('#userMenuButton').onclick = () => showView('settings');
  $('#investigationMenuButton').onclick = () => $('#investigationMenu').classList.toggle('hidden');
  $('#saveIncidentMenu').onclick = () => { $('#investigationMenu').classList.add('hidden'); saveCurrentIncident(); };
  $('#exportInvestigationMenu').onclick = () => { $('#investigationMenu').classList.add('hidden'); exportCurrentInvestigation(); };
  $('#explainHypothesis').onclick = () => askAgent('Explain why you reached this conclusion and show the strongest supporting evidence.');
  $('#resetInvestigationMenu').onclick = () => { $('#investigationMenu').classList.add('hidden'); resetInvestigation(); };
  $$('.tab').forEach(b => b.onclick = () => showResultTab(b.dataset.tab));
  $('#periodButton').onclick = cyclePeriod;
  $('#evidenceViewAll').onclick = () => openModal('Supporting Evidence', `<ol class="modal-list">${[...$('#evidenceList').children].map(x => `<li>${x.innerHTML}</li>`).join('')}</ol>${state.lastSources?.length ? `<h3>Grounding sources</h3><ul>${state.lastSources.slice(0,8).map(s => `<li>${esc(s.source_id || s.id || s.title || 'Source')}</li>`).join('')}</ul>` : ''}`);
  $('#knowledgeAskButton').onclick = () => { const q = $('#knowledgeAskInput').value.trim(); if (!q) return; showView('investigations'); $('#knowledgeAskInput').value = ''; askAgent(q); };
  $('#knowledgeAskInput').addEventListener('keydown', e => { if (e.key === 'Enter') $('#knowledgeAskButton').click(); });
  $('#closeModal').onclick = closeModal;
  $('#modalBackdrop').addEventListener('click', e => { if (e.target === $('#modalBackdrop')) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeModal(); $('#datasetDrawer').classList.remove('open'); $('#investigationMenu').classList.add('hidden'); } });
  window.addEventListener('resize', () => state.datasetSummary && renderChart(state.datasetSummary));
}

window.addEventListener('DOMContentLoaded', async () => {
  try {
    bind();
    $('#nameInput').value = state.userName;
    $('#plantIdInput').value = state.plantId;
    $('#plantCardId').textContent = state.plantId;
    $('#periodButton').textContent = `▣ Last ${state.periodDays} days ⌄`;
    if (state.userName) openApp();
    await Promise.all([refreshDatasets(), checkHealth()]);
    renderOverview();
  } catch (e) {
    console.error(e);
    toast(`Interface error: ${e.message}`);
  }
});
