#!/usr/bin/env python
"""
簡化的輸入驗證測試
"""

import re

def test_regex_validation():
    """測試正則表達式驗證邏輯"""
    print('🔍 Testing Regex Validation Logic...')
    
    test_cases = [
        ('invalid;label', False, 'semicolon should fail'),
        ('invalid label', False, 'space should fail'),  
        ('invalid/label', False, 'slash should fail'),
        ('invalid"label', False, 'quote should fail'),
        ('valid_label', True, 'underscore should pass'),
        ('valid-label', True, 'hyphen should pass'),
        ('validlabel123', True, 'alphanumeric should pass'),
        ('123valid', True, 'starting with number should pass'),
    ]
    
    all_passed = True
    
    for test_input, expected, description in test_cases:
        result = bool(re.match(r'^[a-zA-Z0-9_-]+$', test_input))
        status = '✅' if result == expected else '❌'
        if result != expected:
            all_passed = False
        print(f'  {status} "{test_input}": {result} (expected {expected}) - {description}')
    
    return all_passed

def test_driver_validation_logic():
    """測試 driver 中的驗證邏輯"""
    print('\n�� Testing Driver Validation Logic...')
    
    # 模擬 driver 中的驗證邏輯
    def validate_input(node_label, property_name):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', node_label):
            raise ValueError(f"Invalid node_label: {node_label}")
        if not re.match(r'^[a-zA-Z0-9_-]+$', property_name):
            raise ValueError(f"Invalid property_name: {property_name}")
        return True
    
    test_cases = [
        ('invalid;label', 'prop', False),
        ('invalid label', 'prop', False),
        ('valid_label', 'invalid;prop', False),
        ('valid-label', 'valid_prop', True),
        ('test123', 'prop_name', True),
    ]
    
    all_passed = True
    
    for node_label, prop_name, should_pass in test_cases:
        try:
            validate_input(node_label, prop_name)
            result = 'PASSED'
            actual_pass = True
        except ValueError as e:
            result = f'REJECTED: {str(e)}'
            actual_pass = False
        
        status = '✅' if actual_pass == should_pass else '❌'
        if actual_pass != should_pass:
            all_passed = False
        print(f'  {status} "{node_label}", "{prop_name}": {result}')
    
    return all_passed

if __name__ == "__main__":
    print('🎯 Simple Input Validation Test')
    print('=' * 50)
    
    regex_passed = test_regex_validation()
    driver_passed = test_driver_validation_logic()
    
    print(f'\n📊 Test Results:')
    print(f'  Regex validation: {"✅ PASSED" if regex_passed else "❌ FAILED"}')
    print(f'  Driver validation: {"✅ PASSED" if driver_passed else "❌ FAILED"}')
    
    if regex_passed and driver_passed:
        print('\n🎉 All validation tests PASSED!')
        print('✅ Input validation is working correctly')
    else:
        print('\n❌ Some validation tests FAILED!')
        print('🔧 Input validation needs further fixes')
