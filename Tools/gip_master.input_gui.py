import json
import os
import streamlit as st

st.set_page_config(
    page_title="GIP - Grid Intelligent Platform", layout="wide"
)
st.title("GIP - Grid Intelligent Platform (Konfigurace sítě & DAE)")

# 1. Globální parametry sítě v bočním panelu
st.sidebar.header("1. Globální parametry sítě")
base_mva = st.sidebar.number_input("Base MVA", value=250.0, step=50.0)
frequency = st.sidebar.number_input("Frekvence [Hz]", value=50.0, step=0.5)

st.sidebar.markdown("---")

# TLAČÍTKO PRO EXPORT KONFIGURACE
st.sidebar.header("Export konfigurace")
if st.sidebar.button("💾 Vygenerovat gip_config.json", type="primary"):
  config_data = {
      "base_mva": base_mva,
      "frequency": frequency,
      "nodes": st.session_state.nodes_list,
      "branches": st.session_state.branches_list,
  }

  download_path = os.path.join(os.path.dirname(__file__), "gip_config.json")
  with open(download_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f, indent=4)

  st.sidebar.success(f"Uloženo do: {download_path}")

st.sidebar.markdown("---")
st.sidebar.header("2. Správa uzlů a zařízení")

# Inicializace stavu uzlů
if "nodes_list" not in st.session_state:
  st.session_state.nodes_list = [
      {
          "id": "B01_gen",
          "type": "Slack",
          "v": 1.0,
          "th": 0.0,
          "p": 0.0,
          "q": 0.0,
      },
      {
          "id": "B02",
          "type": "STATCOM",
          "v": 1.02,
          "th": 0.0,
          "p": 0.0,
          "q": 0.0,
      },
      {
          "id": "B03",
          "type": "PV_Inverter",
          "v": 1.01,
          "th": 0.0,
          "p": 50.0,
          "q": 0.0,
      },
      {
          "id": "B04",
          "type": "BESS",
          "v": 1.0,
          "th": 0.0,
          "p": 20.0,
          "q": 0.0,
      },
      {
          "id": "B05",
          "type": "EV_Charger",
          "v": 1.0,
          "th": 0.0,
          "p": -30.0,
          "q": -10.0,
      },
  ]

# Formulář pro přidání uzlu
with st.sidebar.form("add_node_form"):
  node_id = st.text_input("ID uzlu", value=f"B0{len(st.session_state.nodes_list)+1}")
  node_type = st.selectbox(
      "Typ zařízení / zátěže",
      [
          "Slack",
          "Generator",
          "PV_Inverter",
          "BESS",
          "Wind_Turbine",
          "EV_Charger",
          "Heat_Pump",
          "HVAC_Load",
          "STATCOM",
          "PQ",
      ],
  )

  v_val = st.number_input("Napětí V [p.u.]", value=1.0, step=0.01)
  p_val = st.number_input("Činný výkon P [MW]", value=0.0, step=5.0)
  q_val = st.number_input("Jalový výkon Q [MVAr]", value=0.0, step=5.0)

  extra_params = {}
  if node_type in ["BESS", "Wind_Turbine", "PV_Inverter"]:
    extra_params["H"] = st.slider("Virtuální setrvačnost H [s]", 1.0, 10.0, 3.5)
    extra_params["t_reg"] = st.number_input(
        "Časová konstanta regulace T_reg [s]", value=0.05, step=0.01
    )

  if node_type in ["EV_Charger", "Heat_Pump", "HVAC_Load"]:
    extra_params["duty_cycle"] = st.slider(
        "Faktor zatížení / Střída [p.u.]", 0.1, 1.0, 0.8
    )

  submitted_node = st.form_submit_button("➕ Přidat uzel do sítě")
  if submitted_node:
    new_node = {
        "id": node_id,
        "type": node_type,
        "v": v_val,
        "th": 0.0,
        "p": p_val / base_mva,
        "q": q_val / base_mva,
    }
    new_node.update(extra_params)
    st.session_state.nodes_list.append(new_node)
    st.rerun()

