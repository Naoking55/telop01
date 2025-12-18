#!/usr/bin/env python3
"""
prtextstyleファイルから実際の色バイトを抽出して表示
"""

import sys
import re
import base64
import xml.etree.ElementTree as ET

MARKER = b'\x02\x00\x00\x00\x41\x61'

def analyze_prtextstyle_colors(prtextstyle_file):
    """prtextstyleファイルの色情報を解析"""
    print("="*60)
    print(f"prtextstyle色情報解析: {prtextstyle_file}")
    print("="*60)

    # ファイル全体を読み込み
    with open(prtextstyle_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # StartKeyframeValue エントリを抽出
    pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
    matches = re.findall(pattern, content, re.DOTALL)

    print(f"\n検出: {len(matches)} StartKeyframeValueエントリ\n")

    for i, b64_text in enumerate(matches, 1):
        # Base64デコード
        b64_clean = b64_text.replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        try:
            binary = base64.b64decode(b64_clean)

            # マーカーを探す
            marker_pos = binary.find(MARKER)

            if marker_pos == -1:
                print(f"エントリ {i:2d}: マーカーなし")
                continue

            # マーカーの前の3バイトを確認（最大で3バイト：R, G, B）
            # 実際には色構造によって1-3バイト
            bytes_before = []
            for j in range(1, 4):
                if marker_pos - j >= 0:
                    bytes_before.append(binary[marker_pos - j])

            bytes_before.reverse()  # 正しい順序に

            # 色バイトを推定
            if len(bytes_before) == 3:
                r, g, b = bytes_before
                structure = "R,G,B (3 bytes)"
            elif len(bytes_before) == 2:
                # 2バイトの場合、どれがskipされているか推定
                b1, b2 = bytes_before
                # とりあえず表示
                structure = "2 bytes"
                r, g, b = "?", b1, b2
            elif len(bytes_before) == 1:
                structure = "1 byte"
                r, g, b = "?", "?", bytes_before[0]
            else:
                structure = "No bytes"
                r, g, b = "?", "?", "?"

            print(f"エントリ {i:2d}: マーカー位置={marker_pos}, 前バイト={bytes_before}, 推定RGB({r}, {g}, {b})")

        except Exception as e:
            print(f"エントリ {i:2d}: デコードエラー - {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python3 analyze_prtextstyle_colors.py <prtextstyle_file>")
        sys.exit(1)

    analyze_prtextstyle_colors(sys.argv[1])
