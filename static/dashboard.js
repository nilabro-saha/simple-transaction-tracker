let byAccountLoaded = false;
let overallLoaded = false;

const TABLEAU10 = [
    '#c21f5b',
    '#fbc02c',
    '#ff5722',
    '#bf360c',
    '#fdf9c3',
    '#c5cae9',
    '#fff177',
    '#f8bbd0',
    '#e1bee7',
    '#3f51b5',
    '#aed581',
    '#253137',
    '#ba68c8',
    '#ffccbc',
    '#9c27b0',
    '#90a4ae',
    '#e92663',
    '#0488d1',
    '#7986cb',
    '#e64a18',
    '#03a9f4',
    '#f06292',
    '#f67f17',
    '#19237e',
    '#03579b',
    '#cfd8dc',
    '#ddedc8',
    '#689f38',
    '#607d8b',
    '#b3e5fc',
    '#303f9f',
    '#33691d',
    '#455a64',
    '#88144f',
    '#8bc34a',
    '#ff8a65',
    '#4a198c',
    '#7b21a2',
    '#4fc3f7',
    '#ffec3a'
]

function colorFromTableau10(i) {
    return TABLEAU10[(i + 1) % TABLEAU10.length]
}

function colorFromLabelTableau10(label) {
    let hash = 0;
    for (let c of label) hash = c.charCodeAt(0) + ((hash << 5) - hash);
    return TABLEAU10[hash % TABLEAU10.length]
}

async function refreshDashboard() {
    console.log("Refreshing dashboard...");

    await loadCashflowByAccount();
    await loadBalanceByAccount();
    await loadOverallBalance();
    await loadOverallCashflow();
}

function onTabActivated(tab) {
    if (tab === "by-account" && !byAccountLoaded) {
        loadBalanceByAccount();
        loadCashflowByAccount();
        byAccountLoaded = true;
    }

    if (tab === "overall" && !overallLoaded) {
        loadOverallBalance();
        loadOverallCashflow();
        overallLoaded = true;
    }
}

function initTabs() {
    console.log("Initializing tabs");
    const buttons = document.querySelectorAll(".tab-btn");
    const contents = document.querySelectorAll(".tab-content");
    
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tab;
            buttons.forEach(b => b.classList.remove("active"));
            contents.forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(target).classList.add("active");
            Object.values(Chart.instances).forEach(chart => chart.resize());
            onTabActivated(target);
        });
    });
}

let charts = {};
console.log("dashboard.js loaded");

function colorFromLabel(label, alpha=0.7) {
    let hash = 0;
    for (let c of label) hash = c.charCodeAt(0) + ((hash << 5) - hash);
    return `rgba(${Math.abs(hash % 255)}, ${(hash >> 8) & 255}, ${(hash >> 16) & 255}, ${alpha})`;
}

function toChartJsData(apiData) {
    return {
        labels: apiData.year_months,
        datasets: apiData.datasets.map(s => ({
            label: s.name,
            data: s.data
        }))
    }
}

function renderChart(id, type, data, options = {}) {
    const ctx = document.getElementById(id);
    data.datasets.forEach((ds, i) => {
        if (ds.label.includes("Trendline")) {
            ds.type = "line";
            ds.fill = false;
            ds.borderDash = [5, 5];
            ds.borderWidth = 2
            ds.tension = 0.3;
            ds.pointRadius = 0;
            ds.hoverRadius = 1;
            ds.order = 1;
        } else if (ds.label.includes("Rolling")) {
            ds.type = "line";
            ds.fill = false;
            ds.borderWidth = 2;
            ds.tension = 0.3;
            ds.pointRadius = 1;
            ds.order = 2;
        } else {
            ds.type = type;
            ds.order = 3;
        }
        const color = colorFromTableau10(i);
        ds.backgroundColor = color;
        ds.borderColor = color;
    });
    if (charts[id]) {
        console.log(`Updating chart... ${id}`);
        charts[id].data = data;
        charts[id].type = type;
        charts[id].options = options;
        charts[id].update();
    } else {
        console.log(`Creating new chart... ${id}`);
        charts[id] = new Chart(ctx, {type, data, options});
    }
}

async function fetchData(endpoint) {
    const res = await fetch(endpoint);
    return await res.json();
}

async function fetchDataPost(endpoint, payload) {
    const res = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });
    return await res.json();
}

async function loadCashflowByAccount() {
    const params = {...getDateParams(), ...getMonthParams()};
    console.log(params);
    const query = buildQuery(params);
    const data = await fetchData(`/api/cashflow-by-account${query}`);
    const chartData = toChartJsData(data);
    renderChart('cashflowChart', 'bar', chartData, {
        responsive: true,
        scales: {
            x: { stacked: true },
            y: { stacked: true }
        },
        plugins: {
            legend: {
                position: "right",
                align: "center"
            }
        }
    });
}

async function loadBalanceByAccount() {
    const params = {...getDateParams(), ...getMonthParams()};
    const query = buildQuery(params);
    const data = await fetchData(`/api/balance-by-account${query}`);
    const chartData = toChartJsData(data);
    renderChart('balanceChart', 'line', chartData, {
        responsive: true,
        scales: {
            x: { stacked: true },
            y: { stacked: true }
        },
        plugins: {
            legend: {
                position: "right",
                align: "center"
            }
        },
        elements: {
            point: {
                radius: 0,
                hitRadius: 5,
                hoverRadius: 5
            },
            line: {
                borderWidth: 0,
                snapGaps: true,
                fill: true
            }
        }
    });
}

