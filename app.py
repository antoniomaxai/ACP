import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="ACP AI Nation Rankings", layout="wide")

# --- 1. DATA LOADING ---
@st.cache_data
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
st.sidebar.write("Set the percentage cutoffs for each tier.")

core_pct = st.sidebar.slider("Core (Top %)", min_value=1.0, max_value=20.0, value=4.5, step=0.1)
sp_pct = st.sidebar.slider("Semi-Periphery (Up to %)", min_value=5.0, max_value=50.0, value=18.0, step=0.1)

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
st.title("🌍 AI Nation Power Rankings")
st.markdown(f"**Total Nations Analyzed:** {N} | **Core:** {core_cutoff} | **Semi-Periphery:** {sp_cutoff - core_cutoff} | **Periphery:** {N - sp_cutoff}")

st.divider()

# --- PLOT A: Regions ---
st.subheader("A) Distribution by World Region")

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
        ticktext=["Core AI Nations", "Semi-Periphery AI Nations", "Periphery AI Nations"],
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
fig_a.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.05, layer="below", line_width=0)
st.plotly_chart(fig_a, width='stretch')

st.divider()

# --- PLOT B: Political Types ---
st.subheader("B) Distribution by Political Type")
st.markdown("""
**Legend:** 
**LD**: Liberal Democracy | **ED**: Electoral Democracy | **EA**: Electoral Autocracy | **CA**: Closed Autocracy  
*(**+** indicates potential to belong to a higher category, **-** indicates potential for a lower category)*
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
        ticktext=["Core AI Nations", "Semi-Periphery AI Nations", "Periphery AI Nations"],
        showgrid=False
    ),
    yaxis=dict(visible=False),  # Hide Y axis, but layout now reflects Score vertically
    showlegend=True,
    legend_title_text="Political Type"
)
fig_b.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.05, layer="below", line_width=0)
st.plotly_chart(fig_b, width='stretch')

st.divider()

# --- PLOT C: Power Concentration ---
st.subheader("C) Power Concentration by Region")
st.markdown("Bubble size represents the Power Concentration metric (`KPIs-PC`). Nations with 0/null values are assigned a baseline size for visibility.")

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
        ticktext=["Core AI Nations", "Semi-Periphery AI Nations", "Periphery AI Nations"],
        showgrid=False
    ),
    yaxis=dict(visible=False), # Hide Y axis
    showlegend=True,
    legend_title_text="Region"
)
fig_c.add_vrect(x0=1.5, x1=2.5, fillcolor="#FDFD96", opacity=0.05, layer="below", line_width=0)
st.plotly_chart(fig_c, use_container_width=True)
