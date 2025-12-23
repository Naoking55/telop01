# ストローク対応実装計画
**作成日**: 2025-12-23
**ベース**: PRTL ストローク仕様（最新確定版）

## 1. 実装概要

### 1.1 目的
PRSLからprtextstyleへの変換において、ストローク（境界線）を正しく処理する。

### 1.2 重要な仕様ポイント
1. **累積サイズ**: `size_i = Σ(k=1..i) wk`（非累積ではない）
2. **1:1:1対応**: Fragment / Painter / Shader は必ず同数
3. **annotation順**: 1が最内、昇順で外側へ
4. **スケーリング**: UI(px) と PRTL は 1:1（変換なし）
5. **補正事故回避**: 構造が崩れると「100/0/0」に補正される

---

## 2. データ構造の追加

### 2.1 新規データクラス

```python
@dataclass
class StrokeLayer:
    """個々のストローク層"""
    annotation: int          # 1が最内、昇順で外側
    width: float            # UI上の幅（px）
    # 色情報
    is_gradient: bool = False
    # 単色
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255
    # グラデーション（4色グラデ用）
    top_left: Optional[GradientStop] = None
    bottom_right: Optional[GradientStop] = None
    angle: float = 0.0      # グラデ角度（0-360）

@dataclass
class Stroke:
    """ストローク全体（複数層）"""
    enabled: bool = False
    layers: List[StrokeLayer] = None

    def __post_init__(self):
        if self.layers is None:
            self.layers = []

    def get_cumulative_sizes(self) -> List[float]:
        """累積サイズを計算

        Returns:
            [w1, w1+w2, w1+w2+w3, ...]
        """
        cumulative = []
        total = 0.0
        for layer in self.layers:
            total += layer.width
            cumulative.append(total)
        return cumulative

@dataclass
class Style:
    name: str
    fill: Fill
    shadow: Shadow
    stroke: Stroke  # ← 追加
```

---

## 3. PRSLパーサーの拡張

### 3.1 embellishments構造の解析

```python
def parse_prsl(prsl_path: str) -> List[Style]:
    """PRSLファイルを解析"""
    # ... (既存のfill, shadow解析)

    # Stroke解析
    stroke = Stroke(enabled=False)
    embellishments = style_data.find('embellishments')
    if embellishments:
        # Fragment, Painter, Shader を収集
        fragments = embellishments.findall('.//fragment')
        painters = embellishments.findall('.//painter')
        shaders = embellishments.findall('.//shader')

        if len(fragments) > 0 and len(fragments) == len(painters) == len(shaders):
            stroke = parse_stroke_layers(fragments, painters, shaders)

    styles.append(Style(name=name, fill=fill, shadow=shadow, stroke=stroke))
```

### 3.2 parse_stroke_layers 関数

```python
def parse_stroke_layers(fragments, painters, shaders) -> Stroke:
    """ストローク層を解析

    Args:
        fragments: fragment要素のリスト
        painters: painter要素のリスト
        shaders: shader要素のリスト

    Returns:
        Stroke オブジェクト
    """
    layers = []

    # annotation順にソート
    fragments_sorted = sorted(fragments, key=lambda f: int(f.get('annotation', '0')))

    # 累積サイズから各層の幅を逆算
    cumulative_sizes = []
    for frag in fragments_sorted:
        size_elem = frag.find('size')
        if size_elem is not None:
            cumulative_sizes.append(float(size_elem.text))

    # 幅の計算: w_i = size_i - size_{i-1}
    widths = []
    for i, cum_size in enumerate(cumulative_sizes):
        if i == 0:
            widths.append(cum_size)
        else:
            widths.append(cum_size - cumulative_sizes[i-1])

    # 各層のShader情報を解析
    for i, frag in enumerate(fragments_sorted):
        annotation = int(frag.get('annotation', '0'))

        # 対応するShaderを探す
        shader = None
        for s in shaders:
            if int(s.get('annotation', '0')) == annotation:
                shader = s
                break

        if shader is None:
            continue

        # Shader色情報を解析
        layer = StrokeLayer(
            annotation=annotation,
            width=widths[i]
        )

        colouring = shader.find('colouring')
        if colouring:
            fill_type_elem = colouring.find('type')
            fill_type = int(fill_type_elem.text) if fill_type_elem is not None else 5

            if fill_type == 1:  # グラデーション
                # （Fillと同じロジック）
                layer.is_gradient = True
                # ... top_left, bottom_right, angle 解析
            else:  # 単色
                solid = colouring.find('.//solid_colour/all')
                if solid:
                    layer.r = int(float(solid.find('red').text) * 255)
                    layer.g = int(float(solid.find('green').text) * 255)
                    layer.b = int(float(solid.find('blue').text) * 255)
                    layer.a = int(float(solid.find('alpha').text) * 255)

        layers.append(layer)

    return Stroke(enabled=True, layers=layers)
```

---

## 4. prtextstyle出力の実装

### 4.1 XML構造の生成