async function loadOverallBalance() {
    const params = {...getDateParams(), ...getMonthParams()};
    const query = buildQuery(params);
    const data = await fetchData(`/api/balance${query}`);

    const trendlineEnabled = document.getElementById("enableTrendline").checked;
    if (trendlineEnabled) {
        const extendByMonths = document.getElementById("extendByMonths").value || 0;
        const trendline = await fetchDataPost(`/api/trendline/`, {
            extend: extendByMonths,
            x: data.year_months,
            y: data.datasets[0].data
        });
        data.year_months = trendline.x;
        data.datasets.push({
            name: `Trendline (R-squared: ${trendline.r_squared}, Equation: ${trendline.formula})`,
            data: trendline.y
        });
    }
    const chartData = toChartJsData(data);
    renderChart('overallBalanceChart', 'line', chartData, {
        responsive: true,
        plugins: {
            legend: {
                position: "top",
                align: "center"
            }
        }
    });
}

async function togglePrediction() {
    const trendlineEnabled = document.getElementById("enableTrendline").checked;
    document.getElementById("extendByMonths").disabled = !trendlineEnabled;
}

async function loadOverallCashflow() {
    let params = {...getDateParams(), ...getMonthParams()};

    const rollingAvgEnabled = document.getElementById("enableRollingAverage").checked;
    if (rollingAvgEnabled) {
        const rollingWindow = document.getElementById("rollingWindow").value;
        params = {...params, window: rollingWindow}
    }
    const query = buildQuery(params);
    const data = await fetchData(`/api/cashflow${query}`);
    const chartData = toChartJsData(data);
    renderChart('overallCashflowChart', 'bar', chartData, {
        responsive: true,
        plugins: {
            legend: {
                position: "top",
                align: "center"
            }
        }
    });
}

async function toggleRollingWindow() {
    const rollingAverageEnabled = document.getElementById("enableRollingAverage").checked;
    document.getElementById("rollingWindow").disabled = !rollingAverageEnabled;
}

function getDateParams() {
    const disabled = document.getElementById("disableDateFilter").checked;
    if (disabled) {
        return {};
    }

    const start = document.getElementById("startDate").value;
    const end = document.getElementById("endDate").value;
    const params = {};
    if (start) params.start = start;
    if (end) params.end = end;
    return params;
}

function buildQuery(params) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach(item => qs.append(key, item));
      } else if (value !== undefined && value !== null) {
        qs.append(key, value);
      }
    });
    return qs.toString() ? `?${qs.toString()}` : "";
}

async function loadContent() {
    initTabs();
    await loadAvailableMonths();
    await refreshDashboard();

    const refreshBtn = document.getElementById("refresh-btn");
    refreshBtn.addEventListener("click", refreshDashboard);
}

function toggleDateInputs() {
    const disabled = document.getElementById("disableDateFilter").checked;
    document.getElementById("startDate").disabled = disabled;
    document.getElementById("endDate").disabled = disabled;
}

async function loadAvailableMonths() {
    const params = {...getDateParams()};
    const query = buildQuery(params);
    const months = await fetchData(`/api/months${query}`);
    renderMonthCheckboxes(months);
}

function getMonthParams() {
    const selectAll = document.getElementById("selectAllMonths");
    if (selectAll.checked) {
        return { month: [] };
    }
    const selectedMonths = Array
        .from(document.querySelectorAll(".month-checkbox"))
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    return { month: selectedMonths };
}

function renderMonthCheckboxes(months) {
    const container = document.getElementById("monthCheckboxes");
    container.innerHTML = "";

    const selectAllRow = document.createElement("div");
    selectAllRow.className = "filter-group";
    selectAllRow.innerHTML = `
        <label>
            <input type="checkbox" id="selectAllMonths" checked>
            Select all
        </label>
    `;
    container.appendChild(selectAllRow);

    months.forEach(month => {
        const row = document.createElement("div");
        row.className = "filter-group month-row";
        row.innerHTML = `
            <label>
                <input type="checkbox" class="month-checkbox" value=${month} disabled>
                ${month}
            </label>
        `;
        container.appendChild(row);
    })
    wireMonthCheckboxLogic();
}

function wireMonthCheckboxLogic() {
    const selectAll = document.getElementById("selectAllMonths");
    const monthCheckboxes = document.querySelectorAll(".month-checkbox");
    selectAll.addEventListener("change", () => {
        const enabled = !selectAll.checked;
        monthCheckboxes.forEach(cb => {
            cb.disabled = !enabled;
            if (!enabled) {
                cb.checked = false;
            } else {
                cb.checked = true;
            }
        })
    })
}

document.addEventListener("DOMContentLoaded", loadContent);
document.getElementById("applyDateFilter").addEventListener("click", async () => {
    await loadAvailableMonths();
    await refreshDashboard();
});
document.getElementById("applyMonthFilter").addEventListener("click", refreshDashboard);
document.getElementById("disableDateFilter").addEventListener("change", toggleDateInputs);
document.getElementById("enableTrendline").addEventListener("change", async () => {
    await togglePrediction();
    await loadOverallBalance();
});
document.getElementById("extendByMonths").addEventListener("input", loadOverallBalance);
document.getElementById("enableRollingAverage").addEventListener("change", async () => {
    await toggleRollingWindow();
    await loadOverallCashflow();
});
document.getElementById("rollingWindow").addEventListener("input", loadOverallCashflow);

toggleDateInputs();
togglePrediction();
toggleRollingWindow();