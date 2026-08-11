import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="ACP - Country Rankings", layout="wide")

# --- 1. DATA LOADING ---
# @st.cache_data
def load_data():
    df = pd.read_csv("ACP-ranked-data.csv")
    
    # Pre-processing
    # Ensure Score is numeric
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    
    # Handle Labels: Only show label if ShowLabel is True/TRUE
    # Handle string boolean and actual booleans
    is_true = df["ShowLabel"].astype(str).str.upper() == "TRUE"
    df["Display_Label"] = np.where(is_true, df["Label"].fillna(""), "")
    
    # Create Jitter for Y-axis (for plots B and C)
    # FIXED: Using a normal distribution (Gaussian) instead of uniform creates a center-heavy diamond shape
    df["jitter_y"] = np.random.normal(0, 0.25, len(df))
    
    # Handle Power Concentration 0s and nulls
    df["KPIs-PC_plot"] = pd.to_numeric(df["KPIs-PC"], errors="coerce").fillna(0)
    df["KPIs-PC_plot"] = df["KPIs-PC_plot"].apply(lambda x: 1 if x == 0 else x)
    
    return df

df_raw = load_data()

# --- 2. SIDEBAR: UI WIDGETS ---
st.sidebar.header("⚙️ Ranking Parameters")

# A. Rank Classification Thresholds
st.sidebar.subheader("Classification Thresholds")
st.sidebar.write("Percentage cutoffs for primary tiers.")

core_pct = st.sidebar.slider("Core (Top % - Default: 4.5)", min_value=2.0, max_value=20.0, value=4.5, step=0.5)
sp_pct = st.sidebar.slider("Semi-Periphery (Up to % - Default: 18)", min_value=9.0, max_value=50.0, value=18.0, step=1.0)

# B. Ranking Weights
st.sidebar.subheader("Ranking Weights (%)")
st.sidebar.write("Adjust the 14 dimension weights. Total must not exceed 99.99%.")

# Dictionary matching exactly the dimension names you provided
default_weights = {
    "Policy vision": 0.00,
    "Policy commitment": 0.00,
    "Compute capacity": 27.00,
    "Enabling technical infrastructure": 15.00,
    "Data quality": 7.00,
    "Governance principles": 3.00,
    "Regulatory compliance": 3.00,
    "Government digital policy": 0.00,
    "e-Government delivery": 0.00,
    "Human capital": 10.00,
    "AI sector maturity": 16.99,
    "AI technology diffusion": 12.00,
    "Societal transition": 3.00,
    "Safety and security": 3.00
}

active_weights = {}
total_weight = 0.0

for dim, default_val in default_weights.items():
    active_weights[dim] = st.sidebar.number_input(f"{dim}", min_value=0.0, max_value=100.0, value=default_val, step=1.0)
    total_weight += active_weights[dim]

if total_weight > 99.99:
    st.sidebar.error(f"⚠️ Total weight is {total_weight:.2f}%. It must be ≤ 99.99%.")

# --- 3. DYNAMIC DATA PROCESSING ---
df = df_raw.copy()

# Try to calculate dynamic score if raw columns exist
has_raw_data = all(dim in df.columns for dim in active_weights.keys())
if has_raw_data:
    df["Score"] = 0
    for dim, weight in active_weights.items():
        df["Score"] += pd.to_numeric(df[dim], errors="coerce").fillna(0) * (weight / 100)
else:
    st.sidebar.info("ℹ️ Raw dimension columns not found in CSV. Using default static 'Score' column.")

# Recalculate Rankings and Tiers
df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
df["Position"] = df.index + 1

# Calculate integer cutoffs based on N
N = len(df)
core_cutoff = max(1, int(N * (core_pct / 100)))
sp_cutoff = max(core_cutoff + 1, int(N * (sp_pct / 100)))

# Assign Tiers dynamically
def assign_tier(pos):
    if pos <= core_cutoff:
        return "Core AI Nation"
    elif pos <= sp_cutoff:
        return "Semi-Periphery AI Nation"
    else:
        return "Periphery AI Nation"

