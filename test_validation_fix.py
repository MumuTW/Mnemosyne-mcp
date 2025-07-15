#!/usr/bin/env python
"""
測試輸入驗證修復
"""

import sys
import os
import re

# 動態添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# 清除模組緩存
modules_to_clear = [
    'mnemosyne.drivers.falkordb_driver',
    'mnemosyne.interfaces.graph_store'
]
for module in modules_to_clear:
    if module in sys.modules:
        del sys.modules[module]

print('🔍 Testing Input Validation Fix...')

# 直接測試正則表達式
test_cases = [
    ('invalid;label', False),  # semicolon - should fail
    ('invalid label', False),  # space - should fail  
    ('valid_label', True),     # underscore - should pass
    ('valid-label', True),     # hyphen - should pass
    ('validlabel', True),      # alphanumeric - should pass
]

print('📋 Regex validation test:')
for test_input, expected in test_cases:
    result = bool(re.match(r'^[a-zA-Z0-9_-]+$', test_input))
    status = '✅' if result == expected else '❌'
    print(f'  {status} "{test_input}": {result} (expected {expected})')

# 測試實際的 FalkorDB driver
try:
    from mnemosyne.drivers.falkordb_driver import FalkorDBDriver
    from mnemosyne.interfaces.graph_store import ConnectionConfig
    
    config = ConnectionConfig('localhost', 6379, 'test')
    driver = FalkorDBDriver(config)
    
    print('\n�� Testing FalkorDB driver validation:')
    
    import asyncio
    async def test_driver_validation():
        for test_input, should_pass in test_cases:
            try:
                await driver.create_vector_index(test_input, 'valid_prop', 1536)
                result = 'PASSED'
            except ValueError as e:
                result = f'REJECTED: {e}'
            except Exception as e:
                result = f'OTHER_ERROR: {e}'
            
            expected_result = 'PASSED' if should_pass else 'REJECTED'
            status = '✅' if (should_pass and 'PASSED' in result) or (not should_pass and 'REJECTED' in result) else '❌'
            print(f'  {status} "{test_input}": {result}')
    
    asyncio.run(test_driver_validation())
    
except ImportError as e:
    print(f'❌ Import failed: {e}')

print('\n🎉 Validation test completed!')
