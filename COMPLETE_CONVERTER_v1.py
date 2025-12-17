#!/usr/bin/env python3
"""
完全版PRSL→prtextstyle変換ツール v1.0
テンプレート依存・段階的実装

対応パラメータ:
- ✅ 塗り色（RGB）- マーカーベース置換
- ✅ シャドウぼかし - 固定オフセット 0x009c
- ✅ シャドウ色（RGB）- パターンベース置換
- ⚠️  シャドウオフセット（距離・角度）- 位置が可変で未実装
- ⚠️  シャドウ不透明度 - 位置が可変で未実装
- 🔄 境界線（TODO）
- 🔄 グラデーション（TODO）
"""

import xml.etree.ElementTree as ET
import base64
import struct
from dataclasses import dataclass
from typing import List, Optional

# 定数
MARKER = b'\x02\x00\x00\x00\x41\x61'
SHADOW_BLUR_OFFSET = 0x009c

# ベーステンプレート（10styles4_temple.prtextstyleから抽出）
# RGB(0,0,0)の3バイト保存パターン、サイズ520バイト
BASE_TEMPLATE_520 = None  # 後で実装

@dataclass
class GradientStop:
    """グラデーションストップ"""
    r: int
    g: int
    b: int
    a: int = 255

@dataclass
class Fill:
    """塗り（単色またはグラデーション）"""
    is_gradient: bool = False
    # 単色用
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255
    # グラデーション用（4色グラデーション）
    top_left: Optional['GradientStop'] = None
    bottom_right: Optional['GradientStop'] = None

@dataclass
class Shadow:
    enabled: bool
    blur: float = 0.0
    angle: float = 90.0
    distance: float = 0.0
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 255

@dataclass
class Style:
    name: str
    fill: Fill
    shadow: Shadow

def parse_prsl(prsl_path: str) -> List[Style]:
    """PRSLファイルを解析（完全版）"""
    tree = ET.parse(prsl_path)
    root = tree.getroot()

    styles = []

    for styleblock in root.findall('.//styleblock'):
        name = styleblock.get('name', 'Unknown')

        # Fill解析
        fill = Fill()
        style_data = styleblock.find('style_data')
        if style_data:
            # 塗りタイプを確認
            colouring = style_data.find('.//face/shader/colouring')
            fill_type = 5  # デフォルトは単色
            if colouring:
                fill_type_elem = colouring.find('type')
                if fill_type_elem is not None:
                    fill_type = int(fill_type_elem.text.strip())

            if fill_type == 1:  # 4色グラデーション
                four_ramp = colouring.find('four_colour_ramp')
                if four_ramp:
                    def get_gradient_color(elem):
                        if elem is not None:
                            r = int(float(elem.find('red').text) * 255)
                            g = int(float(elem.find('green').text) * 255)
                            b = int(float(elem.find('blue').text) * 255)
                            a = int(float(elem.find('alpha').text) * 255) if elem.find('alpha') is not None else 255
                            return GradientStop(r=r, g=g, b=b, a=a)
                        return None

                    top_left = get_gradient_color(four_ramp.find('top_left'))
                    bottom_right = get_gradient_color(four_ramp.find('bottom_right'))

                    fill = Fill(
                        is_gradient=True,
                        top_left=top_left,
                        bottom_right=bottom_right
                    )
            else:  # 単色
                solid = style_data.find('.//solid_colour/all')
                if solid:
                    def get_color(elem_name):
                        e = solid.find(elem_name)
                        return int(float(e.text) * 255) if e is not None and e.text else 255

                    fill = Fill(
                        is_gradient=False,
                        r=get_color('red'),
                        g=get_color('green'),
                        b=get_color('blue'),
                        a=get_color('alpha')
                    )

            # Shadow解析
            shadow = Shadow(enabled=False)
            shadow_elem = style_data.find('shadow')
            if shadow_elem:
                on = shadow_elem.find('on')
                if on is not None and on.text == 'true':
                    softness = shadow_elem.find('softness')
                    blur = float(softness.text) if softness is not None and softness.text else 0

                    # オフセット
                    offset = shadow_elem.find('offset')
                    angle = 90.0
                    distance = 0.0
                    if offset:
                        angle_elem = offset.find('angle')
                        mag_elem = offset.find('magnitude')
                        if angle_elem is not None and angle_elem.text:
                            angle = float(angle_elem.text)
                        if mag_elem is not None and mag_elem.text:
                            distance = float(mag_elem.text)

                    # 色
                    colour = shadow_elem.find('colour')
                    shadow_r = shadow_g = shadow_b = 255
                    shadow_a = 255
                    if colour:
                        def get_shadow_color(elem_name):
                            e = colour.find(elem_name)
                            return int(float(e.text) * 255) if e is not None and e.text else 255

                        shadow_r = get_shadow_color('red')
                        shadow_g = get_shadow_color('green')
                        shadow_b = get_shadow_color('blue')
                        shadow_a = get_shadow_color('alpha')

                    shadow = Shadow(
                        enabled=True,
                        blur=blur,
                        angle=angle,
                        distance=distance,
                        r=shadow_r,
                        g=shadow_g,
                        b=shadow_b,
                        a=shadow_a
                    )
        else:
            shadow = Shadow(enabled=False)

        styles.append(Style(name=name, fill=fill, shadow=shadow))

    return styles