df["Classification"] = df["Position"].apply(assign_tier)

# Enforce category order for plots
tier_order = ["Core AI Nation", "Semi-Periphery AI Nation", "Periphery AI Nation"]
df["Classification"] = pd.Categorical(df["Classification"], categories=tier_order, ordered=True)

# --- Y-Axis Jitter Mapping for Plot A ---
# Maps regions to integers and adds a normal distribution jitter to create diamond shapes without overlapping

# --- MANUAL JITTER FOR PLOT A (Strip Plot Style) ---
# Map Tiers to integers
tier_mapping = {"Core AI Nation": 1, "Semi-Periphery AI Nation": 2, "Periphery AI Nation": 3}
df["Tier_Num"] = df["Classification"].map(tier_mapping)

# Map Regions to integers
unique_regions = df["Region"].dropna().unique()
region_mapping = {region: i for i, region in enumerate(unique_regions)}
df["Region_Num"] = df["Region"].map(region_mapping)

# Apply wide uniform horizontal jitter (spreads dots along the X axis) and tight normal vertical jitter
df["Tier_Num"] = df["Tier_Num"].astype(float)
# df["PlotA_X"] = df["Tier_Num"] + np.random.uniform(-0.35, 0.35, len(df))
# df["PlotA_Y"] = df["Region_Num"] + np.random.normal(0, 0.05, len(df))
tier_min = df.groupby("Tier_Num")["Score"].transform("min")
tier_max = df.groupby("Tier_Num")["Score"].transform("max")
score_range = tier_max - tier_min
score_range = score_range.replace(0, 1) # Prevent division by zero if all scores are identical
# Normalize scores from 0 to 1 (1 being the highest score in that tier)
norm_score = (df["Score"] - tier_min) / score_range
# Map horizontal (X) spacing: Highest score goes to the left (-0.35 offset), lowest to the right (+0.35 offset)
df["PlotA_X"] = df["Tier_Num"] - 0.35 + (1 - norm_score) * 0.70
# Apply improved vertical (Y) jitter to fan them out and prevent identical scores from stacking
df["PlotA_Y"] = df["Region_Num"] + np.random.normal(0, 0.12, len(df))

# --- NEW: JITTER & BASE COLORS FOR PLOTS B & C ---
# Create lateral (X) and vertical (Y) normal distributions for the diamond/violin shapes
df["PlotBC_X"] = df["Tier_Num"] + np.random.normal(0, 0.16, len(df))
# df["PlotBC_Y"] = np.random.normal(0, 0.25, len(df))
# df["PlotBC_Y"] = df["Score"]
tier_mean = df.groupby("Tier_Num")["Score"].transform("mean")
df["PlotBC_Y"] = df["Score"] - tier_mean

# Strip + and - for Plot B base colors and map to full descriptive names for the legend
pol_mapping = {
    "LD": "LD - Liberal Democracy",
    "ED": "ED - Electoral Democracy",
    "EA": "EA - Electoral Autocracy",
    "CA": "CA - Closed Autocracy"
}
df["KPIs-R_base"] = df["KPIs-R"].astype(str).str.replace(r'[\+\-]', '', regex=True).map(pol_mapping)

# --- 4. MAIN PAGE & CHARTS ---
st.title("AI Core-Periphery - Country Rankings")
st.markdown(f"**Total Countries Analyzed:** `{N}` | **Core:** `{core_cutoff}` | **Semi-Periphery:** `{sp_cutoff - core_cutoff}` | **Periphery:** `{N - sp_cutoff}`")

st.divider()

# Creates 3 columns with a 1:2:1 ratio. The middle column takes up 50% of the space.
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    st.image("ACP-33.png", use_container_width=True, caption="The AI Core–Periphery Framework")

