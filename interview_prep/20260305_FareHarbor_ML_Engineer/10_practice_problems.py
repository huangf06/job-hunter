"""
FareHarbor Live Coding 实战训练
时间: 2026-03-04 晚上 - 2026-03-05 早上

使用方法:
1. 关闭 Copilot/自动补全 (模拟 CoderPad 环境)
2. 每道题设置计时器
3. 边写边大声说出思路
4. 写完后运行测试
5. 分析时间/空间复杂度
"""

from collections import Counter, defaultdict, deque
from functools import reduce
import heapq
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np


# ============================================================================
# 题目 1: 数据处理 (15分钟)
# ============================================================================

def user_purchase_summary(purchases):
    """
    计算每个用户的总消费和购买次数

    输入:
    purchases = [
        {"user_id": 1, "amount": 100, "date": "2024-01-01"},
        {"user_id": 2, "amount": 200, "date": "2024-01-02"},
        {"user_id": 1, "amount": 150, "date": "2024-01-03"},
    ]

    输出:
    {
        1: {"total": 250, "count": 2},
        2: {"total": 200, "count": 1}
    }

    要求:
    1. 用 defaultdict
    2. 处理边界: 空列表、负金额
    3. 分析时间复杂度
    """
    # TODO: 你的代码
    pass


# 测试
if __name__ == "__main__":
    purchases = [
        {"user_id": 1, "amount": 100, "date": "2024-01-01"},
        {"user_id": 2, "amount": 200, "date": "2024-01-02"},
        {"user_id": 1, "amount": 150, "date": "2024-01-03"},
    ]
    result = user_purchase_summary(purchases)
    print("题目1 测试:")
    print(result)
    # 期望: {1: {"total": 250, "count": 2}, 2: {"total": 200, "count": 1}}

    # 边界测试
    print(user_purchase_summary([]))  # 空列表
    print(user_purchase_summary([{"user_id": 1, "amount": -50, "date": "2024-01-01"}]))  # 负金额


# ============================================================================
# 题目 2: Top K 频繁元素 (20分钟)
# ============================================================================

def top_k_frequent(nums, k):
    """
    返回出现频率最高的 k 个元素

    输入: nums = [1,1,1,2,2,3], k = 2
    输出: [1, 2]

    要求:
    1. 时间复杂度 O(n log k)
    2. 用 Counter + heap
    3. 测试边界: k=0, k>len(nums), 空数组
    """
    # TODO: 你的代码
    pass


# 测试
if __name__ == "__main__":
    print("\n题目2 测试:")
    print(top_k_frequent([1,1,1,2,2,3], 2))  # [1, 2]
    print(top_k_frequent([1], 1))  # [1]
    print(top_k_frequent([], 0))  # []
    print(top_k_frequent([1,2,3], 5))  # [1, 2, 3] (k > len)


# ============================================================================
# 题目 3: Supervised ML - 用户购买预测 (25分钟)
# ============================================================================

def train_purchase_predictor():
    """
    用户购买预测

    数据:
    - age: 年龄
    - num_visits: 访问次数
    - avg_session_time: 平均停留时间 (秒)
    - purchased: 是否购买 (0/1)

    任务:
    1. 特征工程: 添加 visits_per_age, engagement_score
    2. Train/test split (80/20, random_state=42)
    3. 训练 RandomForest
    4. 计算 precision, recall, F1
    5. 返回 feature importance
    """
    # 数据
    data = pd.DataFrame({
        "age": [25, 35, 45, 30, 50, 28, 40, 55, 32, 38],
        "num_visits": [10, 5, 20, 15, 3, 12, 8, 2, 18, 6],
        "avg_session_time": [300, 150, 600, 450, 100, 350, 200, 80, 550, 180],
        "purchased": [1, 0, 1, 1, 0, 1, 0, 0, 1, 0]
    })

    # TODO: 你的代码
    # 1. 特征工程
    # data["visits_per_age"] = ...
    # data["engagement_score"] = ...

    # 2. Split
    # X = ...
    # y = ...
    # X_train, X_test, y_train, y_test = ...

    # 3. Train
    # model = RandomForestClassifier(...)
    # model.fit(...)

    # 4. Evaluate
    # y_pred = ...
    # precision = ...
    # recall = ...
    # f1 = ...

    # 5. Feature importance
    # importance = ...

    pass


