import streamlit as st
import numpy as np
import pandas as pd

# App Title
st.title("Freight Transport Reliability")

st.sidebar.title("Simulation Parameters")

# Capacities Section
st.sidebar.subheader("Capacities")
cap_06_07 = st.sidebar.number_input("C06→C07 Capacity", 1, 100, 10)
cap_07_08 = st.sidebar.number_input("C07→C08 Capacity", 1, 100, 5)

# Grouped Capacity Reductions and Corresponding Failure Probabilities
st.sidebar.subheader("Capacity Reductions & Failure Probabilities")

# For C06→C07 reductions
reduction_c06_c07_type1 = st.sidebar.number_input("C06→C07 Reduction Type1", 0, 100, 1)
p_c06_c07_type1 = st.sidebar.slider("P C06→C07 Type1", 0.0, 1.0, 0.2)

reduction_c06_c07_type2 = st.sidebar.number_input("C06→C07 Reduction Type2", 0, 100, 5)
p_c06_c07_type2 = st.sidebar.slider("P C06→C07 Type2", 0.0, 1.0, 0.15)

# For C07 node reduction (parametric value)
reduction_c07 = st.sidebar.number_input("C07 Node Reduction", 0, 100, 1)
p_c07 = st.sidebar.slider("P C07", 0.0, 1.0, 0.1)

# For C07→C08 reductions
reduction_c07_c08_type1 = st.sidebar.number_input("C07→C08 Reduction Type1", 0, 100, 1)
p_c07_c08_type1 = st.sidebar.slider("P C07→C08 Type1", 0.0, 1.0, 0.09)

reduction_c07_c08_type2 = st.sidebar.number_input("C07→C08 Reduction Type2", 0, 100, 2)
p_c07_c08_type2 = st.sidebar.slider("P C07→C08 Type2", 0.0, 1.0, 0.05)

# Other parameters and simulation settings
st.sidebar.subheader("Other Parameters")
critical_value = st.sidebar.number_input("Critical Delivery Threshold (C08)", 1, 100, 4)

st.sidebar.subheader("Simulation Settings")
num_sim = st.sidebar.number_input("No. of Simulations", 100, 100000, 10000, step=1000)

################################################################
# SCENARIO TABLE CONSTRUCTION
################################################################

# Possible states for C06→C07
c06_c07_states = [
    max(cap_06_07, 0),
    max(cap_06_07 - reduction_c06_c07_type1, 0),
    max(cap_06_07 - reduction_c06_c07_type2, 0)
]

# Whether C07 node fails or not
c07_failure_states = [False, True]

# Possible states for meltdown on C07→C08
c07_c08_states = [
    (0, 0),  # No meltdown
    (reduction_c07_c08_type1, -reduction_c07_c08_type1),
    (reduction_c07_c08_type2, -reduction_c07_c08_type2)
]

scenarios = []
for capacity_06_07_eff in c06_c07_states:
    for c07_fail in c07_failure_states:

        # C07 meltdown
        meltdown_c07 = reduction_c07 if c07_fail else 0
        node_red_display = -meltdown_c07

        for meltdown_c07_c08_val, c07_c08_display in c07_c08_states:
            # 1) Arrive at C07 => subtract meltdown_c07
            flow_to_C07 = max(capacity_06_07_eff - meltdown_c07, 0)

            # 2) C07 keeps up to 5
            c07_keeps = min(flow_to_C07, 5)

            # 3) Leftover for C08 before meltdown
            leftover_for_c08 = flow_to_C07 - c07_keeps

            # 4) Subtract meltdown from leftover
            leftover_for_c08 = max(leftover_for_c08 - meltdown_c07_c08_val, 0)

            # 5) Finally clamp by link capacity
            delivered_to_C08 = min(leftover_for_c08, cap_07_08)

            fail = (delivered_to_C08 < critical_value)

            scenarios.append({
                "C06→C07 (post-cap)": capacity_06_07_eff,
                "C07 Node Red.": node_red_display,
                "Arrive at C07": flow_to_C07,
                "C07→C08 Red.": c07_c08_display,
                "C08 Delivered": delivered_to_C08,
                f"Fail (C08<{critical_value})": "❌" if fail else "✅"
            })

scenario_df = pd.DataFrame(scenarios)
scenario_df.index = scenario_df.index + 1
scenario_df.index.name = "No."

