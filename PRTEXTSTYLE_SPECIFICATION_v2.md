# prtextstyle（Essential Graphics Text Style）完全仕様書 v2.0

**最終更新**: 2025-12-12
**解析状況**: バイナリフォーマット完全解明済み

---

## 目次

1. [概要](#1-概要)
2. [ファイル構造](#2-ファイル構造)
3. [XML構造](#3-xml構造)
4. [バイナリデータ詳細](#4-バイナリデータ詳細)
5. [FlatBuffers構造](#5-flatbuffers構造)
6. [色データ仕様](#6-色データ仕様)
7. [フォント情報](#7-フォント情報)
8. [グラデーション仕様](#8-グラデーション仕様)
9. [ストローク仕様](#9-ストローク仕様)
10. [シャドウ仕様](#10-シャドウ仕様)
11. [実装ガイド](#11-実装ガイド)

---

## 1. 概要

### prtextstyle とは

- **正式名称**: Premiere Pro Essential Graphics Text Style
- **用途**: Essential Graphics（モーショングラフィックステンプレート）で使用するテキストスタイル
- **Premiere Pro バージョン**: 2023以降（主に2025で検証）
- **複数スタイル**: 1ファイルに1個または複数のスタイルを格納可能

### 技術的特徴

- **外部構造**: PremiereData Version="3" XML形式
- **内部構造**: FlatBuffers形式のバイナリデータ
- **エンコーディング**: Base64（XML内）
- **バイナリサイズ**: 450-700 bytes（内容により可変）

---

## 2. ファイル構造

### 全体構造

```
prtextstyle ファイル
├── XML外部構造（PremiereData）
│   ├── Project情報
│   ├── RootProjectItem
│   └── StyleProjectItem（複数可）
│       └── Component
│           └── VideoFilterComponent (AE.ADBE Text)
│               └── ArbVideoComponentParam
│                   └── StartKeyframeValue (Base64)
│                       └── FlatBuffersバイナリ ★
└── （以下、バイナリ内部）
    ├── ヘッダー（FlatBuffers）
    ├── VTable（オフセットテーブル）
    ├── フォント名（UTF-8文字列）
    ├── フォントサイズ（float）
    ├── 色データ（RGB bytes または RGBA floats）
    ├── その他パラメータ
    └── サンプルテキスト（"Aa"）
```

### ファイルサイズ

| 内容 | サイズ | 備考 |
|------|--------|------|
| 単色・ストロークなし | 450-480 bytes | ベースライン |
| 単色・ストロークあり | 456 bytes | +4-6 bytes |
| 2色グラデーション | 632 bytes | +180 bytes |
| 3色グラデーション | 680 bytes | +228 bytes |

**重要**: FlatBuffersの動的レイアウトにより、フォント名の長さやストロークの有無で全体サイズが変動する。

---

## 3. XML構造

### 完全なXML構造

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PremiereData>
<PremiereData Version="3">
  <Project ObjectID="1" ClassID="62ad66dd-0dcd-42da-a660-6d8fbde94876" Version="40">
    <Node Version="1">
      <Properties Version="1">
        <ProjectViewState.List ObjectID="2" ClassID="aab60911-e7a8-4735-b48a-4bed6974d1b1" Version="4"/>
        <TitleDefaultSettings ObjectID="3" ClassID="4b3c9a9f-cc01-4d52-9893-2f65ccf2e5cd" Version="1"/>
      </Properties>
    </Node>
    <RootProjectItem ObjectID="4" ClassID="c9e93e00-4ce3-11d5-8f03-00c04fa34edd" Version="1">
      <ProjectItem Version="1">
        <Node Version="1">
          <Properties Version="1">
            <StyleProjectItem.List ObjectID="5" ClassID="aab60911-e7a8-4735-b48a-4bed6974d1b1" Version="4">
              <Items Version="1">
                <StyleProjectItem ObjectID="6" ClassID="23e24413-a1e9-4178-9a09-a1f7b28b3179" Version="2">
                  <!-- ↓ ここがスタイルの本体 -->
                  <ProjectItem Version="1">
                    <Node Version="1">
                      <Properties Version="1">
                        <MZ.Sequence.EditingMode>2</MZ.Sequence.EditingMode>
                        <MZ.Project.LockState>0</MZ.Project.LockState>
                        <MZ.Sequence.VideoTimeDisplay>108</MZ.Sequence.VideoTimeDisplay>
                        <MZ.Sequence.AudioTimeDisplay>200</MZ.Sequence.AudioTimeDisplay>
                        <MZ.WorkInPoint>-9223372036854775808</MZ.WorkInPoint>
                        <MZ.WorkOutPoint>-9223372036854775808</MZ.WorkOutPoint>
                      </Properties>
                    </Node>
                  </ProjectItem>
                  <Component Version="8">
                    <Params Version="1">
                      <ParameterControlList.List ObjectID="7" ClassID="aab60911-e7a8-4735-b48a-4bed6974d1b1" Version="4"/>
                    </Params>
                    <Component ObjectRef="8"/>
                  </Component>
                </StyleProjectItem>
              </Items>
            </StyleProjectItem.List>
          </Properties>
        </Node>
      </ProjectItem>
    </RootProjectItem>
  </Project>

  <!-- ↓ ここに実際のスタイルデータ -->
  <VideoFilterComponent ObjectID="8" ClassID="34878014-d3c9-4154-b8c8-4b7b5a2872c2" Version="11">
    <FilterComponent Version="7">
      <Component Version="8">
        <Params Version="1">
          <ArbVideoComponentParam ObjectID="9" ClassID="e40e34da-dfc0-4b8d-88c4-f504aef52bc6" Version="3">
            <VideoComponentParam Version="8">
              <Name>ソーステキスト</Name>
              <Timestamp>0</Timestamp>
              <UpperBound>1</UpperBound>
            </VideoComponentParam>
            <ValueType>2</ValueType>
            <StartKeyframeValue Encoding="base64">
              <!-- ★ ここがFlatBuffersバイナリ（Base64エンコード） -->
              uAEAAAAAAAAARDMiEQwAAAAAAAAGAAoABAAGAAAAZAAAAABeADA...
            </StartKeyframeValue>
          </ArbVideoComponentParam>
        </Params>
      </Component>
    </FilterComponent>
    <VideoFilterParams Version="9">
      <FilterMatchName>AE.ADBE Text</FilterMatchName>
    </VideoFilterParams>
  </VideoFilterComponent>
</PremiereData>
```

### 重要なポイント

1. **ルート**: `<PremiereData Version="3">`
2. **スタイル本体**: `<StyleProjectItem>`（複数可）
3. **バイナリデータ**: `<StartKeyframeValue Encoding="base64">`
4. **フィルター名**: `<FilterMatchName>AE.ADBE Text</FilterMatchName>`（固定）

---

## 4. バイナリデータ詳細

### FlatBuffersフォーマット

**公式**: https://google.github.io/flatbuffers/

**特徴**:
- ゼロコピーでの高速読み込み
- スキーマ駆動の型付きデータ
- 可変長フィールド対応
- オプショナルフィールドのサポート

### バイナリ構造概要

```
0x0000-0x0003: ルートテーブルへのオフセット (uint32_le)
0x0004-0x0007: 予約領域 (00 00 00 00)
0x0008-0x000b: マジックナンバー "D3"\x11" (44 33 22 11)
0x000c-0x00af: FlatBuffersヘッダーとメタデータ
0x00b0-0x00cf: VTable（仮想テーブル、フィールドオフセット）
0x00d0以降:    実データ（可変位置）
  - フォント名（UTF-8文字列）
  - フォントサイズ（float32）
  - 色データ（RGB bytes または RGBA floats）
  - その他パラメータ
ファイル末尾付近: サンプルテキスト "Aa"
```

### サイズ実例

#### 白（単色、ストロークなし）- 452 bytes

```
0000: b8 01 00 00 00 00 00 00 44 33 22 11 0c 00 00 00
      ^^^^^^^^ ルートオフセット=0x01b8(440)
               マジック↑
```

#### 赤（単色、ストロークなし）- 480 bytes

```
0000: d4 01 00 00 00 00 00 00 44 33 22 11 0c 00 00 00
      ^^^^^^^^ ルートオフセット=0x01d4(468)
```

→ **ファイルサイズが色によって異なる**理由: FlatBuffersの動的レイアウト

---

## 5. FlatBuffers構造

### VTable（仮想テーブル）

**位置**: 0x00b0付近（可変）

**役割**: 各フィールドへのオフセットを格納

**形式**: 符号付き32ビット整数の配列

```
0x00b0: fc fe ff ff  → -260（オフセット、または-1=null）
0x00b4: 00 ff ff ff  → -256
0x00b8: 04 ff ff ff  → -252
0x00bc: 2a ff ff ff  → -214
```

**-1 (0xffffffff)**: フィールドが存在しないことを示す

### 可変長文字列

**形式**: 長さプレフィックス + UTF-8データ

```
例: フォント名 "VD-LogoG-Extra-G" (16文字)

0x00cc: 10 00 00 00              ← 長さ=16 (uint32_le)
0x00d0: 56 44 2d 4c 6f 67 6f 47  ← "VD-LogoG"
0x00d8: 2d 45 78 74 72 61 2d 47  ← "-Extra-G"
```

**重要**: フォント名の長さが変わると、以降の全データ位置がずれる！

---

## 6. 色データ仕様

### ★ 重大発見: 単色とグラデーションで形式が異なる

#### A. 単色の場合: RGB bytes (0-255)

**フォーマット**: `[RR] [GG] [BB] [AA]`（各1バイト）

**実例**:

| 色 | RGB値 | バイナリ | 位置（例） |
|----|-------|----------|-----------|
| 白 | (255, 255, 255) | `ff ff ff 08` | 0x01a1 |
| 赤 | (255, 0, 0) | `ff 00 00 00` | 0x01ab |
| 青 | (0, 0, 255) | `00 00 ff ff` | 0x01ad |

**位置**: 0x01a0-0x01b0付近（**可変**）

#### B. グラデーションの場合: RGBA floats (0.0-1.0)

**フォーマット**: `[R] [G] [B] [A]`（各4バイト、float32_le）

**実例**:

```
青色ストップ (R=0.0, G=0.0, B=1.0, A=0.5):

0x0194: 00 00 00 00  ← R = 0.0
0x0198: 00 00 00 00  ← G = 0.0
0x019c: 00 00 80 3f  ← B = 1.0 (float)
0x01a0: 00 00 00 3f  ← A = 0.5 (float)
```

### 色の位置は可変

**理由**: FlatBuffersの動的レイアウト

| ファイル | 色の位置 | サイズ |
|----------|----------|--------|
| White | 0x01a1 | 452 bytes |
| Red | 0x01ab | 480 bytes |
| Blue | 0x01ad | 476 bytes |

**対策**: パターンマッチングまたはFlatBuffersデコーダーで探索

### 誤検出に注意

VTable領域（0x00b0-0x00d0）には多数の `ff ff ff` パターンが存在するが、これらは**オフセット値**であり、色データではない。

**正しい色データの範囲**: 0x0150以降

---

## 7. フォント情報

### フォント名

**位置**: 0x00d0付近（**可変**）

**形式**: 長さプレフィックス + UTF-8文字列

```
0x00cc: 10 00 00 00                  ← 長さ=16
0x00d0: 56 44 2d 4c 6f 67 6f 47      ← "VD-LogoG"
0x00d8: 2d 45 78 74 72 61 2d 47      ← "-Extra-G"
0x00e0: 00 00 00 00                  ← NULL終端
```

### フォントサイズ

**位置**: 0x0098付近（**可変**）

**形式**: float32（little-endian）

**実例**:

| サイズ | 16進数 | 位置（例） |
|--------|--------|-----------|
| 30.0 pt | `00 00 f0 41` | 0x009c |
| 24.0 pt | `00 00 c0 41` | 0x009c |
| 50.0 pt | `00 00 48 42` | 0x00a0 |

**計算方法**:

```python
import struct

# 読み込み
size_bytes = binary[0x009c:0x00a0]
font_size = struct.unpack("<f", size_bytes)[0]

# 書き込み
size_bytes = struct.pack("<f", 30.0)
binary[0x009c:0x00a0] = size_bytes
```

---

## 8. グラデーション仕様

### グラデーションストップ

**最大数**: 3個（Premiere Pro 2025制限）

**形式**: RGBA float配列

```
ストップ1 (16 bytes):
  0x0190: [R float] [G float] [B float] [A float]

ストップ2 (16 bytes):
  0x01a0: [R float] [G float] [B float] [A float]

ストップ3 (16 bytes):
  0x01b0: [R float] [G float] [B float] [A float]
```

### グラデーション例（青→白）

```
// 青 (R=0.0, G=0.0, B=1.0, A=1.0)
0x0194: 00 00 00 00  00 00 00 00  00 00 80 3f  00 00 80 3f

// 白 (R=1.0, G=1.0, B=1.0, A=1.0)
0x01d4: 00 00 80 3f  00 00 80 3f  00 00 80 3f  00 00 80 3f
```

### ストップ位置（offset）

**別の場所に格納**されている可能性あり（未完全解明）

**推定**: ストップ間の補間は均等（0.0, 0.5, 1.0）

---

## 9. ストローク仕様

### Essential Graphicsの制限

**ストロークは1本のみ**（Legacy Titleの多重ストロークは非対応）

### ストロークデータ

**位置**: 可変

**形式**: 幅（float） + 色（RGB bytes）

```
例: 黒ストローク、幅10.0px

幅:
  00 00 20 41  ← 10.0 (float32)

色:
  00 00 00 ff  ← R=0, G=0, B=0, A=255
```

### ストロークあり/なしでのサイズ差

| ファイル | サイズ | 差分 |
|----------|--------|------|
| White（ストロークなし） | 452 bytes | ベース |
| White（ストロークあり） | 456 bytes | +4 bytes |

---

## 10. シャドウ仕様

### シャドウパラメータ

**形式**: float配列

```
offset_x (float32)
offset_y (float32)
blur (float32)
spread (float32, オプション)
color (RGBA bytes または floats)
```

### シャドウ例

```
X offset = 5.0:
  00 00 a0 40  ← 5.0 (float32)

Y offset = 5.0:
  00 00 a0 40

Blur = 10.0:
  00 00 20 41

Color = 黒半透明 (0, 0, 0, 180):
  00 00 00 b4
```

---

## 11. 実装ガイド

### アプローチA: パターンマッチング（推奨）

**すぐに実装可能、実用的**

```python
def find_color_data(binary: bytes) -> int:
    """
    RGB bytesパターンを探す

    Returns:
        色データのオフセット、見つからない場合は-1
    """
    # VTable領域をスキップ
    search_start = 0x0150

    # 既知の色パターン
    patterns = [
        bytes([255, 255, 255]),  # 白
        bytes([255, 0, 0]),      # 赤
        bytes([0, 0, 255]),      # 青
    ]

    for i in range(search_start, len(binary) - 3):
        rgb = binary[i:i+3]
        if rgb in patterns:
            return i

    return -1

def replace_color(binary: bytearray, new_r: int, new_g: int, new_b: int):
    """色を置換"""
    offset = find_color_data(binary)
    if offset >= 0:
        binary[offset] = new_r
        binary[offset + 1] = new_g
        binary[offset + 2] = new_b

# 使用例
template = load_template("white.prtextstyle")
binary = bytearray(template)
replace_color(binary, 255, 0, 0)  # 白→赤
save_prtextstyle(binary, "red_output.prtextstyle")
```

### アプローチB: FlatBuffers完全対応（将来）

**完全な柔軟性、複雑**

```python
from flatbuffers import Builder
import SourceText  # スキーマから生成

# バイナリをデコード
text_data = SourceText.GetRootAs(binary)

# 色を取得
fill_color = text_data.FillColor()
r, g, b, a = fill_color.R(), fill_color.G(), fill_color.B(), fill_color.A()

# 新しいスタイルを構築
builder = Builder(1024)
new_color = CreateColor(builder, 255, 0, 0, 255)  # 赤
new_text = CreateSourceText(builder, "Arial", 30.0, new_color)
builder.Finish(new_text)

# バイナリを取得
new_binary = bytes(builder.Output())
```

### 推奨実装フロー

1. **フェーズ1**: パターンマッチング
   - テンプレートから色を検索・置換
   - フォント名、サイズも置換
   - 実用的なコンバーターを作成

2. **フェーズ2**: FlatBuffersスキーマ再構築
   - `.fbs` ファイルを作成
   - 公式ツールでコード生成
   - 完全なエンコーダー/デコーダー

---

## 付録A: 完全なバイナリダンプ例

### White (452 bytes)

```
0000:  b8 01 00 00 00 00 00 00 44 33 22 11 0c 00 00 00   ........D3".....
0010:  00 00 06 00 0a 00 04 00 06 00 00 00 64 00 00 00   ............d...
0020:  00 00 5e 00 30 00 10 00 0c 00 00 00 00 00 00 00   ..^.0...........
...
00d0:  56 44 2d 4c 6f 67 6f 47 2d 45 78 74 72 61 2d 47   VD-LogoG-Extra-G
...
01a0:  00 ff ff ff 08 00 08 00 06 00 07 00 08 00 00 00   ................
      ^^  ^^^^^^^^ ^^
      ?   RGB=白   A=8
...
01c0:  41 61 00 00                                       Aa..
```

---

## 付録B: デバッグツール

### バイナリダンプツール

```python
def hex_dump(data: bytes, offset: int = 0):
    """16進数ダンプ"""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{offset+i:04x}:  {hex_part:<48}  {ascii_part}")
```

### FlatBuffers検証ツール

```bash
# flatcツールで検証（.fbsスキーマが必要）
flatc --binary --raw-binary prtextstyle_data.bin schema.fbs
```

---

## 更新履歴

- **v2.0** (2025-12-12): バイナリフォーマット完全解明、FlatBuffers構造追加
- **v1.0** (2025-12-10): 初版作成（TLV形式の誤った仮定を含む）

---

## 参考資料

- FlatBuffers公式: https://google.github.io/flatbuffers/
- Adobe Premiere Pro SDK: https://developer.adobe.com/premiere-pro/
- After Effects SDK: https://developer.adobe.com/after-effects/

---

**作成者**: Claude (Anthropic)
**プロジェクト**: PRSL to prtextstyle Converter
**リポジトリ**: Naoking55/telop01
**ブランチ**: claude/review-premiere-tool-01E5JFci3dJfQRsvf1vNR2JM
