#!/usr/bin/env python3
"""
完全一致テンプレート方式
Style 4 RGB(255, 174, 0) の G値だけを 0 に変更 → RGB(255, 0, 0)
"""

import sys
import re
import base64

def create_red_from_style4():
    """
    Style 4 (RGB(255, 174, 0)) をベースに赤 (RGB(255, 0, 0)) を作成
    174 → 0 に変更するだけ（1バイトのみ変更）
    """

    print("="*80)
    print("完全一致テンプレート方式：Style 4 → 赤")
    print("="*80)

    # 手動変換ファイルを読み込み
    with open('/tmp/10styles.prtextstyle', 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    # Style 4（4番目）を取得
    if len(matches) < 4:
        print("✗ Style 4 not found!")
        return

    match = matches[3]  # 0-indexed, so 3 = Style 4
    orig_b64 = match.group(2).replace('\n', '').replace(' ', '').replace('\t', '')
    orig_binary = base64.b64decode(orig_b64)

    print(f"\nStyle 4 (ベース):")
    print(f"  RGB(255, 174, 0)")
    print(f"  Binary size: {len(orig_binary)} bytes")

    # マーカーを探す
    marker = b'\x02\x00\x00\x00\x41\x61'
    marker_pos = orig_binary.find(marker)

    print(f"  Marker at: 0x{marker_pos:04x}")

    # 色バイトを確認
    color_bytes = orig_binary[marker_pos-2:marker_pos]
    print(f"  Color bytes: {list(color_bytes)}")
    print(f"  Expected: [174, 0] for RGB(255, 174, 0)")

    # 赤に変更: 174 → 0
    modified_binary = bytearray(orig_binary)
    modified_binary[marker_pos-2] = 0  # G: 174 → 0

    print(f"\n目標: RGB(255, 0, 0) 赤")
    print(f"  変更: G値 174 → 0")
    print(f"  新しい色バイト: [0, 0]")

    # Base64エンコード
    new_b64 = base64.b64encode(bytes(modified_binary)).decode('ascii')

    # ファイル内容を更新（Style 4だけ変更）
    new_content = content[:match.start(2)] + new_b64 + content[match.end(2):]

    # Style 4の名前を変更
    name_pattern = r'<Name>(\d+)</Name>'
    name_matches = list(re.finditer(name_pattern, new_content))
    if len(name_matches) >= 4:
        name_match = name_matches[3]  # Style 4
        new_content = (
            new_content[:name_match.start(1)] +
            'RED-EXACT-TEMPLATE' +
            new_content[name_match.end(1):]
        )

    # 保存
    output_path = '/home/user/telop01/test_RED_exact_template_style4.prtextstyle'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✓ テストファイル作成: {output_path}")
    print(f"\n【重要】このアプローチ:")
    print(f"  - Style 4 の構造を完全保持")
    print(f"  - G値のみ変更: 174 → 0")
    print(f"  - バイナリ長さ変更なし")
    print(f"  - パターンバイト変更なし")
    print(f"\nこれでも赤にならなければ、色情報が別の場所にも存在する可能性")
    print(f"\nPremiereでテストしてください！")

if __name__ == "__main__":
    create_red_from_style4()
