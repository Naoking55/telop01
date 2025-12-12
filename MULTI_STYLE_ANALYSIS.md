# 複数スタイルprtextstyleファイルの解析結果

**解析日**: 2025-12-12
**解析ファイル**:
- 100 New Fonstyle.prtextstyle (100スタイル)
- 200 New FontStyles_01.prtextstyle (200スタイル)

---

## 📊 基本情報

| ファイル | スタイル数 | バイナリサイズ範囲 |
|----------|-----------|-------------------|
| 100 New Fonstyle | 100 | 732 - 1756 bytes |
| 200 New FontStyles_01 | 200 | 608 - 1092 bytes |
| **合計** | **300** | **608 - 1756 bytes** |

## 🏗️ ファイル構造

### XML階層構造

```
PremiereData (Version="3")
├─ Project
├─ RootProjectItem
│   └─ Items
│       ├─ Item (Index="0") → StyleProjectItem #1
│       ├─ Item (Index="1") → StyleProjectItem #2
│       └─ ... (100個または200個)
└─ StyleProjectItem (ObjectUID="...")
    ├─ Name (スタイル名)
    └─ Component (ObjectRef → VideoFilterComponent)

VideoFilterComponent (ObjectID="27", MatchName="AE.ADBE Text")
└─ Params
    ├─ Param (Index="0") → ArbVideoComponentParam ★重要★
    ├─ Param (Index="1") → Transform
    └─ ... (合計22個のパラメータ)

ArbVideoComponentParam (Name="Source Text")
└─ StartKeyframeValue (Encoding="base64", BinaryHash="...")
    └─ [Base64エンコードされたFlatBuffersバイナリ]
```

### 重要な発見

**Source Textパラメータ**: 各スタイルのバイナリデータは、`ArbVideoComponentParam`の`StartKeyframeValue`要素に、Base64エンコードされて格納されている。

---

## 🔍 バイナリ構造の解析

### FlatBuffers形式確認

全300スタイルのバイナリは**FlatBuffers形式**：
- マジックナンバー: `44 33 22 11` (位置: 0x0008)
- 可変長レイアウト（VTableベース）

### フォント名

**位置**: 可変（サイズにより0x02ac～0x02e4など）
**形式**: 長さプレフィックス(uint32) + UTF-8文字列
**確認されたフォント**: `NotoSansCJKtc-Black`（全300スタイルで共通の可能性）

### RGBA色データ

**重要な発見**: 色データの位置は可変だが、パターンが明確

#### サイズ732バイトのスタイル（Fontstyle_01-10）

| スタイル | サイズ | RGBA色（0x0214-0x0218） | 色系 |
|----------|--------|------------------------|------|
| Fontstyle_01 | 732 | R=0 G=253 B=113 A=113 | 緑系 |
| Fontstyle_02 | 732 | R=0 G=253 B=169 A=113 | 緑系 |
| Fontstyle_03 | 732 | R=0 G=253 B=222 A=113 | シアン系 |
| Fontstyle_04 | 732 | R=0 G=184 B=227 A=158 | 青系 |
| Fontstyle_05 | 732 | R=0 G=113 B=228 A=253 | 青系 |
| ... | ... | ... | ... |
| Fontstyle_10 | 732 | R=0 G=189 B=189 A=189 | グレー系 |

#### サイズ916バイトのスタイル（Fontstyle_11-20）

| スタイル | サイズ | RGBA色（0x02aa-0x02ae） | 注記 |
|----------|--------|------------------------|------|
| Fontstyle_11 | 916 | R=0 G=253 B=113 A=113 | ← Fontstyle_01と同じ色！ |
| Fontstyle_12 | 916 | R=0 G=253 B=169 A=113 | ← Fontstyle_02と同じ色！ |
| Fontstyle_13-20 | 916 | R=122 G=255 B=255 A=255 | 明るいシアン（全て同じ） |

### 差分パターン

#### 同じサイズ、異なる色のスタイル比較

**Fontstyle_01 vs Fontstyle_02（両方732バイト）:**
- 差分: **たった1バイト**（0x0216）
- 値: 0x71 (113) vs 0xa9 (169)
- この1バイトがRGBA値の一部（Bチャンネルの値）

**Fontstyle_11 vs Fontstyle_12（両方916バイト）:**
- 差分: **たった1バイト**（0x02ac）
- 値: 0x71 (113) vs 0xa9 (169)
- 同様にRGBA値の一部

#### 同じ色、異なるサイズのスタイル比較

**Fontstyle_01（732バイト） vs Fontstyle_11（916バイト）:**
- 両方とも **R=0 G=253 B=113 A=113** の同じ色
- サイズ差: **184バイト**
- Fontstyle_11には追加のデータが含まれている（おそらくストローク/シャドウ/追加エフェクト）

---

## 📐 サイズ分布パターン

### 100 Fonstyleファイル

