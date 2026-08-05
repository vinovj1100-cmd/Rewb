# 🏭 WMS v4.4 — Quantum Warehouse Management System

**Version:** 4.4.0  
**License:** Proprietary  
**Python:** 3.11+

---

## 📋 Overview

Quantum WMS v4.4 is an enterprise-grade warehouse management system featuring:

- 🤖 **Quantum AI Engine** — Multi-algorithm optimization (SA, GA, Tabu, ACO + Ensemble)
- 🏷️ **WB Label Processor** — Enhanced vertical text detection and barcode parsing
- 📊 **Advanced Forecasting** — ETS, SARIMA, and Ensemble demand forecasting
- 🛡️ **Guardian** — Real-time system health monitoring
- 🤖 **Copilot** — Natural language analytics interface
- ⚡ **Realtime Event Bus** — Pub/sub event system
- 🔐 **RBAC + Audit Trail** — Hash-chained immutable audit logs
- 📄 **Report Generator** — PDF, Excel, CSV export
- ⚙️ **YAML-driven Rules** — Configurable business rules engine
- 🔄 **Offline Sync** — Queue-based disconnected operation support

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements_v44.txt

# 2. Launch the application
streamlit run app_v44.py

# 3. Login with demo credentials
#    admin / admin  (full access)
#    operator / operator  (floor access)
```

---

## 📁 Package Structure

```
wms_v44/
├── app_v44.py                 # Main Streamlit application
├── quantum_ai_engine.py       # AI optimization engine
├── wb_label_processor.py      # Label/barcode processing
├── db.py                      # Database layer (SQLite)
├── workflow_engine.py         # State machine workflows
├── rule_engine.py             # YAML-driven business rules
├── rbac_engine.py             # Role-based access control
├── audit_trail.py             # Hash-chained audit logs
├── advanced_forecasting.py    # Time series forecasting
├── report_generator.py        # PDF/Excel/CSV reports
├── floor_ops.py               # Pick/pack/putaway/andon
├── efficiency.py              # Wave planning, slotting, KPIs
├── guardian.py                # System health monitoring
├── dashboard.py               # Guardian renderer
├── copilot.py                 # Natural language analytics
├── realtime.py                # Event bus
├── sync.py                    # Offline queue
├── memory.py                  # Settings and aliases
├── seed_data.py               # Demo data generator
├── integrations.py            # ERP/TMS/EDI connectors
├── config.yaml                # System configuration
├── requirements_v44.txt       # Python dependencies
└── structured_data/           # JSON schemas and data
```

---

## 🔧 Modules

### Quantum AI Engine
Multi-algorithm task/resource optimization:
- **Simulated Annealing** — Global search with temperature cooling
- **Genetic Algorithm** — Population-based evolution
- **Tabu Search** — Local search with memory
- **Ant Colony** — Pheromone-based pathfinding
- **Ensemble** — Weighted vote aggregation

### WB Label Processor
- OCR text normalization
- Vertical text detection and reconstruction
- Multi-carrier tracking extraction (DHL, FedEx, UPS, USPS, Amazon)
- Confidence scoring and anomaly detection

### Advanced Forecasting
- **ETS** (Error-Trend-Seasonality) with Holt-Winters
- **SARIMA** for seasonal autoregressive models
- **Naive** baseline
- **Ensemble** weighted combination

### Guardian Health Monitor
- Service latency tracking
- Resource utilization (CPU, Memory, Disk, DB connections)
- Alert generation and escalation
- Dashboard rendering

---

## 🔐 Security

- SHA-256 password hashing
- Session-based authentication with TTL
- Role-based access control (Admin, Manager, Operator, Viewer)
- Hash-chained audit trail (tamper-evident)
- Rule-based data validation

---

## 📊 Demo Data

Run seeding to populate the database:

```python
from db import Database
from seed_data import SeedData

db = Database()
seed = SeedData()
stats = seed.seed_database(db)
print(f"Seeded: {stats}")
```

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 📞 Support

For support, contact: support@quantum-wms.com

---

*Built with ❤️ for modern warehouse operations.*
