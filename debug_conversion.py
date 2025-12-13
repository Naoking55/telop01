#!/usr/bin/env python3
"""
変換されたファイルの詳細検証
PRSLのパラメータと変換後のprtextstyleを比較
"""

import sys
import base64
import struct
import xml.etree.ElementTree as ET

def extract_binary_from_prtextstyle(filepath):
    """prtextstyleファイルからバイナリを抽出"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for binary_elem in root.findall('.//StartKeyframeValue[@Encoding="base64"]'):
        if binary_elem.text:
            return base64.b64decode(binary_elem.text.strip())
    return None

def check_fill_color(binary, offset=0x0100):
    """Fill色を確認"""
    print(f"\n=== Fill Color Check (around 0x{offset:04x}) ===")

    for off in range(offset - 16, offset + 48, 4):
        if off + 16 > len(binary):
            break

        try:
            r = struct.unpack('<f', binary[off:off+4])[0]
            g = struct.unpack('<f', binary[off+4:off+8])[0]
            b = struct.unpack('<f', binary[off+8:off+12])[0]
            a = struct.unpack('<f', binary[off+12:off+16])[0]

            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]) and a > 0.01:
                rgb_255 = (int(r*255), int(g*255), int(b*255), int(a*255))
                print(f"  0x{off:04x}: RGBA({r:.3f}, {g:.3f}, {b:.3f}, {a:.3f}) = RGB{rgb_255}")
        except:
            pass

def check_shadow_params(binary, start=0x02dc):
    """Shadow パラメータを確認"""
    print(f"\n=== Shadow Parameters Check (from 0x{start:04x}) ===")

    if len(binary) <= start:
        print("  No shadow block (file too small)")
        return

    found = []
    for offset in range(start, min(start + 300, len(binary) - 7), 4):
        try:
            x = struct.unpack('<f', binary[offset:offset+4])[0]
            y = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                if abs(x) > 0.1 or abs(y) > 0.1:
                    found.append((offset, x, y))
        except:
            pass

    if found:
        print(f"  Found {len(found)} potential shadow X,Y pairs:")
        for offset, x, y in found[:5]:
            print(f"    0x{offset:04x}: X={x:.2f}, Y={y:.2f}")
    else:
        print("  No shadow X,Y pairs found")

def compare_files(prsl_file, converted_file, template_file):
    """PRSLと変換後のファイルとテンプレートを比較"""
    print("="*80)
    print(f"Comparing:")
    print(f"  PRSL: {prsl_file}")
    print(f"  Converted: {converted_file}")
    print(f"  Template: {template_file}")
    print("="*80)

    # PRSL解析
    from test_prsl_conversion import parse_prsl
    styles = parse_prsl(prsl_file)

    if not styles:
        print("ERROR: No styles found in PRSL")
        return

    style = styles[0]
    print(f"\n=== PRSL Style: {style.name} ===")
    print(f"Fill: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")
    print(f"  → Float: ({style.fill.r/255:.3f}, {style.fill.g/255:.3f}, {style.fill.b/255:.3f}, {style.fill.a/255:.3f})")

    if style.shadow.enabled:
        print(f"Shadow: Enabled")
        print(f"  Offset: ({style.shadow.offset_x:.2f}, {style.shadow.offset_y:.2f})")
        print(f"  Blur: {style.shadow.blur:.2f}")
    else:
        print(f"Shadow: Disabled")

    # 変換後のファイル確認
    print(f"\n{'='*80}")
    print(f"CONVERTED FILE: {converted_file}")
    print('='*80)

    binary_converted = extract_binary_from_prtextstyle(converted_file)
    if binary_converted:
        print(f"Binary size: {len(binary_converted)} bytes")
        check_fill_color(binary_converted)
        check_shadow_params(binary_converted)
    else:
        print("ERROR: Could not extract binary")

    # テンプレート確認
    print(f"\n{'='*80}")
    print(f"TEMPLATE FILE: {template_file}")
    print('='*80)

    binary_template = extract_binary_from_prtextstyle(template_file)
    if binary_template:
        print(f"Binary size: {len(binary_template)} bytes")
        check_fill_color(binary_template)
        check_shadow_params(binary_template)
    else:
        print("ERROR: Could not extract binary")

    # バイナリ比較
    if binary_converted and binary_template:
        print(f"\n{'='*80}")
        print(f"BINARY COMPARISON")
        print('='*80)

        if binary_converted == binary_template:
            print("⚠️  WARNING: Converted binary is IDENTICAL to template!")
            print("    → Parameters were NOT modified")
        else:
            # 差分を探す
            diffs = []
            for i in range(min(len(binary_converted), len(binary_template))):
                if binary_converted[i] != binary_template[i]:
                    diffs.append(i)

            print(f"✓ Binaries are DIFFERENT")
            print(f"  Differences found: {len(diffs)} bytes")

            if diffs:
                print(f"\n  First 10 difference locations:")
                for i in diffs[:10]:
                    print(f"    0x{i:04x}: {binary_template[i]:02x} → {binary_converted[i]:02x}")

if __name__ == "__main__":
    compare_files(
        "10styles.prsl",
        "converted_10styles/A-OTF_リュウミン_Pro_EH-KL_167.prtextstyle",
        "prtextstyle/100 New Fonstyle.prtextstyle"
    )
