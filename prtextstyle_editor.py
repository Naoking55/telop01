#!/usr/bin/env python3
"""
prtextstyle Editor - 実装テスト
これまでの解析結果を使って、prtextstyleファイルを編集するライブラリ
"""

import xml.etree.ElementTree as ET
import base64
import struct
import copy

class PrtextstyleEditor:
    """prtextstyleファイルの編集クラス"""

    def __init__(self, filepath):
        """ファイルを読み込む"""
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.styles = {}
        self._load_styles()

    def _load_styles(self):
        """全スタイルを読み込む"""
        for style_item in self.root.findall('.//StyleProjectItem'):
            name_elem = style_item.find('.//Name')
            if name_elem is not None:
                style_name = name_elem.text
                component_ref_elem = style_item.find('.//Component[@ObjectRef]')
                component_ref = component_ref_elem.get('ObjectRef')
                vfc = self.root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
                first_param_ref = vfc.find(".//Param[@Index='0']")
                param_obj_ref = first_param_ref.get('ObjectRef')
                arb_param = self.root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
                binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")

                self.styles[style_name] = {
                    'binary': base64.b64decode(binary_elem.text.strip()),
                    'binary_elem': binary_elem,
                    'style_item': style_item
                }

    def get_style_binary(self, style_name):
        """スタイルのバイナリデータを取得"""
        if style_name not in self.styles:
            return None
        return self.styles[style_name]['binary']

    def set_style_binary(self, style_name, new_binary):
        """スタイルのバイナリデータを更新"""
        if style_name not in self.styles:
            return False

        self.styles[style_name]['binary'] = new_binary
        # XML要素も更新
        encoded = base64.b64encode(new_binary).decode('ascii')
        self.styles[style_name]['binary_elem'].text = encoded
        return True

    def save(self, output_path):
        """変更を保存"""
        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)

    # === グラデーション編集 ===

    def find_gradient_stops(self, binary):
        """グラデーションストップ（Position + Alpha）を検索"""
        stops = []
        for offset in range(0, len(binary) - 7, 4):
            try:
                position = struct.unpack('<f', binary[offset:offset+4])[0]
                alpha = struct.unpack('<f', binary[offset+4:offset+8])[0]

                # Position: 0.0-1.0, Alpha: 0.0-1.0
                if 0.0 <= position <= 1.0 and 0.0 <= alpha <= 1.0:
                    # 特定のパターンに一致するか確認
                    if abs(position - 0.0) < 0.01 or abs(position - 1.0) < 0.01 or (0.2 <= position <= 0.8):
                        stops.append({
                            'offset': offset,
                            'position': position,
                            'alpha': alpha
                        })
            except:
                pass
        return stops

    def modify_gradient_position(self, style_name, old_position, new_position):
        """グラデーションストップの位置を変更"""
        binary = bytearray(self.get_style_binary(style_name))
        if binary is None:
            return False

        stops = self.find_gradient_stops(binary)
        modified = False

        for stop in stops:
            if abs(stop['position'] - old_position) < 0.01:
                # Position値を更新
                struct.pack_into('<f', binary, stop['offset'], new_position)
                modified = True
                print(f"  変更: 0x{stop['offset']:04x}: Position {old_position:.2f} → {new_position:.2f}")

        if modified:
            self.set_style_binary(style_name, bytes(binary))

        return modified

    # === ストローク編集 ===

    def find_stroke_width(self, binary):
        """ストローク幅を検索（0x0184付近）"""
        # 0x0180-0x0190の範囲を探索
        for offset in range(0x0180, min(0x0190, len(binary) - 3), 4):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                if 0 < val < 200:  # 妥当なストローク幅（0-200pt）
                    return {'offset': offset, 'width': val}
            except:
                pass
        return None

    def modify_stroke_width(self, style_name, new_width):
        """ストローク幅を変更"""
        binary = bytearray(self.get_style_binary(style_name))
        if binary is None:
            return False

        stroke = self.find_stroke_width(binary)
        if stroke:
            struct.pack_into('<f', binary, stroke['offset'], new_width)
            self.set_style_binary(style_name, bytes(binary))
            print(f"  ストローク幅変更: 0x{stroke['offset']:04x}: {stroke['width']:.1f} → {new_width:.1f} pt")
            return True

        return False

    # === シャドウ検出・編集 ===

    def has_shadow(self, binary):
        """シャドウブロックの有無を判定"""
        # 基本サイズ以下ならシャドウなし
        if len(binary) <= 732:
            return False

        # シャドウブロック開始位置
        shadow_start = 0x02dc
        if len(binary) <= shadow_start:
            return False

        # X,Yオフセットペアを検索
        return len(self.find_shadow_xy_offsets(binary, shadow_start)) > 0

    def find_shadow_xy_offsets(self, binary, start_offset=0x02dc):
        """シャドウX,Yオフセットペアを検索"""
        xy_pairs = []
        end_offset = len(binary)

        for offset in range(start_offset, end_offset - 7, 4):
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

    def find_shadow_blur(self, binary, xy_offset):
        """X,Yオフセット近くのBlur値を検索"""
        for delta in [-12, -8, -4, 4, 8, 12]:
            blur_offset = xy_offset + delta
            if 0 <= blur_offset + 4 <= len(binary):
                try:
                    val = struct.unpack('<f', binary[blur_offset:blur_offset+4])[0]
                    if 0 <= val <= 100:
                        return {'offset': blur_offset, 'blur': val, 'distance': delta}
                except:
                    pass
        return None

    def get_shadow_params(self, style_name):
        """シャドウパラメータを取得"""
        binary = self.get_style_binary(style_name)
        if binary is None:
            return None

        if not self.has_shadow(binary):
            return {'enabled': False}

        xy_pairs = self.find_shadow_xy_offsets(binary)
        shadows = []

        for xy in xy_pairs[:5]:  # 最初の5個のみ
            blur = self.find_shadow_blur(binary, xy['offset'])
            shadows.append({
                'x': xy['x'],
                'y': xy['y'],
                'blur': blur['blur'] if blur else None,
                'xy_offset': xy['offset'],
                'blur_offset': blur['offset'] if blur else None
            })

        return {
            'enabled': True,
            'shadows': shadows
        }

    def modify_shadow_xy(self, style_name, index, new_x, new_y):
        """シャドウのX,Yオフセットを変更"""
        binary = bytearray(self.get_style_binary(style_name))
        if binary is None:
            return False

        xy_pairs = self.find_shadow_xy_offsets(binary)
        if index >= len(xy_pairs):
            return False

        offset = xy_pairs[index]['offset']
        struct.pack_into('<f', binary, offset, new_x)
        struct.pack_into('<f', binary, offset + 4, new_y)
        self.set_style_binary(style_name, bytes(binary))
        print(f"  シャドウX,Y変更: 0x{offset:04x}: ({xy_pairs[index]['x']:.1f}, {xy_pairs[index]['y']:.1f}) → ({new_x:.1f}, {new_y:.1f})")
        return True

    def modify_shadow_blur(self, style_name, index, new_blur):
        """シャドウのBlurを変更"""
        binary = bytearray(self.get_style_binary(style_name))
        if binary is None:
            return False

        xy_pairs = self.find_shadow_xy_offsets(binary)
        if index >= len(xy_pairs):
            return False

        blur_info = self.find_shadow_blur(binary, xy_pairs[index]['offset'])
        if not blur_info:
            return False

        struct.pack_into('<f', binary, blur_info['offset'], new_blur)
        self.set_style_binary(style_name, bytes(binary))
        print(f"  シャドウBlur変更: 0x{blur_info['offset']:04x}: {blur_info['blur']:.1f} → {new_blur:.1f}")
        return True


