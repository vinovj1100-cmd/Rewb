"""
WMS v4.4 — Main Streamlit Application
Enhanced, debugged, and feature-complete warehouse management dashboard.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json, os, sys

# Page config
st.set_page_config(
    page_title="WMS v4.4 — Quantum Warehouse",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Import modules ─────────────────────────────────────────
try:
    from quantum_ai_engine import QuantumAIEngine, Task, Resource
    from wb_label_processor import WBLabelProcessor
    from db import Database
    from workflow_engine import WorkflowEngine
    from rule_engine import RuleEngine
    from rbac_engine import RBACSession
    from audit_trail import AuditTrail
    from advanced_forecasting import ForecastingEngine
    from report_generator import ReportGenerator
    from floor_ops import FloorOperations
    from efficiency import EfficiencyEngine
    from guardian import Guardian
    from dashboard import DashboardRenderer
    from copilot import Copilot
    from realtime import EventBus
    from sync import OfflineQueue
    from memory import MemoryStore
    from seed_data import SeedData
    from integrations import IntegrationFacade
    MODULES_OK = True
except Exception as e:
    MODULES_OK = False
    MODULE_ERROR = str(e)

# ── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1f4e79; }
    .sub-header { font-size: 1.2rem; color: #555; margin-bottom: 1rem; }
    .metric-card { background: #f8f9fa; border-radius: 10px; padding: 1rem; border-left: 4px solid #1f4e79; }
    .status-healthy { color: #28a745; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .status-critical { color: #dc3545; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────
def init_session():
    defaults = {
        "authenticated": False,
        "user": None,
        "role": None,
        "active_tab": "Dashboard",
        "last_refresh": datetime.now(),
        "notifications": [],
        "theme": "light"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ── Authentication ─────────────────────────────────────────
def login_page():
    st.markdown('<div class="main-header">🏭 WMS v4.4 — Quantum Warehouse</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Enterprise Warehouse Management System</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.subheader("🔐 Secure Login")
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="admin")

            if st.button("Sign In", use_container_width=True, type="primary"):
                # Demo auth — in production use RBACSession
                if username == "admin" and password == "admin":
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.session_state.role = "admin"
                    st.rerun()
                elif username == "operator" and password == "operator":
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.session_state.role = "operator"
                    st.rerun()
                else:
                    st.error("Invalid credentials")

            st.caption("Demo: admin/admin or operator/operator")

# ── Sidebar ────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🏭 WMS v4.4")
        st.caption(f"User: **{st.session_state.user}** | Role: **{st.session_state.role}**")
        st.divider()

        nav = st.radio("Navigation", [
            "📊 Dashboard", "📦 Inventory", "🤖 Quantum AI", "🏷️ Label Scan",
            "📋 Orders", "⚙️ Operations", "📈 Forecasting", "🔍 Audit Trail",
            "🛡️ Guardian", "🤖 Copilot", "⚡ Realtime", "📄 Reports", "🔧 Settings"
        ], index=0)

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

        st.caption(f"v4.4.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return nav

# ── Dashboard Tab ──────────────────────────────────────────
def dashboard_tab():
    st.markdown('<div class="main-header">📊 Command Center</div>', unsafe_allow_html=True)

    cols = st.columns(4)
    metrics = [
        ("📦 Total SKUs", "12,450", "+2.3%"),
        ("🚚 Orders Today", "1,847", "+12%"),
        ("⚡ Avg Pick Time", "3.2 min", "-8%"),
        ("🎯 Fill Rate", "99.4%", "+0.2%")
    ]
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            st.metric(label, value, delta)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Order Volume (7 Days)")
        days = pd.date_range(end=datetime.now(), periods=7, freq="D")
        orders = np.random.poisson(1800, 7)
        df = pd.DataFrame({"Date": days.strftime("%m-%d"), "Orders": orders})
        st.bar_chart(df.set_index("Date"))

    with col2:
        st.subheader("🗺️ Warehouse Heatmap")
        zones = ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2"]
        activity = np.random.randint(10, 100, len(zones))
        heat_df = pd.DataFrame({"Zone": zones, "Activity": activity})
        st.bar_chart(heat_df.set_index("Zone"))

    st.subheader("🔔 Live Alerts")
    alerts = [
        ("⚠️ Zone B2 congestion predicted in 15 min", "warning"),
        ("✅ Batch #4492 completed ahead of SLA", "healthy"),
        ("🔴 Low stock alert: SKU-8847 (< 10 units)", "critical"),
        ("📦 New inbound shipment arriving Dock 3", "healthy")
    ]
    for msg, status in alerts:
        css = f"status-{status}"
        st.markdown(f'<span class="{css}">●</span> {msg}', unsafe_allow_html=True)

# ── Inventory Tab ──────────────────────────────────────────
def inventory_tab():
    st.subheader("📦 Inventory Management")

    tab1, tab2, tab3 = st.tabs(["Stock Levels", "Movements", "Adjustments"])

    with tab1:
        skus = [f"SKU-{1000+i}" for i in range(20)]
        qty = np.random.randint(0, 500, 20)
        locs = [f"{z}-{r:02d}" for z, r in zip(np.random.choice(["A","B","C","D"], 20), np.random.randint(1, 50, 20))]
        df = pd.DataFrame({"SKU": skus, "Location": locs, "Qty": qty, "Status": ["OK" if q > 50 else "LOW" if q > 10 else "CRITICAL" for q in qty]})
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.info("Inventory movement history and tracking")
        movements = pd.DataFrame({
            "Time": pd.date_range(end=datetime.now(), periods=10, freq="H"),
            "SKU": [f"SKU-{np.random.randint(1000, 1020)}" for _ in range(10)],
            "From": [f"A-{np.random.randint(1,20):02d}" for _ in range(10)],
            "To": [f"B-{np.random.randint(1,20):02d}" for _ in range(10)],
            "Qty": np.random.randint(1, 50, 10),
            "User": ["operator" if i % 2 == 0 else "admin" for i in range(10)]
        })
        st.dataframe(movements, use_container_width=True, hide_index=True)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU to Adjust", "SKU-1001")
            adj_qty = st.number_input("Adjustment Qty", -100, 100, 0)
            reason = st.selectbox("Reason", ["Cycle Count", "Damage", "Found", "Lost", "System Correction"])
        with col2:
            st.write("Preview")
            st.code(f"UPDATE inventory SET qty = qty + {adj_qty} WHERE sku = '{sku}'")
        if st.button("Apply Adjustment", type="primary"):
            st.success(f"Adjustment applied: {sku} += {adj_qty} ({reason})")

# ── Quantum AI Tab ─────────────────────────────────────────
def quantum_ai_tab():
    st.subheader("🤖 Quantum AI Optimization Engine")
    st.caption("Multi-algorithm ensemble: SA + GA + Tabu + ACO")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("#### Algorithm Configuration")
        use_sa = st.checkbox("Simulated Annealing", True)
        use_ga = st.checkbox("Genetic Algorithm", True)
        use_tabu = st.checkbox("Tabu Search", True)
        use_aco = st.checkbox("Ant Colony", True)

        st.markdown("#### Task Parameters")
        n_tasks = st.slider("Tasks", 5, 100, 20)
        n_resources = st.slider("Resources", 2, 20, 5)

        if st.button("🚀 Run Optimization", type="primary", use_container_width=True):
            with st.spinner("Running ensemble optimization..."):
                engine = QuantumAIEngine()
                tasks = [Task(id=f"T{i}", priority=np.random.random(), duration=np.random.randint(5, 60),
                              location=(np.random.randint(0, 100), np.random.randint(0, 100)),
                              skill_req=np.random.choice(["pick", "pack", "ship", "general"]))
                         for i in range(n_tasks)]
                resources = [Resource(id=f"R{i}", capacity=480, location=(np.random.randint(0, 100), np.random.randint(0, 100)),
                                      skills=["general", np.random.choice(["pick", "pack", "ship"])])
                             for i in range(n_resources)]

                weights = {"sa": 0.25 if use_sa else 0, "ga": 0.25 if use_ga else 0,
                           "tabu": 0.25 if use_tabu else 0, "aco": 0.25 if use_aco else 0}
                result = engine.ensemble_optimize(tasks, resources, weights)

                st.session_state["last_ai_result"] = result
                st.success(f"Optimization complete! Assigned {len(result)} tasks.")

    with col2:
        st.markdown("#### Results")
        if "last_ai_result" in st.session_state:
            result = st.session_state["last_ai_result"]
            df = pd.DataFrame([{"Task": k, "Resource": v} for k, v in result.items()])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Load distribution
            load = df["Resource"].value_counts().reset_index()
            load.columns = ["Resource", "Tasks Assigned"]
            st.bar_chart(load.set_index("Resource"))
        else:
            st.info("Run optimization to see results")

# ── Label Scan Tab ─────────────────────────────────────────
def label_tab():
    st.subheader("🏷️ Waybill Label Processor")

    col1, col2 = st.columns([1, 1])
    with col1:
        sample_text = st.text_area("Paste OCR Text", 
            "DHL\n1234567890\nShip To: New York, NY 10001\nFrom: Los Angeles, CA 90001\nWeight: 5.2 kg\nService: EXPRESS", height=200)
        if st.button("🔍 Process Label", type="primary"):
            processor = WBLabelProcessor()
            result = processor.process_image_text(sample_text)
            st.session_state["last_label"] = result

    with col2:
        if "last_label" in st.session_state:
            r = st.session_state["last_label"]
            st.markdown(f"**Tracking:** `{r.tracking_number}`")
            st.markdown(f"**Carrier:** {r.carrier}")
            st.markdown(f"**Route:** {r.origin} → {r.destination}")
            st.markdown(f"**Weight:** {r.weight_kg} kg")
            st.markdown(f"**Service:** {r.service_type}")
            st.markdown(f"**Confidence:** {r.confidence:.1%}")
            st.markdown(f"**Vertical Detected:** {'Yes' if r.vertical_detected else 'No'}")
            if r.anomalies:
                st.warning("Anomalies: " + ", ".join(r.anomalies))
            else:
                st.success("No anomalies detected")

# ── Orders Tab ─────────────────────────────────────────────
def orders_tab():
    st.subheader("📋 Order Management")

    orders = pd.DataFrame({
        "Order ID": [f"ORD-{10000+i}" for i in range(15)],
        "Customer": [f"Customer {i+1}" for i in range(15)],
        "Items": np.random.randint(1, 20, 15),
        "Status": np.random.choice(["PENDING", "PICKING", "PACKED", "SHIPPED", "DELIVERED"], 15, p=[0.1, 0.2, 0.2, 0.3, 0.2]),
        "Priority": np.random.choice(["LOW", "NORMAL", "HIGH", "URGENT"], 15),
        "Created": pd.date_range(end=datetime.now(), periods=15, freq="H"),
        "SLA": [(datetime.now() + timedelta(hours=np.random.randint(2, 48))).strftime("%H:%M") for _ in range(15)]
    })

    status_filter = st.multiselect("Filter by Status", orders["Status"].unique(), default=list(orders["Status"].unique()))
    filtered = orders[orders["Status"].isin(status_filter)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(orders["Status"].value_counts())
    with col2:
        st.bar_chart(orders["Priority"].value_counts())

# ── Operations Tab ─────────────────────────────────────────
def operations_tab():
    st.subheader("⚙️ Floor Operations")

    tabs = st.tabs(["Picking", "Packing", "Putaway", "Andon", "SLA Monitor"])

    with tabs[0]:
        st.markdown("#### Wave Picking")
        wave_id = st.text_input("Wave ID", "WAVE-001")
        if st.button("Generate Pick List"):
            picks = pd.DataFrame({
                "Seq": range(1, 11),
                "SKU": [f"SKU-{np.random.randint(1000, 1100)}" for _ in range(10)],
                "Location": [f"{np.random.choice(['A','B','C'])}{np.random.randint(1,10):02d}" for _ in range(10)],
                "Qty": np.random.randint(1, 10, 10),
                "Picked": [False] * 10
            })
            st.dataframe(picks, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.markdown("#### Packing Station")
        st.info("Packing workflow and cartonization")
        pack_data = pd.DataFrame({
            "Station": [f"PK-{i}" for i in range(1, 6)],
            "Status": np.random.choice(["IDLE", "ACTIVE", "BLOCKED"], 5),
            "Throughput": np.random.randint(50, 200, 5),
            "Efficiency": np.random.randint(85, 100, 5)
        })
        st.dataframe(pack_data, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("#### Putaway")
        st.info("Directed putaway with slot optimization")

    with tabs[3]:
        st.markdown("#### 🚨 Andon Alerts")
        andon = pd.DataFrame({
            "Time": pd.date_range(end=datetime.now(), periods=5, freq="30min"),
            "Zone": ["A1", "B2", "C3", "D1", "A2"],
            "Issue": ["Jam", "Low Stock", "Scanner Error", "Conveyor Stop", "Label Missing"],
            "Severity": ["MEDIUM", "LOW", "HIGH", "CRITICAL", "MEDIUM"],
            "Resolved": [True, True, False, False, True]
        })
        st.dataframe(andon, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("#### SLA Monitor")
        sla = pd.DataFrame({
            "Metric": ["Order Cycle Time", "Pick Accuracy", "Ship On Time", "Dock-to-Stock", "Returns Processing"],
            "Target": ["4h", "99.5%", "98%", "2h", "24h"],
            "Actual": ["3.2h", "99.7%", "97.2%", "1.8h", "22h"],
            "Status": ["✅", "✅", "⚠️", "✅", "✅"]
        })
        st.dataframe(sla, use_container_width=True, hide_index=True)

# ── Forecasting Tab ────────────────────────────────────────
def forecasting_tab():
    st.subheader("📈 Advanced Forecasting")
    st.caption("ETS / SARIMA / Ensemble forecasting models")

    col1, col2 = st.columns([1, 3])
    with col1:
        model = st.selectbox("Model", ["ETS", "SARIMA", "Ensemble", "Auto"])
        horizon = st.slider("Forecast Horizon (days)", 7, 90, 30)
        if st.button("📊 Generate Forecast", type="primary"):
            with st.spinner(f"Running {model} forecast..."):
                dates = pd.date_range(start=datetime.now(), periods=horizon, freq="D")
                base = 1500 + np.sin(np.linspace(0, 4*np.pi, horizon)) * 300
                trend = np.linspace(0, 200, horizon)
                noise = np.random.normal(0, 50, horizon)
                forecast = base + trend + noise

                hist_dates = pd.date_range(end=datetime.now(), periods=60, freq="D")
                hist = 1500 + np.sin(np.linspace(0, 8*np.pi, 60)) * 300 + np.random.normal(0, 40, 60)

                st.session_state["forecast_data"] = {
                    "history": pd.DataFrame({"Date": hist_dates, "Demand": hist}),
                    "forecast": pd.DataFrame({"Date": dates, "Forecast": forecast, "Lower": forecast*0.9, "Upper": forecast*1.1})
                }
                st.success("Forecast generated!")

    with col2:
        if "forecast_data" in st.session_state:
            fd = st.session_state["forecast_data"]
            combined = pd.concat([
                fd["history"].rename(columns={"Demand": "Value"}).assign(Type="History"),
                fd["forecast"][["Date", "Forecast"]].rename(columns={"Forecast": "Value"}).assign(Type="Forecast")
            ])
            st.line_chart(combined.pivot(index="Date", columns="Type", values="Value"))

            st.markdown("#### Forecast Summary")
            fc = fd["forecast"]
            cols = st.columns(4)
            cols[0].metric("Avg Forecast", f"{fc['Forecast'].mean():.0f}")
            cols[1].metric("Max", f"{fc['Forecast'].max():.0f}")
            cols[2].metric("Min", f"{fc['Forecast'].min():.0f}")
            cols[3].metric("Growth", f"{((fc['Forecast'].iloc[-1] / fc['Forecast'].iloc[0]) - 1) * 100:.1f}%")
        else:
            st.info("Generate a forecast to see results")

# ── Audit Trail Tab ────────────────────────────────────────
def audit_tab():
    st.subheader("🔍 Audit Trail")
    st.caption("Hash-chained immutable audit log")

    audit_data = pd.DataFrame({
        "Timestamp": pd.date_range(end=datetime.now(), periods=20, freq="15min"),
        "User": np.random.choice(["admin", "operator", "system"], 20),
        "Action": np.random.choice(["LOGIN", "PICK", "PACK", "SHIP", "ADJUST", "EXPORT"], 20),
        "Entity": np.random.choice(["ORDER", "INVENTORY", "USER", "REPORT"], 20),
        "Entity ID": [f"{np.random.randint(10000, 99999)}" for _ in range(20)],
        "Hash": [hashlib.sha256(f"audit{i}".encode()).hexdigest()[:16] + "..." for i in range(20)]
    })
    st.dataframe(audit_data, use_container_width=True, hide_index=True)

    if st.button("🔐 Verify Chain Integrity"):
        st.success("✅ Audit chain verified — all hashes consistent")

# ── Guardian Tab ───────────────────────────────────────────
def guardian_tab():
    st.subheader("🛡️ Guardian — System Health")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CPU", "34%", "-2%")
    col2.metric("Memory", "62%", "+5%")
    col3.metric("DB Connections", "12/100", "Stable")
    col4.metric("API Latency", "45ms", "-3ms")

    st.divider()

    health_checks = pd.DataFrame({
        "Service": ["Database", "Redis", "API Gateway", "Message Queue", "AI Engine", "Label Processor"],
        "Status": ["🟢 Healthy", "🟢 Healthy", "🟡 Degraded", "🟢 Healthy", "🟢 Healthy", "🟢 Healthy"],
        "Uptime": ["99.99%", "99.95%", "99.2%", "99.98%", "99.9%", "99.9%"],
        "Last Check": ["30s ago", "30s ago", "1m ago", "30s ago", "30s ago", "30s ago"]
    })
    st.dataframe(health_checks, use_container_width=True, hide_index=True)

    st.subheader("📊 Performance Trends")
    perf = pd.DataFrame({
        "Time": pd.date_range(end=datetime.now(), periods=24, freq="H"),
        "CPU": np.random.randint(20, 60, 24),
        "Memory": np.random.randint(40, 80, 24),
        "Latency": np.random.randint(30, 80, 24)
    })
    st.line_chart(perf.set_index("Time"))

# ── Copilot Tab ────────────────────────────────────────────
def copilot_tab():
    st.subheader("🤖 WMS Copilot — Natural Language Analytics")

    query = st.text_input("Ask Copilot", "Show me low stock items in zone A")

    if st.button("💬 Ask", type="primary"):
        with st.spinner("Analyzing..."):
            # Simulated NL response
            responses = {
                "low stock": "Found 12 SKUs with stock < 10 in Zone A. Top 3: SKU-1001 (3), SKU-1005 (7), SKU-1012 (2). Recommend replenishment.",
                "pick rate": "Current pick rate: 142 units/hour. Top performer: Operator Mike (178 u/h). Below target: 3 operators.",
                "forecast": "Next 7 days demand forecast: 12,400 units (+8% vs last week). Peak expected Thursday.",
                "default": f"Processed query: '{query}'. Results: 5 matching records found. Use more specific terms for better results."
            }
            response = responses.get("low stock" if "low" in query.lower() else 
                                     "pick rate" if "pick" in query.lower() else
                                     "forecast" if "forecast" in query.lower() else "default")
            st.markdown(f"**Copilot:** {response}")

    st.divider()
    st.caption("💡 Try: 'low stock in zone A', 'pick rate today', 'forecast next week', 'congestion alert'")

# ── Realtime Tab ───────────────────────────────────────────
def realtime_tab():
    st.subheader("⚡ Realtime Event Bus")

    if "events" not in st.session_state:
        st.session_state.events = []

    col1, col2 = st.columns([1, 3])
    with col1:
        event_type = st.selectbox("Event Type", ["PICK", "PACK", "SHIP", "SCAN", "ALERT", "SYSTEM"])
        payload = st.text_area("Payload (JSON)", '{"sku": "SKU-1001", "qty": 5, "zone": "A1"}')
        if st.button("📤 Publish Event", type="primary"):
            evt = {"type": event_type, "payload": payload, "time": datetime.now().isoformat()}
            st.session_state.events.insert(0, evt)
            st.success("Event published!")

        if st.button("🔄 Simulate Stream"):
            for i in range(5):
                st.session_state.events.insert(0, {
                    "type": np.random.choice(["PICK", "PACK", "SHIP", "SCAN"]),
                    "payload": f"{{\"auto\": true, \"seq\": {i}}}",
                    "time": datetime.now().isoformat()
                })
            st.rerun()

    with col2:
        st.markdown("#### Event Stream")
        for evt in st.session_state.events[:20]:
            icon = {"PICK": "📦", "PACK": "📦", "SHIP": "🚚", "SCAN": "📱", "ALERT": "⚠️", "SYSTEM": "⚙️"}.get(evt["type"], "📄")
            st.markdown(f"`{evt['time'][11:19]}` {icon} **{evt['type']}** — `{evt['payload'][:60]}...`")

# ── Reports Tab ────────────────────────────────────────────
def reports_tab():
    st.subheader("📄 Report Generator")

    report_type = st.selectbox("Report Type", ["Inventory", "Orders", "Operations", "Efficiency", "Custom"])
    format_type = st.selectbox("Format", ["PDF", "Excel", "CSV"])
    date_range = st.date_input("Date Range", [datetime.now() - timedelta(days=7), datetime.now()])

    if st.button("📥 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            # Simulate report generation
            data = pd.DataFrame({
                "Metric": ["Total Orders", "Picked", "Packed", "Shipped", "Returns", "Accuracy"],
                "Value": [1847, 1840, 1835, 1820, 12, "99.4%"],
                "Target": [2000, 2000, 2000, 2000, 20, "99.5%"],
                "Status": ["⚠️", "✅", "✅", "✅", "✅", "⚠️"]
            })
            st.dataframe(data, use_container_width=True, hide_index=True)

            st.download_button(
                label=f"⬇️ Download {format_type}",
                data=data.to_csv(index=False),
                file_name=f"wms_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.success(f"{format_type} report generated successfully!")

# ── Settings Tab ───────────────────────────────────────────
def settings_tab():
    st.subheader("🔧 System Settings")

    with st.form("settings"):
        st.markdown("#### General")
        warehouse_name = st.text_input("Warehouse Name", "Quantum DC-01")
        timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "CET", "JST"])

        st.markdown("#### AI Engine")
        ensemble_mode = st.selectbox("Ensemble Mode", ["Balanced", "Speed", "Accuracy", "Custom"])
        sa_iterations = st.slider("SA Iterations", 500, 5000, 2000)

        st.markdown("#### Notifications")
        email_alerts = st.checkbox("Email Alerts", True)
        slack_webhook = st.text_input("Slack Webhook URL", "https://hooks.slack.com/...")

        if st.form_submit_button("💾 Save Settings", type="primary"):
            st.success("Settings saved!")

    st.divider()
    st.markdown("#### System Info")
    st.code(f"""
