# Bianpo Visualization

## 项目简介

`Bianpo Visualization` 是一个用于可视化电力系统数据的 Python 项目。项目从指定 API 获取设备的电力数据，并将其存储为 CSV 文件。用户可以通过命令行指定时间范围，生成并保存折线图，展示设备的电力消耗情况。

## 目录结构

```bash
bianpo_visualization/
│
├── config/               # 配置文件目录，挂载到数据卷
│   └── device_id_map.csv  # 设备ID到点位编号的映射表
├── data_directory/       # 数据存储目录，挂载到数据卷
│   ├── 2024/  # 存放对应年份的数据
│   │   └── 09/  # 当年9月的数据
│   │       ├── 2024-09-ZJ-LS-JY_1-0001.csv  # 一号设备24年9月的数据
│   │       ├── 2024-09-ZJ-LS-JY_1-0002.csv  # 二号设备24年9月的数据
│   │       └── 2024-09-ZJ-LS-JY_1-0003.csv  # 三号设备24年9月的数据
│   └── image/  # 存放生成的可视化图片
│       ├── ZJ-LS-JY_1-0001_plot.png  # 一号设备生成的图片
│       ├── ZJ-LS-JY_1-0002_plot.png  # 二号设备生成的图片
│       └── ZJ-LS-JY_1-0003_plot.png  # 三号设备生成的图片
├── powersystem_client.py # 主程序，用于采集数据
├── visualize.py          # 可视化程序，生成折线图
├── Dockerfile            # 用于生成 Docker 镜像的文件
└── requirements.txt      # 项目依赖文件
```

## 安装与使用

### 创建数据卷

#### 创建配置类数据卷
`docker volume create bianpo_visualization_config`

#### 创建数据存储数据卷
`docker volume create bianpo_visualization_data_directory`

### 项目运行
运行此代码时项目已经自动开始采集数据
```docker run -d -v bianpo_visualization_config:/app/config -v bianpo_visualization_data_directory:/app/data_directory --name bianpo_visualization_container bianpo_visualization```

使用方法
该代码效果为指定账号密码运行采集程序，当不指定时有默认账号密码
`python powersystem_client.py --username '需要指定的账号' --password '需要指定的密码'`
该代码效果为指定数据可视化的开始时间点和截至时间点，不指定时默认将当天数据进行可视化
`python visualize.py --start_time 'YYYY-MM-DD HH:MM:SS' --end_time 'YYYY-MM-DD HH:MM:SS'`

## 注意事项
采集定时结束功能，暂时无法在打包成镜像化后使用 其他功能呢运行正常
去重功能导致数据量少时报错
只有表格没有数据时报错
没有表格没有数据只有文件时报错
