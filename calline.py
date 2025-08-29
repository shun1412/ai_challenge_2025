def calculate_point_on_line(point1: tuple[float, float], point2: tuple[float, float], x_new: float) -> list[float, float]:
    """
    2点を通る一次関数を求め、新しいx座標に対するy座標を計算します。

    Args:
        point1: 1つ目の点の座標 (x1, y1)。
        point2: 2つ目の点の座標 (x2, y2)。
        x_new: y座標を求めたい新しい点のx座標。

    Returns:
        計算された新しい点の座標 [x_new, y_new]。

    Raises:
        ValueError: 2点のx座標が同じ場合（垂直線）。
    """
    x1, y1 = point1
    x2, y2 = point2

    # 2点のx座標が同じ場合は、傾きが無限大になるため計算不可
    if x1 == x2:
        raise ValueError("エラー: 2点のx座標が同じなため、一次関数を定義できません。")

    # 傾き(a)を計算
    a = (y2 - y1) / (x2 - x1)

    # 切片(b)を計算
    b = y1 - a * x1

    # 新しいx座標に対するy座標を計算
    y_new = a * x_new + b

    return [x_new,round(y_new, 7)]

if __name__ == "__main__":
    print("Starting line detection...")
    
    try:
        # --- 標準入力からの値の受け付け ---
        # 点1の座標を入力
        p1_input = input("1つ目の点の座標をカンマ区切りで入力してください (例: 2,3): ")
        p1 = tuple(map(float, p1_input.split(',')))

        # 点2の座標を入力
        p2_input = input("2つ目の点の座標をカンマ区切りで入力してください (例: 6,11): ")
        p2 = tuple(map(float, p2_input.split(',')))

        num_input = input("計算するx座標の数を入力してください:")
        num_x = int(num_input)
        new_coordinate = [0]*num_x
        # 新しいx座標を入力
        for i in range(num_x):
            x3_input = input(f"{i+1}つ目のx座標を入力してください:")
            x3 = float(x3_input)
            new_coordinate[i] = calculate_point_on_line(p1, p2, x3)
        for j in range(num_x):
            print(f"{j+1}:{new_coordinate[j]}")
        # --- ここまで ---

        # 座標が2つの要素で構成されているかチェック
        # if len(p1) != 2 or len(p2) != 2:
            # raise ValueError("座標はx,yの2つの数値をカンマ区切りで入力してください。")

        # 関数を呼び出して座標を計算
        # new_coordinate = calculate_point_on_line(p1, p2, x3)
        # print(f"点{p1}と点{p2}を通る直線上で、x座標が{x3}の点の座標は {new_coordinate} です。")
        
    except ValueError as e:
        print(f"入力エラー: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}") 