def main():
    """テスト"""
    print("="*80)
    print("prtextstyle Editor - 実装テスト")
    print("="*80)
    print()

    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"
    editor = PrtextstyleEditor(filepath)

    print(f"読み込み: {filepath}")
    print(f"スタイル数: {len(editor.styles)}")
    print()

    # テスト1: グラデーションストップを探す
    print("="*80)
    print("テスト1: グラデーションストップの検出")
    print("="*80)
    print()

    test_style = "Fontstyle_01"
    binary = editor.get_style_binary(test_style)
    if binary:
        stops = editor.find_gradient_stops(binary)
        print(f"{test_style}: {len(stops)} 個のストップを検出")
        for i, stop in enumerate(stops[:5], 1):
            print(f"  {i}. 0x{stop['offset']:04x}: Position={stop['position']:.3f}, Alpha={stop['alpha']:.3f}")
        print()

    # テスト2: シャドウパラメータを取得
    print("="*80)
    print("テスト2: シャドウパラメータの取得")
    print("="*80)
    print()

    for test_style in ["Fontstyle_01", "Fontstyle_90"]:
        shadow_params = editor.get_shadow_params(test_style)
        print(f"{test_style}:")
        if shadow_params['enabled']:
            print(f"  シャドウ: あり")
            for i, shadow in enumerate(shadow_params['shadows'][:3], 1):
                blur_str = f"{shadow['blur']:.1f}" if shadow['blur'] is not None else "N/A"
                print(f"  {i}. X={shadow['x']:.1f}, Y={shadow['y']:.1f}, Blur={blur_str}")
        else:
            print(f"  シャドウ: なし")
        print()

if __name__ == "__main__":
    main()
