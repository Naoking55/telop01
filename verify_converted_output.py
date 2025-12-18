#!/usr/bin/env python3
"""
変換結果の検証
CONVERTED_OUTPUT.prtextstyle と 10styles.prtextstyle を比較
"""

import re
import base64
import json

# 期待される色データ
with open('/tmp/prsl_complete_data.json', 'r') as f:
    expected_data = json.load(f)

# 変換結果を読み込み
with open('/home/user/telop01/CONVERTED_OUTPUT.prtextstyle', 'r') as f:
    converted_content = f.read()

# オリジナルを読み込み
with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    original_content = f.read()

# Base64エントリを抽出
pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
converted_matches = re.findall(pattern, converted_content, re.DOTALL)
original_matches = re.findall(pattern, original_content, re.DOTALL)

FILL_MARKER = b'\x02\x00\x00\x00\x41\x61'

print("="*80)
print("変換結果の検証")
print("="*80)

total_tests = 0
passed_tests = 0

for i in range(min(len(converted_matches), len(expected_data))):
    expected = expected_data[i]

    # 変換結果のバイナリ
    conv_b64 = converted_matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    conv_binary = base64.b64decode(conv_b64)

    # オリジナルのバイナリ
    orig_b64 = original_matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    orig_binary = base64.b64decode(orig_b64)

    print(f"\n{'='*80}")
    print(f"スタイル {i+1}: {expected['name']}")
    print('='*80)

    # 塗り色の検証
    fill = expected['fill']
    exp_r, exp_g, exp_b = fill['r'], fill['g'], fill['b']

    # 色構造
    stored = []
    if exp_r != 255:
        stored.append(('R', exp_r))
    if exp_g != 255:
        stored.append(('G', exp_g))
    if exp_b != 255:
        stored.append(('B', exp_b))

    # マーカー位置
    conv_marker_pos = conv_binary.find(FILL_MARKER)
    orig_marker_pos = orig_binary.find(FILL_MARKER)

    if conv_marker_pos >= len(stored) and orig_marker_pos >= len(stored):
        conv_color_bytes = [conv_binary[conv_marker_pos - len(stored) + j] for j in range(len(stored))]
        orig_color_bytes = [orig_binary[orig_marker_pos - len(stored) + j] for j in range(len(stored))]
        expected_bytes = [val for _, val in stored]

        print(f"\n塗り色: RGB({exp_r}, {exp_g}, {exp_b})")
        print(f"  期待:       {expected_bytes}")
        print(f"  変換結果:   {conv_color_bytes} {'✓' if conv_color_bytes == expected_bytes else '✗'}")
        print(f"  オリジナル: {orig_color_bytes} {'✓' if orig_color_bytes == expected_bytes else '✗'}")

        total_tests += 1
        if conv_color_bytes == expected_bytes:
            passed_tests += 1

    # シャドウぼかしの検証
    shadow = expected.get('shadow', {})
    if shadow.get('enabled'):
        import struct

        if len(conv_binary) > 0x009c + 4 and len(orig_binary) > 0x009c + 4:
            conv_blur = struct.unpack('<f', conv_binary[0x009c:0x00a0])[0]
            orig_blur = struct.unpack('<f', orig_binary[0x009c:0x00a0])[0]
            exp_blur = shadow['blur']

            print(f"\nシャドウぼかし:")
            print(f"  期待:       {exp_blur:.1f}")
            print(f"  変換結果:   {conv_blur:.1f} {'✓' if abs(conv_blur - exp_blur) < 0.1 else '✗'}")
            print(f"  オリジナル: {orig_blur:.1f} {'✓' if abs(orig_blur - exp_blur) < 0.1 else '✗'}")

            total_tests += 1
            if abs(conv_blur - exp_blur) < 0.1:
                passed_tests += 1

        # シャドウ色の検証（パターンベース）
        SHADOW_RGB_PATTERN = b'\x00\x00\x00\x00'

        conv_shadow_rgb = None
        for offset in range(len(conv_binary) - 7):
            if (conv_binary[offset:offset+4] == SHADOW_RGB_PATTERN and
                conv_binary[offset+7] == 0x01):
                conv_shadow_rgb = [conv_binary[offset+4], conv_binary[offset+5], conv_binary[offset+6]]
                break

        orig_shadow_rgb = None
        for offset in range(len(orig_binary) - 7):
            if (orig_binary[offset:offset+4] == SHADOW_RGB_PATTERN and
                orig_binary[offset+7] == 0x01):
                orig_shadow_rgb = [orig_binary[offset+4], orig_binary[offset+5], orig_binary[offset+6]]
                break

        exp_shadow_rgb = [shadow['r'], shadow['g'], shadow['b']]

        print(f"\nシャドウ色: RGB({shadow['r']}, {shadow['g']}, {shadow['b']})")
        print(f"  期待:       {exp_shadow_rgb}")
        if conv_shadow_rgb:
            print(f"  変換結果:   {conv_shadow_rgb} {'✓' if conv_shadow_rgb == exp_shadow_rgb else '✗'}")
        else:
            print(f"  変換結果:   パターン未検出 ✗")

        if orig_shadow_rgb:
            print(f"  オリジナル: {orig_shadow_rgb} {'✓' if orig_shadow_rgb == exp_shadow_rgb else '✗'}")
        else:
            print(f"  オリジナル: パターン未検出")

        total_tests += 1
        if conv_shadow_rgb == exp_shadow_rgb:
            passed_tests += 1

print(f"\n{'='*80}")
print("検証結果サマリー")
print('='*80)
print(f"合格: {passed_tests}/{total_tests} テスト")
print(f"成功率: {passed_tests/total_tests*100:.1f}%")
print('='*80)
