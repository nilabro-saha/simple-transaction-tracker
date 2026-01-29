let byAccountLoaded = false;
let overallLoaded = false;

async function refreshDashboard() {
    console.log("Refreshing dashboard...");

    await loadCashflowByAccount();
    await loadBalanceByAccount();
}

function onTabActivated(tab) {
    if (tab === "by-account" && !byAccountLoaded) {
        loadCashflowByAccount();
        loadBalanceByAccount();
        byAccountLoaded = true;
    }

    if (tab === "overall" && !overallLoaded) {
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
            Chart.helpers.each(Chart.instances, chart => chart.resize());
            onTabActivated(target);
        });
    });
}

let charts = {}
console.log("dashboard.js loaded")

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
    })
    charts[id] = new Chart(ctx, {type, data, options})
}

async function fetchData(endpoint) {
    const res = await fetch(endpoint);
    return await res.json();
}

async function loadCashflowByAccount() {
    const data = await fetchData('/api/cashflow-by-account')
    const chartData = toChartJsData(data)
    renderChart('cashflowChart', 'bar', chartData, {
        responsive: true,
        scales: {
            x: { 
                grid: { display: false },
                stacked: true 
            },
            y: { stacked: true }
        },
        plugins: {
            legend: {
                position: "right",
                align: "center"
            }
        }
    })
}

async function loadBalanceByAccount() {
    const data = await fetchData('/api/balance-by-account')
    const chartData = toChartJsData(data)
    renderChart('balanceChart', 'line', chartData, {
        responsive: true,
        scales: {
            x: { 
                grid: { display: false },
                stacked: true 
            },
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
    })
}

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadCashflowByAccount();
    loadBalanceByAccount();

    const refreshBtn = document.getElementById("refresh-btn");
    refreshBtn.addEventListener("click", refreshDashboard);
});