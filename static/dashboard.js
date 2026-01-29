let byAccountLoaded = false;
let overallLoaded = false;

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
    if (charts[id]) charts[id].destroy();
    data.datasets.forEach(ds => {
        const color = colorFromLabel(ds.label);
        ds.backgroundColor = color;
        ds.borderColor = color;
    });
    charts[id] = new Chart(ctx, {type, data, options});
}

async function fetchData(endpoint) {
    const res = await fetch(endpoint);
    return await res.json();
}

async function loadCashflowByAccount() {
    const params = {...getDateParams()};
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
    const params = {...getDateParams()};
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
                borderWidth: 1,
                snapGaps: true,
                fill: true
            }
        }
    });
}

async function loadOverallBalance() {
    const params = {...getDateParams()};
    const query = buildQuery(params);
    const data = await fetchData(`/api/balance${query}`);
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

async function loadOverallCashflow() {
    const params = {...getDateParams()};
    const query = buildQuery(params);
    const data = await fetchData(`/api/cashflow${query}`);
    const chartData = toChartJsData(data);
    chartData.datasets.forEach((ds, i) => {
        if (ds.label.includes("Rolling")) {
            ds.type = "line";
            ds.fill = false;
            ds.borderWidth = 2;
            ds.tension = 0.3;
            ds.pointRadius = 2;
            ds.borderColor = colorFromLabel(ds.label);
            ds.backgroundColor = colorFromLabel(ds.label);
            ds.order = 2;
        } else {
            ds.type = "bar";
            ds.backgroundColor = colorFromLabel(ds.label);
            ds.order = 1;
        }
    });
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
    const qs = new URLSearchParams(params);
    return qs.toString() ? `?${qs.toString()}` : "";
}

async function loadContent() {
    initTabs();
    await refreshDashboard();

    const refreshBtn = document.getElementById("refresh-btn");
    refreshBtn.addEventListener("click", refreshDashboard);
}

function toggleDateInputs() {
    const disabled = document.getElementById("disableDateFilter").checked;
    document.getElementById("startDate").disabled = disabled;
    document.getElementById("endDate").disabled = disabled;
}

document.addEventListener("DOMContentLoaded", loadContent);
document.getElementById("applyDateFilter").addEventListener("click", async () => {
    await refreshDashboard();
});
document.getElementById("disableDateFilter").addEventListener("change", toggleDateInputs);

toggleDateInputs();