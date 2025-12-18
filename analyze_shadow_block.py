#!/usr/bin/env python3
"""
シャドウブロック (0x02dc - 0x06dc) の詳細解析
黒色RGBAとX,Yオフセットの位置関係を特定
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

def find_rgba_in_region(binary, start, end):
    """指定領域内のRGBA float色を検索"""
    colors = []

    for offset in range(start, min(end, len(binary) - 15), 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]):
                color_name = ''
                if abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1 and a > 0.01:
                    color_name = '黒'
                elif abs(b - 1.0) < 0.1 and abs(r) < 0.1 and abs(g) < 0.1 and a > 0.01:
                    color_name = '青'
                elif abs(r - 1.0) < 0.1 and abs(g - 1.0) < 0.1 and abs(b - 1.0) < 0.1 and a > 0.01:
                    color_name = '白'

                if color_name:
                    colors.append({
                        'offset': offset,
                        'r': r, 'g': g, 'b': b, 'a': a,
                        'name': color_name
                    })
        except:
            pass

    return colors

def find_xy_in_region(binary, start, end):
    """指定領域内のX,Yオフセットペアを検索"""
    xy_pairs = []

    for offset in range(start, min(end, len(binary) - 7), 4):
        try:
            x = struct.unpack('<f', binary[offset:offset+4])[0]
            y = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                    if abs(x) > 0.5 or abs(y) > 0.5:
                        xy_pairs.append({
                            'offset': offset,
                            'x': x,
                            'y': y
                        })
        except:
            pass

    return xy_pairs

def dump_hex(binary, start, end, highlight_offsets=None):
    """16進ダンプ（ハイライト付き）"""
    if highlight_offsets is None:
        highlight_offsets = set()

    for offset in range(start, end, 16):
        hex_bytes = []
        for i in range(16):
            pos = offset + i
            if pos >= end or pos >= len(binary):
                break
            byte = binary[pos]
            if pos in highlight_offsets:
                hex_bytes.append(f'\033[91m{byte:02x}\033[0m')  # 赤色
            else:
                hex_bytes.append(f'{byte:02x}')

        hex_str = ' '.join(hex_bytes)
        ascii_part = ''.join(chr(binary[offset+i]) if 32 <= binary[offset+i] < 127 and offset+i < len(binary) else '.' for i in range(min(16, end-offset, len(binary)-offset)))
        print(f"  0x{offset:04x}: {hex_str:<48s} {ascii_part}")

def analyze_shadow_structure(binary, shadow_block_start, shadow_block_end):
    """シャドウブロック内の構造を解析"""
    colors = find_rgba_in_region(binary, shadow_block_start, shadow_block_end)
    xy_pairs = find_xy_in_region(binary, shadow_block_start, shadow_block_end)

    print(f"\nシャドウブロック内の要素:")
    print(f"  黒色RGBA: {len(colors)} 箇所")
    print(f"  X,Yオフセット: {len(xy_pairs)} 箇所")
    print()

    # 各X,Yオフセットに対して最も近い黒色RGBAを見つける
    print("="*80)
    print("X,Yオフセットと最も近い黒色RGBAの関係")
    print("="*80)
    print()

    shadow_pairs = []

    for xy in xy_pairs:
        # 前後の黒色RGBAを探す
        nearby_colors = []
        for c in colors:
            distance = c['offset'] - xy['offset']
            if -200 <= distance <= 200:  # 200バイト以内
                nearby_colors.append((distance, c))

        nearby_colors.sort(key=lambda x: abs(x[0]))

        if nearby_colors:
            closest_distance, closest_color = nearby_colors[0]
            shadow_pairs.append({
                'xy_offset': xy['offset'],
                'x': xy['x'],
                'y': xy['y'],
                'color_offset': closest_color['offset'],
                'color_distance': closest_distance,
                'color': closest_color
            })

            print(f"📍 X,Y @ 0x{xy['offset']:04x}: X={xy['x']:5.1f}, Y={xy['y']:5.1f}")
            print(f"   最も近い黒色RGBA @ 0x{closest_color['offset']:04x} (距離: {closest_distance:+4d})")
            print(f"   色: RGBA({closest_color['r']:.2f}, {closest_color['g']:.2f}, {closest_color['b']:.2f}, {closest_color['a']:.2f})")

            # Blur候補
            for delta in [-12, -8, -4, 4, 8, 12]:
                blur_offset = xy['offset'] + delta
                if shadow_block_start <= blur_offset + 4 <= shadow_block_end:
                    try:
                        val = struct.unpack('<f', binary[blur_offset:blur_offset+4])[0]
                        if 0 <= val <= 100:
                            print(f"   Blur @ 0x{blur_offset:04x} (距離{delta:+3d}): {val:.1f}")
                    except:
                        pass
            print()

    # 距離パターンの統計
    print("="*80)
    print("シャドウ色とX,Yオフセットの距離パターン")
    print("="*80)
    print()

    distance_counts = {}
    for pair in shadow_pairs:
        dist = pair['color_distance']
        if dist not in distance_counts:
            distance_counts[dist] = 0
        distance_counts[dist] += 1

    print("距離の頻度:")
    for dist in sorted(distance_counts.keys(), key=lambda x: distance_counts[x], reverse=True):
        count = distance_counts[dist]
        print(f"  距離 {dist:+4d}: {count:2d} 回")

    return shadow_pairs, colors, xy_pairs

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"

    bin_90 = get_style_binary(filepath, "Fontstyle_90")

    if not bin_90:
        print("❌ Fontstyle_90の取得に失敗")
        return

    print("="*80)
    print("Fontstyle_90 シャドウブロック詳細解析")
    print("="*80)
    print(f"サイズ: {len(bin_90)} bytes")
    print()

    # シャドウブロックの範囲
    shadow_block_start = 0x02dc
    shadow_block_end = 0x06dc

    print(f"シャドウブロック: 0x{shadow_block_start:04x} - 0x{shadow_block_end:04x} ({shadow_block_end - shadow_block_start} bytes)")
    print()

    # 構造解析
    shadow_pairs, colors, xy_pairs = analyze_shadow_structure(bin_90, shadow_block_start, shadow_block_end)

    # 最も一般的な距離パターンを持つペアを詳細表示
    print()
    print("="*80)
    print("典型的なシャドウパラメータの構造例")
    print("="*80)
    print()

    if shadow_pairs:
        # 最初の3つを詳細表示
        for i, pair in enumerate(shadow_pairs[:3], 1):
            xy_offset = pair['xy_offset']
            color_offset = pair['color_offset']

            print(f"\n例{i}: シャドウパラメータセット")
            print(f"  X,Yオフセット: 0x{xy_offset:04x}")
            print(f"  シャドウ色:     0x{color_offset:04x}")
            print(f"  距離:           {pair['color_distance']:+4d} バイト")
            print()

            # この範囲の16進ダンプ
            dump_start = min(xy_offset, color_offset) - 32
            dump_end = max(xy_offset, color_offset) + 32

            # ハイライトするオフセット
            highlight = set()
            for j in range(16):
                highlight.add(color_offset + j)  # RGBA 16バイト
            for j in range(8):
                highlight.add(xy_offset + j)  # X,Y 8バイト

            print(f"  16進ダンプ (0x{dump_start:04x} - 0x{dump_end:04x}):")
            dump_hex(bin_90, dump_start, dump_end, highlight)

if __name__ == "__main__":
    main()
