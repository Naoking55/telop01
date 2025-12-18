#!/usr/bin/env python3
"""
グラデーション変換結果の検証
"""

import re
import base64
import struct

# 変換結果を読み込み
with open('/home/user/telop01/CONVERTED_OUTPUT.prtextstyle', 'r') as f:
    content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, content, re.DOTALL)

print("="*80)
print("グラデーション変換結果の検証")
print("="*80)

# スタイル8（グラデーション）
print("\n[スタイル8] 満天青空レストラン")
print("期待: RGB(253,255,0) → RGB(188,163,0)")
print()

b64 = matches[7].replace('\n', '').replace(' ', '').replace('\t', '')
binary = base64.b64decode(b64)

# RGBA floatブロックを探す（0x0190-0x0220）
print("検出されたRGBA floatブロック:")
for offset in range(0x0190, min(len(binary), 0x0220) - 15, 4):
    try:
        vals = struct.unpack('<ffff', binary[offset:offset+16])
        if all(0.0 <= v <= 1.0 for v in vals):
            r = int(vals[0] * 255)
            g = int(vals[1] * 255)
            b = int(vals[2] * 255)
            a = int(vals[3] * 255)
            print(f"  0x{offset:04x}: RGBA({r:3d}, {g:3d}, {b:3d}, {a:3d})")

            # 期待値チェック
            if (abs(r - 253) < 2 and abs(g - 255) < 2 and abs(b - 0) < 2):
                print(f"           ✓ 開始色に一致！")
            elif (abs(r - 188) < 2 and abs(g - 163) < 2 and abs(b - 0) < 2):
                print(f"           ✓ 終了色に一致！")
    except:
        pass

# スタイル10（グラデーション）
print("\n" + "="*80)
print("[スタイル10] A-OTF 新ゴ Pro U 145")
print("期待: RGB(255,244,161) → RGB(255,223,0)")
print()

b64 = matches[9].replace('\n', '').replace(' ', '').replace('\t', '')
binary = base64.b64decode(b64)

print("検出されたRGBA floatブロック:")
for offset in range(0x0190, min(len(binary), 0x0220) - 15, 4):
    try:
        vals = struct.unpack('<ffff', binary[offset:offset+16])
        if all(0.0 <= v <= 1.0 for v in vals):
            r = int(vals[0] * 255)
            g = int(vals[1] * 255)
            b = int(vals[2] * 255)
            a = int(vals[3] * 255)
            print(f"  0x{offset:04x}: RGBA({r:3d}, {g:3d}, {b:3d}, {a:3d})")

            # 期待値チェック
            if (abs(r - 255) < 2 and abs(g - 244) < 2 and abs(b - 161) < 2):
                print(f"           ✓ 開始色に一致！")
            elif (abs(r - 255) < 2 and abs(g - 223) < 2 and abs(b - 0) < 2):
                print(f"           ✓ 終了色に一致！")
    except:
        pass

print(f"\n{'='*80}")