st.write("""
This analysis applies Antonio Max’s [AI Core–Periphery (ACP) Framework](https://antoniomax.substack.com/p/techno-economic-protagonism-and-ai), an adaptation of Immanuel Wallerstein’s [world-systems theory](https://en.wikipedia.org/wiki/World-systems_theory) to the emerging political economy of artificial intelligence. The framework extends the core–periphery model to examine the techno-economic asymmetries that AI is consolidating among states, with particular attention to the distribution of AI capabilities, infrastructures, data, technological dependencies, and market power.

At its core, the ACP Framework asks: *Where does each country sit within the global distribution of AI capability, data, and power?*
    
##### Key ACP Concepts:
- **Core countries**: States possessing the strongest AI capabilities and the greatest capacity to develop, deploy, and shape AI systems, infrastructures, standards  and associated market rules (eg. establishing tokens as de facto economic accounting unit for generative-AI inference).
- **Semi-periphery countries**: States with meaningful AI capabilities and/or capacity to participate in the AI economy, but with structural limitations relative to  the Core. They may function simultaneously as technology developers, adopters, partners, suppliers, and customers within Core-dominated AI ecosystems. Often geopolitical allies and Core intermediaries for Periphery countries.
- **Periphery countries**: States with comparatively limited domestic AI capabilities and greater dependence on technologies, talent, infrastructure, capital and expertise from both Core and Semi-periphery countries. Predominantly AI customers and raw data suppliers, Periphery AI countries are higly path dependent on Core business models and their geopolitical doctrines.

##### ACP Ranking:

The ACP Ranking is derived from a customized weighted composite of Oxford Insights’ [Government AI Readiness Index (2025)](https://oxfordinsights.com/ai-readiness/government-ai-readiness-index-2025/). The original pillars and corresponding weights are provided in their [methodology report](https://oxfordinsights.com/wp-content/uploads/2026/05/Methodology-Report-2025-1.pdf) and reproduced on the sidebar.
         
The ACP weighting scheme modifies original weights to emphasize variables considered more directly indicative of structural AI capability. In particular, AI Infrastructure receives a substantially greater weight, while Public Sector Adoption and Policy Capacity are comparatively downweighted, treated as partially orthogonal to the core–periphery dimension being modeled.

The resulting classification is therefore not intended to reproduce/modify Oxford Insights’ original ranking. Rather, it repurposes its underlying weights to construct an analytical measure of countries’ relative position within the emerging global political economy of AI.
""")

st.divider()

# --- PLOT A: Regions ---
st.subheader("A) ACP Distribution by World Region")

fig_a = px.scatter(
    df, 
    x="PlotA_X", 
    y="PlotA_Y", 
    color="Region",
    hover_name="Country",
    text="Display_Label",
    # hover_data={"Region": False, "PlotA_X": False, "PlotA_Y": False, "Classification": True, "Score": ":.2f"}
    custom_data=["Region", "Classification", "Score"]
)
fig_a.update_traces(
    marker=dict(size=10, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')),
    textposition='top center',
    textfont=dict(size=10, color='Gray'),
    hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<br>%{customdata[1]}<br>Score: %{customdata[2]:.2f}<extra></extra>" 
)
fig_a.update_layout(
    xaxis_title="", 
    yaxis_title="",
    # Rebuild the categorical axes visually using our numerical mapping
    xaxis=dict(
        tickmode='array',
        tickvals=[1, 2, 3],
        ticktext=["Core AI Countries", "Semi-Periphery AI Countries", "Periphery AI Countries"],
        showgrid=False
    ),
    yaxis=dict(
        tickmode='array',
        tickvals=list(region_mapping.values()),
        ticktext=list(region_mapping.keys()),
        showgrid=True,
        zeroline=False
    )
)
fig_a.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.02, layer="below", line_width=0)
st.plotly_chart(fig_a, width='stretch')

st.divider()

# --- PLOT B: Political Types ---
st.subheader("B) ACP Distribution by Regime Type")
st.markdown("""
This graph presents the ACP segmentation based on V-Dem’s 2026 data. Countries are classified according to their latest regime typology, with dots sized according to their ACP rank/score and a minimum size applied for visibility. V-Dem’s original ranking table is available at https://www.v-dem.net.
                        
**Notes:** 
`+` indicates potential to belong to a higher category and `-` indicates potential for a lower category (eg. `EA+`)
""")

