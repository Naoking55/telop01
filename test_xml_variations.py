#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML構造のバリエーションテスト
"""

import base64
import struct

def build_tlv(tag: int, payload: bytes) -> bytes:
    return struct.pack("<HI", tag, len(payload)) + payload

def create_test_binary():
    """シンプルなテストバイナリを作成"""
    blob = b""

    # Font Name
    blob += build_tlv(0x0001, "Arial".encode("utf-8"))

    # Font Style
    blob += build_tlv(0x0002, struct.pack("<I", 0))

    # Font Size
    blob += build_tlv(0x0003, struct.pack("<f", 48.0))

    # Fill Color (赤)
    blob += build_tlv(0x0004, struct.pack("<ffff", 1.0, 0.0, 0.0, 1.0))

    return blob

binary = create_test_binary()
b64 = base64.b64encode(binary).decode("ascii")

print("=" * 70)
print("XML構造バリエーションテスト")
print("=" * 70)

# バリエーション1: 現在の形式
xml1 = f'''<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="1">
  <Styles>
    <Style>
      <Name>Test Style 1</Name>
      <BinaryData Encoding="base64">{b64}</BinaryData>
    </Style>
  </Styles>
</PremiereData>
'''

# バリエーション2: Version="3"
xml2 = f'''<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="3">
  <Styles>
    <Style>
      <Name>Test Style 2</Name>
      <BinaryData Encoding="base64">{b64}</BinaryData>
    </Style>
  </Styles>
</PremiereData>
'''

# バリエーション3: TextStyles
xml3 = f'''<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="1">
  <TextStyles>
    <TextStyle>
      <Name>Test Style 3</Name>
      <BinaryData Encoding="base64">{b64}</BinaryData>
    </TextStyle>
  </TextStyles>
</PremiereData>
'''

# バリエーション4: Version="3" + TextStyles
xml4 = f'''<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="3">
  <TextStyles>
    <TextStyle>
      <Name>Test Style 4</Name>
      <BinaryData Encoding="base64">{b64}</BinaryData>
    </TextStyle>
  </TextStyles>
</PremiereData>
'''

# 保存
files = [
    ("test_var1_version1_styles.prtextstyle", xml1),
    ("test_var2_version3_styles.prtextstyle", xml2),
    ("test_var3_version1_textstyles.prtextstyle", xml3),
    ("test_var4_version3_textstyles.prtextstyle", xml4),
]

for filename, content in files:
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 作成: {filename}")

print("\n" + "=" * 70)
print("テスト手順")
print("=" * 70)
print("""
Premiere Pro 2025 でテストしてください:

1. test_var1_version1_styles.prtextstyle
   → Version="1" + <Styles>

2. test_var2_version3_styles.prtextstyle
   → Version="3" + <Styles>

3. test_var3_version1_textstyles.prtextstyle
   → Version="1" + <TextStyles>

4. test_var4_version3_textstyles.prtextstyle
   → Version="3" + <TextStyles>

どれがリストに表示されるか教えてください！
""")

print("\nバイナリ内容:")
print(f"  サイズ: {len(binary)} bytes")
print(f"  Hex: {binary[:32].hex()}")
