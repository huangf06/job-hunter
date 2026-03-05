# 今晚实战训练计划 - FareHarbor Live Coding

**时间**: 2026-03-04 22:40 - 2026-03-05 08:30
**目标**: 通过 Round 1 Technical Screen (45分钟 live coding)

---

## 官方要求解读

### 1. Easy-to-medium coding problem with bug-free solution
- **不是 LeetCode Hard**，是实用的数据处理/算法题
- **Bug-free** = 必须测试，处理边界情况
- **Python** = 语法必须熟练，不能卡在基础语法上

### 2. Work with small datasets, discuss complexity
- 会给你数据 (list/dict/DataFrame)
- 要求: 处理数据 + 分析时间/空间复杂度
- 例子: "这个是 O(n²)，可以用 hash table 优化到 O(n)"

### 3. Apply supervised/unsupervised ML techniques
- 不是理论题，是**写代码实现**
- Supervised: 分类/回归 (sklearn pipeline)
- Unsupervised: 聚类/降维 (KMeans, PCA)

### 4. CoderPad-style editor (syntax highlighting only)
- **没有自动补全**
- **没有 linter**
- **没有 AI copilot**
- 必须靠肌肉记忆写出正确代码

---

## 🎯 今晚训练计划 (22:40 - 01:00, 2小时20分钟)

### Phase 1: Python 语法肌肉记忆 (22:40-23:20, 40分钟)

**工具**: 纸+笔 (模拟 CoderPad 无补全环境)

**必练清单**:

```python
# 1. 数据结构操作 (10分钟)
# List
nums = [1, 2, 3, 4, 5]
nums.append(6)          # O(1)
nums.insert(0, 0)       # O(n)
nums.pop()              # O(1)
nums.remove(3)          # O(n)
nums.index(4)           # O(n)
nums.sort()             # O(n log n)

# Dict
d = {"a": 1, "b": 2}
d["c"] = 3              # O(1)
d.get("d", 0)           # O(1)
d.pop("a")              # O(1)
d.keys(), d.values(), d.items()

# Set
s = {1, 2, 3}
s.add(4)                # O(1)
s.remove(2)             # O(1)
s1.intersection(s2)     # O(min(len(s1), len(s2)))
s1.union(s2)            # O(len(s1) + len(s2))

# 2. List comprehension (5分钟)
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
matrix = [[1,2], [3,4], [5,6]]
flat = [item for row in matrix for item in row]
word_lens = {word: len(word) for word in ["hello", "world"]}

# 3. 常用函数 (10分钟)
# Sorting
sorted(nums)                    # 返回新列表
sorted(nums, reverse=True)
sorted(words, key=len)          # 按长度排序
sorted(dicts, key=lambda x: x["score"])  # 按字段排序

# Filtering
list(filter(lambda x: x > 0, nums))
[x for x in nums if x > 0]      # 更 Pythonic

# Mapping
list(map(lambda x: x*2, nums))
[x*2 for x in nums]             # 更 Pythonic

# Reducing
from functools import reduce
reduce(lambda x, y: x+y, nums)  # 求和
sum(nums)                       # 更简洁

# 4. String 操作 (5分钟)
s = "hello world"
s.split()                       # ["hello", "world"]
s.split(",")
" ".join(["a", "b", "c"])       # "a b c"
s.strip()                       # 去除首尾空格
s.replace("world", "python")
s.startswith("hello")
s.endswith("world")
s.lower(), s.upper()

# 5. Collections 模块 (10分钟)
from collections import Counter, defaultdict, deque

# Counter - 计数
words = ["apple", "banana", "apple", "cherry"]
counter = Counter(words)
counter.most_common(2)          # [("apple", 2), ...]

# defaultdict - 避免 KeyError
from collections import defaultdict
d = defaultdict(int)            # 默认值 0
d = defaultdict(list)           # 默认值 []
d = defaultdict(lambda: [])     # 自定义默认值

# deque - 双端队列
q = deque([1, 2, 3])
q.append(4)                     # 右端添加
q.appendleft(0)                 # 左端添加
q.pop()                         # 右端弹出
q.popleft()                     # 左端弹出
```

**验证**: 闭上眼睛，能默写出每个操作的语法

---

### Phase 2: 实战编码训练 (23:20-00:40, 80分钟)

**工具**: VS Code (关闭 Copilot/补全)，计时器

#### 题目 1: 数据处理 (15分钟)

```python
"""
给定用户购买记录，计算每个用户的总消费和购买次数

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
2. 分析时间复杂度
3. 处理边界: 空列表、负金额
"""

# 你的代码 (15分钟内完成)
```