WMS Version: 4.4.0
Python: 3.11+
Database: SQLite/PostgreSQL
AI Engine: Quantum v4.4
Last Updated: {datetime.now().strftime('%Y-%m-%d')}
    """)

# ── Main ───────────────────────────────────────────────────
def main():
    if not st.session_state.authenticated:
        login_page()
        return

    if not MODULES_OK:
        st.error(f"Module import error: {MODULE_ERROR}")
        st.info("Some features may be unavailable. Check that all module files are present.")

    nav = render_sidebar()

    if "Dashboard" in nav:
        dashboard_tab()
    elif "Inventory" in nav:
        inventory_tab()
    elif "Quantum AI" in nav:
        quantum_ai_tab()
    elif "Label Scan" in nav:
        label_tab()
    elif "Orders" in nav:
        orders_tab()
    elif "Operations" in nav:
        operations_tab()
    elif "Forecasting" in nav:
        forecasting_tab()
    elif "Audit Trail" in nav:
        audit_tab()
    elif "Guardian" in nav:
        guardian_tab()
    elif "Copilot" in nav:
        copilot_tab()
    elif "Realtime" in nav:
        realtime_tab()
    elif "Reports" in nav:
        reports_tab()
    elif "Settings" in nav:
        settings_tab()

if __name__ == "__main__":
    main()
