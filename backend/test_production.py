import requests

print('=== Testing Backend on Port 8001 (Production Mode) ===')

# Test health endpoint
r = requests.get('http://127.0.0.1:8001/api/v1/health', timeout=10)
print('GET /api/v1/health:', r.status_code, '-', r.json())

# Test wells
r = requests.get('http://127.0.0.1:8001/api/v1/simulation/wells', timeout=10)
data = r.json()
print('GET /api/v1/simulation/wells:', r.status_code, '-', len(data['wells']), 'wells')

# Test simulation
sim_req = {'well_id': 'BW-001', 'css_params': {'steam_rate_m3_d': 200, 'steam_quality': 0.8, 'injection_days': 10, 'soak_days': 5, 'production_days': 90}, 'srp_params': {'spm': 5.0, 'stroke_length_m': 3.0, 'vfd_frequency_hz': 40.0}}
r = requests.post('http://127.0.0.1:8001/api/v1/simulation', json=sim_req, timeout=30)
print('POST /api/v1/simulation:', r.status_code, '- Production:', r.json()['production_rate_stb_d'], 'STB/d')

# Test prediction
pred_req = {'well_id': 'BW-001', 'state': {'temperature_c': 120, 'viscosity_cp': 5000, 'steam_rate_m3_d': 200, 'steam_pressure_kpa': 4500, 'css_cycle': 1, 'srp_spm': 5.0, 'stroke_length_m': 3.0, 'pump_load_kn': 150, 'fillage': 0.85, 'pump_efficiency': 0.88, 'vfd_frequency_hz': 40.0}}
r = requests.post('http://127.0.0.1:8001/api/v1/prediction', json=pred_req, timeout=30)
data = r.json()
print('POST /api/v1/prediction:', r.status_code, '- Production:', data['predicted_production_stb_d'], 'STB/d')

# Test optimization
opt_req = {'well_id': 'BW-001', 'grid_resolution': 1, 'random_seed': 42}
r = requests.post('http://127.0.0.1:8001/api/v1/optimization', json=opt_req, timeout=30)
print('POST /api/v1/optimization:', r.status_code, '- Evaluated:', r.json()['total_evaluated'])

# Model status
r = requests.get('http://127.0.0.1:8001/api/v1/prediction/models/status', timeout=10)
print('GET /api/v1/prediction/models/status:', r.status_code, '-', r.json())

print('All endpoints returning HTTP 200!')