# Filter out empty KPIs-R
df_b = df.dropna(subset=["KPIs-R"]).copy()

fig_b = px.scatter(
    df_b, 
    x="PlotBC_X", 
    y="PlotBC_Y", 
    color="KPIs-R_base",
    size="Score",  # NEW: Size dots proportionally to Score
    hover_name="Country",
    # hover_data={"PlotBC_X": False, "PlotBC_Y": False, "Classification": True, "KPIs-R": True, "Score": ":.2f"},
    custom_data=["KPIs-R_base","KPIs-R", "Classification", "Score"],
    category_orders={"KPIs-R_base": [
        "LD - Liberal Democracy", 
        "ED - Electoral Democracy", 
        "EA - Electoral Autocracy", 
        "CA - Closed Autocracy"
    ]},
    color_discrete_sequence=px.colors.qualitative.Set3,
    size_max=25 # Adjust max bubble size for Plot B
)
fig_b.update_traces(
    marker=dict(opacity=0.8, line=dict(width=1, color='White')), 
    textposition='top center',
    hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<br>Raw class: %{customdata[1]}<br>Rank: %{customdata[2]}<br>Score: %{customdata[3]:.2f}<extra></extra>"
)
fig_b.update_layout(
    xaxis_title="", 
    yaxis_title="",
    xaxis=dict(
        tickmode='array',
        tickvals=[1, 2, 3],
        ticktext=["Core AI Countries", "Semi-Periphery AI Countries", "Periphery AI Countries"],
        showgrid=False
    ),
    yaxis=dict(visible=False),  # Hide Y axis, but layout now reflects Score vertically
    showlegend=True,
    height=600,
    legend_title_text="Political Type"
)
fig_b.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.02, layer="below", line_width=0)
st.plotly_chart(fig_b, width='stretch')

st.divider()

# --- PLOT C: Power Concentration ---
st.subheader("C) ACP & Political Power Concentration")
st.markdown("""
The Power Concentration score (0–100) is a composite measure based on portfolio consolidation, multi-role leadership, and executive power density across governments. Data comes from the CIA World Factbook Archive project and is static, with the latest update dated July 2, 2026. The original analysis and further information are available at https://worldfactbookarchive.org/analysis/world-leaders/concentration.

Dot size represents the Power Concentration score, while colors indicate geopolitical regions. Countries with zero or null values are assigned a baseline dot size for visibility.
""")

fig_c = px.scatter(
    df, 
    x="PlotBC_X", 
    y="PlotBC_Y", 
    size="KPIs-PC_plot", 
    color="Region",
    hover_name="Country",
    # hover_data={"PlotBC_X": False, "PlotBC_Y": False, "Classification": True, "Score": ":.2f"},
    custom_data=["Region", "Classification", "Score"],
    color_discrete_sequence=px.colors.qualitative.Set2,
    size_max=50 # Adjust max bubble size here
)
fig_c.update_traces(
    marker=dict(opacity=0.7, line=dict(width=1, color='White')),
    textposition='top center',
    hovertemplate="<b>%{hovertext}</b><br>Region: %{customdata[0]}<br>Rank: %{customdata[1]}<br>Score: %{customdata[2]:.2f}<extra></extra>"
)
fig_c.update_layout(
    xaxis_title="", 
    yaxis_title="",
    height=700,
    xaxis=dict(
        tickmode='array',
        tickvals=[1, 2, 3],
        ticktext=["Core AI Countries", "Semi-Periphery AI Countries", "Periphery AI Countries"],
        showgrid=False
    ),
    yaxis=dict(visible=False), # Hide Y axis
    showlegend=True,
    legend_title_text="Region"
)
fig_c.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.02, layer="below", line_width=0)
st.plotly_chart(fig_c, use_container_width=True)


st.divider()

