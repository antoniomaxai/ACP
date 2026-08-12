

# ACP AI Nation Rankings App

An interactive Streamlit application applying Antonio Max’s **AI Core–Periphery (ACP) Framework**—an adaptation of Immanuel Wallerstein’s *world-systems theory* to the emerging political economy of artificial intelligence.

This application dynamically re-weights and classifies over 190 nations into **Core**, **Semi-Periphery**, and **Periphery** AI tiers, mapping techno-economic asymmetries, structural capabilities, hardware bottlenecks, human capital, and digital capital flows.

---

## Overview & Theoretical Background

At its core, the ACP Framework evaluates where each country sits within the global distribution of AI capability, data, and power:

* **Core Nations**: States possessing dominant AI capabilities, hardware infrastructure, and the capacity to develop, deploy, and set global market rules/standards for AI ecosystems.
* **Semi-Periphery Nations**: States with meaningful AI capabilities and/or energy/developer capacity, functioning simultaneously as adopters, partners, and regional technology bridges, while remaining dependent on Core hardware or foundational models.
* **Periphery Nations**: States with limited domestic AI infrastructure, acting primarily as AI consumers, raw data sources, or API endpoints dependent on Core business models.

---

## 📊 Visualizations Included

The app features six interactive Plotly scatter distributions across the ACP tiers:

* **Plot A: ACP Distribution by World Region** — Maps structural rank against geographic regions.
* **Plot B: ACP Distribution by Regime Type** — Overlays V-Dem political regime typologies (Liberal Democracy, Electoral Democracy, Electoral Autocracy, Closed Autocracy).
* **Plot C: Executive Power Concentration** — Compares ACP tier standings against political authority density (sourced from CIA World Factbook Archive).
* **Plot D: Energy Infrastructure & Leapfrog Potential** — Scales nation dots by Total Installed Power Capacity in GW (sourced from IRENA) as a proxy for compute readiness.
* **Plot E: Absorptive Capacity & Developer Density** — Scales nation dots by GitHub developer counts (sourced from GitHub Innovation Graph) to measure sovereign human capital.
* **Plot F: Unequal Exchange: ICT Services Exports** — Scales nation dots by ICT services exports in USD (sourced from World Bank) to measure digital capital extraction vs. dependency.

---

## ⚙️ Key App Features

* **Dynamic Weight Adjustment**: Customize weights across all 14 Oxford Insights dimensions organized into 6 collapsible pillar expanders.
* **Real-time Tier Cutoffs**: Adjust percentage cutoffs for Core and Semi-Periphery classifications dynamically using sidebar sliders.
* **Responsive Layout**: Designed with custom visual jittering for data points, hover tooltips, and responsive image scaling.
* **Live Budget Tracking**: Integrated sidebar status tracking to ensure total active weights do not exceed $99.99\%$.

---

## 🚀 Quickstart & Local Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY

```


2. **Create a virtual environment (optional but recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


4. **Run the Streamlit app:**
```bash
streamlit run app.py

```



---

## 📦 Requirements

Create a `requirements.txt` file in your repository root with:

```text
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
numpy>=1.24.0

```

---

## 📑 Data Sources & Credits

* **Primary Ranking Data**: Adapted from [Oxford Insights Government AI Readiness Index (2025)](https://oxfordinsights.com/).
* **Regime Typology**: [V-Dem Institute (2026 Data)](https://www.v-dem.net).
* **Power Concentration**: [CIA World Factbook Archive Project](https://worldfactbookarchive.org/).
* **Energy Capacity (GW)**: [International Renewable Energy Agency (IRENA)](https://pxweb.irena.org/).
* **Developer Density**: [GitHub Innovation Graph](https://www.google.com/search?q=https://github.com/innovationgraph).
* **ICT Services Exports**: [World Bank Open Data](https://data.worldbank.org/).

---

### 📝 License & Citation

If you use this app or framework in your research, please cite:

> **Antonio Max**, *Techno-Economic Protagonism and the AI Core–Periphery (ACP) Framework*.
