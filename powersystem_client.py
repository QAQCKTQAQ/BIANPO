import requests
import schedule
import pandas as pd
import os
import argparse
import threading
import time
from datetime import datetime
import csv
class powersystem_client():

    # 设备ID到点位编号的映射表
    DEVICE_ID_MAP = {}

    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.load_device_id_map('./config/device_id_map.csv')

    def load_device_id_map(self, map_file_path):
        if os.path.exists(map_file_path):
            with open(map_file_path, mode='r') as file:
                reader = csv.DictReader(file)
                self.DEVICE_ID_MAP = {row['device_id']: row['point_number'] for row in reader}
        else:
            raise FileNotFoundError(f"config file not found: {map_file_path}")

    def start_updateStatus(self):
        # 在开始数据收集之前，首先对所有设备状态进行一次更新
        print("INFO: 更新所有设备状态...")
        client.get_accessToken()  # 确保获取到有效的 accessToken
        for attempt in range(3):
            try:
                deviceListApiUrl = "http://xmnengjia.com/sdLamp/api/external/deviceList"
                deviceListData = {"accessToken": client.accessToken, "pageNumber": 1, "pageSize": 100}
                deviceListResp = requests.post(deviceListApiUrl, deviceListData)
                deviceListResp.raise_for_status()
                deviceListRespJson = deviceListResp.json()

                if deviceListRespJson.get('success') is False:
                    raise ValueError(deviceListRespJson.get('msg'))

                deviceListRespData = deviceListRespJson.get('data')
                deviceListRespDataList = deviceListRespData.get('list')

                # 对所有设备状态进行一次更新
                for device in deviceListRespDataList:
                    device_serial = device.get('serial')
                    client.updateStatus(client.accessToken, device_serial)

                print("INFO: 所有设备状态更新完成")
                break  # 如果成功更新设备状态，则跳出重试循环

            except (requests.RequestException, ValueError) as e:
                print(f"ERROR: 更新设备状态失败 (第{attempt + 1}次): {e}")
                if attempt >= 2:
                    print("多次重试失败，放弃设备状态更新。")

    def get_accessToken(self):
        print("Username:" + self.username + ", Password:" + self.password)
        # curl -X POST -H "Content-Type:application/x-www-form-urlencoded" "http://xmnengjia.com/sdLamp/api/external/accessToken?username=15691610692&password=a15691610692"
        api_url = "http://xmnengjia.com/sdLamp/api/external/accessToken"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"username": self.username, "password": self.password}
        resp = requests.post(api_url,data,headers = headers)
        res_json = resp.json()
        accessToken = res_json.get('data')
        if accessToken is not None:
            self.accessToken = accessToken
            print("INFO: " + "get accesstoken success,accesstoken is " + self.accessToken)
        else:
            print("ERROR: " + resp.text)
            exit(1)

    def get_deviceStatus(self):
        # 获取设备数据
        def fetch_device_data(device_serial, retry_count=4):
            success = False
            for attempt in range(retry_count):
                try:
                    deviceStatusApiUrl = "http://xmnengjia.com/sdLamp/api/external/deviceStatus"
                    deviceStatusData = {"accessToken": self.accessToken, "serial": device_serial}
                    deviceStatusResp = requests.post(deviceStatusApiUrl, deviceStatusData)
                    deviceStatusResp.raise_for_status()  # 捕获HTTP错误
                    deviceStatusJson = deviceStatusResp.json()

                    if deviceStatusJson.get('success') is False:
                        raise ValueError(deviceStatusJson.get('msg'))

                    deviceStatusJsonData = deviceStatusJson.get('data')
                    solar_panel_power = deviceStatusJsonData.get('solar_panel_power')
                    led_power = deviceStatusJsonData.get('led_power')
                    timestamp = deviceStatusJsonData.get('timestamp')
                    battery_percent = deviceStatusJsonData.get('battery_percent')

                    print("device_serial: " + device_serial +
                          ", solar_panel_power: " + str(solar_panel_power) +
                          ", led_power: " + str(led_power) +
                          ", timestamp: " + timestamp +
                          ", battery_percent: " + str(battery_percent))

                    # 存储获取到的数据
                    self.store_data(device_serial, solar_panel_power, led_power, timestamp, battery_percent)
                    success = True
                    break  # 成功后退出重试循环

                except (requests.RequestException, ValueError) as e:
                    print(f"ERROR: 获取设备数据失败 (第{attempt + 1}次): {e}")
                    if attempt >= retry_count - 1:
                        print("多次重试失败，放弃获取该设备的数据。")

                finally:
                    # 无论获取设备信息成功还是失败，都更新设备状态
                    self.updateStatus(self.accessToken, device_serial)

            return success

        for attempt in range(3):
            try:
                # 获取设备列表 获取成功后调用上面的方法开新线程获取设备数据
                self.get_accessToken()
                deviceListApiUrl = "http://xmnengjia.com/sdLamp/api/external/deviceList"
                deviceListData = {"accessToken": self.accessToken, "pageNumber": 1, "pageSize": 100}
                deviceListResp = requests.post(deviceListApiUrl, deviceListData)
                deviceListResp.raise_for_status()
                deviceListRespJson = deviceListResp.json()

                if deviceListRespJson.get('success') is False:
                    raise ValueError(deviceListRespJson.get('msg'))

                deviceListRespData = deviceListRespJson.get('data')
                deviceListRespDataList = deviceListRespData.get('list')
                threads = []

                for device in deviceListRespDataList:
                    device_serial = device.get('serial')
                    t = threading.Thread(target=fetch_device_data, args=(device_serial,))
                    t.start()
                    threads.append(t)

                for t in threads:
                    t.join()

                break  # 如果成功获取设备列表，则跳出重试循环

            except (requests.RequestException, ValueError) as e:
                print(f"ERROR: 获取设备列表失败 (第{attempt + 1}次): {e}")
                if attempt >= 2:
                    print("多次重试失败，放弃获取设备列表。")

    def updateStatus(self,accessToken,serial):
            deviceStatusUpdateUrl = "http://xmnengjia.com/sdLamp/api/external/updateStatus"
            deviceStatusData = {"accessToken": accessToken,"serial": serial}
            deviceStatusUpdateresp = requests.post(deviceStatusUpdateUrl,deviceStatusData)
            deviceStatusUpdaterespJson = deviceStatusUpdateresp.json()
            success = deviceStatusUpdaterespJson.get('success')
            if success is not True:
                print(deviceStatusUpdaterespJson)

    def store_data(self, device_serial, solar_panel_power, led_power, timestamp, battery_percent):
        # 将时间戳转换为东八区时间
        timestamp = pd.to_numeric(timestamp)
        timestamp = pd.to_datetime(timestamp, unit='ms')
        timestamp = timestamp.tz_localize('UTC').tz_convert('Asia/Shanghai')

        # 获取年份和月份
        year = timestamp.strftime('%Y')
        month = timestamp.strftime('%m')

        # 通过设备序列号查找对应的点位编号
        point_code = self.DEVICE_ID_MAP.get(device_serial, None)

        if point_code is None:
            raise ValueError(f"未找到设备序列号 {device_serial} 对应的点位编号")

        # 生成文件夹路径和文件名
        base_directory = os.path.join('./data_directory', year, month)
        os.makedirs(base_directory, exist_ok=True)  # 如果文件夹不存在，则自动创建

        data_file_name = f"{year}-{month}-{point_code}.csv"
        data_file_path = os.path.join(base_directory, data_file_name)

        # 准备要写入的数据
        new_data = {
            "device_serial": device_serial,
            "solar_panel_power": solar_panel_power,
            "led_power": led_power,
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # 转换后的时间
            "battery_percent": battery_percent
        }
        df = pd.DataFrame([new_data])

        # 检查文件是否存在，如果存在则附加数据，如果不存在则创建新的文件
        if os.path.exists(data_file_path):
            df.to_csv(data_file_path, mode='a', header=False, index=False)
        else:
            df.to_csv(data_file_path, mode='w', header=True, index=False)

    def start_collector(self, stop_time=None):
        # 设定调度任务
        schedule.every(5).minutes.do(self.get_deviceStatus)
        try:
            while True:
                # 运行待处理的任务
                schedule.run_pending()
                time.sleep(1)

                # 检查是否需要停止
                if stop_time and datetime.now() >= stop_time:
                    print("已达到指定停止时间，停止采集。")
                    break
        except KeyboardInterrupt:
            print("INFO: 数据收集程序被用户中断。")

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动数据收集程序')
    parser.add_argument('--stop_time', type=str, help='指定数据收集程序的停止时间，格式为 YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--username', type=str, default='', help='用户名')
    parser.add_argument('--password', type=str, default='', help='密码')
    args = parser.parse_args()

    stop_time = args.stop_time
    if stop_time:
        stop_time = datetime.strptime(stop_time, '%Y-%m-%d %H:%M:%S')

    client = powersystem_client(args.username, args.password)

    # 启动前更新设备状态
    client.start_updateStatus()

    # 启动数据收集程序
    print("INFO: 启动数据收集程序...")

    # 启动数据收集程序的线程
    collector_thread = threading.Thread(target=client.start_collector, args=(stop_time,))
    collector_thread.start()
    try:
        collector_thread.join()  # 等待子线程完成
    except KeyboardInterrupt:
        print("INFO: 主程序被用户中断。")