# 测试
if __name__ == "__main__":
    print("\n题目3 测试:")
    train_purchase_predictor()


# ============================================================================
# 题目 4: Unsupervised ML - 用户分群 (20分钟)
# ============================================================================

def cluster_users():
    """
    用户分群

    数据:
    - user_id
    - total_spent: 总消费
    - num_purchases: 购买次数

    任务:
    1. 计算 avg_order_value = total_spent / num_purchases
    2. 标准化特征 (StandardScaler)
    3. KMeans 聚类 (k=3, random_state=42)
    4. 分析每个簇的特征 (均值)
    5. 返回每个用户的簇标签
    """
    # 数据
    data = pd.DataFrame({
        "user_id": range(1, 11),
        "total_spent": [1000, 5000, 200, 3000, 150, 4500, 300, 2500, 100, 4000],
        "num_purchases": [10, 50, 5, 30, 3, 45, 8, 25, 2, 40],
    })

    # TODO: 你的代码
    # 1. 特征工程
    # data["avg_order_value"] = ...

    # 2. 标准化
    # scaler = StandardScaler()
    # X_scaled = ...

    # 3. 聚类
    # kmeans = KMeans(...)
    # labels = ...

    # 4. 分析
    # data["cluster"] = labels
    # print(data.groupby("cluster").mean())

    pass


# 测试
if __name__ == "__main__":
    print("\n题目4 测试:")
    cluster_users()


# ============================================================================
# 题目 5: 复杂度分析快速练习
# ============================================================================

def complexity_quiz():
    """
    快速说出每段代码的时间复杂度 (30秒内)
    """

    # 1. 单层循环
    def func1(n):
        for i in range(n):
            print(i)
    # 答案: O(n)

    # 2. 嵌套循环
    def func2(n):
        for i in range(n):
            for j in range(n):
                print(i, j)
    # 答案: O(n²)

    # 3. 三角循环
    def func3(n):
        for i in range(n):
            for j in range(i):
                print(i, j)
    # 答案: O(n²)  # 0+1+2+...+(n-1) = n(n-1)/2

    # 4. 排序 + 遍历
    def func4(nums):
        nums.sort()
        for num in nums:
            print(num)
    # 答案: O(n log n)  # sort 主导

    # 5. 哈希表计数
    def func5(nums):
        d = {}
        for num in nums:
            d[num] = d.get(num, 0) + 1
        return d
    # 答案: O(n) 时间, O(n) 空间

    # 6. 二分查找
    def func6(arr, target):
        left, right = 0, len(arr) - 1
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1
    # 答案: O(log n)

    # 7. Counter + most_common
    def func7(nums, k):
        counter = Counter(nums)
        return counter.most_common(k)
    # 答案: O(n + k log n)  # Counter O(n), most_common O(n log n)

    print("复杂度分析练习 - 检查你的答案!")


# ============================================================================
# 明早热身题 (07:00-07:30)
# ============================================================================

def find_kth_largest(nums, k):
    """
    找出数组中第 k 大的元素

    输入: nums = [3,2,1,5,6,4], k = 2
    输出: 5

    要求: 不看答案，手写
    """
    # TODO: 你的代码
    pass


def is_anagram(s1, s2):
    """
    判断两个字符串是否是 anagram

    输入: s1 = "listen", s2 = "silent"
    输出: True

    要求: 不看答案，手写
    """
    # TODO: 你的代码
    pass


def merge_sorted_arrays(arr1, arr2):
    """
    合并两个有序数组

    输入: arr1 = [1,3,5], arr2 = [2,4,6]
    输出: [1,2,3,4,5,6]

    要求: 不看答案，手写
    """
    # TODO: 你的代码
    pass


# 测试
if __name__ == "__main__":
    print("\n明早热身题:")
    print(find_kth_largest([3,2,1,5,6,4], 2))  # 5
    print(is_anagram("listen", "silent"))  # True
    print(merge_sorted_arrays([1,3,5], [2,4,6]))  # [1,2,3,4,5,6]


# ============================================================================
# 运行所有测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("FareHarbor Live Coding 实战训练")
    print("=" * 80)
    print("\n开始训练! 记住:")
    print("1. 关闭 Copilot/自动补全")
    print("2. 设置计时器")
    print("3. 边写边说出思路")
    print("4. 写完后测试")
    print("5. 分析复杂度")
    print("\n加油! 💪\n")
