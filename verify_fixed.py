#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from debug_conversion import extract_binary_from_prtextstyle, check_fill_color, check_shadow_params

print("="*80)
print("Verifying FIXED conversion")
print("="*80)

# 元のテンプレート
binary_template = extract_binary_from_prtextstyle("prtextstyle/100 New Fonstyle.prtextstyle")
print(f"\nTemplate binary size: {len(binary_template)} bytes")
check_fill_color(binary_template, 0x01b8)

# 変換後
binary_converted = extract_binary_from_prtextstyle("test_fixed_conversion.prtextstyle")
print(f"\nConverted binary size: {len(binary_converted)} bytes")
check_fill_color(binary_converted, 0x01b8)
check_shadow_params(binary_converted)

# 比較
if binary_template == binary_converted:
    print("\n⚠️ WARNING: Binaries are IDENTICAL!")
else:
    diffs = []
    for i in range(min(len(binary_template), len(binary_converted))):
        if binary_template[i] != binary_converted[i]:
            diffs.append(i)
    
    print(f"\n✓ Binaries are DIFFERENT: {len(diffs)} bytes changed")
    print("\nFirst 20 changes:")
    for i in diffs[:20]:
        print(f"  0x{i:04x}: 0x{binary_template[i]:02x} → 0x{binary_converted[i]:02x}")
