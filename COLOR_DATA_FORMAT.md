# 色データフォーマット - 完全解明

## 決定的な発見

### 色の格納形式

**RGB bytes (0-255) + Alpha**

- **フォーマット**: `RR GG BB AA` (各1バイト)
- **値の範囲**: 0-255 (NOT 0.0-1.0 floats!)
- **位置**: 可変（FlatBuffersの動的レイアウトによる）

## 実データ検証

### White (255, 255, 255)
```
位置: 0x01a1
データ: ff ff ff 08
解釈: R=255, G=255, B=255, A=8

周辺:
01a0:  00 ff ff ff 08 00 08 00 06 00 07 00 08 00 00 00
       ^^  ^^^^^^^^ ^^
       ?   RGB=白   A=8
```

### Red (255, 0, 0)
```
位置: 0x01ab
データ: ff 00 00 00
解釈: R=255, G=0, B=0, A=0

周辺:
01a0:  04 00 04 00 04 00 00 00 f6 ff ff ff 00 00 00 ff
01b0:  ff ff 0a 00 0a 00 07 00 08 00 09 00 0a 00 00 00
                ^^       ^^^^^^^^ ^^
                ?        RGB?     ?

実際のデータ:
01ab:  ff 00 00 00 ff ff ff 0a
       ^^^^^^^^^^^ ^^
       RGB=赤      A=0
```

### Blue (0, 0, 255)
```
位置: 0x01ad
データ: 00 00 ff ff
解釈: R=0, G=0, B=255, A=255

周辺:
01a0:  0a 00 07 00 08 00 09 00 0a 00 00 00 00 00 00 ff
01b0:  ff ff 0a 00 08 00 05 00 06 00 07 00 0a 00 00 00
                      ^^^^^^^^^^^ ^^
                      RGB=青      A=255
```

## 重要な観察

### 1. 位置が可変

| ファイル | RGB位置 | サイズ |
|---------|---------|--------|
| White   | 0x01a1  | 452 bytes |
| Red     | 0x01ab  | 480 bytes |
| Blue    | 0x01ad  | 476 bytes |

**結論**: 色データの位置は **固定されていない**

### 2. FlatBuffersの動的レイアウト

FlatBuffersは以下の特性を持つ:

1. **VTable**: フィールドへのオフセットを格納
2. **可変長データ**: 文字列、配列のサイズが異なると全体のレイアウトが変わる
3. **オプショナルフィールド**: 存在しないフィールドはスキップされる

**影響**:
- フォント名の長さが変わる → 色データの位置がずれる
- ストロークの有無 → 色データの位置がずれる
- グラデーションストップの数 → 色データの位置がずれる

### 3. 誤検出に注意

`ff ff ff ff` パターンは複数箇所に出現するが、多くは **VTableのオフセット値 (-1)** である。

**VTable領域 (0x00b0付近)**:
```
White:
00b0:  fc fe ff ff 00 ff ff ff 04 ff ff ff 2a ff ff ff
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
       これらは色データではなく、オフセット値！
```

**実際の色データ (0x01a0付近)**:
```
White:
01a0:  00 ff ff ff 08 00 08 00 06 00 07 00 08 00 00 00
          ^^^^^^^^^^ ^^
          これが実際の色データ！
```

## グラデーションでの色データ

### グラデーションファイルの特徴

グラデーションファイルでは **RGBA float (0.0-1.0)** 形式も使用される:

```
BlueWhite グラデーション (632 bytes):
  0x0194: R=0.000, G=0.000, B=1.000, A=0.500
```

**結論**:
- **単色**: RGB bytes (0-255)
- **グラデーション**: RGBA floats (0.0-1.0)

## 実装への影響

### 従来の誤った仮定

```python
# ❌ これは動かない（オフセットが固定だと思っていた）
def set_color(binary, r, g, b):
    binary[0x01a1] = r  # 白のファイルでしか動かない！
    binary[0x01a2] = g
    binary[0x01a3] = b
```

### 正しいアプローチ

#### 方法A: パターンマッチング

```python
def find_color_offset(binary):
    # RGB パターンを探す
    # (255, 255, 255), (255, 0, 0), (0, 0, 255) など

    # VTable領域（0x00b0-0x00d0）は除外
    search_start = 0x0150

    for i in range(search_start, len(binary) - 3):
        r, g, b, a = binary[i:i+4]

        # 色らしいパターン
        if (r == 255 and g == 255 and b == 255) or \
           (r == 255 and g == 0 and b == 0) or \
           (r == 0 and g == 0 and b == 255):
            return i

    return None
```

