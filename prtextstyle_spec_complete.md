# prtextstyle（Essential Graphics Style）完全仕様書 v1.0（詳細版）

---

## 1. prtextstyle の全体構造

prtextstyle は以下の構造で構成される：

1. **XML構造（PremiereData）**
2. **Fill / Stroke / Shadow の Base64 バイナリ（TLV構造）**

---

## 2. XML の代表構造（EG）

```xml
<PremiereData Version="3">
 <StyleProjectItem>
   <Component>
     <Params>
       <Param Index="0" ObjectRef="40"/> ← Fill
       <Param Index="1" ObjectRef="41"/> ← Transform
       <Param Index="11" ObjectRef="50"/> ← Stroke Width
       <Param Index="12" ObjectRef="51"/> ← Stroke Color
       <Param Index="21" ObjectRef="60"/> ← Parent rotate
     </Params>
   </Component>
 </StyleProjectItem>
</PremiereData>
```

---

## 3. Base64 バイナリ（TLV）構造の解説

### TLV：Tag / Length / Value

- **T (Tag)** = 1–2 bytes  
- **L (Length)** = 2–4 bytes  
- **V (Value)** = データ本体（可変）

例：`05 00 30 00 FF FF 00 00 …`

---

## 4. GradientStop の 48bytes 完全構造（確定版）

```
00–03 : Offset (float32)
04–07 : Midpoint (float32)
08–11 : R (uint32 or uint8 padded)
12–15 : G
16–19 : B
20–23 : Alpha
24–47 : 未知領域（色追従ブロック・内部補完パラメータ）
```

Stop数により 48bytes × N が並ぶ。

---

## 5. Stroke の仕様（EG側）

### EG では **ストロークは 1 本のみ**

項目一覧：

|項目|型|説明|
|---|---|---|
|Width|float32|
|Color|RGB（TLV内で表現）|
|Opacity|0–255|
|Position|Inside/Outside（自動）|

---

## 6. Shadow の仕様

TLV では以下の float32 群で格納：

- x offset
- y offset
- blur
- spread
- color（RGB + Alpha）  

---

## 7. 角度（Angle）の float32 化法則

### 実測から得た確定式：

```
angle_float = radians(angle_deg)
bytes = float32(angle_float)
```

例：45°  
→ 0.785398163 → `3f 49 0f db`

---

## 8. prtextstyle が保持できるスタイル要素

|要素|保持|備考|
|---|---|---|
|Fill 単色|○||
|Fill グラデ 2–3色|○||
|多色グラデ（4+）|△|Premiere が無理やり縮約|
|Stroke 単色|○|1本のみ|
|Stroke 多重|×|縮約必要|
|Shadow|○||
|光沢|×|グラデ変換|
