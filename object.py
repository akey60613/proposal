import random
import matplotlib.pyplot as plt
from math import sqrt

# 計算兩點距離的函數
def distance(p1, p2):
    return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# 基礎類別 (所有通訊設備的共通屬性)
class CommunicationEntity:
    def __init__(self, entity_id, x, y, z, range_):
        self.id = entity_id
        self.x = x
        self.y = y
        self.z = z
        self.range = range_

    def __repr__(self):
        return f"{self.__class__.__name__}(ID={self.id}, Pos=({self.x}, {self.y}, {self.z}), Range={self.range})"

class Satellite(CommunicationEntity):
    def __init__(self, sat_id, x, y, range_):
        super().__init__(sat_id, x, y, 500, range_)

# 基地台 (BS)
class BaseStation(CommunicationEntity):
    def __init__(self, bs_id, x, y, range_):
        super().__init__(bs_id, x, y, 0, range_)

# UAV 類別
class UAV(CommunicationEntity):
    def __init__(self, uav_id, bs, existing_uavs, existing_rsus, uav_range):
        attempt = 0
        while attempt < 1000:
            x = random.randint(bs.x - bs.range, bs.x + bs.range)
            y = random.randint(bs.y - bs.range, bs.y + bs.range)
            
            if distance((x, y), (bs.x, bs.y)) <= bs.range: #讓UAV跟RSU或UAV之間的範圍不要重疊
                if all(distance((x, y), (r.x, r.y)) > r.range + uav_range for r in existing_rsus):
                    if all(distance((x, y), (u.x, u.y)) > u.range + uav_range for u in existing_uavs):
                        super().__init__(uav_id, x, y, random.randint(50, 150), uav_range)
                        return
            attempt += 1
        print(f"⚠️ 無法放置 UAV {uav_id}，請減少 UAV 數量或增加 BS 範圍。")

# RSU 類別
class RSU(CommunicationEntity):
    def __init__(self, rsu_id, bs, existing_rsus, rsu_range):
        attempt = 0
        while attempt < 1000:
            x = random.randint(bs.x - bs.range, bs.x + bs.range)
            y = random.randint(bs.y - bs.range, bs.y + bs.range)

            if distance((x, y), (bs.x, bs.y)) <= bs.range:#讓RSU跟RSU或UAV之間的範圍不要重疊
                if all(distance((x, y), (r.x, r.y)) > r.range + rsu_range for r in existing_rsus):
                    super().__init__(rsu_id, x, y, 0, rsu_range)
                    return
            attempt += 1
        print(f"⚠️ 無法放置 RSU {rsu_id}，請減少 RSU 數量或增加 BS 範圍。")

# 車輛 (Vehicle)，可以隨機分佈在 BS 內或 BS 外
class Vehicle(CommunicationEntity):
    def __init__(self, vehicle_id,sat, bs, existing_vehicles, existing_uavs, existing_rsus, vehicle_range):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        super().__init__(vehicle_id, x, y, 0, vehicle_range)

        # 紀錄車輛連接的設備
        self.connected_to = self.find_nearest_connection(sat,bs, existing_uavs, existing_rsus)

    def find_nearest_connection(self,sat, bs, uavs, rsus):
        """ 找到最近的設備 (BS、UAV、RSU)，並確認是否在通訊範圍內 """
        candidates = [(bs, distance((self.x, self.y), (bs.x, bs.y)))]  # 先加入 BS
        
        for uav in uavs:#先把所有設備加入candidates內
            candidates.append((uav, distance((self.x, self.y), (uav.x, uav.y))))
        
        for rsu in rsus:
            candidates.append((rsu, distance((self.x, self.y), (rsu.x, rsu.y))))

        # 根據距離排序
        candidates.sort(key=lambda x: x[1])

        # 選擇最近且在範圍內的設備
        for entity, dist in candidates:
            if dist <= entity.range:
                return entity

        return sat  # 如果沒有可連接的設備，回傳 Sat


# 環境類別
class Environment:
    def __init__(self, num_uavs, num_rsus, num_vehicles):
        self.sat = Satellite(0, 0, 0, 5000)
        self.bs = BaseStation(0, 500, 500, 300)

        self.rsus = []#部屬設備
        for i in range(num_rsus):
            rsu = RSU(i, self.bs, self.rsus, rsu_range=100)
            if isinstance(rsu, RSU) and hasattr(rsu, 'id'):
                self.rsus.append(rsu)

        self.uavs = []
        for i in range(num_uavs):
            uav = UAV(i, self.bs, self.uavs, self.rsus, uav_range=100)
            if isinstance(uav, UAV) and hasattr(uav, 'id'):
                self.uavs.append(uav)

        self.vehicles = []
        for i in range(num_vehicles):
            vehicle = Vehicle(i,self.sat,self.bs, self.vehicles, self.uavs, self.rsus, vehicle_range=50)
            if isinstance(vehicle, Vehicle) and hasattr(vehicle, 'id'):
                self.vehicles.append(vehicle)

    def display_environment(self):
        print(self.sat)
        print(self.bs)

        for entity in self.uavs + self.rsus:
            print(entity)

        for vehicle in self.vehicles:
            connection = vehicle.connected_to
            connection_str = f" -> Connected to {connection.__class__.__name__} (ID={connection.id})" if connection else " -> No connection"
            print(vehicle, connection_str)


    def plot_environment(self):#製圖
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(0, 1000)
        ax.set_ylim(0, 1000)

        bs_circle = plt.Circle((self.bs.x, self.bs.y), self.bs.range, color='blue', fill=False, linestyle='dashed', label="BS Range")
        ax.add_patch(bs_circle)
        ax.scatter(self.bs.x, self.bs.y, c='blue', marker='o', label="BS")

        for u in self.uavs:
            ax.scatter(u.x, u.y, c='red', marker='^', label="UAV" if u == self.uavs[0] else "")
            ax.add_patch(plt.Circle((u.x, u.y), u.range, color='red', fill=False))

        for r in self.rsus:
            ax.scatter(r.x, r.y, c='green', marker='s', label="RSU" if r == self.rsus[0] else "")
            ax.add_patch(plt.Circle((r.x, r.y), r.range, color='green', fill=False))

        for v in self.vehicles:
            ax.scatter(v.x, v.y, c='orange', marker='d', label="Vehicle" if v == self.vehicles[0] else "")
            ax.add_patch(plt.Circle((v.x, v.y), v.range, color='orange', fill=False))

        ax.set_xlabel("X Position")
        ax.set_ylabel("Y Position")
        ax.set_title("BS, UAV, RSU, Vehicle Deployment (No Overlapping)")

        plt.legend()
        plt.show()# 測試環境

env = Environment(num_uavs=3, num_rsus=3, num_vehicles=5)
env.display_environment()
env.plot_environment()