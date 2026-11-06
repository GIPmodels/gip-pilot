import json
import torch
import numpy as np
import pandas as pd

# 1. Načtení exaktně vyřešeného master JSON exportu z Mathematiky
json_path = "gip_5node_export.json"
with open(json_path, "r") as f:
    data = json.load(f)

print(f"--- Načten systém: {data.get('system_name')} ---")
print(f"Base MVA: {data.get('base_MVA')}")

# 2. Rekonstrukce komplexní matice Ybus jako PyTorch tenzor
Ybus_real = np.array(data["Ybus_real"])
Ybus_imag = np.array(data["Ybus_imag"])
Ybus_tensor = torch.tensor(Ybus_real + 1j * Ybus_imag, dtype=torch.cfloat)
print(f"Komplexní matice Ybus převedena na tenzor, tvar: {Ybus_tensor.shape}")

# 3. Zpracování uzlových stavů (Nodes) a sestavení uzlové matice X
nodes_data = data["nodes"]
node_ids = [node["id"] for node in nodes_data]
node_mapping = {n_id: idx for idx, n_id in enumerate(node_ids)}

# Extrakce exaktních AC stavů spočtených v Mathematici (napětí, úhly, činný a jalový výkon)
node_features = []
for node in nodes_data:
    vm = node.get("vm_pu", 1.0)
    va = node.get("va_deg", 0.0)
    p = node.get("p_mw", 0.0)
    q = node.get("q_mvar", 0.0)
    node_features.append([vm, va, p, q])

x_tensor = torch.tensor(node_features, dtype=torch.float32)
print(f"Uzlová tenzorová matice X (vlastnosti uzlů): shape {x_tensor.shape}")

# 4. Zpracování topologie větví (Branches / Lines) pro PyTorch Geometric edge_index
edge_indices = []
edge_attributes = []

for branch in data["branches"]:
    u_idx = node_mapping[branch["from"]]
    v_idx = node_mapping[branch["to"]]
    
    # Bi-direkcionální propojení pro grafovou síť
    edge_indices.append([u_idx, v_idx])
    edge_indices.append([v_idx, u_idx])
    
    # Vlastnosti hrany: [délka, r, x, b]
    attr = [branch["length"], branch["r"], branch["x"], branch["b"]]
    edge_attributes.append(attr)
    edge_attributes.append(attr)

# Zpracování transformátorů jako speciálních hran
for trafo in data.get("transformers", []):
    # Pokud je nízkonapěťová strana 22kV svorka generátoru, ověříme její přítomnost v mapování
    lv_bus = trafo["lv_bus"]
    if lv_bus not in node_mapping:
        # Pokud generátorový uzel nebyl v hlavních 5 uzlech, registrujeme jej
        node_mapping[lv_bus] = len(node_ids)
        node_ids.append(lv_bus)
        # Přidáme jej i do uzlového tenzoru jako Slack / generátorový uzel
        x_tensor = torch.cat([x_tensor, torch.tensor([[1.00, 0.0, -900.0, 0.0]], dtype=torch.float32)], dim=0)

    hv_idx = node_mapping[trafo["hv_bus"]]
    lv_idx = node_mapping[lv_bus]
    
    edge_indices.append([hv_idx, lv_idx])
    edge_indices.append([lv_idx, hv_idx])
    
    # Vlastnosti transformátoru: ekvivalentní r, x odvozené z vk_percent
    vk = trafo["vk_percent"] / 100.0
    vkr = trafo["vkr_percent"] / 100.0
    trafo_attr = [0.0, vkr, vk, 0.0]  # [délka=0, r, x, b]
    edge_attributes.append(trafo_attr)
    edge_attributes.append(trafo_attr)

edge_index_tensor = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
edge_attr_tensor = torch.tensor(edge_attributes, dtype=torch.float32)

print(f"Grafová topologie - Edge Index shape: {edge_index_tensor.shape}")
print(f"Hraniční atributy - Edge Attr shape: {edge_attr_tensor.shape}")

# 5. Sestavení finálního PyTorch Geometric Data objektu
from torch_geometric.data import Data

gip_graph_data = Data(
    x=x_tensor,
    edge_index=edge_index_tensor,
    edge_attr=edge_attr_tensor,
    ybus=Ybus_tensor
)

print("\n--- Úspěšně sestaven deterministický GIP Graph Data objekt ---")
print(gip_graph_data)

# Uložení připravených tenzorů pro fázi trénování GNN/PINN
torch.save(gip_graph_data, "gip_5node_tensor_state.pt")
print("Tenzorový stav sítě uložen do souboru: gip_5node_tensor_state.pt")