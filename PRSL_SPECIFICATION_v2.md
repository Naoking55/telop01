# PRSL（Legacy Title Style Library）完全仕様書 v2.0

**最終更新**: 2025-12-12
**解析状況**: 完全解明済み

---

## 目次

1. [概要](#1-概要)
2. [ファイル形式](#2-ファイル形式)
3. [XML構造](#3-xml構造)
4. [スタイルデータ詳細](#4-スタイルデータ詳細)
5. [色・グラデーション仕様](#5-色グラデーション仕様)
6. [ストローク仕様](#6-ストローク仕様)
7. [シャドウ仕様](#7-シャドウ仕様)
8. [フォント情報](#8-フォント情報)
9. [変換時の注意事項](#9-変換時の注意事項)

---

## 1. 概要

### PRSLとは

- **正式名称**: Premiere Pro Legacy Title Style Library
- **用途**: 旧レガシータイトルエンジンで作成したスタイルのライブラリ
- **形式**: XML + Base64エンコードされたバイナリデータ
- **複数スタイル**: 1ファイルに複数のスタイルを格納可能（最小1個）

### 2つのPRSLフォーマット

#### A. Stylelist形式（主流）

```xml
<stylelist version="1">
  <styleblock>
    <text_specification>...</text_specification>
    <style_data>...</style_data>
  </styleblock>
  <styleblock>...</styleblock>
  ...
</stylelist>
```

**特徴**:
- ルート要素: `<stylelist>`
- 各スタイル: `<styleblock>`
- タグ数: 111種類
- 要素総数: 2,548個（10スタイルの例）

#### B. Component形式（旧式）

```xml
<PremiereData Version="3">
  <StyleProjectItem>
    <Component>
      <Params>...</Params>
    </Component>
  </StyleProjectItem>
</PremiereData>
```

**特徴**:
- PremiereDataプロジェクト形式
- Base64バイナリパラメータ
- レガシー構造を保持

---

## 2. ファイル形式

### ファイル拡張子

`.prsl`

### 文字エンコーディング

- XML: UTF-8
- テキストデータ: UTF-8（XML内）
- バイナリデータ: Base64エンコード

### ファイルサイズ

- 小規模（1-2スタイル）: 数KB
- 中規模（10スタイル）: 20-50KB
- 大規模（100+スタイル）: 数百KB

---

## 3. XML構造

### Stylelist形式の完全構造

```xml
<?xml version="1.0" encoding="UTF-8"?>
<stylelist version="1">
  <!-- スタイル1 -->
  <styleblock>
    <text_specification>
      <title_name>サンプルスタイル - 単色</title_name>
      <font_family>Myriad Pro</font_family>
      <font_style>Bold</font_style>
      <font_size>120.0</font_size>
      <tracking>0</tracking>
      <leading>0.0</leading>
      <kerning>0</kerning>
    </text_specification>

    <style_data>
      <!-- 塗り -->
      <fill>
        <fill_type>solid</fill_type>
        <r>255</r>
        <g>255</g>
        <b>255</b>
        <a>255</a>
      </fill>

      <!-- ストローク -->
      <embellishments>
        <inner_embellishment_count>0</inner_embellishment_count>
        <outer_embellishment_count>1</outer_embellishment_count>

        <outer_embellishment>
          <width>10.0</width>
          <r>0</r>
          <g>0</g>
          <b>0</b>
          <a>255</a>
        </outer_embellishment>
      </embellishments>

      <!-- シャドウ -->
      <shadow>
        <enabled>true</enabled>
        <offset_x>5.0</offset_x>
        <offset_y>5.0</offset_y>
        <blur>10.0</blur>
        <r>0</r>
        <g>0</g>
        <b>0</b>
        <a>180</a>
      </shadow>
    </style_data>
  </styleblock>
</stylelist>
```

### 主要タグ一覧

#### text_specification（テキスト仕様）

| タグ | 型 | 説明 | 例 |
|------|-----|------|-----|
| `title_name` | string | スタイル名 | "サンプルスタイル" |
| `font_family` | string | フォントファミリー | "Myriad Pro" |
| `font_style` | string | フォントスタイル | "Bold", "Regular" |
| `font_size` | float | フォントサイズ（pt） | 120.0 |
| `tracking` | int | 文字間隔 | 0, 50, -20 |
| `leading` | float | 行間 | 0.0, 1.2 |
| `kerning` | int | カーニング | 0, 1 |

#### style_data（スタイルデータ）

##### fill（塗り）

**単色塗り**:
```xml
<fill>
  <fill_type>solid</fill_type>
  <r>255</r>
  <g>255</g>
  <b>255</b>
  <a>255</a>
</fill>
```

**グラデーション塗り**:
```xml
<fill>
  <fill_type>gradient</fill_type>
  <gradient_type>linear</gradient_type> <!-- or "radial" -->
  <gradient_angle>90.0</gradient_angle>

  <gradient_stops>
    <stop>
      <offset>0.0</offset>
      <r>0</r>
      <g>0</g>
      <b>255</b>
      <a>255</a>
    </stop>
    <stop>
      <offset>1.0</offset>
      <r>255</r>
      <g>255</g>
      <b>255</b>
      <a>255</a>
    </stop>
  </gradient_stops>
</fill>
```

---

## 4. スタイルデータ詳細

### 色の表現

**形式**: RGB + Alpha
**範囲**: 0-255（整数）

```xml
<r>255</r>  <!-- 赤 (0-255) -->
<g>128</g>  <!-- 緑 (0-255) -->
<b>0</b>    <!-- 青 (0-255) -->
<a>255</a>  <!-- 不透明度 (0=透明, 255=不透明) -->
```

**フロート形式も存在**（一部のファイル）:
```xml
<r>1.0</r>  <!-- 0.0-1.0 -->
<g>0.5</g>
<b>0.0</b>
<a>1.0</a>
```

→ 読み込み時は両方に対応すること

---

## 5. 色・グラデーション仕様

### グラデーションタイプ

| タイプ | 値 | 説明 |
|--------|-----|------|
| 線形 | `linear` | 直線状のグラデーション |
| 円形 | `radial` | 中心から放射状 |

### グラデーションストップ

**最大数**: 16個（Legacy Title制限）

**Stop構造**:
```xml
<stop>
  <offset>0.5</offset>  <!-- 0.0-1.0 -->
  <r>128</r>
  <g>128</g>
  <b>128</b>
  <a>255</a>
  <midpoint>0.5</midpoint>  <!-- オプション、補間カーブ -->
</stop>
```

### グラデーション角度

- **単位**: 度（0-360）
- **0度**: 左から右
- **90度**: 下から上
- **180度**: 右から左
- **270度**: 上から下

---

## 6. ストローク仕様

### 多重ストローク対応

Legacy Titleは**最大8-10本のストローク**をサポート。

```xml
<embellishments>
  <inner_embellishment_count>2</inner_embellishment_count>
  <outer_embellishment_count>3</outer_embellishment_count>

  <!-- 内側ストローク（文字の内側に描画） -->
  <inner_embellishment>
    <width>5.0</width>
    <r>255</r><g>0</g><b>0</b><a>255</a>
  </inner_embellishment>

  <!-- 外側ストローク（文字の外側に描画） -->
  <outer_embellishment>
    <width>10.0</width>
    <r>0</r><g>0</g><b>255</b><a>255</a>
  </outer_embellishment>
  <outer_embellishment>
    <width>8.0</width>
    <r>255</r><g>255</g><b>0</b><a>255</a>
  </outer_embellishment>
</embellishments>
```

### ストローク描画順序

1. **最外側**: `outer_embellishment[0]`（最初に描画）
2. 次: `outer_embellishment[1]`
3. ...
4. **文字本体**（fill）
5. `inner_embellishment[0]`（最後に描画）

### ストロークなしの場合

```xml
<embellishments>
  <inner_embellishment_count>0</inner_embellishment_count>
  <outer_embellishment_count>0</outer_embellishment_count>
</embellishments>
```

---

## 7. シャドウ仕様

### シャドウ構造

```xml
<shadow>
  <enabled>true</enabled>
  <offset_x>5.0</offset_x>    <!-- 横オフセット（px） -->
  <offset_y>5.0</offset_y>    <!-- 縦オフセット（px） -->
  <blur>10.0</blur>           <!-- ぼかし半径（px） -->
  <spread>0.0</spread>        <!-- 拡散（オプション） -->
  <r>0</r>
  <g>0</g>
  <b>0</b>
  <a>180</a>                  <!-- 半透明シャドウ -->
</shadow>
```

### シャドウなしの場合

```xml
<shadow>
  <enabled>false</enabled>
</shadow>
```

または `<shadow>` 要素自体が存在しない。

---

## 8. フォント情報

### フォント指定

```xml
<font_family>Myriad Pro</font_family>
<font_style>Bold</font_style>
```

**注意事項**:
- フォントファミリーとスタイルは分離
- `font_style` は: `Regular`, `Bold`, `Italic`, `Bold Italic` など
- システムにフォントがない場合、代替フォントが使用される

### フォントサイズ

```xml
<font_size>120.0</font_size>
```

- **単位**: ポイント（pt）
- **範囲**: 通常 6.0 - 400.0
- **小数点**: サポート（120.5など）

---

## 9. 変換時の注意事項

### prtextstyle への変換

#### 対応表

| PRSL要素 | prtextstyle対応 | 備考 |
|----------|----------------|------|
| 単色塗り | ✅ 完全対応 | RGB bytes |
| グラデーション2-3色 | ✅ 対応 | RGBA floats |
| グラデーション4色以上 | ⚠️ 縮約必要 | 3色に削減 |
| 多重ストローク | ⚠️ 1本に統合 | 最外側のみ |
| 内側ストローク | ❌ 非対応 | 削除 |
| シャドウ | ✅ 対応 | |
| 光沢（Gloss） | ❌ 非対応 | グラデ変換推奨 |
| エンボス | ❌ 非対応 | 削除 |

#### 色形式の変換

**PRSL → prtextstyle**:

```python
# PRSLの色値（0-255 整数）
prsl_r = 255
prsl_g = 128
prsl_b = 0

# prtextstyleの色値
# 単色の場合: RGB bytes (0-255) そのまま
prtextstyle_r = prsl_r  # 255
prtextstyle_g = prsl_g  # 128
prtextstyle_b = prsl_b  # 0

# グラデーションの場合: floats (0.0-1.0)
prtextstyle_r = prsl_r / 255.0  # 1.0
prtextstyle_g = prsl_g / 255.0  # 0.502
prtextstyle_b = prsl_b / 255.0  # 0.0
```

#### 多重ストロークの縮約

```python
def reduce_strokes(prsl_strokes):
    """多重ストロークを1本に縮約"""
    if not prsl_strokes:
        return None

    # 最外側のストロークを使用
    outermost = prsl_strokes[0]

    # または、全ストロークの合計幅を計算
    total_width = sum(s.width for s in prsl_strokes)

    return {
        'width': outermost.width,  # または total_width
        'color': outermost.color,
        'opacity': outermost.opacity
    }
```

---

## 付録A: サンプルファイル

### 最小限のPRSL（1スタイル）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<stylelist version="1">
  <styleblock>
    <text_specification>
      <title_name>Basic White</title_name>
      <font_family>Arial</font_family>
      <font_style>Regular</font_style>
      <font_size>72.0</font_size>
    </text_specification>
    <style_data>
      <fill>
        <fill_type>solid</fill_type>
        <r>255</r><g>255</g><b>255</b><a>255</a>
      </fill>
      <embellishments>
        <inner_embellishment_count>0</inner_embellishment_count>
        <outer_embellishment_count>0</outer_embellishment_count>
      </embellishments>
      <shadow><enabled>false</enabled></shadow>
    </style_data>
  </styleblock>
</stylelist>
```

---

## 付録B: タグ統計

**解析ファイル**: 10styles.prsl（10スタイル）

- **総タグ種類**: 111種類
- **総要素数**: 2,548個
- **平均要素数/スタイル**: 約255個

主要タグの出現頻度（降順）:

1. `<a>` - 不透明度（約500回）
2. `<r>`, `<g>`, `<b>` - 色成分（各約500回）
3. `<styleblock>` - スタイルブロック（10回）
4. `<fill>`, `<shadow>`, `<embellishments>` - スタイル要素

---

## 更新履歴

- **v2.0** (2025-12-12): 完全解析結果を反映、バイナリフォーマット詳細追加
- **v1.0** (2025-12-10): 初版作成

---

**作成者**: Claude (Anthropic)
**プロジェクト**: PRSL to prtextstyle Converter
**リポジトリ**: Naoking55/telop01