# --- 3. SPRÁVA VĚTVÍ A LINEK ---
st.sidebar.markdown("---")
st.sidebar.header("3. Správa větví a linek sítě")

if "branches_list" not in st.session_state:
  st.session_state.branches_list = [
      {
          "id": "L1",
          "from": "B01_gen",
          "to": "B02",
          "length": 20.0,
          "r": 0.08,
          "x": 0.40,
          "b": 2.8,
      },
      {
          "id": "L2",
          "from": "B02",
          "to": "B03",
          "length": 25.0,
          "r": 0.08,
          "x": 0.40,
          "b": 2.8,
      },
      {
          "id": "L3",
          "from": "B03",
          "to": "B04",
          "length": 15.0,
          "r": 0.08,
          "x": 0.40,
          "b": 2.8,
      },
      {
          "id": "L4",
          "from": "B04",
          "to": "B05",
          "length": 30.0,
          "r": 0.08,
          "x": 0.40,
          "b": 3.8,
          "ratio": 1.0,
          "phase_deg": 0.0,
      },
  ]

node_ids = [node["id"] for node in st.session_state.nodes_list]

with st.sidebar.form("add_branch_form"):
  branch_id = st.text_input(
      "ID větve / linky", value=f"L{len(st.session_state.branches_list)+1}"
  )

  if len(node_ids) >= 2:
    from_node = st.selectbox("Počáteční uzel (from)", node_ids, index=0)
    to_node = st.selectbox(
        "Koncový uzel (to)",
        node_ids,
        index=1 if len(node_ids) > 1 else 0,
    )
  else:
    st.warning("Nejprve přidejte alespoň 2 uzly!")
    from_node, to_node = "", ""

  length_val = st.number_input("Délka vedení [km]", value=20.0, step=5.0)
  r_val = st.number_input(
      "Měrný odpor r [pu/km]", value=0.08, step=0.01, format="%.3f"
  )
  x_val = st.number_input(
      "Měrná reaktance x [pu/km]", value=0.40, step=0.01, format="%.3f"
  )
  b_val = st.number_input(
      "Kapacitní susceptance b [µS/km]", value=2.8, step=0.1
  )

  is_pst = st.checkbox("Obsahuje PST / Transformátor?", value=False)
  ratio_val = 1.0
  phase_val = 0.0
  if is_pst:
    ratio_val = st.number_input(
        "Transformační poměr (ratio)", value=1.0, step=0.05
    )
    phase_val = st.number_input(
        "Fázový posun PST [deg]", value=0.0, step=1.0
    )

  submitted_branch = st.form_submit_button("➕ Přidat větev do sítě")
  if submitted_branch and from_node and to_node:
    new_branch = {
        "id": branch_id,
        "from": from_node,
        "to": to_node,
        "length": length_val,
        "r": r_val,
        "x": x_val,
        "b": b_val,
    }
    if is_pst:
      new_branch["ratio"] = ratio_val
      new_branch["phase_deg"] = phase_val

    st.session_state.branches_list.append(new_branch)
    st.rerun()

# --- HLAVNÍ PLOCHA APLIKACE ---
st.subheader("📋 Přehled uzlů v konfigurované síti")
if st.session_state.nodes_list:
  st.dataframe(st.session_state.nodes_list, use_container_width=True)

st.subheader("⚡ Přehled větví a linek sítě")
if st.session_state.branches_list:
  st.dataframe(st.session_state.branches_list, use_container_width=True)

with st.expander("Zobrazit kompletní surový JSON výstup pro Mathematica"):
  st.json({
      "base_mva": base_mva,
      "frequency": frequency,
      "nodes": st.session_state.nodes_list,
      "branches": st.session_state.branches_list,
  })