#!/usr/bin/env python3
"""
同じフォントで色だけ異なるスタイルを比較
バイト単位の差分を調査
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor

def compare_binaries_detailed(bin1, bin2, name1, name2, prsl1, prsl2):
    """2つのバイナリを詳細比較"""

    print(f"\n{'='*80}")
    print(f"Detailed Binary Comparison")
    print(f"  {name1}: RGB({prsl1.fill.r}, {prsl1.fill.g}, {prsl1.fill.b})")
    print(f"  {name2}: RGB({prsl2.fill.r}, {prsl2.fill.g}, {prsl2.fill.b})")
    print('='*80)

    print(f"\nBinary sizes:")
    print(f"  {name1}: {len(bin1)} bytes")
    print(f"  {name2}: {len(bin2)} bytes")

    if len(bin1) != len(bin2):
        print(f"\n✗ Different sizes! Size difference: {abs(len(bin1) - len(bin2))} bytes")
        print("  Cannot do simple byte-by-byte comparison")
        return

    print(f"\n✓ Same size! Proceeding with byte-by-byte comparison...")

    # バイト単位で比較
    differences = []
    for i in range(len(bin1)):
        if bin1[i] != bin2[i]:
            differences.append(i)

    print(f"\nFound {len(differences)} different bytes ({len(differences)/len(bin1)*100:.1f}%)")

    if len(differences) == 0:
        print("✓ Files are identical!")
        return

    # 差分のグループを見つける（連続した差分）
    groups = []
    if differences:
        current_group = [differences[0]]
        for i in range(1, len(differences)):
            if differences[i] == differences[i-1] + 1:
                current_group.append(differences[i])
            else:
                groups.append(current_group)
                current_group = [differences[i]]
        groups.append(current_group)

    print(f"\nDifferences grouped into {len(groups)} regions:")

    for idx, group in enumerate(groups[:20]):  # 最初の20グループまで表示
        start = group[0]
        end = group[-1]
        length = len(group)

        print(f"\n[Region {idx+1}] 0x{start:04x} - 0x{end:04x} ({length} bytes)")

        # その領域のバイトを表示
        display_len = min(length, 16)
        bytes1 = [bin1[start+i] for i in range(display_len)]
        bytes2 = [bin2[start+i] for i in range(display_len)]

        print(f"  {name1}: {' '.join(f'{b:02x}' for b in bytes1)}")
        print(f"  {name2}: {' '.join(f'{b:02x}' for b in bytes2)}")

        # 差分を解釈
        # RGB色の成分かチェック
        if any(b in [prsl1.fill.r, prsl1.fill.g, prsl1.fill.b] for b in bytes1):
            print(f"  → Contains color from {name1}!")
        if any(b in [prsl2.fill.r, prsl2.fill.g, prsl2.fill.b] for b in bytes2):
            print(f"  → Contains color from {name2}!")

    if len(groups) > 20:
        print(f"\n... and {len(groups) - 20} more regions")

    # 色成分が含まれる差分を特定
    print(f"\n{'='*80}")
    print("Color-related differences:")
    print('='*80)

    color_diffs = []
    for offset in differences:
        b1 = bin1[offset]
        b2 = bin2[offset]

        # Style 1の色成分をチェック
        is_color1 = b1 in [prsl1.fill.r, prsl1.fill.g, prsl1.fill.b]
        is_color2 = b2 in [prsl2.fill.r, prsl2.fill.g, prsl2.fill.b]

        if is_color1 or is_color2:
            color_diffs.append({
                'offset': offset,
                'byte1': b1,
                'byte2': b2,
                'is_color1': is_color1,
                'is_color2': is_color2
            })

    if color_diffs:
        print(f"\nFound {len(color_diffs)} color-related byte differences:")
        for diff in color_diffs[:20]:
            marker1 = "COLOR" if diff['is_color1'] else ""
            marker2 = "COLOR" if diff['is_color2'] else ""
            print(f"  0x{diff['offset']:04x}: {diff['byte1']:3d} ({marker1:5s}) → {diff['byte2']:3d} ({marker2:5s})")
    else:
        print("\n✗ No obvious color-related differences found!")

def find_similar_styles():
    """同じフォント・設定で色だけ異なるスタイルを見つける"""

    print("="*80)
    print("Finding styles with same font but different colors")
    print("="*80)

    # PRSL解析
    prsl_styles = parse_prsl("/tmp/10styles.prsl")

    # 手動変換prtextstyle解析
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    # フォント別にグループ化
    font_groups = {}
    for i, prsl_style in enumerate(prsl_styles):
        font = prsl_style.name.split()[0:3]  # フォント名の最初の部分
        font_key = ' '.join(font)

        if font_key not in font_groups:
            font_groups[font_key] = []

        font_groups[font_key].append({
            'index': i,
            'prsl': prsl_style,
            'prt_name': list(editor.styles.keys())[i],
            'prt_binary': editor.get_style_binary(list(editor.styles.keys())[i])
        })

    # 同じフォントで複数のスタイルがあるものを探す
    print(f"\nFont groups:")
    for font_key, styles in font_groups.items():
        if len(styles) > 1:
            print(f"\n{font_key}: {len(styles)} styles")
            for s in styles:
                print(f"  - RGB({s['prsl'].fill.r}, {s['prsl'].fill.g}, {s['prsl'].fill.b})")

    # 全スタイルをサイズでグループ化
    all_styles = []
    for i, prsl_style in enumerate(prsl_styles):
        prt_name = list(editor.styles.keys())[i]
        prt_binary = editor.get_style_binary(prt_name)
        all_styles.append({
            'index': i,
            'prsl': prsl_style,
            'prt_name': prt_name,
            'prt_binary': prt_binary,
            'size': len(prt_binary)
        })

    # サイズ別にグループ化
    size_groups = {}
    for s in all_styles:
        size = s['size']
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(s)

    print(f"\n{'='*80}")
    print("Styles grouped by binary size:")
    print('='*80)
    for size, styles in sorted(size_groups.items()):
        print(f"\n{size} bytes: {len(styles)} styles")
        for s in styles:
            print(f"  - Style {s['index']+1}: RGB({s['prsl'].fill.r}, {s['prsl'].fill.g}, {s['prsl'].fill.b})")

    # 同じサイズで複数あるグループを比較
    for size, styles in sorted(size_groups.items()):
        if len(styles) >= 2:
            print(f"\n{'='*80}")
            print(f"Comparing styles with same size ({size} bytes)")
            print('='*80)

            style1 = styles[0]
            style2 = styles[1]

            compare_binaries_detailed(
                style1['prt_binary'],
                style2['prt_binary'],
                f"Style {style1['index']+1}",
                f"Style {style2['index']+1}",
                style1['prsl'],
                style2['prsl']
            )

            # 最初の1ペアだけ比較
            break

if __name__ == "__main__":
    find_similar_styles()
