import requests
import time

print('=== Testing First POST /api/v1/prediction (should include startup training time) ===')
pred_req = {
    'well_id': 'BW-001',
    'state': {
        'temperature_c': 120,
        'viscosity_cp': 5000,
        'steam_rate_m3_d': 200,
        'steam_pressure_kpa': 4500,
        'css_cycle': 1,
        'srp_spm': 5.0,
        'stroke_length_m': 3.0,
        'pump_load_kn': 150,
        'fillage': 0.85,
        'pump_efficiency': 0.88,
        'vfd_frequency_hz': 40.0
    }
}

start = time.time()
try:
    r = requests.post('http://127.0.0.1:8000/api/v1/prediction', json=pred_req, timeout=60)
    elapsed = time.time() - start
    print('Status:', r.status_code)
    print('First prediction latency:', f'{elapsed:.2f}s')
    data = r.json()
    print('Predicted Production:', data.get('predicted_production_stb_d'))
    print('Disclaimer present:', 'disclaimer' in r.json())
except Exception as e:
    print('Error:', e)

print()
print('=== Testing Second POST /api/v1/prediction (should be fast) ===')
start = time.time()
try:
    r = requests.post('http://127.0.0.1:8000/api/v1/prediction', json=pred_req, timeout=60)
    elapsed = time.time() - start
    print('Status:', r.status_code)
    print('Second prediction latency:', f'{elapsed:.2f}s')
    data = r.json()
    print('Predicted Production:', data.get('predicted_production_stb_d'))
except Exception as e:
    print('Error:', e)

print()
print('=== Testing First POST /api/v1/optimization (should include startup if not trained) ===')
opt_req = {'well_id': 'BW-001', 'grid_resolution': 1, 'random_seed': 42}
start = time.time()
try:
    r = requests.post('http://127.0.0.1:8000/api/v1/optimization', json=opt_req, timeout=60)
    elapsed = time.time() - start
    print('Status:', r.status_code)
    print('First optimization latency:', f'{elapsed:.2f}s')
    data = r.json()
    print('Total evaluated:', data.get('total_evaluated'))
    print('Disclaimer present:', 'disclaimer' in r.json())
except Exception as e:
    print('Error:', e)

print()
print('=== Testing Second POST /api/v1/optimization ===')
start = time.time()
try:
    r = requests.post('http://127.0.0.1:8000/api/v1/optimization', json=opt_req, timeout=60)
    elapsed = time.time() - start
    print('Status:', r.status_code)
    print('Second optimization latency:', f'{elapsed:.2f}s')
    data = r.json()
    print('Total evaluated:', data.get('total_evaluated'))
except Exception as e:
    print('Error:', e)

print()
print('=== Health Check ===')
try:
    r = requests.get('http://127.0.0.1:8000/api/v1/health', timeout=10)
    print('Status:', r.status_code)
    print('Response:', r.json())
except Exception as e:
    print('Error:', e)