# Reorder columns
scenario_df = scenario_df[
    [
        "C06→C07 (post-cap)",
        "C07 Node Red.",
        "Arrive at C07",
        "C07→C08 Red.",
        "C08 Delivered",
        f"Fail (C08<{critical_value})"
    ]
]

# Rename columns for narrower width (multi-line headers)
# Rename columns to shorter versions
scenario_df.rename(
    columns={
        "C06→C07 (post-cap)": "C06→C07",
        "C07 Node Red.":      "C07 Red.",
        "Arrive at C07":      "Arv C07",
        "C07→C08 Red.":       "C07→C08 Red.",
        "C08 Delivered":      "C08",
        f"Fail (C08<{critical_value})": f"Fail (C08<{critical_value})"
    },
    inplace=True
)


st.subheader("Possible Capacity Scenarios")
st.dataframe(scenario_df)

################################################################
# MONTE CARLO SIMULATION
################################################################

failures = []
delivered_quantities = []

for _ in range(int(num_sim)):
    # Random draws for disruptions
    r_c06_c07_type1 = np.random.rand() < p_c06_c07_type1
    r_c06_c07_type2 = np.random.rand() < p_c06_c07_type2
    r_c07           = np.random.rand() < p_c07
    r_c07_c08_type1 = np.random.rand() < p_c07_c08_type1
    r_c07_c08_type2 = np.random.rand() < p_c07_c08_type2

    # --- Effective C06→C07 capacity ---
    cap_06_07_eff = cap_06_07
    if r_c06_c07_type2:
        cap_06_07_eff -= reduction_c06_c07_type2
    elif r_c06_c07_type1:
        cap_06_07_eff -= reduction_c06_c07_type1
    cap_06_07_eff = max(cap_06_07_eff, 0)

    # --- Node meltdown (C07) if r_c07
    meltdown_c07 = reduction_c07 if r_c07 else 0

    # --- meltdown on C07→C08 ---
    meltdown_c07_c08 = 0
    if r_c07_c08_type2:
        meltdown_c07_c08 = reduction_c07_c08_type2
    elif r_c07_c08_type1:
        meltdown_c07_c08 = reduction_c07_c08_type1

    # 1) Arrive at C07 => subtract meltdown_c07
    flow_to_C07 = max(cap_06_07_eff - meltdown_c07, 0)

    # 2) C07 keeps up to 5
    c07_keeps = min(flow_to_C07, 5)

    # 3) leftover for C08
    leftover_for_c08 = flow_to_C07 - c07_keeps

    # 4) meltdown on leftover
    leftover_for_c08 = max(leftover_for_c08 - meltdown_c07_c08, 0)

    # 5) clamp by link capacity
    delivered_to_C08 = min(leftover_for_c08, cap_07_08)

    failures.append(delivered_to_C08 < critical_value)
    delivered_quantities.append(delivered_to_C08)

failure_rate = np.mean(failures)

st.subheader("Simulation Result")
# Final probabilities
failure_rate = np.mean(failures)
success_rate = 1 - failure_rate

col1, col2 = st.columns(2)
with col1:
    st.metric(f"Probability of < {critical_value} units", f"{failure_rate:.2%}")
with col2:
    st.metric(f"Probability of ≥ {critical_value} units", f"{success_rate:.2%}")

################################################################
# VISUALIZATION: Delivery Probability Table
################################################################

result_counts = pd.Series(delivered_quantities).value_counts().sort_index()
total = result_counts.sum()
percentages = (result_counts / total) * 100

summary_df = pd.DataFrame({
    'Delivered Units': result_counts.index,
    'Probability (%)': percentages
})

st.markdown("#### Delivery Probability Table")
for i, row in summary_df.iterrows():
    progress = float(row['Probability (%)']) / 100
    # Quick color-cue: red if below threshold, green otherwise
    bar_color = 'red' if row['Delivered Units'] < critical_value else 'green'
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"{int(row['Delivered Units'])} units:")
        st.progress(progress)
    with col2:
        st.markdown(
            f"<span style='color:{bar_color}'>{row['Probability (%)']:.1f}%</span>",
            unsafe_allow_html=True
        )

st.write(f"Total Failures: {sum(failures)} out of {num_sim}")

st.write("""
This app simulates the delivery of goods to City C08, accounting for node and link
“reductions” as direct subtractions from the flow, on top of always keeping 5 units
at C07. 

Sam-Sadjad Siadat  
27683332
""")
