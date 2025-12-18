#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL変換ツール - 簡易テストスクリpt

このスクリプトでモジュールの動作を確認できます。
"""

import sys
import os

# 動作確認
def test_imports():
    """必要なモジュールがインストールされているか確認"""
    print("=" * 60)
    print("モジュールインポートテスト")
    print("=" * 60)

    results = {}

    # Python バージョン
    print(f"\n✓ Python: {sys.version.split()[0]}")

    # 必須モジュール
    modules = [
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("tkinter", "Tkinter（標準ライブラリ）"),
    ]

    for module, display_name in modules:
        try:
            __import__(module)
            print(f"✓ {display_name}: インストール済み")
            results[module] = True
        except ImportError:
            print(f"✗ {display_name}: 未インストール")
            results[module] = False

    # オプション
    try:
        import scipy
        print(f"✓ SciPy: インストール済み（高速化有効）")
        results["scipy"] = True
    except ImportError:
        print(f"⚠ SciPy: 未インストール（動作しますが、低速です）")
        results["scipy"] = False

    # 結果
    print("\n" + "=" * 60)
    if all([results.get("PIL"), results.get("numpy"), results.get("tkinter")]):
        print("✅ すべての必須モジュールがインストールされています！")
        return True
    else:
        print("❌ 一部のモジュールが不足しています。")
        print("\n以下のコマンドでインストールしてください:")
        if not results.get("PIL"):
            print("  pip install pillow")
        if not results.get("numpy"):
            print("  pip install numpy")
        if not results.get("scipy"):
            print("\n推奨:")
            print("  pip install scipy  # 高速化のため")
        return False


def test_prsl_parse():
    """サンプルPRSLファイルの解析テスト"""
    print("\n" + "=" * 60)
    print("PRSLファイル解析テスト")
    print("=" * 60)

    sample_file = "sample_style.prsl"

    if not os.path.exists(sample_file):
        print(f"⚠ サンプルファイル '{sample_file}' が見つかりません")
        print("  同じディレクトリにsample_style.prslを配置してください")
        return False

    try:
        # モジュールインポート
        from prsl_converter_modern import parse_prsl, Style

        # パース
        print(f"\n'{sample_file}' を解析中...")
        styles = parse_prsl(sample_file)

        print(f"✓ {len(styles)} 個のスタイルを検出:")
        for i, style in enumerate(styles, 1):
            print(f"  {i}. {style.name}")
            print(f"     - Font: {style.font_family} ({style.font_size}pt)")
            print(f"     - Fill: {style.fill.fill_type}")
            print(f"     - Strokes: {len(style.strokes)}個")
            print(f"     - Shadow: {'有効' if style.shadow.enabled else '無効'}")

        print("\n✅ PRSL解析テスト成功！")
        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_render():
    """レンダリングテスト"""
    print("\n" + "=" * 60)
    print("レンダリングテスト")
    print("=" * 60)

    try:
        from prsl_converter_modern import Style, Fill, Stroke, Shadow, StyleRenderer

        # テストスタイル作成
        style = Style(
            name="テストスタイル",
            font_family="Arial",
            font_size=64.0,
            fill=Fill(fill_type="solid", r=255, g=100, b=100, a=255)
        )

        # レンダラー作成
        renderer = StyleRenderer(canvas_size=(400, 200))

        # レンダリング
        print("\nレンダリング中...")
        img = renderer.render("Test", style)

        print(f"✓ 画像生成成功: {img.size[0]}x{img.size[1]} RGBA")

        # 保存してみる
        output_file = "test_render.png"
        img.save(output_file)
        print(f"✓ '{output_file}' として保存しました")

        print("\n✅ レンダリングテスト成功！")
        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export():
    """エクスポートテスト"""
    print("\n" + "=" * 60)
    print("prtextstyle エクスポートテスト")
    print("=" * 60)

    try:
        from prsl_converter_modern import Style, Fill, export_prtextstyle

        # テストスタイル
        style = Style(
            name="エクスポートテスト",
            font_family="Arial",
            font_size=48.0,
            fill=Fill(fill_type="solid", r=0, g=200, b=255, a=255)
        )

        # エクスポート
        output_file = "test_export.prtextstyle"
        print(f"\n'{output_file}' にエクスポート中...")
        export_prtextstyle(style, output_file)

        # ファイル確認
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"✓ ファイル作成成功: {size} bytes")

            # 中身確認
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read(200)
                if "<?xml" in content and "PremiereData" in content:
                    print("✓ XML形式として正しい構造です")
                else:
                    print("⚠ XML構造が不正な可能性があります")

        print("\n✅ エクスポートテスト成功！")
        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("\n" + "=" * 60)
    print("🧪 PRSL変換ツール - 統合テスト")
    print("=" * 60)

    results = []

    # テスト実行
    results.append(("モジュールインポート", test_imports()))

    if results[0][1]:  # インポートが成功した場合のみ続行
        results.append(("PRSL解析", test_prsl_parse()))
        results.append(("レンダリング", test_render()))
        results.append(("エクスポート", test_export()))

    # サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)

    for name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{name}: {status}")

    success_count = sum(1 for _, r in results if r)
    total_count = len(results)

    print(f"\n合計: {success_count}/{total_count} テスト成功")

    if success_count == total_count:
        print("\n🎉 すべてのテストに合格しました！")
        print("以下のコマンドでGUIを起動できます:")
        print("  python prsl_converter_modern.py")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
        print("エラーメッセージを確認して、必要なモジュールをインストールしてください。")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
