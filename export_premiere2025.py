#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premiere Pro 2025 対応エクスポート関数（スタンドアロン版）
"""

import base64
import struct
import os

def build_tlv(tag: int, payload: bytes) -> bytes:
    """TLV (Tag-Length-Value) バイナリを構築"""
    return struct.pack("<HI", tag, len(payload)) + payload


def export_prtextstyle_premiere2025(style, filepath: str):
    """prtextstyle ファイルとしてエクスポート（Premiere 2025 float形式）"""

    # TLV構築
    blob = b""

    # Font Name
    blob += build_tlv(0x0001, style.font_family.encode("utf-8"))

    # Font Style
    flags = 0
    if hasattr(style, 'bold') and style.bold:
        flags |= 1
    if hasattr(style, 'italic') and style.italic:
        flags |= 2
    blob += build_tlv(0x0002, struct.pack("<I", flags))

    # Font Size
    blob += build_tlv(0x0003, struct.pack("<f", float(style.font_size)))

    # Fill
    if hasattr(style.fill, 'is_gradient') and style.fill.is_gradient():
        # グラデーション
        grad_payload = b""
        for stop in style.fill.gradient_stops:
            # Premiere 2025: 色をfloat (0.0-1.0) で出力
            stop_data = struct.pack("<ffffff",
                float(stop.position),
                float(stop.midpoint),
                stop.r / 255.0, stop.g / 255.0, stop.b / 255.0, stop.a / 255.0
            )
            stop_data += b"\x00" * (48 - len(stop_data))
            grad_payload += build_tlv(0x00F0, stop_data)

        grad_payload += build_tlv(0x000A, struct.pack("<f", float(style.fill.gradient_angle)))
        blob += build_tlv(0x0005, grad_payload)
    else:
        # 単色 - Premiere 2025: 色をfloat (0.0-1.0) で出力
        blob += build_tlv(0x0004, struct.pack("<ffff",
            style.fill.r / 255.0,
            style.fill.g / 255.0,
            style.fill.b / 255.0,
            style.fill.a / 255.0
        ))

    # Strokes
    if hasattr(style, 'strokes'):
        for stroke in style.strokes:
            # Premiere 2025: 色をfloat (0.0-1.0) で出力
            s_payload = struct.pack("<fffff",
                float(stroke.width),
                stroke.r / 255.0, stroke.g / 255.0, stroke.b / 255.0, stroke.a / 255.0
            )
            blob += build_tlv(0x0006, s_payload)

    # Shadow
    if hasattr(style, 'shadow') and style.shadow.enabled:
        # Premiere 2025: 色をfloat (0.0-1.0) で出力
        s_payload = struct.pack("<fffffff",
            float(style.shadow.offset_x),
            float(style.shadow.offset_y),
            float(style.shadow.blur),
            style.shadow.r / 255.0, style.shadow.g / 255.0, style.shadow.b / 255.0, style.shadow.a / 255.0
        )
        blob += build_tlv(0x0007, s_payload)

    # Base64エンコード
    b64 = base64.b64encode(blob).decode("ascii")

    # XML作成
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="1">
  <Styles>
    <Style>
      <Name>{style.name}</Name>
      <BinaryData Encoding="base64">{b64}</BinaryData>
    </Style>
  </Styles>
</PremiereData>
'''

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"✓ Exported: {os.path.basename(filepath)}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/home/user/telop01')

    from prsl_parser_stylelist import parse_prsl_stylelist

    print("=" * 70)
    print("Premiere Pro 2025 対応エクスポートテスト")
    print("=" * 70)

    test_file = "10styles.prsl"
    styles = parse_prsl_stylelist(test_file)
    print(f"\n✓ {len(styles)} スタイルを読み込み")

    if styles:
        style = styles[0]
        print(f"\nスタイル: {style.name}")
        print(f"  フォント: {style.font_family} ({style.font_size}pt)")
        print(f"  塗り色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")

        output_file = "test_premiere2025.prtextstyle"
        print(f"\nエクスポート中...")
        export_prtextstyle_premiere2025(style, output_file)

        import os
        print(f"ファイルサイズ: {os.path.getsize(output_file)} bytes")

        print("\n" + "=" * 70)
        print("バイナリ解析")
        print("=" * 70)
        import subprocess
        subprocess.run(["python3", "analyze_prtextstyle.py", output_file])
