let chart;

async function uploadFile() {
  const file = document.getElementById('fileInput').files[0];
  if (!file) return alert('Selecciona un archivo');
  const form = new FormData();
  form.append('file', file);

  const res = await fetch('/api/upload', { method: 'POST', body: form });
  const data = await res.json();
  document.getElementById('uploadResult').textContent = data.ok
    ? `OK: ${data.rows} filas históricas y ${data.forecast_rows} filas de forecast.`
    : `Error: ${data.error}`;
}

function getDates() {
  return {
    start: document.getElementById('startDate').value,
    end: document.getElementById('endDate').value,
  };
}

async function loadCharts() {
  const { start, end } = getDates();
  const h = await fetch(`/api/history?start=${start}&end=${end}`).then(r => r.json());
  const f = await fetch(`/api/forecast?start=${start}&end=${end}`).then(r => r.json());

  const labels = [...new Set([...h.map(x => x.day), ...f.map(x => x.day)])].sort();
  const historyMap = new Map(h.map(x => [x.day, x.calls]));
  const forecastMap = new Map(f.map(x => [x.day, x.calls]));

  const historyData = labels.map(l => historyMap.get(l) || null);
  const forecastData = labels.map(l => forecastMap.get(l) || null);

  const ctx = document.getElementById('demandChart');
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Histórico', data: historyData, borderColor: '#2f855a', tension: 0.2 },
        { label: 'Forecast', data: forecastData, borderColor: '#2954ff', tension: 0.2 },
      ],
    },
    options: { responsive: true, scales: { x: { ticks: { maxTicksLimit: 24 } } } }
  });
}

async function calcFte() {
  const { start, end } = getDates();
  const payload = {
    start,
    end,
    source: document.getElementById('source').value,
    nda: Number(document.getElementById('nda').value),
    nds: Number(document.getElementById('nds').value),
    nds_seconds: Number(document.getElementById('nds_seconds').value),
    aht: Number(document.getElementById('aht').value),
    absentismo: Number(document.getElementById('absentismo').value),
    descanso: Number(document.getElementById('descanso').value),
    pausa_visual: Number(document.getElementById('pausa_visual').value),
    ata: Number(document.getElementById('ata').value),
    asa: Number(document.getElementById('asa').value),
    occupancy: Number(document.getElementById('occupancy').value),
  };

  const res = await fetch('/api/fte', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json());

  document.getElementById('peakFte').textContent = res.peak_fte;
  document.getElementById('avgFte').textContent = res.avg_fte;

  const body = document.getElementById('fteTable');
  body.innerHTML = '';
  res.intervals.slice(0, 50).forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.day}</td><td>${row.franja}</td><td>${Math.round(row.calls)}</td><td>${row.fte}</td>`;
    body.appendChild(tr);
  });
}

document.getElementById('uploadBtn').addEventListener('click', uploadFile);
document.getElementById('loadChartsBtn').addEventListener('click', loadCharts);
document.getElementById('calcFteBtn').addEventListener('click', calcFte);
