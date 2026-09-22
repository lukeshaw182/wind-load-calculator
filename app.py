import math
import streamlit as st

st.set_page_config(page_title="EN 1991-1-4 Wind Load Process Map", layout="centered")

# --- HEADER ---
st.markdown("### EN 1991-1-4 → EC3")
st.title("Wind Load Calculation Tool")
st.write("An interactive step-by-step walkthrough from site data to design wind force for structural design.")

with st.expander("📌 Project Data Sheet", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        job_name = st.text_input("Job Name", value="Temporary bracing frame, EGL1")
        location = st.text_input("Location", value="East Lothian (coastal)")
        z = st.number_input("Reference Height, z (m)", value=10.0, step=0.5)
    with col2:
        terrain_cat = st.selectbox(
            "Terrain Category",
            options=["0 (Sea/Coastal)", "I (Lakes/Flat)", "II (Open Country)", "III (Suburban/Forest)", "IV (Urban)"],
            index=2
        )
        altitude = st.number_input("Altitude, A (m AOD)", value=30.0, step=5.0)
        solidity = st.number_input("Solidity Ratio, phi (for lattice frame)", value=0.30, step=0.05)

# Terrain constants mapping (z0, zmin)
terrain_params = {
    "0 (Sea/Coastal)": (0.003, 1.0),
    "I (Lakes/Flat)": (0.01, 1.0),
    "II (Open Country)": (0.05, 2.0),
    "III (Suburban/Forest)": (0.30, 5.0),
    "IV (Urban)": (1.00, 10.0)
}
z0, zmin = terrain_params[terrain_cat]

# --- STAGE 2: Basic Wind Velocity ---
st.markdown("---")
st.subheader("Stage 2: Basic Wind Velocity ($v_b$)")
col_v1, col_v2 = st.columns(2)
with col_v1:
    vb_map = st.number_input("v_b,map (m/s) [Manual Map Input]", value=21.5, step=0.5)
with col_v2:
    c_season = st.number_input("c_season (Season factor)", value=1.0, step=0.05)
    c_dir = st.number_input("c_dir (Direction factor)", value=1.0, step=0.05)

c_alt = 1.0 + 0.001 * altitude
vb_0 = vb_map * c_alt
vb = c_dir * c_season * vb_0

st.latex(r"v_b = c_{\text{dir}} \cdot c_{\text{season}} \cdot v_{b,\text{map}} \cdot c_{\text{alt}}")
st.info(f"**Calculated Basic Wind Velocity ($v_b$):** `{vb:.2f} m/s` (where $c_{\text{alt}} = {c_alt:.3f}$)")

# --- STAGE 3: Wind Speed & Turbulence at Height z ---
st.markdown("---")
st.subheader("Stage 3: Wind Speed & Turbulence at Height z")

kr = 0.19 * (z0 / 0.05)**0.07
cr_z = kr * math.log(max(z, zmin) / z0)
co_z = 1.0  # Orography factor defaults to 1.0
vm_z = cr_z * co_z * vb
kl = 1.0
Iv_z = kl / (co_z * math.log(max(z, zmin) / z0))

st.latex(r"v_m(z) = c_r(z) \cdot c_o(z) \cdot v_b \quad | \quad I_v(z) = \frac{k_I}{c_o(z) \cdot \ln(z/z_0)}")
st.write(f"* Roughness Factor $k_r$: `{kr:.3f}`")
st.write(f"* Mean Velocity $v_m(z)$: `{vm_z:.2f} m/s`")
st.write(f"* Turbulence Intensity $I_v(z)$: `{Iv_z:.3f}`")

# --- STAGE 4: Peak Velocity Pressure ---
st.markdown("---")
st.subheader("Stage 4: Peak Velocity Pressure ($q_p(z)$)")

rho = 1.226  # UK air density kg/m³
qp_z = (1.0 + 7.0 * Iv_z) * 0.5 * rho * (vm_z**2)  # Pa

st.latex(r"q_p(z) = [1 + 7 \cdot I_v(z)] \cdot \frac{1}{2} \cdot \rho \cdot v_m(z)^2")
st.success(f"**Peak Velocity Pressure $q_p(z)$:** `{qp_z / 1000:.3f} kN/m²` (`{qp_z:.1f} Pa`)")

# --- STAGE 5 & 6: Force Calculation ---
st.markdown("---")
st.subheader("Stages 5 & 6: Structural Force ($F_w$)")

col_f1, col_f2 = st.columns(2)
with col_f1:
    cf = st.number_input("Force Coefficient (c_f)", value=1.6, step=0.1, help="From §7.11 for lattice structures based on solidity.")
    envelope_area = st.number_input("Total Envelope Area (m²)", value=60.0, step=5.0)
with col_f2:
    cscd = st.number_input("Structural Factor (c_s c_d)", value=1.0, step=0.05)

aref = solidity * envelope_area
fw = cscd * cf * (qp_z / 1000.0) * aref  # in kN

st.latex(r"F_w = c_s c_d \cdot c_f \cdot q_p(z_e) \cdot A_{\text{ref}}")
st.write(f"* Solid Reference Area ($A_{\text{ref}}$): `{aref:.1f} m²`")
st.warning(f"**Characteristic Wind Force ($F_w$):** `{fw:.2f} kN`")

# --- STAGE 7 & 8: Design Actions & EC3 Handover ---
st.markdown("---")
st.subheader("Stages 7 & 8: EN 1990 Combinations & EC3 Handover")

gamma_q = st.number_input("Partial Factor for Wind ($\gamma_Q$)", value=1.5, step=0.05)
fw_ed = gamma_q * fw

st.latex(r"F_{w,\text{Ed}} = \gamma_Q \cdot F_w")
st.success(f"**Design Wind Force ($F_{w,\text{Ed}}$):** `{fw_ed:.2f} kN`")
st.markdown("This design force now resolves into individual member axial/shear forces to feed directly into **EN 1993-1-1** member checks and **EN 1993-1-8** connection design.")