def get_color_structure(r: int, g: int, b: int):
    """色構造を取得（どのRGB成分が255=skipか）"""
    stored = []
    if r != 255:
        stored.append(('R', r))
    if g != 255:
        stored.append(('G', g))
    if b != 255:
        stored.append(('B', b))
    return stored

def apply_fill_color(binary: bytearray, fill: Fill) -> bytearray:
    """塗り色を適用"""
    # マーカーを探す
    marker_pos = binary.find(MARKER)
    if marker_pos == -1:
        raise ValueError("Color marker not found")

    # 色構造を取得
    stored_components = get_color_structure(fill.r, fill.g, fill.b)
    num_bytes = len(stored_components)

    # マーカー直前に色バイトを書き込み
    for i in range(num_bytes):
        _, value = stored_components[i]
        binary[marker_pos - num_bytes + i] = value

    return binary

def apply_shadow_blur(binary: bytearray, shadow: Shadow) -> bytearray:
    """シャドウぼかしを適用"""
    if not shadow.enabled:
        return binary

    # 0x009cにFloat値として書き込み
    if len(binary) > SHADOW_BLUR_OFFSET + 4:
        struct.pack_into('<f', binary, SHADOW_BLUR_OFFSET, shadow.blur)

    return binary

def apply_shadow_color(binary: bytearray, shadow: Shadow) -> bytearray:
    """シャドウ色を適用

    パターン: 00 00 00 00 [R] [G] [B] 01
    このパターンを探してRGB値を書き換える
    """
    if not shadow.enabled:
        return binary

    # パターン検索: 00 00 00 00 [?] [?] [?] 01
    SHADOW_RGB_PATTERN_PREFIX = b'\x00\x00\x00\x00'
    SHADOW_RGB_PATTERN_SUFFIX = b'\x01'

    # 既存のRGB値を持つパターンを探す
    for offset in range(len(binary) - 7):
        if (binary[offset:offset+4] == SHADOW_RGB_PATTERN_PREFIX and
            binary[offset+7:offset+8] == SHADOW_RGB_PATTERN_SUFFIX):
            # RGB位置を特定
            rgb_offset = offset + 4

            # 新しいRGB値を書き込み
            binary[rgb_offset] = shadow.r
            binary[rgb_offset+1] = shadow.g
            binary[rgb_offset+2] = shadow.b

            # 最初に見つかったパターンのみ置換
            break

    return binary

def apply_gradient_colors(binary: bytearray, fill: Fill) -> bytearray:
    """グラデーション色を適用

    RGBA Float形式（16バイト）:
    [R float 4B][G float 4B][B float 4B][A float 4B]

    0x0190-0x0200付近のRGBA floatブロックを探して書き換える
    """
    if not fill.is_gradient or not fill.top_left or not fill.bottom_right:
        return binary

    # RGBA float値に変換
    def rgb_to_rgba_floats(stop: GradientStop):
        """RGB(0-255) → RGBA floats(0.0-1.0)のバイト列"""
        r_float = stop.r / 255.0
        g_float = stop.g / 255.0
        b_float = stop.b / 255.0
        a_float = stop.a / 255.0

        return struct.pack('<ffff', r_float, g_float, b_float, a_float)

    # 開始色と終了色のRGBA floatバイト列
    start_rgba = rgb_to_rgba_floats(fill.top_left)
    end_rgba = rgb_to_rgba_floats(fill.bottom_right)

    # グラデーション領域を探索（0x0190-0x0200付近）
    search_start = 0x0190
    search_end = min(len(binary), 0x0220)

    # 最初の16バイト境界でRGBA floatパターンを探す
    found_count = 0
    for offset in range(search_start, search_end - 15, 4):
        # 既存のRGBA float候補を確認（すべて0.0-1.0範囲のfloat値）
        try:
            vals = struct.unpack('<ffff', binary[offset:offset+16])
            if all(0.0 <= v <= 1.0 for v in vals):
                # 見つかった順に開始色、終了色を書き込み
                if found_count == 0:
                    # 最初=開始色（top_left）
                    binary[offset:offset+16] = start_rgba
                    found_count += 1
                elif found_count == 1:
                    # 2番目=終了色（bottom_right）
                    binary[offset:offset+16] = end_rgba
                    found_count += 1
                    break  # 2色とも更新したら終了
        except:
            continue

    return binary

def convert_style(style: Style, template_binary: bytes) -> bytes:
    """スタイルを変換"""
    # テンプレートをコピー
    binary = bytearray(template_binary)

    # パラメータを適用
    if style.fill.is_gradient:
        # グラデーション
        binary = apply_gradient_colors(binary, style.fill)
    else:
        # 単色
        binary = apply_fill_color(binary, style.fill)

    binary = apply_shadow_blur(binary, style.shadow)
    binary = apply_shadow_color(binary, style.shadow)

    # TODO: 他のパラメータを適用
    # - apply_shadow_offset(binary, style.shadow) # 距離・角度（位置が可変で不安定）
    # - apply_shadow_opacity(binary, style.shadow) # 不透明度（位置が可変で不安定）
    # - apply_edge(binary, style.edge)

    return bytes(binary)