```python
def create_prtextstyle_xml(styles: List[Style], binaries: List[bytes], output_path: str):
    """prtextstyleXMLファイルを生成（ストローク対応版）"""
    root = ET.Element('PremiereData', Version='3')

    for i, (style, binary) in enumerate(zip(styles, binaries)):
        # StyleProjectItem
        item = ET.SubElement(root, 'StyleProjectItem', ...)

        # ストローク情報を追加（Premiereが期待する構造）
        if style.stroke.enabled and len(style.stroke.layers) > 0:
            cumulative_sizes = style.stroke.get_cumulative_sizes()

            # Embellishments
            embellish = ET.SubElement(item, 'Embellishments')

            # Fragments（累積サイズ）
            for j, (layer, cum_size) in enumerate(zip(style.stroke.layers, cumulative_sizes)):
                frag = ET.SubElement(embellish, 'Fragment', annotation=str(layer.annotation))
                size_elem = ET.SubElement(frag, 'Size')
                size_elem.text = str(cum_size)

            # Painters（1:1:1対応を保証）
            for layer in style.stroke.layers:
                painter = ET.SubElement(embellish, 'Painter',
                                      annotation=str(layer.annotation),
                                      fragment=str(layer.annotation),
                                      shader=str(layer.annotation))

            # Shaders（色情報）
            for layer in style.stroke.layers:
                shader = ET.SubElement(embellish, 'Shader', annotation=str(layer.annotation))

                colouring = ET.SubElement(shader, 'Colouring')
                type_elem = ET.SubElement(colouring, 'Type')

                if layer.is_gradient:
                    type_elem.text = '1'  # グラデーション
                    # 角度変換: PRTL_angle = (270 - UI_angle) % 360
                    prtl_angle = (270 - layer.angle) % 360
                    # ... グラデーション構造生成
                else:
                    type_elem.text = '5'  # 単色
                    solid = ET.SubElement(colouring, 'SolidColour')
                    all_elem = ET.SubElement(solid, 'All')

                    r_elem = ET.SubElement(all_elem, 'Red')
                    r_elem.text = str(layer.r / 255.0)
                    g_elem = ET.SubElement(all_elem, 'Green')
                    g_elem.text = str(layer.g / 255.0)
                    b_elem = ET.SubElement(all_elem, 'Blue')
                    b_elem.text = str(layer.b / 255.0)
                    a_elem = ET.SubElement(all_elem, 'Alpha')
                    a_elem.text = str(layer.a / 255.0)

    # ファイル保存
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
```

---

## 5. テストケース

### 5.1 最小テストケース（3層ストローク: 50/50/50）

```xml
<!-- PRSL入力 -->
<embellishments>
  <fragment annotation="1">
    <size>50</size>  <!-- 累積: 50 -->
  </fragment>
  <fragment annotation="2">
    <size>100</size>  <!-- 累積: 50+50=100 -->
  </fragment>
  <fragment annotation="3">
    <size>150</size>  <!-- 累積: 50+50+50=150 -->
  </fragment>

  <painter annotation="1" fragment="1" shader="1"/>
  <painter annotation="2" fragment="2" shader="2"/>
  <painter annotation="3" fragment="3" shader="3"/>

  <shader annotation="1">
    <colouring>
      <type>5</type>
      <solid_colour>
        <all>
          <red>0.0</red>
          <green>0.933</green>
          <blue>1.0</blue>
        </all>
      </solid_colour>
    </colouring>
  </shader>
  <!-- shader 2, 3 も同様 -->
</embellishments>
```

### 5.2 期待される出力

```
スタイル: テスト3層ストローク
  Stroke 1: 幅=50px, 色=#00eeff (annotation=1)
  Stroke 2: 幅=50px, 色=#ffffff (annotation=2)
  Stroke 3: 幅=50px, 色=#0084ff (annotation=3)
  累積サイズ: [50, 100, 150]
```

### 5.3 補正事故のテスト

**NG例（非累積サイズ）**:
```
Fragment 1: size=50
Fragment 2: size=50  ← 累積ではない（NG）
Fragment 3: size=50  ← 累積ではない（NG）
```
→ Premiereで開くと「100/0/0」に補正される

**OK例（累積サイズ）**:
```
Fragment 1: size=50
Fragment 2: size=100  ← 累積 (50+50)
Fragment 3: size=150  ← 累積 (50+50+50)
```
→ Premiereで正しく表示される

---

## 6. 実装の優先順位

### Phase 1: 基本実装（単色ストロークのみ）
- [ ] データクラス追加
- [ ] PRSLパーサー（単色のみ）
- [ ] 累積サイズ計算
- [ ] prtextstyle出力（Fragment/Painter/Shader）

### Phase 2: グラデーション対応
- [ ] グラデーションストロークのパース
- [ ] 角度変換実装
- [ ] グラデーションShader生成

### Phase 3: テスト＆検証
- [ ] 3層ストローク（50/50/50）でテスト
- [ ] Premiereで動作確認
- [ ] 補正事故が起きないか確認

---

## 7. 既知の制約・注意点

### 7.1 補正事故を回避するために
1. **必ず累積サイズを使用**（非累積は禁止）
2. **Fragment/Painter/Shader数を一致させる**
3. **annotation は 1始まりの連番**
4. **参照整合性を保つ**（fragment="1" → annotation="1"のShaderが存在）

### 7.2 未対応項目（将来の拡張）
- ストロークのぼかし（現在は境界線のみ）
- ストロークの不透明度の個別設定
- 複雑なストロークパターン

---

## 8. 次のアクション

1. **ユーザー確認**: この実装計画でOKか確認
2. **サンプルPRSL作成**: ストローク付きのテストファイルを用意
3. **Phase 1実装**: 基本的なストローク対応を実装
4. **テスト**: Premiereで動作確認

---

**参考文献**:
- PRTL ストローク仕様（最新確定版 / 2025-12-23）
- FIX_SUMMARY.md（既存の修正履歴）
- COMPLETE_CONVERTER_v1.py（現在の実装）
