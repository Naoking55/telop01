#!/usr/bin/env python3
"""
GUI v2.1 の動作をテスト
"""

import sys
import os
sys.path.insert(0, '/home/user/telop01')

print("="*60)
print("GUI v2.1 動作テスト")
print("="*60)

# 1. PRSLファイルの存在確認
prsl_file = "/tmp/10styles.prsl"
template_file = "/tmp/10styles.prtextstyle"

print(f"\n[1] ファイル存在確認:")
print(f"  PRSL: {prsl_file}")
print(f"    存在: {os.path.exists(prsl_file)}")
if os.path.exists(prsl_file):
    print(f"    サイズ: {os.path.getsize(prsl_file)} bytes")

print(f"  Template: {template_file}")
print(f"    存在: {os.path.exists(template_file)}")
if os.path.exists(template_file):
    size = os.path.getsize(template_file)
    print(f"    サイズ: {size} bytes ({size/1024:.1f} KB)")

# 2. GUI版の関数をインポート
print(f"\n[2] GUI関数のインポート:")
try:
    from prsl_to_prtextstyle_gui import get_color_structure, replace_color_bytes_in_binary, MARKER
    print(f"  ✓ インポート成功")
    print(f"  MARKER: {MARKER.hex()}")
except Exception as e:
    print(f"  ✗ インポートエラー: {e}")
    sys.exit(1)

# 3. テンプレートにマーカーがあるか確認
print(f"\n[3] テンプレート内のマーカー検索:")
try:
    with open(template_file, 'rb') as f:
        content = f.read()

    marker_count = content.count(MARKER)
    print(f"  マーカー出現回数: {marker_count}")

    if marker_count > 0:
        # 最初のマーカー位置
        pos = content.find(MARKER)
        print(f"  最初のマーカー位置: 0x{pos:04x}")
except Exception as e:
    print(f"  ✗ エラー: {e}")

# 4. base64エンコードされたバイナリ内のマーカー確認
print(f"\n[4] StartKeyframeValue内のマーカー確認:")
try:
    import re
    import base64

    with open(template_file, 'r', encoding='utf-8') as f:
        template_text = f.read()

    pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
    matches = re.findall(pattern, template_text, re.DOTALL)

    print(f"  StartKeyframeValue エントリ数: {len(matches)}")

    if len(matches) > 0:
        # 最初のエントリをチェック
        b64 = matches[0].replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        binary = base64.b64decode(b64)

        has_marker = MARKER in binary
        print(f"  最初のエントリにマーカー: {has_marker}")

        if has_marker:
            marker_pos = binary.find(MARKER)
            print(f"    マーカー位置: 0x{marker_pos:04x}")
            print(f"    バイナリサイズ: {len(binary)} bytes")

except Exception as e:
    print(f"  ✗ エラー: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "="*60)
print("テスト完了")
print("="*60)
