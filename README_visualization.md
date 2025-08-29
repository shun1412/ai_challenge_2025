# 車の軌跡とコースマップ可視化ツール

このツールは、AI Challenge 2025の車の軌跡データとコースマップを同じグラフ上に描画するためのPythonスクリプトです。

## 機能

- **マップ表示**: OSMファイルから道路マップを読み込み、幅を持つ道路として表示
- **軌跡表示**: 30km/hと15km/hの車の軌跡を異なる色で表示
- **開始・終了点マーク**: 各軌跡の開始点と終了点を明確にマーク
- **高解像度出力**: 300 DPIの高品質な画像として保存
- **速度制限ベースの色分け**: 道路の速度制限に基づいた色分け表示
- **詳細分析**: 速度制限の統計情報とセグメント数表示
- **アニメーション機能**: 車の移動をアニメーションで表示（オプション）

## 必要なファイル

以下のファイルが必要です：

```
aichallenge/workspace/src/aichallenge_submit/
├── aichallenge_submit_launch/map/lanelet2_map.osm
└── simple_trajectory_generator/data/
    ├── raceline_awsim_30km.csv
    └── raceline_awsim_15km.csv
```

## セットアップ

1. 必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な可視化

```bash
python3 visualize_trajectory_and_map_en.py
```

このコマンドを実行すると：
1. マップデータと軌跡データを読み込み
2. 道路マップを幅を持つグレーのポリゴンとして描画
3. 30km/h軌跡を赤線、15km/h軌跡を青線で描画
4. 開始点と終了点をマーク
5. 結果を`trajectory_and_map_visualization.png`として保存
6. グラフを画面に表示

### 拡張版可視化（推奨）

```bash
python3 visualize_trajectory_and_map_enhanced.py
```

このコマンドを実行すると：
1. **基本可視化**: 速度制限に基づいた色分けで道路を表示
2. **詳細可視化**: 速度制限の凡例付きで道路を表示
3. **速度分析**: 各速度制限のセグメント数を統計表示
4. 結果を以下のファイルとして保存：
   - `trajectory_and_map_enhanced.png` (2つのサブプロット)
   - `speed_analysis.png` (速度制限分析)

### 簡単実行

```bash
./run_visualization.sh
```

## 出力ファイル

### 基本版
- **trajectory_and_map_visualization.png**: 基本的な可視化（1MB、高解像度）

### 拡張版
- **trajectory_and_map_enhanced.png**: 2つのサブプロット付き詳細可視化（1.7MB）
- **speed_analysis.png**: 速度制限分析付き可視化（1MB）

## グラフの要素

### 道路表示
- **速度制限ベースの色分け**:
  - 10km/h以下: ライトレッド (#FF6B6B)
  - 11-20km/h: ティール (#4ECDC4)
  - 21-30km/h: ブルー (#45B7D1)
  - 31-40km/h: グリーン (#96CEB4)
  - 41km/h以上: イエロー (#FFEAA7)

### 軌跡表示
- **赤線**: 30km/hでの車の軌跡
- **青線**: 15km/hでの車の軌跡
- **マーカー**: 
  - 円形（o）: 開始点
  - 四角形（s）: 終了点

### その他
- **グリッド**: 座標系の補助線
- **凡例**: 速度制限とセグメント数の統計情報

## 技術詳細

### データ形式
- **OSMファイル**: Lanelet2形式のマップデータ
  - `relation`要素で`lanelet`タイプを定義
  - `left`、`right`、`centerline`のway要素で道路境界を定義
  - `speed_limit`タグで速度制限を定義
- **CSVファイル**: x, y座標とその他の車両情報を含む軌跡データ

### アルゴリズム
1. **Lanelet2解析**: 道路の左右境界線からポリゴン形状を作成
2. **速度制限抽出**: 各道路セグメントの速度制限を取得
3. **色分け**: 速度制限に基づいた色分けを適用
4. **可視化**: matplotlibを使用した高品質な描画

## カスタマイズ

### 道路の色を変更

```python
def get_road_color(speed_limit):
    if speed_limit <= 10:
        return '#FF6B6B'  # 色を変更
    # ... 他の速度制限
```

### 画像サイズを変更

```python
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))  # サイズを変更
```

### 道路の透明度を変更

```python
road_patch = Polygon(road_array, facecolor=road_color, alpha=0.7, ...)  # alpha値を変更
```

## トラブルシューティング

### ファイルが見つからない場合

ファイルパスを確認してください：
```bash
ls -la aichallenge/workspace/src/aichallenge_submit/
```

### 依存関係エラー

必要なパッケージがインストールされているか確認：
```bash
pip list | grep -E "(pandas|matplotlib|numpy)"
```

### メモリ不足

大きなマップファイルの場合、メモリ使用量を削減するために：
- 画像サイズを小さくする
- 不要な道路セグメントを除外する
- 透明度を下げる

### 日本語フォントエラー

日本語版でフォントエラーが発生した場合は、英語版を使用してください：
```bash
python3 visualize_trajectory_and_map_en.py
```

## 統計情報

現在のマップでは以下の統計が確認されています：
- **道路セグメント数**: 15個
- **速度制限**: 10km/h, 15km/h
- **軌跡データ**: 30km/hと15km/hの2種類

## ライセンス

このスクリプトはMITライセンスの下で提供されています。 