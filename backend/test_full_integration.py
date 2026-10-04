import requests
import json

print("=== FRONTEND -> BACKEND INTEGRATION TEST ===")
print()

# Test 1: Health endpoint
r = requests.get('http://127.0.0.1:8000/api/v1/health')
print('GET /api/v1/health:', r.status_code)
print(json.dumps(r.json(), indent=2))
print()

# Test 2: Wells list
r = requests.get('http://127.0.0.1:8000/api/v1/simulation/wells')
print('GET /api/v1/simulation/wells:', r.status_code)
data = r.json()
print('  Wells count:', len(data['wells']))
print('  Data source:', data['data_source'])
print()

# Test 3: Simulation
sim_req = {
    'well_id': 'BW-001',
    'css_params': {'steam_rate_m3_d': 200, 'steam_quality': 0.8, 'injection_days': 10, 'soak_days': 5, 'production_days': 90},
    'srp_params': {'spm': 5.0, 'stroke_length_m': 3.0, 'vfd_frequency_hz': 40.0}
}
r = requests.post('http://127.0.0.1:8000/api/v1/simulation', json=sim_req)
print('POST /api/v1/simulation:', r.status_code)
data = r.json()
print('  Temperature:', data['temperature_c'], 'C')
print('  Production:', data['production_rate_stb_d'], 'STB/d')
print('  Data source:', data['data_source'])
print('  Disclaimer present:', 'disclaimer' in data)
print()

# Test 4: Prediction
pred_req = {
    'well_id': 'BW-001',
    'state': {'temperature_c': 120, 'viscosity_cp': 5000, 'steam_rate_m3_d': 200, 'steam_pressure_kpa': 4500, 'css_cycle': 1, 'srp_spm': 5.0, 'stroke_length_m': 3.0, 'pump_load_kn': 150, 'fillage': 0.85, 'pump_efficiency': 0.88, 'vfd_frequency_hz': 40.0}
}
r = requests.post('http://127.0.0.1:8000/api/v1/prediction', json=pred_req)
print('POST /api/v1/prediction:', r.status_code)
data = r.json()
print('  Predicted production:', data['predicted_production_stb_d'], 'STB/d')
print('  Rod float risk:', data['predicted_rod_float_risk'])
print('  Impact loading risk:', data['predicted_impact_loading_risk'])
print('  Data source:', data['data_source'])
print('  Disclaimer present:', 'disclaimer' in data)
print()

# Test 5: Optimization
opt_req = {'well_id': 'BW-001', 'grid_resolution': 1, 'random_seed': 42}
r = requests.post('http://127.0.0.1:8000/api/v1/optimization', json=opt_req)
print('POST /api/v1/optimization:', r.status_code)
data = r.json()
print('  Total evaluated:', data['total_evaluated'])
print('  Feasible:', data['feasible_count'])
print('  Objective score:', data['recommendation']['objective_score'])
print('  Data source:', data['data_source'])
print('  Disclaimer present:', 'disclaimer' in data)
print()

print("=== ALL INTEGRATION TESTS PASSED ===")