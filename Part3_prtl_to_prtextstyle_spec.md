# Part3: PRTL → prtextstyle 変換アルゴリズム完全設計書（決定版）

（以下に内容をフルで統合し、単一MDとして保存）

## 0. 概要
PRTL → prtextstyle 変換は「完全一致」ではなく「視覚的に最も近いスタイルを生成する」ことを目的とする。
光沢・複数シャドウ・複数ストローク・塗り透明度など、EGP仕様で再現できない項目は近似変換または破棄。

## 1. 変換フロー（確定）
PRTL → 中間JSON（正規化データ） → prtextstyle(XML + Base64)

## 2. 中間JSON仕様（要点）
- fill: {type, colors[], angle, opacity}
- stroke: [{size, color, opacity}]（最外ストロークのみ採用）
- shadow: {dx, dy, blur, color, opacity}（最影響の1つのみ）
- font: {family, style, size, tracking}
- bevel/gloss：gradient 近似に変換

## 3. PRTL → JSON 変換規則（確定）
- グラデーションは stop[] に正規化し、location 0–1 float に変換
- 光沢は 3 stop gradient で近似（high-mid-low）
- Fill opacity は無視（100固定）
- 複数 shadow → 最大 blur のものを採用
- ストロークの順序は外側へ積み重ねる方式 → EGPは単層なので最外層のみ採用

## 4. JSON → prtextstyle 変換ルール
prtextstyle の Base64 は TLV 構造。  
特に **GradientStop 48 byte 構造** は以下に確定：

Offset | Size | Content
------|------|---------
0x00 | 4 | Location(float32)
0x04 | 4 | Midpoint(float32)
0x08 | 4 | R (0–1 float32)
0x0C | 4 | G (0–1 float32)
0x10 | 4 | B (0–1 float32)
0x14 | 4 | A (0–1 float32)
0x18 | 24 | 固定（Gradient 内部識別 padding）

### TLVブロック構成（例）
- FillSolid: Tag 0x20
- FillGradient: Tag 0x21
- Stroke: Tag 0x30
- Shadow: Tag 0x40
- Transform: Tag 0x50

※Tag番号は Adobe 内部実測に基づく（正式名称非公開）

## 5. Gradient 角度の float32 対応（確定）
EGPでは角度は **float32（度数法）** で格納。
例: 90° → 0x42 B4 00 00

## 6. 擬似コード（完全版）

### 6.1 PRTL → JSON
```
data = parse_prtl(file)
json.fill = convert_fill(data)
json.stroke = select_outer_stroke(data.strokes)
json.shadow = select_primary_shadow(data.shadows)
json.font = normalize_font(data.font)
json.transform = normalize_transform(data.transform)
return json
```

### 6.2 JSON → prtextstyle Base64
```
bin = TLV()
bin.add( make_fill_block(json.fill) )
bin.add( make_stroke_block(json.stroke) )
bin.add( make_shadow_block(json.shadow) )
bin.add( make_font_block(json.font) )
bin.add( make_transform_block(json.transform) )
base64 = encode_base64(bin)
xml = wrap_prtextstyle_xml(base64)
return xml
```

## 7. 再現不可能／破棄される項目一覧
- 塗り opacity（EGPに存在しない） → 常に100%
- グラデーションストローク → 単色へ強制変換
- 光沢（複雑） → 3-stop gradient で近似
- 複数ストローク → 最外のみ
- 複数シャドウ → 最影響1つ
- 立体押し出し → 非対応

## 8. 品質保証
視覚一致率 90%以上を目標にするために：
- グラデ location は float32 で高精度化
- RGB は uint8 → float32 に正規化し損失なし
- stroke width は px → pt 換算調整

