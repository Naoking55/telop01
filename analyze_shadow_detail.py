#!/usr/bin/env python3
"""
シャドウパラメータの詳細解析
特定のオフセット周辺のデータを詳細に調べる
"""

import xml.etree.ElementTree as ET
import base64
import struct

def get_style_binary(filepath, style_name):
    """スタイルのバイナリデータを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for style_item in root.findall('.//StyleProjectItem'):
        name_elem = style_item.find('.//Name')
        if name_elem is not None and name_elem.text == style_name:
            component_ref_elem = style_item.find('.//Component[@ObjectRef]')
            component_ref = component_ref_elem.get('ObjectRef')
            vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
            first_param_ref = vfc.find(".//Param[@Index='0']")
            param_obj_ref = first_param_ref.get('ObjectRef')
            arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            return base64.b64decode(binary_elem.text.strip())
    return None

def dump_hex(binary, start, end):
    """16進数ダンプ"""
    for offset in range(start, end, 16):
        hex_part = ' '.join(f'{b:02x}' for b in binary[offset:min(offset+16, end)])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in binary[offset:min(offset+16, end)])
        print(f"  0x{offset:04x}: {hex_part:<48s} {ascii_part}")

def analyze_as_floats(binary, start, count):
    """float値として解析"""
    results = []
    for i in range(count):
        offset = start + i * 4
        if offset + 4 <= len(binary):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                results.append((offset, val))
            except:
                results.append((offset, None))
    return results

def analyze_shadow_region(binary, xy_offset, context=64):
    """シャドウオフセット周辺を詳細解析"""
    start = max(0, xy_offset - context)
    end = min(len(binary), xy_offset + context)

    print(f"\n{'='*80}")
    print(f"オフセット 0x{xy_offset:04x} 周辺の詳細解析 (±{context} bytes)")
    print(f"{'='*80}")

    # 16進ダンプ
    print("\n16進ダンプ:")
    dump_hex(binary, start, end)

    # X,Y値
    if xy_offset + 8 <= len(binary):
        x = struct.unpack('<f', binary[xy_offset:xy_offset+4])[0]
        y = struct.unpack('<f', binary[xy_offset+4:xy_offset+8])[0]
        print(f"\nシャドウX,Y @ 0x{xy_offset:04x}:")
        print(f"  X = {x:.2f}")
        print(f"  Y = {y:.2f}")

    # 前後のfloat値を解析
    print(f"\n前方のfloat値 (0x{start:04x} - 0x{xy_offset-4:04x}):")
    floats_before = analyze_as_floats(binary, start, (xy_offset - start) // 4)
    for offset, val in floats_before[-8:]:  # 最後の8個
        if val is not None:
            if -1000 < val < 1000:  # 妥当な範囲
                print(f"  0x{offset:04x}: {val:10.4f}")

    print(f"\n後方のfloat値 (0x{xy_offset+8:04x} - 0x{end-4:04x}):")
    floats_after = analyze_as_floats(binary, xy_offset + 8, (end - xy_offset - 8) // 4)
    for offset, val in floats_after[:8]:  # 最初の8個
        if val is not None:
            if -1000 < val < 1000:  # 妥当な範囲
                print(f"  0x{offset:04x}: {val:10.4f}")

    # ぼかし候補を探す（0-100の範囲）
    print("\nぼかし（Blur）候補（0-100の範囲）:")
    blur_candidates = []
    for offset, val in floats_before[-16:] + floats_after[:16]:
        if val is not None and 0 <= val <= 100:
            blur_candidates.append((offset, val))

    if blur_candidates:
        for offset, val in blur_candidates:
            distance = offset - xy_offset
            print(f"  0x{offset:04x} (距離: {distance:+4d}): {val:.2f}")
    else:
        print("  (候補なし)")

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"

    # Fontstyle_90を解析
    bin_90 = get_style_binary(filepath, "Fontstyle_90")

    if not bin_90:
        print("❌ Fontstyle_90の取得に失敗")
        return

    print("="*80)
    print("Fontstyle_90 のシャドウパラメータ詳細解析")
    print("="*80)
    print(f"サイズ: {len(bin_90)} bytes")

    # 注目すべきX,Yオフセット
    shadow_offsets = [
        (0x009c, "前回検出: X=0.00, Y=2.00"),
        (0x00a0, "新規検出: X=2.00, Y=2.00"),
        (0x020c, "前回検出: X=4.00, Y=20.00"),
        (0x0478, "前回検出: X=4.00, Y=11.00"),
    ]

    for xy_offset, description in shadow_offsets:
        print(f"\n\n{'#'*80}")
        print(f"# {description}")
        print(f"{'#'*80}")
        analyze_shadow_region(bin_90, xy_offset, context=48)

if __name__ == "__main__":
    main()
