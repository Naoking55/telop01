# PRTL → prtextstyle 変換プログラム設計書 v1.0（詳細版）

---

## 1. 全体アーキテクチャ

```
PRSL / PRTL
     ↓（XML + バイナリ抽出）
 Legacy JSON 中間形式
     ↓（正規化）
 EG JSON 中間形式
     ↓（XML + Base64 生成）
 prtextstyle 出力
```

---

## 2. Legacy → EG 正規化テーブル

|Legacy|EG|変換方針|
|---|---|---|
|多重ストローク|1本|最外側のみ採用|
|光沢|線形グラデ3色|Gloss → GradientStop 3本化|
|塗り不透明度|非対応|破棄|
|影|対応|そのまま float32 変換|
|中央揃えなどの微調整|非対応|破棄|

---

## 3. GradientStop 生成アルゴリズム（確定版）

```
for stop in stops:
    offset_bytes = float32(stop.offset)
    midpoint_bytes = float32(stop.midpoint)
    r,g,b,a = stop.color
    append TLV packet:
       offset_bytes
       midpoint_bytes
       r_pad
       g_pad
       b_pad
       a_pad
       unknown_24bytes
```

unknown_24bytes は EG 内部で自動補完されるので **PRTL のものをそのままコピー** する。

---

## 4. 多重ストローク縮約

### 選択ルール：

1. 最外側ストロークを優先  
2. 塗りつぶしサイズと視覚一致性を確保  
3. 色、太さはそのストロークの値を採用  

---

## 5. シャドウの変換公式

```
x_px → float32(x_px)
y_px → float32(y_px)
blur → float32
spread → float32
color RGBA → TLV
```

---

## 6. 変換プログラムのディレクトリ構成案

```
converter/
  ├─ parser/
  │    ├─ prsl_reader.py
  │    ├─ prtl_reader.py
  ├─ normalizer/
  │    ├─ stroke_reduce.py
  │    ├─ gradient_mapper.py
  │    └─ shadow_mapper.py
  ├─ generator/
  │    ├─ xml_builder.py
  │    └─ base64_encoder.py
  ├─ ui/
  │    └─ preview_renderer.py
  └─ main.py
```

---

## 7. スタイルプレビューの生成方式

- Pillow 使用  
- ストローク太さ / グラデーションを正確再現  
- EG と視覚一致性を重視  