# --- PLOT D: Energy Capacity (IRENA) ---
st.subheader("D) Energy Infrastructure & ACP Leapfrog Potential")
st.markdown("""
Power capacity serves as a critical proxy for compute readiness. As AI hardware becomes increasingly accessible, domestic energy grids will dictate which countries can scale hyperscale data centers and leapfrog in AI capabilities. 

Dot size represents Total Installed Capacity (GW), sourced from the [International Renewable Energy Agency](https://pxweb.irena.org/pxweb/en/IRENASTAT/IRENASTAT__Power%20Capacity%20and%20Generation/Country_ELECCAP_2026_H1_v-PX%201.px/) (IRENA / 2025 data). Colors map to political regime typologies to highlight the intersection of infrastructural capacity and governance models. Countries with zero or null capacity data are assigned a baseline dot size for visibility.
""")

# Create a plot-safe version of KPIs-E to handle nulls/zeros for bubble sizes
df["KPIs-E_plot"] = pd.to_numeric(df["KPIs-E"], errors="coerce").fillna(0)
df["KPIs-E_plot"] = df["KPIs-E_plot"].apply(lambda x: 1 if x <= 0 else x)

# Filter out empty regime types to keep the legend clean, matching Plot B
df_d = df.dropna(subset=["KPIs-R"]).copy()

fig_d = px.scatter(
    df_d, 
    x="PlotBC_X", 
    y="PlotBC_Y", 
    size="KPIs-E_plot", 
    color="KPIs-R_base",
    hover_name="Country",
    text="Display_Label",
    custom_data=["KPIs-E", "Region", "Classification", "Score"],
    category_orders={"KPIs-R_base": [
        "LD - Liberal Democracy", 
        "ED - Electoral Democracy", 
        "EA - Electoral Autocracy", 
        "CA - Closed Autocracy"
    ]},
    color_discrete_sequence=px.colors.qualitative.Set3,
    size_max=50 
)

fig_d.update_traces(
    marker=dict(opacity=0.7, line=dict(width=1, color='White')),
    textposition='top center',
    hovertemplate="<b>%{hovertext}</b><br>Total GW: %{customdata[0]}<br>Region: %{customdata[1]}<br>Rank: %{customdata[2]}<br>Score: %{customdata[3]:.2f}<extra></extra>"
)

fig_d.update_layout(
    xaxis_title="", 
    yaxis_title="",
    height=700,
    xaxis=dict(
        tickmode='array',
        tickvals=[1, 2, 3],
        ticktext=["Core AI Countries", "Semi-Periphery AI Countries", "Periphery AI Countries"],
        showgrid=False
    ),
    yaxis=dict(visible=False), 
    showlegend=True,
    legend_title_text="Political Type"
)

fig_d.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.02, layer="below", line_width=0)
st.plotly_chart(fig_d, use_container_width=True)


st.divider()

# --- PLOT E: Developer Density (GitHub) ---
st.subheader("E) ACP & Developer Density")
st.markdown("""
While energy dictates physical compute readiness, **Developer Density** serves as the proxy for "brain gain". It highlights which countries possess the sovereign talent to build, fine-tune, and maintain domestic AI models, and which are relegated to being consumer endpoints for Core APIs.

Dot size represents the number of GitHub developers, sourced from the [GitHub Innovation Graph Q1 2026](https://innovationgraph.github.com/economies). Colors indicate geopolitical regions. States with zero or null data are assigned a baseline dot size for visibility.
            
**Note:** This indicator reflects GitHub accounts, not the total number of developers within a country. GitHub's coverage may also underrepresent China, where access to the platform may be restricted. Gitee, a major Chinese counterpart, [reports more than 14 million registered members](https://gitee.com/about_us); however, the geographic composition of its user base is not publicly established, and the extent of overlap with GitHub accounts is likewise unknown.

""")

# Create a plot-safe version of KPIs-GH to handle nulls/zeros for bubble sizes
df["KPIs-GH_plot"] = pd.to_numeric(df["KPIs-GH"], errors="coerce").fillna(0)
df["KPIs-GH_plot"] = df["KPIs-GH_plot"].apply(lambda x: 1 if x <= 0 else x)

fig_e = px.scatter(
    df, 
    x="PlotBC_X", 
    y="PlotBC_Y", 
    size="KPIs-GH_plot", 
    color="Region",
    hover_name="Country",
    text="Display_Label",
    custom_data=["KPIs-GH", "Region", "Classification", "Score"],
    color_discrete_sequence=px.colors.qualitative.Pastel, # Unique color theme
    size_max=50 
)

