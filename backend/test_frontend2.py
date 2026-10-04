import requests

print('=== Testing Frontend Build on Port 5176 ===')
r = requests.get('http://127.0.0.1:5176', timeout=10)
print('Status:', r.status_code)
print('Content-Type:', r.headers.get('content-type'))
print('HTML length:', len(r.text))
if 'THERMALIFT' in r.text:
    print('SUCCESS: Frontend loads THERMALIFT title')
if '<div id="root"></div>' in r.text:
    print('SUCCESS: React root div present')
if 'index-DDHhZkGh.js' in r.text:
    print('SUCCESS: Main JS bundle referenced')
if 'index-CxtrvALN.css' in r.text:
    print('SUCCESS: Main CSS bundle referenced')