#### 方法B: FlatBuffersデコーダー

```python
# FlatBuffersの公式ライブラリを使用
from flatbuffers import Builder

# スキーマ定義(.fbs)から生成されたコード
import SourceText  # 仮

# バイナリをデコード
text_data = SourceText.GetRootAs(binary)

# 色データにアクセス
fill_color = text_data.FillColor()
r = fill_color.R()
g = fill_color.G()
b = fill_color.B()
a = fill_color.A()

# 色を変更
builder = Builder(1024)
new_color = CreateColor(builder, 255, 0, 0, 255)  # 赤
# ... 再構築
```

#### 方法C: テンプレート + パターン置換

```python
# テンプレートを読み込み
template = load_template("white.prtextstyle")

# 既存の色パターンを探して置換
old_pattern = bytes([255, 255, 255])  # 白
new_pattern = bytes([255, 0, 0])      # 赤

# VTable領域を避けて置換
binary = template[:]
offset = find_color_in_range(binary, old_pattern, 0x0150, len(binary))
if offset:
    binary[offset:offset+3] = new_pattern
```

## 推奨実装戦略

### フェーズ1: パターンマッチング方式（今すぐ実装可能）

1. テンプレートファイルを読み込む
2. 色パターン (RGB bytes) を探す
3. 見つけた位置を置換

**メリット**:
- すぐに実装できる
- FlatBuffersの完全理解不要
- 実用的

**デメリット**:
- パターンが複数ある場合に誤検出の可能性
- 新しい色の追加は困難

### フェーズ2: FlatBuffers完全対応（将来の拡張）

1. `.fbs` スキーマを再構築
2. 公式ライブラリでエンコード/デコード
3. 完全な柔軟性

**メリット**:
- 任意の色を生成可能
- 構造の完全な理解
- 拡張性が高い

**デメリット**:
- スキーマの完全解明が必要
- 実装が複雑

## 次のステップ

### 即座に実装すべき

**パターンマッチング方式のプロトタイプ**

```python
#!/usr/bin/env python3
"""
PRSL to prtextstyle converter (Pattern Matching Version)
"""

def convert_prsl_to_prtextstyle(prsl_style, output_path):
    # 1. PRSLから色を取得
    r = prsl_style.fill.r
    g = prsl_style.fill.g
    b = prsl_style.fill.b

    # 2. 最も近いテンプレートを選択
    if r > 200 and g > 200 and b > 200:
        template = load_template("white.prtextstyle")
        old_rgb = (255, 255, 255)
    elif r > 200 and g < 50 and b < 50:
        template = load_template("red.prtextstyle")
        old_rgb = (255, 0, 0)
    elif r < 50 and g < 50 and b > 200:
        template = load_template("blue.prtextstyle")
        old_rgb = (0, 0, 255)
    else:
        # デフォルトは白テンプレート
        template = load_template("white.prtextstyle")
        old_rgb = (255, 255, 255)

    # 3. フォント名を置換（既に位置が分かっている）
    binary = bytearray(template)
    replace_font_name(binary, prsl_style.font_family)

    # 4. 色を置換（パターンマッチング）
    color_offset = find_color_pattern(binary, old_rgb)
    if color_offset:
        binary[color_offset] = r
        binary[color_offset+1] = g
        binary[color_offset+2] = b

    # 5. 保存
    with open(output_path, 'wb') as f:
        f.write(binary)
```

### 今後の調査

1. **フォントサイズの置換**
   - 位置: 0x0098付近（`00 00 f0 41` = 30.0）
   - 形式: float (little-endian)

2. **ストロークデータ**
   - ストロークあり/なしの差分を完全解析
   - 色、幅、位置などのパラメータ

3. **グラデーション対応**
   - RGBA float配列の生成
   - ストップ位置の計算

## まとめ

### 判明したこと

✅ 色は **RGB bytes (0-255) + Alpha** で格納
✅ 位置は **可変**（FlatBuffersの動的レイアウト）
✅ 白: 0x01a1, 赤: 0x01ab, 青: 0x01ad（参考値）
✅ VTable領域の `ff ff ff` は色ではない
✅ グラデーションは **RGBA float (0.0-1.0)** も使用

### 実装可能なこと

✅ パターンマッチングによる色の置換
✅ テンプレートベースの変換
✅ 基本的な単色スタイルの生成

### 今後の課題

❓ FlatBuffersスキーマの完全再構築
❓ 任意の色の動的生成
❓ グラデーション対応

---

作成日: 2025-12-12
プロジェクト: PRSL to prtextstyle Converter
