
import pandas as pd
import numpy as np
from scipy.optimize import ling prog
import streamlit as st
import xlsxwriter

# Sample Data
patient_data = pd.DataFrame({
    'Patient Group': ['A', 'B', 'C', 'D'],
    'Volume of Requests': [100, 150, 120, 80],
    'Lead Time': [5, 7, 6, 4]
})

provider_data = pd.DataFrame({
    'Provider': ['P1', 'P1', 'P2', 'P2', 'P3', 'P3', 'P4', 'P4'],
    'Subspecialty': ['Cardiology', 'Neurology', 'Neurology', 'Orthopedics', 'Orthopedics', 'Oncology', 'Oncology', 'Cardiology']
})

session_limits = pd.DataFrame({
    'Patient Group': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D'],
    'Provider': ['P1', 'P1', 'P2', 'P2', 'P3', 'P3', 'P4', 'P4'],
    'Subspecialty': ['Cardiology', 'Neurology', 'Neurology', 'Orthopedics', 'Orthopedics', 'Oncology', 'Oncology', 'Cardiology'],
    'Max Sessions': [10, 12, 15, 14, 12, 10, 8, 10],
    'Current Utilization': [8, 9, 12, 11, 10, 9, 6, 7],
    'Overbooked Sessions': [0, 0, 1, 0, 0, 0, 0, 0]
})

operational_data = pd.DataFrame({
    'Provider': ['P1', 'P1', 'P2', 'P2', 'P3', 'P3', 'P4', 'P4'],
    'Subspecialty': ['Cardiology', 'Neurology', 'Neurology', 'Orthopedics', 'Orthopedics', 'Oncology', 'Oncology', 'Cardiology'],
    'Operating Hours': [8, 7, 7, 6, 6, 8, 8, 7],
    'Downtime': [1, 2, 2, 1, 1, 1, 1, 2],
    'Support Staff': [2, 1, 1, 2, 2, 1, 1, 2]
})

historical_data = pd.DataFrame({
    'Patient Group': ['A', 'B', 'C', 'D'],
    'Appointment Volume': [120, 180, 150, 100],
    'No-Shows': [10, 15, 12, 8],
    'Cancellations': [5, 10, 8, 3],
    'Seasonality': ['High', 'High', 'Low', 'Low']
})

# Merge Data for Analysis
data = pd.merge(patient_data, session_limits, on='Patient Group')
data = pd.merge(data, provider_data, on=['Provider', 'Subspecialty'])
data = pd.merge(data, operational_data, on=['Provider', 'Subspecialty'])
data = pd.merge(data, historical_data, on='Patient Group')

# Streamlit App
st.title("Session Limit Control Panel")

# Display Data
st.subheader("Patient and Provider Data")
st.dataframe(data)

# Input for Session Limits
st.subheader("Adjust Session Limits")
patient_group = st.selectbox("Select Patient Group", data['Patient Group'].unique())
provider = st.selectbox("Select Provider", data['Provider'].unique())
subspecialty = st.selectbox("Select Subspecialty", data['Subspecialty'].unique())
new_session_limit = st.number_input("New Session Limit", min_value=0)

# Update session limits
if st.button("Update Session Limit"):
    session_limits.loc[(session_limits['Patient Group'] == patient_group) & 
                       (session_limits['Provider'] == provider) & 
                       (session_limits['Subspecialty'] == subspecialty), 'Max Sessions'] = new_session_limit
    st.success(f"Session limit for {patient_group} with {provider} ({subspecialty}) updated to {new_session_limit}")

# Display updated data
st.subheader("Updated Data")
st.dataframe(data)

# Input for Adding Providers
st.subheader("Add New Provider")
new_provider = st.text_input("New Provider Name")
new_subspecialty = st.selectbox("Subspecialty", ['Cardiology', 'Neurology', 'Orthopedics', 'Oncology'])
new_operating_hours = st.number_input("Operating Hours", min_value=0)
new_downtime = st.number_input("Downtime", min_value=0)
new_support_staff = st.number_input("Support Staff", min_value=0)

# Add new provider
if st.button("Add New Provider"):
    new_row = {
        'Provider': new_provider,
        'Subspecialty': new_subspecialty,
        'Operating Hours': new_operating_hours,
        'Downtime': new_downtime,
        'Support Staff': new_support_staff
    }
    operational_data = operational_data.append(new_row, ignore_index=True)
    st.success(f"New provider {new_provider} added successfully")

# Display updated data
st.subheader("Updated Data")
st.dataframe(data)

# Re-optimize the model
if st.button("Re-optimize"):
    # Define the objective function
    c = -data['Volume of Requests'].values  # Maximize volume of requests

    # Define the constraints
    A_eq = data[['Patient Group', 'Provider', 'Subspecialty']].pivot_table(index='Patient Group', columns=['Provider', 'Subspecialty'], aggfunc='size', fill_value=0).values
    b_eq = data['Max Sessions'].values

    A_ub = data[['Patient Group', 'Provider', 'Subspecialty']].pivot_table(index='Patient Group', columns=['Provider', 'Subspecialty'], aggfunc='size', fill_value=0).values
    b_ub = data['Operating Hours'].values - data['Downtime'].values

    # Define the bounds
    x_bounds = [(0, None) for _ in range(len(data))]

    # Solve the linear programming problem
    result = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=x_bounds, method='highs')

    # Extract the solution
    solution = result.x
    data['Optimized Sessions'] = solution
    st.success("Optimization performed successfully")
    st.dataframe(data)


