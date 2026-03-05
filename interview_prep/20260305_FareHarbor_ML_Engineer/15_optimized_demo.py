"""
FareHarbor Live Coding 实战演练 - 优化版
题目: 用户购买预测

优化点:
1. 特征工程不除以 1000（更简洁）
2. RandomForest 不需要 StandardScaler（更高效）
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# ============================================================================
# 第 1 步: 理解数据 (2 分钟)
# ============================================================================

print("=" * 80)
print("第 1 步: 理解数据")
print("=" * 80)

# 创建示例数据
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

print("\n数据预览:")
print(data.head())

print("\n数据统计:")
print(data.describe())

print("\n缺失值检查:")
print(data.isnull().sum())

print("\n目标变量分布:")
print(data["purchased"].value_counts())

# ============================================================================
# 第 2 步: 特征工程 (5 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 2 步: 特征工程")
print("=" * 80)

# 【边想边说】
# "我打算创建几个新特征:"
# "1. engagement_score: 结合访问次数和停留时间"
# "2. price_per_visit: 价格除以访问次数"
# "3. is_frequent_visitor: 访问次数是否超过中位数"

# 创建新特征（优化版：不除以 1000）
data["engagement_score"] = data["num_visits"] * data["avg_session_time"]
# 解释: 访问次数 * 平均停留时间，衡量用户参与度

data["price_per_visit"] = data["price"] / (data["num_visits"] + 1)
# 解释: 价格相对于访问频率的比值，+1 避免除零

data["is_frequent_visitor"] = (data["num_visits"] > data["num_visits"].median()).astype(int)
# 解释: 二值特征，是否是高频访问用户

print("\n新特征预览:")
print(data[["user_id", "engagement_score", "price_per_visit", "is_frequent_visitor"]].head())

# ============================================================================
# 第 3 步: 准备训练数据 (3 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 3 步: 准备训练数据")
print("=" * 80)

# 【边想边说】
# "我会选择这些特征: age, num_visits, avg_session_time, viewed_reviews, price"
# "加上我们新创建的 engagement_score, price_per_visit, is_frequent_visitor"
# "user_id 不用，因为它只是标识符"

feature_cols = [
    "age", "num_visits", "avg_session_time", "viewed_reviews", "price",
    "engagement_score", "price_per_visit", "is_frequent_visitor"
]

X = data[feature_cols]
y = data["purchased"]

print("\n特征矩阵形状:", X.shape)
print("目标变量形状:", y.shape)

# 【边想边说】
# "现在做 train/test split，用 80/20 分割，设置 random_state 保证可复现"

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("\n训练集大小:", X_train.shape)
print("测试集大小:", X_test.shape)

# 【边想边说】
# "因为我用的是 RandomForest，它对特征尺度不敏感，所以不需要标准化"
# "如果用 Logistic Regression 或 SVM，就需要 StandardScaler"

# ============================================================================
# 第 4 步: 训练模型 (5 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 4 步: 训练模型")
print("=" * 80)

# 【边想边说】
# "我选择 RandomForest，因为:"
# "1. 能处理非线性关系"
# "2. 对特征尺度不敏感（不需要标准化）"
# "3. 能给出特征重要性"
# "4. 不容易过拟合"

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42,
    n_jobs=-1
)

print("\n开始训练...")
model.fit(X_train, y_train)
print("训练完成!")

# ============================================================================
# 第 5 步: 评估模型 (5 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 5 步: 评估模型")
print("=" * 80)

y_pred = model.predict(X_test)

precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print("\n评估指标:")
print(f"Precision: {precision:.3f}")
print(f"Recall: {recall:.3f}")
print(f"F1 Score: {f1:.3f}")

print("\n混淆矩阵:")
cm = confusion_matrix(y_test, y_pred)
print(cm)
print("\n解释:")
print(f"True Negatives: {cm[0,0]}")
print(f"False Positives: {cm[0,1]}")
print(f"False Negatives: {cm[1,0]}")
print(f"True Positives: {cm[1,1]}")

# ============================================================================
# 第 6 步: 特征重要性 (3 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 6 步: 特征重要性")
print("=" * 80)

feature_importance = pd.DataFrame({
    "feature": feature_cols,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print("\n特征重要性排名:")
print(feature_importance)

# ============================================================================
# 第 7 步: 复杂度分析 (2 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 7 步: 复杂度分析")
print("=" * 80)

print("\n时间复杂度:")
print("- 特征工程: O(n) - 遍历数据一次")
print("- RandomForest 训练: O(n*d*log(n)*T) - n 样本, d 特征, T 树的数量")
print("- 预测: O(d*T) - 每个样本")
print("\n空间复杂度:")
print("- 数据存储: O(n*d)")
print("- 模型存储: O(T*nodes)")

# ============================================================================
# 第 8 步: 边界情况测试
# ============================================================================

print("\n" + "=" * 80)
print("第 8 步: 边界情况测试")
print("=" * 80)

# 测试 1: 低参与度用户
new_user_low = pd.DataFrame({
    "age": [25],
    "num_visits": [1],
    "avg_session_time": [100],
    "viewed_reviews": [0],
    "price": [100],
    "engagement_score": [1 * 100],  # 不除以 1000
    "price_per_visit": [100 / 2],
    "is_frequent_visitor": [0]
})
pred_low = model.predict(new_user_low)
print(f"低参与度用户预测: {'购买' if pred_low[0] == 1 else '不购买'}")

# 测试 2: 高参与度用户
new_user_high = pd.DataFrame({
    "age": [35],
    "num_visits": [20],
    "avg_session_time": [600],
    "viewed_reviews": [1],
    "price": [50],
    "engagement_score": [20 * 600],  # 不除以 1000
    "price_per_visit": [50 / 21],
    "is_frequent_visitor": [1]
})
pred_high = model.predict(new_user_high)
print(f"高参与度用户预测: {'购买' if pred_high[0] == 1 else '不购买'}")

print("\n" + "=" * 80)
print("完成! 总用时: ~25 分钟")
print("=" * 80)

# ============================================================================
# 优化总结
# ============================================================================

print("\n" + "=" * 80)
print("优化总结")
print("=" * 80)

summary = """
✅ 优化点:

1. 特征工程不除以 1000
   - 原因: StandardScaler 会自动处理尺度
   - 好处: 代码更简洁，逻辑更清晰

2. RandomForest 不需要 StandardScaler
   - 原因: 基于树的模型对特征尺度不敏感
   - 好处: 减少一步操作，提高效率

3. 何时需要标准化？
   - Logistic Regression: 需要
   - SVM: 需要
   - Neural Network: 需要
   - RandomForest/XGBoost: 不需要
   - KNN: 需要

💡 面试话术:

"我创建了 engagement_score，直接用访问次数乘以停留时间。
因为我用的是 RandomForest，它对特征尺度不敏感，所以不需要
额外的归一化或标准化。如果用 Logistic Regression，我会用
StandardScaler 标准化所有特征。"
"""

print(summary)