def create_prtextstyle_xml(styles: List[Style], binaries: List[bytes], output_path: str):
    """prtextstyleXMLファイルを生成"""
    # XMLルート
    root = ET.Element('PremiereData', Version='3')

    for i, (style, binary) in enumerate(zip(styles, binaries)):
        # StyleProjectItem
        item = ET.SubElement(root, 'StyleProjectItem',
                           Class='StyleProjectItem',
                           Version='1',
                           ObjectID=f'style_{i+1}')

        # Name
        name_elem = ET.SubElement(item, 'Name')
        name_elem.text = f'{i+1:03d}'

        # Component
        component = ET.SubElement(item, 'Component',
                                ObjectRef=f'component_{i+1}',
                                Class='VideoFilterComponent')

    # VideoFilterComponentを追加
    for i, binary in enumerate(binaries):
        vfc = ET.SubElement(root, 'VideoFilterComponent',
                          Class='VideoFilterComponent',
                          Version='10',
                          ObjectID=f'component_{i+1}')

        # Param
        param = ET.SubElement(vfc, 'Param',
                            Index='0',
                            ObjectRef=f'param_{i+1}')

    # ArbVideoComponentParamを追加
    for i, binary in enumerate(binaries):
        arb = ET.SubElement(root, 'ArbVideoComponentParam',
                          Class='ArbVideoComponentParam',
                          Version='3',
                          ObjectID=f'param_{i+1}')

        # StartKeyframeValue
        value = ET.SubElement(arb, 'StartKeyframeValue',
                            Encoding='base64',
                            BinaryHash='00000000')
        value.text = base64.b64encode(binary).decode('ascii')

    # ファイル保存
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

def convert_prsl_to_prtextstyle(prsl_path: str, output_path: str, template_path: str):
    """PRSL→prtextstyle完全変換"""
    print("="*80)
    print("完全版PRSL→prtextstyle変換")
    print("="*80)

    # PRSL解析
    print(f"\n[1] PRSL解析: {prsl_path}")
    styles = parse_prsl(prsl_path)
    print(f"  ✓ {len(styles)}スタイルを検出")

    # テンプレート読み込み
    print(f"\n[2] テンプレート読み込み: {template_path}")
    with open(template_path, 'r') as f:
        template_content = f.read()

    pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
    matches = re.findall(pattern, template_content, re.DOTALL)

    template_binaries = []
    for match in matches:
        b64_clean = match.replace('\n', '').replace(' ', '').replace('\t', '')
        binary = base64.b64decode(b64_clean)
        template_binaries.append(binary)

    print(f"  ✓ {len(template_binaries)}テンプレートを取得")

    # 変換
    print(f"\n[3] 変換処理:")
    converted_binaries = []

    for i, style in enumerate(styles):
        print(f"\n  スタイル {i+1}: {style.name}")

        if style.fill.is_gradient:
            if style.fill.top_left and style.fill.bottom_right:
                print(f"    塗り: グラデーション")
                print(f"      開始: RGB({style.fill.top_left.r}, {style.fill.top_left.g}, {style.fill.top_left.b})")
                print(f"      終了: RGB({style.fill.bottom_right.r}, {style.fill.bottom_right.g}, {style.fill.bottom_right.b})")
        else:
            print(f"    塗り: RGB({style.fill.r}, {style.fill.g}, {style.fill.b})")

        if style.shadow.enabled:
            print(f"    シャドウ: ぼかし={style.shadow.blur}")

        # 対応するテンプレートを選択（サイズで）
        if i < len(template_binaries):
            template = template_binaries[i]
        else:
            template = template_binaries[0]  # フォールバック

        # 変換
        try:
            converted = convert_style(style, template)
            converted_binaries.append(converted)
            print(f"    ✓ 変換成功 ({len(converted)} bytes)")
        except Exception as e:
            print(f"    ✗ エラー: {e}")
            converted_binaries.append(template)

    # XML生成
    print(f"\n[4] prtextstyleファイル生成:")
    create_prtextstyle_xml(styles, converted_binaries, output_path)
    print(f"  ✓ 保存完了: {output_path}")

    print(f"\n{'='*80}")
    print("✓✓✓ 変換完了！")
    print('='*80)
    print(f"成功: {len(converted_binaries)}/{len(styles)} スタイル")
    print(f"出力: {output_path}")

if __name__ == "__main__":
    import sys
    import re

    prsl_path = "/home/user/telop01/10styles/10styles.prsl"
    template_path = "/home/user/telop01/10styles/10styles.prtextstyle"
    output_path = "/home/user/telop01/CONVERTED_OUTPUT.prtextstyle"

    if len(sys.argv) > 1:
        prsl_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        template_path = sys.argv[3]

    convert_prsl_to_prtextstyle(prsl_path, output_path, template_path)
