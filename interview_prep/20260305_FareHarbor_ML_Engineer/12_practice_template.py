"""
FareHarbor Live Coding 练习模板
题目: 用户购买预测

时间: 25 分钟
要求: 关闭 Copilot，不看答案，从头写到尾

==================== 题目 ====================
我们有用户浏览活动的数据，想预测他们是否会购买。
请训练一个分类模型并评估效果。

数据字段:
- user_id: 用户ID
- age: 年龄
- num_visits: 过去30天访问次数
- avg_session_time: 平均停留时间(秒)
- viewed_reviews: 是否查看过评论 (0/1)
- price: 活动价格
- purchased: 是否购买 (0/1) - 目标变量

要求:
1. 做必要的特征工程
2. 训练一个分类模型
3. 评估模型效果 (precision, recall, F1)
4. 讨论时间复杂度
5. 测试边界情况

开始计时! ⏱️
================================================
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

# 数据
data = pd.DataFrame({
    "user_id": range(1, 21),
    "age": [25, 35, 45, 30, 50, 28, 40, 55, 32, 38,
            27, 42, 48, 33, 52, 29, 44, 51, 31, 39],
    "num_visits": [10, 5, 20, 15, 3, 12, 8, 2, 18, 6,
                   11, 7, 19, 14, 4, 13, 9, 1, 16, 5],
    "avg_session_time": [300, 150, 600, 450, 100, 350, 200, 80, 550, 180,
                         320, 220, 580, 430, 120, 370, 240, 90, 520, 160],
    "viewed_reviews": [1, 0, 1, 1, 0, 1, 0, 0, 1, 0,
                       1, 0, 1, 1, 0, 1, 0, 0, 1, 0],
    "price": [50, 100, 60, 70, 120, 55, 90, 130, 65, 95,
              52, 85, 62, 72, 125, 57, 92, 135, 67, 97],
    "purchased": [1, 0, 1, 1, 0, 1, 0, 0, 1, 0,
                  1, 0, 1, 1, 0, 1, 0, 0, 1, 0]
})

# ============================================================================
# 第 1 步: 理解数据 (2 分钟)
# ============================================================================

# TODO: 你的代码
df = pd.DataFrame(data)  # 这里直接使用给定的数据
print(df.head(5))
print(df.isnull().sum())
print(df.describe())

# - 查看数据预览
# - 检查缺失值
# - 查看目标变量分布


# ============================================================================
# 第 2 步: 特征工程 (5 分钟)
# ============================================================================

# TODO: 你的代码
df['engagement_score'] = df['num_visits'] * df['avg_session_time']
df['price_per_visit'] = df['price'] / (df['num_visits']+1)
df['is_frequent_visitor'] = (df['num_visits'] > df['num_visits'].median()).astype(int)
# - 创建 engagement_score = num_visits * avg_session_time / 1000
# - 创建 price_per_visit = price / (num_visits + 1)
# - 创建 is_frequent_visitor = (num_visits > median).astype(int)


# ============================================================================
# 第 3 步: 准备训练数据 (3 分钟)
# ============================================================================

# TODO: 你的代码
features = ['age', 'num_visits', 'avg_session_time', 'viewed_reviews', 'price',
            'engagement_score', 'price_per_visit', 'is_frequent_visitor']
X = df[features]
y = df['purchased']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(X_train_scaled.shape)
print(X_test_scaled.shape)
# - 选择特征列
# - 创建 X, y
# - train_test_split (test_size=0.2, random_state=42, stratify=y)
# - StandardScaler 标准化


# ============================================================================
# 第 4 步: 训练模型 (5 分钟)
# ============================================================================

# TODO: 你的代码
# - 创建 RandomForestClassifier
# - fit 训练
model = RandomForestClassifier(random_state=42)
model.fit(X_train_scaled, y_train)

# ============================================================================
# 第 5 步: 评估模型 (5 分钟)
# ============================================================================

# TODO: 你的代码
# - 预测测试集
# - 计算 precision, recall, F1
# - 打印混淆矩阵
y_pred = model.predict(X_test_scaled)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1 Score: {f1:.2f}")
print("Confusion Matrix:")
print(cm)


# ============================================================================
# 第 6 步: 特征重要性 (3 分钟)
# ============================================================================

# TODO: 你的代码
# - 获取 feature_importances_
# - 排序并打印


# ============================================================================
# 第 7 步: 复杂度分析 (2 分钟)
# ============================================================================

# TODO: 口述
# - 时间复杂度: 特征工程 O(?), 训练 O(?), 预测 O(?)
# - 空间复杂度: O(?)


# ============================================================================
# 第 8 步: 边界测试
# ============================================================================

# TODO: 你的代码
# - 测试低参与度用户
# - 测试高参与度用户


# ============================================================================
# 完成后检查清单
# ============================================================================

checklist = """
✅ 检查清单:
[ ] 数据探索 (head, describe, isnull)
[ ] 特征工程 (至少 2-3 个新特征)
[ ] Train/test split (设置 random_state)
[ ] 标准化特征 (fit_transform 训练集, transform 测试集)
[ ] 训练模型 (设置 random_state)
[ ] 评估指标 (precision, recall, F1)
[ ] 混淆矩阵
[ ] 特征重要性
[ ] 复杂度分析
[ ] 边界测试

⏱️ 时间控制:
- 理解数据: 2 分钟
- 特征工程: 5 分钟
- 准备数据: 3 分钟
- 训练模型: 5 分钟
- 评估模型: 5 分钟
- 特征重要性: 3 分钟
- 复杂度分析: 2 分钟
总计: 25 分钟

💡 记住:
1. 边想边说 (不要沉默)
2. 先说思路再写代码
3. 写完后测试
4. 主动讨论权衡
"""

print(checklist)
