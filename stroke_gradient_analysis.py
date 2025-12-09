#!/usr/bin/env python3
"""
Stroke色とグラデーションの解析
"""

import base64
import zlib
import xml.etree.ElementTree as ET


def extract_binary(file_path: str) -> bytes:
    """バイナリ抽出"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    for elem in root.iter():
        if elem.tag == 'StartKeyframeValue' and elem.get('Encoding') == 'base64':
            if elem.text:
                encoded = elem.text.strip()
                decoded = base64.b64decode(encoded)
                try:
                    return zlib.decompress(decoded)
                except:
                    return decoded
    return None


def find_rgb_pattern(data: bytes, r: int, g: int, b: int, name: str):
    """RGB値のパターンを検索"""
    pattern = bytes([r, g, b])
    matches = []

    for i in range(len(data) - 2):
        if data[i:i+3] == pattern:
            matches.append(i)

    print(f"\n{name} で RGB({r}, {g}, {b}) のパターン:")
    for offset in matches:
        # 前後16バイトを表示
        start = max(0, offset - 8)
        end = min(len(data), offset + 12)
        context = data[start:end]
        hex_str = " ".join(f"{b:02X}" for b in context)
        print(f"  0x{offset:04X}: {hex_str}")

        # RGBA候補
        if offset + 3 < len(data):
            rgba = data[offset:offset+4]
            r2, g2, b2, a = rgba
            print(f"         → RGBA({r2}, {g2}, {b2}, {a})")

    return matches


from pathlib import Path
import glob

print("="*80)
print("Stroke色の解析: 黄エッジ vs 水色エッジ")
print("="*80)

# globでファイルを取得
files = {p.name: str(p) for p in Path(".").glob("*.prtextstyle")}
print(f"見つかったファイル: {list(files.keys())}\n")

# 正確なファイル名を取得
yellow_file = [f for f in files.keys() if "黄" in f][0]
cyan_file = [f for f in files.keys() if "水" in f][0]

yellow_stroke = extract_binary(files[yellow_file])
cyan_stroke = extract_binary(files[cyan_file])

print(f"\n黄エッジサイズ: {len(yellow_stroke)} bytes")
print(f"水色エッジサイズ: {len(cyan_stroke)} bytes")

# 黄色: RGB(255, 255, 0) または類似
# 水色: RGB(0, 255, 255) または類似
# 白: RGB(255, 255, 255)

# まず白色を探す（両方に共通しているはず - Fill色）
print("\n" + "-"*80)
print("白色 RGB(255, 255, 255) を検索:")
print("-"*80)

find_rgb_pattern(yellow_stroke, 255, 255, 255, "黄エッジ")
find_rgb_pattern(cyan_stroke, 255, 255, 255, "水色エッジ")

# 黄色を探す
print("\n" + "-"*80)
print("黄色 RGB(255, 255, 0) を検索:")
print("-"*80)

find_rgb_pattern(yellow_stroke, 255, 255, 0, "黄エッジ")

# 水色を探す (シアン)
print("\n" + "-"*80)
print("水色(シアン) RGB(0, 255, 255) を検索:")
print("-"*80)

find_rgb_pattern(cyan_stroke, 0, 255, 255, "水色エッジ")

# 全体の差分
print("\n" + "="*80)
print("Strokeファイル間の差分")
print("="*80)

min_len = min(len(yellow_stroke), len(cyan_stroke))
diffs = []
for i in range(min_len):
    if yellow_stroke[i] != cyan_stroke[i]:
        diffs.append((i, yellow_stroke[i], cyan_stroke[i]))

print(f"\n差分バイト数: {len(diffs)}")
print("\n255を含む差分:")
for offset, y_byte, c_byte in diffs:
    if y_byte == 255 or c_byte == 255:
        print(f"  0x{offset:04X}: 黄={y_byte:3d}, 水={c_byte:3d}")

print("\n" + "="*80)
print("グラデーションの解析: 2色 vs 3色")
print("="*80)

# グラデーションファイルを取得
print(f"\nすべてのファイル: {list(files.keys())}")
grad_files = [f for f in files.keys() if "青白" in f]
print(f"青白を含むファイル: {grad_files}")

if len(grad_files) >= 2:
    grad2_file = [f for f in grad_files if "赤" not in f][0]
    grad3_file = [f for f in grad_files if "赤" in f][0]
else:
    print("\nグラデーションファイルが見つかりません")
    print(f"グラデーション候補: {grad_files}")
    import sys
    sys.exit(1)

grad2 = extract_binary(files[grad2_file])
grad3 = extract_binary(files[grad3_file])

print(f"\n2色グラデサイズ: {len(grad2)} bytes")
print(f"3色グラデサイズ: {len(grad3)} bytes")
print(f"サイズ差: {len(grad3) - len(grad2)} bytes")

# 青 RGB(0, 0, 255)
# 白 RGB(255, 255, 255)
# 赤 RGB(255, 0, 0)

print("\n" + "-"*80)
print("2色グラデで 青 RGB(0, 0, 255) を検索:")
print("-"*80)
grad2_blue = find_rgb_pattern(grad2, 0, 0, 255, "2色グラデ")

print("\n" + "-"*80)
print("2色グラデで 白 RGB(255, 255, 255) を検索:")
print("-"*80)
grad2_white = find_rgb_pattern(grad2, 255, 255, 255, "2色グラデ")

print("\n" + "-"*80)
print("3色グラデで 青 RGB(0, 0, 255) を検索:")
print("-"*80)
grad3_blue = find_rgb_pattern(grad3, 0, 0, 255, "3色グラデ")

print("\n" + "-"*80)
print("3色グラデで 白 RGB(255, 255, 255) を検索:")
print("-"*80)
grad3_white = find_rgb_pattern(grad3, 255, 255, 255, "3色グラデ")

print("\n" + "-"*80)
print("3色グラデで 赤 RGB(255, 0, 0) を検索:")
print("-"*80)
grad3_red = find_rgb_pattern(grad3, 255, 0, 0, "3色グラデ")

# グラデーションの差分解析
print("\n" + "="*80)
print("グラデーションファイル間の差分（最初の部分）")
print("="*80)

# 2色と3色の共通部分を比較
min_grad_len = min(len(grad2), len(grad3))
grad_diffs = []
for i in range(min_grad_len):
    if grad2[i] != grad3[i]:
        grad_diffs.append(i)

print(f"差分バイト数: {len(grad_diffs)}")
print(f"差分開始位置: 0x{grad_diffs[0]:04X} ({grad_diffs[0]})")
print()

# 最初の差分周辺を表示
if grad_diffs:
    first_diff = grad_diffs[0]
    print(f"最初の差分 0x{first_diff:04X} 周辺:")
    print("\n2色グラデ:")
    for i in range(max(0, first_diff-16), min(len(grad2), first_diff+48), 16):
        chunk = grad2[i:i+16]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        marker = " <--" if i <= first_diff < i+16 else ""
        print(f"  0x{i:04X}: {hex_str}{marker}")

    print("\n3色グラデ:")
    for i in range(max(0, first_diff-16), min(len(grad3), first_diff+48), 16):
        chunk = grad3[i:i+16]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        marker = " <--" if i <= first_diff < i+16 else ""
        print(f"  0x{i:04X}: {hex_str}{marker}")

print("\n" + "="*80)
print("まとめ")
print("="*80)
print("""
解析結果:
1. Fill色（単色）は RGB または RGBA として、0-255の範囲でuint8配列で格納
2. Stroke色も同様の形式と推測
3. グラデーションは複数のRGB/RGBA値を含む
4. ファイルサイズの違いは構造の違いを反映
   - サイズ差から、追加のGradientStopは約48バイト程度と推測

次のステップ:
- RGB/RGBAの正確な位置を特定するためのパターン解析
- FlatBuffer/Protobuf形式の構造解析
- オフセット対応表の作成
""")