#### 题目 2: 算法实现 (20分钟)

```python
"""
Top K 频繁元素

给定整数数组和 k，返回出现频率最高的 k 个元素

输入: nums = [1,1,1,2,2,3], k = 2
输出: [1, 2]

要求:
1. 时间复杂度 O(n log k)
2. 用 Counter + heap
3. 测试边界: k=0, k>len(nums), 空数组
"""

from collections import Counter
import heapq

def top_k_frequent(nums, k):
    # 你的代码
    pass

# 测试
assert set(top_k_frequent([1,1,1,2,2,3], 2)) == {1, 2}
assert top_k_frequent([1], 1) == [1]
assert top_k_frequent([], 0) == []
```

#### 题目 3: Supervised ML (25分钟)

```python
"""
用户购买预测

给定用户特征，预测是否会购买

数据:
- age: 年龄
- num_visits: 访问次数
- avg_session_time: 平均停留时间 (秒)
- purchased: 是否购买 (0/1)

任务:
1. 特征工程: 添加 visits_per_age, engagement_score
2. Train/test split (80/20)
3. 训练 RandomForest
4. 计算 precision, recall, F1
5. 解释哪些特征最重要
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score

# 数据
data = pd.DataFrame({
    "age": [25, 35, 45, 30, 50, 28, 40, 55, 32, 38],
    "num_visits": [10, 5, 20, 15, 3, 12, 8, 2, 18, 6],
    "avg_session_time": [300, 150, 600, 450, 100, 350, 200, 80, 550, 180],
    "purchased": [1, 0, 1, 1, 0, 1, 0, 0, 1, 0]
})

# 你的代码 (25分钟内完成)
# 1. 特征工程
# 2. Split
# 3. Train
# 4. Evaluate
# 5. Feature importance
```

#### 题目 4: Unsupervised ML (20分钟)

```python
"""
用户分群

给定用户行为数据，用 KMeans 聚类分为 3 组

数据:
- user_id
- total_spent: 总消费
- num_purchases: 购买次数
- avg_order_value: 平均订单价值

任务:
1. 标准化特征 (StandardScaler)
2. KMeans 聚类 (k=3)
3. 分析每个簇的特征 (均值)
4. 可视化 (可选)
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np

# 数据
data = pd.DataFrame({
    "user_id": range(1, 11),
    "total_spent": [1000, 5000, 200, 3000, 150, 4500, 300, 2500, 100, 4000],
    "num_purchases": [10, 50, 5, 30, 3, 45, 8, 25, 2, 40],
})

# 你的代码 (20分钟内完成)
```

---

### Phase 3: 复杂度分析训练 (00:40-01:00, 20分钟)

**练习**: 快速分析时间/空间复杂度

```python
# 题目: 说出每段代码的时间复杂度

# 1.
for i in range(n):
    print(i)
# 答案: O(n)

# 2.
for i in range(n):
    for j in range(n):
        print(i, j)
# 答案: O(n²)

# 3.
for i in range(n):
    for j in range(i):
        print(i, j)
# 答案: O(n²)  # 0+1+2+...+(n-1) = n(n-1)/2

# 4.
nums.sort()
for num in nums:
    print(num)
# 答案: O(n log n)  # sort 主导

# 5.
d = {}
for num in nums:
    d[num] = d.get(num, 0) + 1
# 答案: O(n) 时间, O(n) 空间

# 6.
def binary_search(arr, target):
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

# 7.
from collections import Counter
counter = Counter(nums)
top_k = counter.most_common(k)
# 答案: O(n + k log n)  # Counter O(n), most_common O(n log n)
```

**练习方法**: 设置 30 秒计时器，快速说出答案

---

## 🌅 明早训练计划 (07:00-08:30)

### 07:00-07:30: 热身编码

**不看答案，手写**:

```python
# 1. 写一个函数: 找出数组中第 k 大的元素
def find_kth_largest(nums, k):
    # 你的代码
    pass

# 2. 写一个函数: 判断两个字符串是否是 anagram
def is_anagram(s1, s2):
    # 你的代码
    pass

# 3. 写一个函数: 合并两个有序数组
def merge_sorted_arrays(arr1, arr2):
    # 你的代码
    pass
```

### 07:30-08:00: ML 快速复习

**口述回答** (30秒内):

1. Precision vs Recall 的区别？什么时候用哪个？
2. 如何处理 imbalanced data？
3. Overfitting 的表现和解决方法？
4. Train/test split 的目的？
5. KMeans 的工作原理？如何选择 k？

