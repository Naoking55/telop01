#!/usr/bin/env python3
"""
最小限のGUI版コンバーター（デバッグ用）
"""

import sys
import re
import base64
import tkinter as tk
from tkinter import filedialog, messagebox

sys.path.insert(0, '/home/user/telop01')
from test_prsl_conversion import parse_prsl

MARKER = b'\x02\x00\x00\x00\x41\x61'

def get_color_structure(r, g, b):
    structure = []
    stored = []
    if r == 255:
        structure.append('R=skip')
    else:
        structure.append('R=store')
        stored.append(('R', r))
    if g == 255:
        structure.append('G=skip')
    else:
        structure.append('G=store')
        stored.append(('G', g))
    if b == 255:
        structure.append('B=skip')
    else:
        structure.append('B=store')
        stored.append(('B', b))
    return ', '.join(structure), stored

def replace_color_bytes_in_binary(binary, target_r, target_g, target_b):
    binary = bytearray(binary)
    marker_pos = binary.find(MARKER)
    if marker_pos == -1:
        raise ValueError("マーカーが見つかりません")
    target_structure, new_components = get_color_structure(target_r, target_g, target_b)
    num_bytes = len(new_components)
    for i in range(num_bytes):
        _, value = new_components[i]
        binary[marker_pos - num_bytes + i] = value
    return bytes(binary)

def convert():
    """変換実行"""
    print("\n" + "="*60)
    print("変換開始")
    print("="*60)

    # PRSLファイル選択
    prsl_file = filedialog.askopenfilename(
        title="PRSLファイルを選択",
        filetypes=[("PRSL files", "*.prsl"), ("All files", "*.*")]
    )
    if not prsl_file:
        print("キャンセルされました")
        return

    print(f"\n[1] PRSL: {prsl_file}")

    # 出力ファイル選択
    output_file = filedialog.asksaveasfilename(
        title="出力ファイル名を指定",
        defaultextension=".prtextstyle",
        filetypes=[("prtextstyle files", "*.prtextstyle"), ("All files", "*.*")]
    )
    if not output_file:
        print("キャンセルされました")
        return

    print(f"[2] 出力: {output_file}")

    # テンプレート選択
    template_file = filedialog.askopenfilename(
        title="テンプレートファイルを選択",
        initialfile="/tmp/10styles.prtextstyle",
        filetypes=[("prtextstyle files", "*.prtextstyle"), ("All files", "*.*")]
    )
    if not template_file:
        print("キャンセルされました")
        return

    print(f"[3] テンプレート: {template_file}")

    try:
        # PRSL解析
        print(f"\n[4] PRSL解析中...")
        styles = parse_prsl(prsl_file)
        print(f"  ✓ {len(styles)} スタイル検出")

        # テンプレート読み込み
        print(f"\n[5] テンプレート読み込み中...")
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        print(f"  ✓ {len(template_content)} chars ({len(template_content)/1024:.1f} KB)")

        # バイナリエントリ抽出
        print(f"\n[6] バイナリエントリ抽出中...")
        pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
        matches = list(re.finditer(pattern, template_content, re.DOTALL))
        print(f"  ✓ {len(matches)} エントリ")

        if len(matches) < len(styles):
            raise ValueError(f"テンプレートのスタイル数不足: {len(matches)} < {len(styles)}")

        # バイナリ取得
        print(f"\n[7] テンプレートバイナリ取得中...")
        template_binaries = []
        for i, match in enumerate(matches):
            b64 = match.group(2).replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
            binary = base64.b64decode(b64)
            template_binaries.append(binary)
        print(f"  ✓ {len(template_binaries)} バイナリ")

        # 変換処理
        print(f"\n[8] 変換処理:")
        conversions = []
        success_count = 0

        for i, style in enumerate(styles):
            r, g, b = style.fill.r, style.fill.g, style.fill.b
            print(f"  {i+1}/{len(styles)}: {style.name} RGB({r},{g},{b})")

            if i < len(template_binaries):
                try:
                    modified = replace_color_bytes_in_binary(template_binaries[i], r, g, b)
                    new_b64 = base64.b64encode(modified).decode('ascii')
                    conversions.append(new_b64)
                    success_count += 1
                    print(f"    ✓")
                except Exception as e:
                    print(f"    ✗ {e}")
                    conversions.append(None)
            else:
                conversions.append(None)

        print(f"\n[9] ファイル更新中...")
        # 後ろから順に置換
        new_content = template_content
        for i in range(len(conversions) - 1, -1, -1):
            if conversions[i] is not None and i < len(matches):
                match = matches[i]
                new_b64 = conversions[i]
                new_content = (
                    new_content[:match.start(2)] +
                    new_b64 +
                    new_content[match.end(2):]
                )

        print(f"  新コンテンツ: {len(new_content)} chars ({len(new_content)/1024:.1f} KB)")

        print(f"\n[10] ファイル保存中...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        import os
        final_size = os.path.getsize(output_file)
        print(f"  ✓ 保存完了: {final_size} bytes ({final_size/1024:.1f} KB)")

        if final_size < 10000:
            messagebox.showerror("警告", f"ファイルサイズが異常に小さい: {final_size} bytes")
        else:
            messagebox.showinfo("成功", f"変換完了！\n\n成功: {success_count}/{len(styles)}\n出力: {output_file}\nサイズ: {final_size/1024:.1f} KB")

        print(f"\n{'='*60}")
        print(f"✓✓✓ 完了")
        print(f"{'='*60}")

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"\n✗✗✗ エラー:\n{error_msg}")
        messagebox.showerror("エラー", f"変換失敗:\n\n{error_msg}")

# メイン
root = tk.Tk()
root.withdraw()  # メインウィンドウを隠す

print("="*60)
print("シンプルGUI変換ツール（デバッグ版）")
print("="*60)

convert()