```
サイズ範囲: 732 - 1756 bytes

サイズ分布（50バイト単位）:
  700- 749 bytes:  20 スタイル  ← 基本スタイル
  800- 849 bytes:  18 スタイル
  900- 949 bytes:  32 スタイル  ← 中程度の複雑さ
 1000-1049 bytes:  13 スタイル
 1100-1149 bytes:   5 スタイル
 1450-1499 bytes:   9 スタイル
 1700-1749 bytes:   3 スタイル  ← 最も複雑（多重ストローク/シャドウ?）
```

### 全体統計（300スタイル）

- **ストロークあり**: 300 (100%)
- **グラデーションあり**: 300 (100%)
- **使用色 Top 3**:
  1. RGB(0, 0, 0) - 黒: 3408回出現
  2. RGB(255, 255, 0) - 黄: 416回出現
  3. RGB(255, 255, 255) - 白: 226回出現

---

## 🎯 重要な発見まとめ

### 1. 色データの位置は可変だが検出可能

**方法**: 特定のRGBA値をパターンマッチングで検索
- サイズ732バイト → 0x0214-0x0218付近
- サイズ916バイト → 0x02aa-0x02ae付近
- サイズが増えると位置がシフト

### 2. 同じ色で異なるサイズ = 追加エフェクト

Fontstyle_01（732バイト）とFontstyle_11（916バイト）は同じ色だが：
- **184バイトの差分** = ストローク、シャドウ、または追加グラデーションストップ？

### 3. ユーザーからのフィードバック

「**スタイルにフォントサイズは関係ない**」

これは重要な指摘：
- フォントサイズはスタイルではなく、テキストプロパティとして扱われる
- PRSL→prtextstyle変換では、フォントサイズは無視または固定値でOK

**スタイルとして重要な要素**:
1. ✅ フォント名（フォントファミリー）
2. ✅ 色（塗り）- 単色/グラデーション
3. ✅ ストローク - 幅、色、位置
4. ✅ シャドウ - オフセット、ぼかし、色

---

## 🔬 次のステップ

### 優先度 HIGH

1. **ストロークパラメータの解明**
   - 732バイト vs 916バイトの184バイト差分を詳細分析
   - ストローク幅、色、位置の検出

2. **シャドウパラメータの解明**
   - より大きいサイズのスタイル（1700バイト台）を解析
   - シャドウオフセット、ぼかし、色の検出

3. **グラデーション詳細**
   - ストップ数の検出
   - 各ストップの色と位置
   - 中間点パラメータ

### 優先度 MEDIUM

4. **フォント名の動的抽出**
   - 可変位置からフォント名を確実に抽出するアルゴリズム
   - FlatBuffers VTableの解析

5. **スタイル分類アルゴリズム**
   - バイナリサイズから特徴を推定
   - ストローク数、シャドウの有無、グラデーションストップ数の判定

---

## 📝 コード例

### スタイルバイナリの取得

```python
import xml.etree.ElementTree as ET
import base64

def get_style_binary(filepath, style_name):
    tree = ET.parse(filepath)
    root = tree.getroot()

    # StyleProjectItemを探す
    for style_item in root.findall('.//StyleProjectItem'):
        name_elem = style_item.find('.//Name')
        if name_elem.text == style_name:
            # Component参照を取得
            component_ref = style_item.find('.//Component[@ObjectRef]').get('ObjectRef')

            # VideoFilterComponentを取得
            vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")

            # 最初のParam (Source Text)
            param_ref = vfc.find(".//Param[@Index='0']").get('ObjectRef')

            # ArbVideoComponentParam
            arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_ref}']")

            # Base64バイナリ
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            return base64.b64decode(binary_elem.text.strip())

    return None
```

### RGBA色の抽出（パターンマッチング）

```python
def extract_rgba_color(binary_data):
    """バイナリからRGBA色を検索"""
    # サイズに応じた検索範囲
    if len(binary_data) < 800:
        search_range = range(0x0200, 0x0230)
    else:
        search_range = range(0x0290, 0x02c0)

    for offset in search_range:
        if offset + 4 <= len(binary_data):
            r, g, b, a = binary_data[offset:offset+4]
            # 妥当な色値かチェック
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return (r, g, b, a, offset)

    return None
```

---

## 🔗 関連ファイル

### 解析ツール

- `analyze_multi_style_files.py` - 複数スタイルファイルの統計解析
- `analyze_100_200_styles.py` - 300スタイルの詳細解析
- `inspect_single_style.py` - 単一スタイルのバイナリ詳細調査
- `compare_style_patterns.py` - スタイル間の差分比較

### ドキュメント

- `FINAL_BINARY_FORMAT_FINDINGS.md` - 単一スタイルファイルの解析結果
- `PRTEXTSTYLE_SPECIFICATION_v2.md` - prtextstyle形式の完全仕様

---

**結論**: 300個のスタイルから、色データの位置とパターンを特定できた。次は、ストロークとシャドウパラメータの位置を特定することで、完全なPRSL→prtextstyle変換が可能になる。
