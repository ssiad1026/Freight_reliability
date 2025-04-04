import streamlit as st
import numpy as np
import pandas as pd

# Streamlit app title
st.title("Freight Transport Reliability")

st.sidebar.title("Simulation Parameters")

# Capacities section
st.sidebar.subheader("Capacities")
cap_06_07 = st.sidebar.number_input("C06→C07 Capacity", 1, 100, 10)
cap_07_08 = st.sidebar.number_input("C07→C08 Capacity", 1, 100, 5)

# Type Reductions section (including C07 Node Reduction)
st.sidebar.subheader("Type Reductions")
reduction_E = st.sidebar.number_input("Type E Reduction", 0, 100, 5)
reduction_D = st.sidebar.number_input("Type D Reduction", 0, 100, 1)
reduction_B = st.sidebar.number_input("Type B Reduction", 0, 100, 1)
reduction_F = st.sidebar.number_input("Type F Reduction", 0, 100, 2)
c07_node_reduction = st.sidebar.number_input("C07 Node Reduction", 0, 100, 1)

# Other parameters
st.sidebar.subheader("Other Parameters")
critical_value = st.sidebar.number_input("Critical Delivery Threshold (C08)", 1, 100, 4)

# Failure probabilities
st.sidebar.subheader("Failure Probabilities")
type_E = st.sidebar.slider("Type E Failure", 0.0, 1.0, 0.05)
type_D = st.sidebar.slider("Type D Failure", 0.0, 1.0, 0.45)
type_B = st.sidebar.slider("Type B Failure", 0.0, 1.0, 0.1)
type_F = st.sidebar.slider("Type F Failure", 0.0, 1.0, 0.3)
type_C = st.sidebar.slider("C07 Node Failure", 0.0, 1.0, 0.05)

# Simulation settings
st.sidebar.subheader("Simulation Settings")
num_sim = st.sidebar.number_input("No. of Simulations", 100, 100000, 10000, step=1000)

# Possible states
c06_c07_states = [cap_06_07, cap_06_07 - reduction_D, cap_06_07 - reduction_E]
c07_node_states = [0, c07_node_reduction]
c07_c08_states = [cap_07_08, cap_07_08 - reduction_B, cap_07_08 - reduction_F]

# Display scenario table
scenarios = []
for c06_c07 in c06_c07_states:
    for c07_node in c07_node_states:
        effective_c06_c07 = max(c06_c07 - c07_node, 0)
        delivered_to_c07 = min(5, effective_c06_c07)
        for c07_c08 in c07_c08_states:
            delivered_to_c08 = min(c07_c08, max(effective_c06_c07 - delivered_to_c07, 0))
            fail = delivered_to_c08 < critical_value
            scenarios.append({
                "C06→C07": c06_c07,
                "C07 Node Reduction": c07_node,
                "Eff C06→C07": effective_c06_c07,
                "C07→C08": c07_c08,
                "C08 Delivered": delivered_to_c08,
                f"Fail (C08<{critical_value})": "❌" if fail else "✅"
            })

scenario_df = pd.DataFrame(scenarios)
scenario_df.index = scenario_df.index + 1  # Start index from 1
scenario_df.index.name = "No."

st.subheader("Possible Capacity Scenarios")
st.dataframe(scenario_df)

# Run Monte Carlo Simulation automatically
failures = []
delivered_quantities = []

for _ in range(int(num_sim)):
    E = np.random.rand() < type_E
    D = np.random.rand() < type_D
    B = np.random.rand() < type_B
    F = np.random.rand() < type_F
    C = np.random.rand() < type_C

    # Initial capacity C06→C07
    cap = cap_06_07
    if E:
        cap -= reduction_E
    elif D:
        cap -= reduction_D

    if C:
        cap -= c07_node_reduction

    cap = max(cap, 0)

    # Demand of C07 is 5
    delivered_to_C07 = min(5, cap)
    cap_remaining_for_C08 = max(cap - delivered_to_C07, 0)

    # Capacity C07→C08
    cap_07_08_eff = cap_07_08
    if F:
        cap_07_08_eff -= reduction_F
    elif B:
        cap_07_08_eff -= reduction_B

    cap_07_08_eff = max(cap_07_08_eff, 0)

    # Final capacity to C08
    delivered_to_C08 = min(cap_07_08_eff, cap_remaining_for_C08)

    failures.append(delivered_to_C08 < critical_value)
    delivered_quantities.append(delivered_to_C08)

failure_rate = np.mean(failures)

st.subheader("Simulation Result")
st.write(f"Probability of delivering less than {critical_value} units to C08: **{failure_rate:.2%}**")

# Visualization - Table with progress bars and percentages
result_counts = pd.Series(delivered_quantities).value_counts().sort_index()
total = sum(result_counts)
percentages = (result_counts / total) * 100

summary_df = pd.DataFrame({
    'Delivered Units': result_counts.index,
    'Probability (%)': percentages
})

st.subheader("Delivery Probability Table")
for i, row in summary_df.iterrows():
    progress = float(row['Probability (%)']) / 100
    bar_color = 'red' if row['Delivered Units'] < critical_value else 'white'
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"{int(row['Delivered Units'])} units:")
        st.progress(progress)
    with col2:
        st.markdown(f"<span style='color:{bar_color}'>{row['Probability (%)']:.1f}%</span>", unsafe_allow_html=True)

st.write(f"Total Failures: {sum(failures)} out of {num_sim}")
st.write("""
This app simulates the delivery of goods to City C08, considering possible failures in the transport line.
You can adjust the failure probabilities and run a Monte Carlo simulation.

Sam-Sadjad Siadat  
27683332
""")
