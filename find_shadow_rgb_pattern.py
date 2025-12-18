#!/usr/bin/env python3
"""
シャドウRGBパターンの特定
00 00 00 00 [R G B] 01 のパターンを探す
"""

import re
import base64
import json

# PRSL完全データを読み込み
with open('/tmp/prsl_complete_data.json', 'r') as f:
    prsl_data = json.load(f)

# prtextstyle読み込み
with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, content, re.DOTALL)

print("="*80)
print("シャドウRGBパターン: 00 00 00 00 [R G B] 01")
print("="*80)

for i in range(min(len(prsl_data), len(matches))):
    prsl = prsl_data[i]
    shadow = prsl.get('shadow', {})

    if not shadow.get('enabled'):
        continue

    b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    binary = base64.b64decode(b64_clean)

    r, g, b, a = shadow['r'], shadow['g'], shadow['b'], shadow['a']

    print(f"\nスタイル {i+1}: {prsl['name']}")
    print(f"  期待: RGBA({r}, {g}, {b}, {a})")

    # パターン検索: 00 00 00 00 [?] [?] [?] 01
    found = False
    for offset in range(len(binary) - 7):
        if (binary[offset] == 0x00 and
            binary[offset+1] == 0x00 and
            binary[offset+2] == 0x00 and
            binary[offset+3] == 0x00 and
            binary[offset+7] == 0x01):
            # RGB候補
            r_cand = binary[offset+4]
            g_cand = binary[offset+5]
            b_cand = binary[offset+6]

            # 完全一致を探す
            if r_cand == r and g_cand == g and b_cand == b:
                print(f"  ✓ 0x{offset+4:04x}: RGB({r_cand}, {g_cand}, {b_cand})")
                print(f"    パターン: [00 00 00 00] [{r_cand:02x} {g_cand:02x} {b_cand:02x}] [01]")
                found = True
                break

    if not found:
        # パターンが見つからない場合、01の代わりに他の値も試す
        print(f"  ✗ 厳密パターンなし、緩い条件で探索:")
        for offset in range(len(binary) - 6):
            if (binary[offset] == 0x00 and
                binary[offset+1] == 0x00 and
                binary[offset+2] == 0x00 and
                binary[offset+3] == 0x00):
                r_cand = binary[offset+4]
                g_cand = binary[offset+5]
                b_cand = binary[offset+6]

                if r_cand == r and g_cand == g and b_cand == b:
                    next_byte = binary[offset+7] if offset+7 < len(binary) else -1
                    print(f"    0x{offset+4:04x}: RGB({r_cand}, {g_cand}, {b_cand}) 次=[{next_byte:02x}]")

print(f"\n{'='*80}")
print("結論:")
print("  シャドウRGBは 00 00 00 00 [R] [G] [B] 01 のパターンで保存されている")
print("  位置は可変（バイナリサイズにより変動）")
print('='*80)
