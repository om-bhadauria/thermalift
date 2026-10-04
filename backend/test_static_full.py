import requests
import sys

try:
    r = requests.get('http://127.0.0.1:5175', timeout=10)
    print('=== Static Server Test ===')
    print('Status:', r.status_code)
    print('Content-Type:', r.headers.get('content-type'))
    print('HTML length:', len(r.text))
    if 'THERMALIFT' in r.text:
        print('SUCCESS: Frontend loads THERMALIFT title')
    if 'Synthetic/Demo Data' in r.text:
        print('SUCCESS: Data policy badge present')
    if '<div id="root"></div>' in r.text:
        print('SUCCESS: React root div present')
    if 'index-DDHhZkGh.js' in r.text:
        print('SUCCESS: Main JS bundle referenced')
    if 'index-CxtrvALN.css' in r.text:
        print('SUCCESS: Main CSS bundle referenced')
    
    # Test JS bundle
    r = requests.get('http://127.0.0.1:5175/assets/index-DDHhZkGh.js', timeout=10)
    print()
    print('=== JS Bundle Test ===')
    print('Status:', r.status_code)
    print('Content-Type:', r.headers.get('content-type'))
    print('Length:', len(r.content))
    if 'THERMALIFT' in r.text:
        print('SUCCESS: JS bundle contains app code')
    
    # Test CSS bundle
    r = requests.get('http://127.0.0.1:5175/assets/index-CxtrvALN.css', timeout=10)
    print()
    print('=== CSS Bundle Test ===')
    print('Status:', r.status_code)
    print('Content-Type:', r.headers.get('content-type'))
    print('Length:', len(r.content))
    
except Exception as e:
    print('Test failed:', e)