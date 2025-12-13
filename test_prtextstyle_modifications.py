#!/usr/bin/env python3
"""
prtextstyle 変更テスト
実際にパラメータを変更して、結果を検証する
"""

from prtextstyle_editor import PrtextstyleEditor

def test_shadow_modifications():
    """シャドウパラメータの変更テスト"""
    print("="*80)
    print("テスト1: シャドウパラメータの変更")
    print("="*80)
    print()

    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"
    editor = PrtextstyleEditor(filepath)

    test_style = "Fontstyle_90"

    # 元のパラメータを取得
    print(f"【{test_style}】元のシャドウパラメータ:")
    original_params = editor.get_shadow_params(test_style)
    if original_params['enabled']:
        for i, shadow in enumerate(original_params['shadows'][:3], 1):
            blur_str = f"{shadow['blur']:.1f}" if shadow['blur'] is not None else "N/A"
            print(f"  {i}. X={shadow['x']:.1f}, Y={shadow['y']:.1f}, Blur={blur_str}")
    print()

    # X,Yを変更
    print("変更1: 最初のシャドウのX,Yを (10.0, 10.0) に変更")
    if editor.modify_shadow_xy(test_style, 0, 10.0, 10.0):
        print("  ✅ 変更成功")
    else:
        print("  ❌ 変更失敗")
    print()

    # Blurを変更
    print("変更2: 最初のシャドウのBlurを 50.0 に変更")
    if editor.modify_shadow_blur(test_style, 0, 50.0):
        print("  ✅ 変更成功")
    else:
        print("  ❌ 変更失敗")
    print()

    # 変更後のパラメータを取得
    print("【{test_style}】変更後のシャドウパラメータ:")
    modified_params = editor.get_shadow_params(test_style)
    if modified_params['enabled']:
        for i, shadow in enumerate(modified_params['shadows'][:3], 1):
            blur_str = f"{shadow['blur']:.1f}" if shadow['blur'] is not None else "N/A"
            print(f"  {i}. X={shadow['x']:.1f}, Y={shadow['y']:.1f}, Blur={blur_str}")
    print()

    # 保存
    output_path = "test_shadow_modified.prtextstyle"
    editor.save(output_path)
    print(f"✅ 変更を保存: {output_path}")
    print()

    return output_path

def test_gradient_modifications():
    """グラデーションパラメータの変更テスト"""
    print("="*80)
    print("テスト2: グラデーションパラメータの変更")
    print("="*80)
    print()

    # 青白赤グラ 30 を使用
    filepath = "prtextstyle/青白赤グラ 30.prtextstyle"
    try:
        editor = PrtextstyleEditor(filepath)
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {filepath}")
        print("  スキップします")
        print()
        return None

    # スタイル名を取得
    if len(editor.styles) == 0:
        print("❌ スタイルが見つかりません")
        return None

    test_style = list(editor.styles.keys())[0]
    print(f"【{test_style}】グラデーションストップを検索:")

    binary = editor.get_style_binary(test_style)
    stops = editor.find_gradient_stops(binary)

    # 0.3前後のストップを探す
    target_stops = [s for s in stops if abs(s['position'] - 0.3) < 0.05]
    if target_stops:
        print(f"  30%付近のストップ: {len(target_stops)} 個")
        for stop in target_stops[:3]:
            print(f"    0x{stop['offset']:04x}: Position={stop['position']:.3f}, Alpha={stop['alpha']:.3f}")
    print()

    # Position 0.3 を 0.5 に変更
    print("変更: Position 0.3 → 0.5")
    if editor.modify_gradient_position(test_style, 0.3, 0.5):
        print("  ✅ 変更成功")
    else:
        print("  ❌ 変更失敗（該当するストップが見つからない）")
    print()

    # 保存
    output_path = "test_gradient_modified.prtextstyle"
    editor.save(output_path)
    print(f"✅ 変更を保存: {output_path}")
    print()

    return output_path

def test_stroke_modifications():
    """ストロークパラメータの変更テスト"""
    print("="*80)
    print("テスト3: ストロークパラメータの変更")
    print("="*80)
    print()

    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"
    editor = PrtextstyleEditor(filepath)

    # ストローク付きスタイルを探す（916 bytes以上）
    stroke_styles = [name for name, data in editor.styles.items() if len(data['binary']) >= 916]

    if not stroke_styles:
        print("❌ ストローク付きスタイルが見つかりません")
        return None

    test_style = stroke_styles[0]
    print(f"【{test_style}】ストローク幅を検索:")

    binary = editor.get_style_binary(test_style)
    stroke = editor.find_stroke_width(binary)

    if stroke:
        print(f"  ストローク幅: {stroke['width']:.1f} pt @ 0x{stroke['offset']:04x}")
    else:
        print("  ストローク幅が見つかりません")
    print()

    # ストローク幅を変更
    new_width = 24.0
    print(f"変更: ストローク幅 → {new_width} pt")
    if editor.modify_stroke_width(test_style, new_width):
        print("  ✅ 変更成功")
    else:
        print("  ❌ 変更失敗")
    print()

    # 保存
    output_path = "test_stroke_modified.prtextstyle"
    editor.save(output_path)
    print(f"✅ 変更を保存: {output_path}")
    print()

    return output_path

def verify_modifications():
    """変更の検証"""
    print("="*80)
    print("変更の検証")
    print("="*80)
    print()

    # シャドウ変更を検証
    if os.path.exists("test_shadow_modified.prtextstyle"):
        print("【シャドウ変更の検証】")
        editor = PrtextstyleEditor("test_shadow_modified.prtextstyle")
        test_style = "Fontstyle_90"
        params = editor.get_shadow_params(test_style)

        if params['enabled'] and len(params['shadows']) > 0:
            shadow = params['shadows'][0]
            blur_str = f"{shadow['blur']:.1f}" if shadow['blur'] is not None else "N/A"
            print(f"  最初のシャドウ: X={shadow['x']:.1f}, Y={shadow['y']:.1f}, Blur={blur_str}")

            # 期待値と比較
            expected_x, expected_y, expected_blur = 10.0, 10.0, 50.0
            if abs(shadow['x'] - expected_x) < 0.1 and abs(shadow['y'] - expected_y) < 0.1:
                print("  ✅ X,Yの変更が正しく保存されています")
            else:
                print(f"  ❌ X,Yの変更が保存されていません（期待: {expected_x}, {expected_y}）")

            if shadow['blur'] is not None and abs(shadow['blur'] - expected_blur) < 0.1:
                print("  ✅ Blurの変更が正しく保存されています")
            else:
                print(f"  ❌ Blurの変更が保存されていません（期待: {expected_blur}）")
        print()

def main():
    """メイン"""
    import os

    print("="*80)
    print("prtextstyle 変更テスト - 実行")
    print("="*80)
    print()

    # テスト1: シャドウ
    test_shadow_modifications()

    # テスト2: グラデーション
    test_gradient_modifications()

    # テスト3: ストローク
    test_stroke_modifications()

    # 検証
    verify_modifications()

    print("="*80)
    print("全テスト完了")
    print("="*80)
    print()
    print("生成されたファイル:")
    for filename in ["test_shadow_modified.prtextstyle", "test_gradient_modified.prtextstyle", "test_stroke_modified.prtextstyle"]:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  - {filename} ({size} bytes)")

if __name__ == "__main__":
    import os
    main()
