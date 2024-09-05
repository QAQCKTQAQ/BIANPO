import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime
import os
import csv
from scipy.interpolate import PchipInterpolator
import numpy as np


def get_file_paths(start_time, end_time, base_directory='./data_directory'):
    start_date = pd.to_datetime(start_time)
    end_date = pd.to_datetime(end_time)

    file_paths = []

    current_date = start_date
    while current_date <= end_date:
        year = current_date.strftime('%Y')
        month = current_date.strftime('%m')

        directory_path = os.path.join(base_directory, year, month)
        if os.path.exists(directory_path):
            for file_name in os.listdir(directory_path):
                if file_name.endswith('.csv'):
                    file_path = os.path.join(directory_path, file_name)
                    file_paths.append(file_path)

        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    return file_paths


def smooth_curve(x, y):
    # 对数据进行线性插值和PCHIP平滑处理
    # 将 x 和 y 转换为 numpy 数组以便处理
    x = np.array(x)
    y = np.array(y)

    # 先去掉重复的 x 值及对应的 y 值
    x_unique, unique_indices = np.unique(x, return_index=True)
    y_unique = y[unique_indices]

    # 如果没有有效的数据点，则直接返回
    if len(x_unique) == 0 or len(y_unique) == 0:
        return np.array([]), np.array([])

    # 进行线性插值来填补空白数据
    x_interp = np.arange(x_unique.min(), x_unique.max() + 1)
    interp_func = np.interp(x_interp, x_unique, y_unique)

    # 使用 PCHIP 进行平滑处理
    pchip = PchipInterpolator(x_interp, interp_func)
    x_new = np.linspace(x_unique.min(), x_unique.max(), 300)
    y_smooth = pchip(x_new)

    return x_new, y_smooth


def visualize_power_data(file_paths, start_time=None, end_time=None):
    output_dir = './data_directory/image'
    os.makedirs(output_dir, exist_ok=True)
    data_frames = []

    def load_device_id_map(map_file_path):
        device_id_map = {}
        with open(map_file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                device_id_map[row['device_id']] = row['point_number']
        return device_id_map

    device_id_map = load_device_id_map('./config/device_id_map.csv')

    for file_path in file_paths:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        if start_time:
            start_time = pd.to_datetime(start_time)
            df = df[df['timestamp'] >= start_time]
        if end_time:
            end_time = pd.to_datetime(end_time)
            df = df[df['timestamp'] <= end_time]

        data_frames.append(df)

    combined_df = pd.concat(data_frames, ignore_index=True)

    for device_serial in combined_df['device_serial'].unique():
        device_data = combined_df[combined_df['device_serial'] == device_serial]

        plt.figure(figsize=(20, 12))

        # 绘制 solar_panel_power 的平滑折线图
        x, y = smooth_curve(device_data['timestamp'].astype(np.int64) // 10**9, device_data['solar_panel_power'])
        if len(x) > 0 and len(y) > 0:
            plt.plot(pd.to_datetime(x, unit='s'), y, label='Solar Panel Power', color='blue')

        # 绘制 led_power 的平滑折线图
        x, y = smooth_curve(device_data['timestamp'].astype(np.int64) // 10**9, device_data['led_power'])
        if len(x) > 0 and len(y) > 0:
            plt.plot(pd.to_datetime(x, unit='s'), y, label='LED Power', color='green')

        # 绘制 battery_percent 的平滑折线图
        x, y = smooth_curve(device_data['timestamp'].astype(np.int64) // 10**9, device_data['battery_percent'])
        if len(x) > 0 and len(y) > 0:
            plt.plot(pd.to_datetime(x, unit='s'), y, label='Battery Percent', color='red')

        plt.title(f'Device Serial: {device_serial}')
        plt.xlabel('Timestamp')
        plt.ylabel('Value')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        point_number = device_id_map.get(device_serial, device_serial)
        output_file = os.path.join(output_dir, f'{point_number}_plot.png')
        plt.savefig(output_file)

        plt.show()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='处理一些命令行参数')
    parser.add_argument('--start_time', type=str, help='指定开始时间，格式为YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--end_time', type=str, help='指定结束时间，格式为YYYY-MM-DD HH:MM:SS')
    args = parser.parse_args()

    today_str = datetime.now().strftime('%Y-%m-%d')
    default_start_time = f"{today_str} 00:00:00"
    default_end_time = f"{today_str} 23:59:59"

    start_time = args.start_time if args.start_time else default_start_time
    end_time = args.end_time if args.end_time else default_end_time

    file_paths = get_file_paths(start_time, end_time)
    visualize_power_data(file_paths, start_time, end_time)