fig_e.update_traces(
    marker=dict(opacity=0.7, line=dict(width=1, color='White')),
    textposition='top center',
    hovertemplate="<b>%{hovertext}</b><br>GitHub Devs: %{customdata[0]:,.0f}<br>Region: %{customdata[1]}<br>Rank: %{customdata[2]}<br>Score: %{customdata[3]:.2f}<extra></extra>"
)

fig_e.update_layout(
    xaxis_title="", 
    yaxis_title="",
    height=700,
    xaxis=dict(
        tickmode='array',
        tickvals=[1, 2, 3],
        ticktext=["Core AI Countries", "Semi-Periphery AI Countries", "Periphery AI Countries"],
        showgrid=False
    ),
    yaxis=dict(visible=False), 
    showlegend=True,
    legend_title_text="Region"
)

fig_e.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.02, layer="below", line_width=0)
st.plotly_chart(fig_e, use_container_width=True)

st.divider()

# --- PLOT F: ICT Services Exports (World Bank) ---
st.subheader("F) Unequal Exchange: ICT Services Exports")
st.markdown("""
In world-systems theory, the Core accumulates capital by exporting high-value manufactured goods, while the Periphery provides raw materials. In the AI economy, **ICT Services Exports** works as the ledger for this dynamic, isolating countries that act as sovereign technology 'makers' extracting capital versus those trapped as digital 'takers' bleeding capital to participate.

Dot size represents ICT services exports in USD, sourced from the [World Bank](https://data.worldbank.org/indicator/BX.GSR.CCIS.CD?most_recent_year_desc=false). Colors indicate geopolitical regions. Countries with zero or null data are assigned a baseline dot size for visibility. Records reflect the most recent year available in the World Bank archives (mostly from 2023-2025).
            
Note: Ireland's ICT export figures are artificially inflated because US tech giants book global revenue through Irish subsidiaries to exploit its low corporate tax rate, distortion known as "[Leprechaun economics](https://en.wikipedia.org/wiki/Leprechaun_economics)."
""")

# Create a plot-safe version of KPIs-ICT to handle nulls/zeros for bubble sizes
# NEW: Strip currency symbols and commas before converting to numbers
cleaned_ict = df["KPIs-ICT"].astype(str).str.replace(r'[\$,]', '', regex=True)
df["KPIs-ICT_plot"] = pd.to_numeric(cleaned_ict, errors="coerce").fillna(0)
df["KPIs-ICT_plot"] = df["KPIs-ICT_plot"].apply(lambda x: 1 if x <= 0 else x)

fig_f = px.scatter(
    df, 
    x="PlotBC_X", 
    y="PlotBC_Y", 
    size="KPIs-ICT_plot", 
    color="Region",
    hover_name="Country",
    text="Display_Label",
    custom_data=["KPIs-ICT", "Region", "Classification", "Score"],
    color_discrete_sequence=px.colors.qualitative.Bold, # Unique color theme
    size_max=50 
)

fig_f.update_traces(
    marker=dict(opacity=0.7, line=dict(width=1, color='White')),
    textposition='top center',
    hovertemplate="<b>%{hovertext}</b><br>ICT Exports (USD): %{customdata[0]}<br>Region: %{customdata[1]}<br>Rank: %{customdata[2]}<br>Score: %{customdata[3]:.2f}<extra></extra>"
)

fig_f.update_layout(
    xaxis_title="", 
    yaxis_title="",
    height=700,
    xaxis=dict(
        tickmode='array',
        tickvals=[1, 2, 3],
        ticktext=["Core AI Countries", "Semi-Periphery AI Countries", "Periphery AI Countries"],
        showgrid=False
    ),
    yaxis=dict(visible=False), 
    showlegend=True,
    legend_title_text="Region"
)

fig_f.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.02, layer="below", line_width=0)
st.plotly_chart(fig_f, use_container_width=True)