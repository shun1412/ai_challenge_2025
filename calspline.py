import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt

def create_spline_function(x_coords, y_coords):
    """
    与えられた座標を通り、滑らかな曲線（3次スプライン）の関数を生成します。

    Args:
        x_coords (list or np.array): x座標のリスト。
        y_coords (list or np.array): y座標のリスト。

    Returns:
        CubicSpline: 任意のx座標に対するy座標を計算できる関数オブジェクト。
    """
    # スプライン補間はx座標が昇順である必要があるため、ソートする
    if not np.all(np.diff(x_coords) > 0):
        sorted_points = sorted(zip(x_coords, y_coords))
        x_sorted, y_sorted = zip(*sorted_points)
    else:
        x_sorted, y_sorted = x_coords, y_coords

    spline_func = CubicSpline(x_sorted, y_sorted)
    return spline_func

# --- ここからがメインの実行部分 ---
if __name__ == '__main__':
    x_original = []
    y_original = []

    print("--- スプライン補間プログラム ---")
    try:
        # 1. 元になる座標データを標準入力から受け取る
        num_points_str = input("データ点の数を入力してください: ")
        num_points = int(num_points_str)
        if num_points < 2:
            raise ValueError("データ点は2つ以上入力してください。")

        print(f"{num_points}個の座標をカンマ区切りで入力してください (例: 3,8)")
        for i in range(num_points):
            while True:
                point_input = input(f"  {i+1}番目の点: ")
                try:
                    x_str, y_str = point_input.split(',')
                    x_original.append(float(x_str))
                    y_original.append(float(y_str))
                    break
                except ValueError:
                    print("  -> 入力形式が正しくありません。再度「x,y」の形式で入力してください。")

        # 2. スプライン補間の関数を作成
        smooth_curve_func = create_spline_function(x_original, y_original)
        print("\n✅ 滑らかな曲線（スプライン関数）を作成しました。")

        # 3. グラフを描画してファイルに保存
        x_smooth = np.linspace(min(x_original), max(x_original), 300)
        y_smooth = smooth_curve_func(x_smooth)

        plt.figure(figsize=(10, 6))
        plt.plot(x_smooth, y_smooth, label='Spline')
        plt.scatter(x_original, y_original, color='red', zorder=5, label='original')
        plt.title('Spline Interpolation')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.legend()
        plt.grid(True)
        
        graph_filename = "spline_curve.png"
        plt.savefig(graph_filename)
        print(f"📈 グラフを '{graph_filename}' として保存しました。\n")

        # 4. x座標を入力してy座標を計算する対話ループ
        print("--- y座標の予測 ---")
        print("x座標を入力するとy座標を計算します。（'q'または'exit'で終了）")
        
        while True:
            x_input = input("計算したいx座標を入力: ")
            
            if x_input.lower() in ['q', 'exit']:
                print("プログラムを終了します。")
                break
                
            try:
                x_val = float(x_input)
                y_pred = smooth_curve_func(x_val)
                print(f"{x_val},{y_pred:.7f}")
            
            except ValueError:
                print("  -> 数値を入力するか、'q'で終了してください。")

    except ValueError as e:
        print(f"\nエラー: {e}")
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")