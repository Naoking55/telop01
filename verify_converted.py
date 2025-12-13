#!/usr/bin/env python3
"""
変換されたprtextstyleファイルの検証
"""

import sys
from prtextstyle_editor import PrtextstyleEditor

def verify_prtextstyle(filepath: str):
    """prtextstyleファイルを検証"""
    print(f"\n{'='*80}")
    print(f"Verifying: {filepath}")
    print('='*80)

    try:
        editor = PrtextstyleEditor(filepath)

        # スタイル一覧
        print(f"\nTotal styles: {len(editor.styles)}")

        for style_name in editor.styles:
            print(f"\n[{style_name}]")

            binary = editor.get_style_binary(style_name)
            print(f"  Binary size: {len(binary)} bytes")

            # シャドウ確認
            has_shadow = editor.has_shadow(binary)
            print(f"  Shadow: {'Yes' if has_shadow else 'No'}")

            if has_shadow:
                shadows = editor.get_shadow_params(style_name)
                if isinstance(shadows, list):
                    for i, shadow in enumerate(shadows):
                        if isinstance(shadow, dict):
                            blur_str = f"{shadow['blur']:.1f}" if shadow.get('blur') is not None else "N/A"
                            print(f"    Shadow[{i}]: X={shadow.get('x', 'N/A'):.1f}, Y={shadow.get('y', 'N/A'):.1f}, Blur={blur_str}")
                        else:
                            print(f"    Shadow[{i}]: {shadow}")
                else:
                    print(f"    Shadow data: {shadows}")

        print(f"\n✓ Verification completed successfully!")

    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # テスト対象のファイル
    test_files = [
        "converted_10styles/満天青空レストラン.prtextstyle",
        "converted_10styles/A-OTF_新ゴ_Pro_U_183.prtextstyle",
    ]

    for f in test_files:
        verify_prtextstyle(f)