### 08:00-08:30: 环境准备 + 心理建设

- [ ] 测试摄像头/麦克风
- [ ] 关闭所有干扰 (Slack, 邮件, 手机)
- [ ] 准备纸笔、水
- [ ] 深呼吸 (4-7-8 技巧)
- [ ] 告诉自己: "我已经练过了，我能写出 bug-free 的代码"

---

## 📋 面试中的执行清单

### 收到题目后 (前 5 分钟):

1. **理解问题**
   - "让我确认一下: 输入是...，输出是...，对吗？"
   - "有没有数据范围限制？比如数组长度？"
   - "需要处理哪些边界情况？空数组？负数？"

2. **说出思路**
   - "我打算用 dictionary 来存储，因为查找是 O(1)"
   - "我会先用 brute force，然后讨论优化"
   - "时间复杂度目标是 O(n)，空间复杂度 O(n)"

### 编码中 (20-30 分钟):

3. **边写边说**
   - "我现在创建一个 Counter 来统计频率"
   - "这里用 defaultdict(list) 来分组"
   - "让我加个边界检查: if not nums: return []"

4. **写完后测试**
   - "让我用例子测试: 输入 [1,1,2]，输出应该是 [1]"
   - "边界情况: 空数组返回空列表，符合预期"
   - "时间复杂度是 O(n)，因为只遍历一次"

### 讨论环节 (最后 10 分钟):

5. **复杂度分析**
   - "时间复杂度: O(n)，因为..."
   - "空间复杂度: O(n)，用了额外的 dictionary"
   - "可以优化到 O(1) 空间，但需要..."

6. **提问**
   - "在生产环境中，数据量有多大？"
   - "这个功能的性能要求是什么？"
   - "有没有实时性要求？"

---

## ⚠️ 常见陷阱

### Python 语法陷阱:

```python
# ❌ 错误: 默认参数是可变对象
def add_item(item, lst=[]):
    lst.append(item)
    return lst

# ✅ 正确:
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst

# ❌ 错误: 闭包变量绑定
funcs = [lambda: i for i in range(3)]
# 所有 lambda 都返回 2

# ✅ 正确:
funcs = [lambda i=i: i for i in range(3)]

# ❌ 错误: 字典遍历时修改
for key in d:
    if key == "bad":
        del d[key]  # RuntimeError

# ✅ 正确:
for key in list(d.keys()):
    if key == "bad":
        del d[key]
```

### ML 常见错误:

```python
# ❌ 错误: 没有 train/test split
model.fit(X, y)
score = model.score(X, y)  # 过拟合的分数

# ✅ 正确:
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model.fit(X_train, y_train)
score = model.score(X_test, y_test)

# ❌ 错误: 没有标准化
kmeans = KMeans(n_clusters=3)
kmeans.fit(X)  # 特征尺度不同会影响聚类

# ✅ 正确:
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
kmeans.fit(X_scaled)
```

---

## 🎯 成功标准

### 今晚必须达到:
- [ ] 能在 15 分钟内写出 bug-free 的数据处理代码
- [ ] 能在 20 分钟内实现一个 ML pipeline (特征工程 + 训练 + 评估)
- [ ] 能在 10 秒内说出任何代码的时间复杂度
- [ ] 能流利使用 Counter, defaultdict, heapq (不查文档)

### 明天面试中:
- [ ] 0 语法错误 (靠肌肉记忆)
- [ ] 主动测试代码 (不等面试官提醒)
- [ ] 清晰解释思路 (边想边说)
- [ ] 正确分析复杂度 (有理有据)

---

## 💪 心理建设

**你已经有的优势**:
- ✅ 6 年 Python 经验
- ✅ 做过生产 ML 系统 (GLP, Baiquan)
- ✅ 处理过真实数据 (不是玩具数据集)
- ✅ 知道什么是 bug-free (生产环境教会你的)

**他们想看到的**:
- ✅ 能写出能跑的代码 (不是伪代码)
- ✅ 能处理边界情况 (工程师思维)
- ✅ 能清晰沟通 (团队协作能力)
- ✅ 能分析权衡 (成熟的判断力)

**记住**:
- 这不是算法竞赛，是工程面试
- 他们要的是能解决实际问题的人，不是背题家
- 你已经在生产环境做过这些事了，面试只是展示

---

**现在开始训练！22:40-01:00，2小时20分钟。明天你会感谢今晚的自己。🚀**
