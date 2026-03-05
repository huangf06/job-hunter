"""
FareHarbor Live Coding 实战演练
题目: 用户购买预测 (典型的 easy-to-medium ML 问题)

时间: 25 分钟
难度: Medium
业务场景: FareHarbor 预测用户是否会购买活动

==================== 面试官说 ====================
"我们有一些用户浏览活动的数据，想预测他们是否会购买。
请你用这些数据训练一个分类模型，并评估模型效果。"

数据字段:
- user_id: 用户ID
- age: 年龄
- num_visits: 过去30天访问次数
- avg_session_time: 平均停留时间(秒)
- viewed_reviews: 是否查看过评论 (0/1)
- price: 活动价格
- purchased: 是否购买 (0/1) - 这是我们要预测的目标

要求:
1. 做必要的特征工程
2. 训练一个分类模型
3. 评估模型效果 (precision, recall, F1)
4. 讨论时间复杂度
5. 如果有时间，讨论如何改进

你有 25 分钟。开始吧！
====================================================

下面是我的解题过程 (边想边说):
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

# ============================================================================
# 第 1 步: 理解数据 (2 分钟)
# ============================================================================

print("=" * 80)
print("第 1 步: 理解数据")
print("=" * 80)

# 【边想边说】
# "让我先看看数据长什么样，了解一下数据分布和是否有缺失值"

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

# 【边想边说】
# "好的，数据看起来没有缺失值，目标变量是平衡的 (10个购买, 10个未购买)"
# "现在我要做一些特征工程"

# ============================================================================
# 第 2 步: 特征工程 (5 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 2 步: 特征工程")
print("=" * 80)

# 【边想边说】
# "我打算创建几个新特征:"
# "1. engagement_score: 结合访问次数和停留时间"
# "2. price_per_visit: 价格除以访问次数，衡量用户对价格的敏感度"
# "3. is_frequent_visitor: 访问次数是否超过中位数"

# 创建新特征
data["engagement_score"] = data["num_visits"] * data["avg_session_time"] / 1000
# 解释: 访问次数 * 平均停留时间，归一化到合理范围

data["price_per_visit"] = data["price"] / (data["num_visits"] + 1)  # +1 避免除零
# 解释: 价格相对于访问频率的比值

median_visits = data["num_visits"].median()
data["is_frequent_visitor"] = (data["num_visits"] > median_visits).astype(int)
# 解释: 二值特征，是否是高频访问用户

print("\n新特征预览:")
print(data[["user_id", "engagement_score", "price_per_visit", "is_frequent_visitor"]].head())

# 【边想边说】
# "现在准备训练数据"

# ============================================================================
# 第 3 步: 准备训练数据 (3 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 3 步: 准备训练数据")
print("=" * 80)

# 【边想边说】
# "我会选择这些特征: age, num_visits, avg_session_time, viewed_reviews, price"
# "加上我们新创建的 engagement_score, price_per_visit, is_frequent_visitor"
# "user_id 不用，因为它只是标识符，没有预测能力"

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
# stratify=y 保证训练集和测试集的类别比例一致

print("\n训练集大小:", X_train.shape)
print("测试集大小:", X_test.shape)

# 【边想边说】
# "特征尺度差异很大 (age 在 20-60, avg_session_time 在 80-600)"
# "我会用 StandardScaler 标准化特征"

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # 注意: 只 transform，不 fit

print("\n特征已标准化")

# ============================================================================
# 第 4 步: 训练模型 (5 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 4 步: 训练模型")
print("=" * 80)

# 【边想边说】
# "我选择 RandomForest，因为:"
# "1. 对特征尺度不敏感 (虽然我们已经标准化了)"
# "2. 能处理非线性关系"
# "3. 能给出特征重要性"
# "4. 不容易过拟合"

model = RandomForestClassifier(
    n_estimators=100,      # 100 棵树
    max_depth=5,           # 限制深度防止过拟合
    random_state=42,       # 可复现
    n_jobs=-1              # 使用所有 CPU 核心
)

print("\n开始训练...")
model.fit(X_train_scaled, y_train)
print("训练完成!")

# ============================================================================
# 第 5 步: 评估模型 (5 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 5 步: 评估模型")
print("=" * 80)

# 【边想边说】
# "现在用测试集评估模型效果"

y_pred = model.predict(X_test_scaled)

# 计算评估指标
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print("\n评估指标:")
print(f"Precision: {precision:.3f}")
print(f"Recall: {recall:.3f}")
print(f"F1 Score: {f1:.3f}")

# 【边想边说】
# "让我解释一下这些指标:"
# "- Precision: 在我们预测为'会购买'的用户中，有多少真的购买了"
# "- Recall: 在所有真正购买的用户中，我们找到了多少"
# "- F1: Precision 和 Recall 的调和平均，综合评估"

print("\n混淆矩阵:")
cm = confusion_matrix(y_test, y_pred)
print(cm)
print("\n解释:")
print(f"True Negatives (正确预测未购买): {cm[0,0]}")
print(f"False Positives (错误预测购买): {cm[0,1]}")
print(f"False Negatives (错误预测未购买): {cm[1,0]}")
print(f"True Positives (正确预测购买): {cm[1,1]}")

# ============================================================================
# 第 6 步: 特征重要性 (3 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 6 步: 特征重要性")
print("=" * 80)

# 【边想边说】
# "让我看看哪些特征最重要"

feature_importance = pd.DataFrame({
    "feature": feature_cols,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print("\n特征重要性排名:")
print(feature_importance)

# 【边想边说】
# "这告诉我们哪些因素最影响用户购买决策"
# "比如如果 engagement_score 很重要，说明用户参与度是关键"

# ============================================================================
# 第 7 步: 复杂度分析 (2 分钟)
# ============================================================================

print("\n" + "=" * 80)
print("第 7 步: 复杂度分析")
print("=" * 80)

# 【边想边说】
# "让我分析一下时间和空间复杂度"

print("\n时间复杂度:")
print("- 特征工程: O(n) - 遍历数据一次")
print("- StandardScaler: O(n*d) - n 样本, d 特征")
print("- RandomForest 训练: O(n*d*log(n)*T) - T 是树的数量")
print("- 预测: O(d*T) - 每个样本")
print("\n空间复杂度:")
print("- 数据存储: O(n*d)")
print("- 模型存储: O(T*nodes) - T 棵树，每棵树的节点数")

# ============================================================================
# 第 8 步: 改进建议 (如果有时间)
# ============================================================================

print("\n" + "=" * 80)
print("第 8 步: 改进建议")
print("=" * 80)

# 【边想边说】
# "如果要改进这个模型，我会考虑:"

print("\n可能的改进:")
print("1. 超参数调优: 用 GridSearchCV 找最优参数")
print("2. 更多特征: 用户历史购买记录、季节性、活动类型")
print("3. 处理类别不平衡: 如果数据不平衡，用 class_weight='balanced'")
print("4. 集成方法: 尝试 XGBoost 或 LightGBM")
print("5. 交叉验证: 用 K-fold CV 更稳定地评估模型")
print("6. 特征选择: 移除不重要的特征，减少过拟合")

# ============================================================================
# 第 9 步: 边界情况测试
# ============================================================================

print("\n" + "=" * 80)
print("第 9 步: 边界情况测试")
print("=" * 80)

# 【边想边说】
# "让我测试一些边界情况，确保代码健壮"

print("\n测试边界情况:")

# 测试 1: 新用户 (最少访问)
new_user_low = pd.DataFrame({
    "age": [25],
    "num_visits": [1],
    "avg_session_time": [100],
    "viewed_reviews": [0],
    "price": [100],
    "engagement_score": [1 * 100 / 1000],
    "price_per_visit": [100 / 2],
    "is_frequent_visitor": [0]
})
pred_low = model.predict(scaler.transform(new_user_low))
print(f"低参与度用户预测: {'购买' if pred_low[0] == 1 else '不购买'}")

# 测试 2: 高参与度用户
new_user_high = pd.DataFrame({
    "age": [35],
    "num_visits": [20],
    "avg_session_time": [600],
    "viewed_reviews": [1],
    "price": [50],
    "engagement_score": [20 * 600 / 1000],
    "price_per_visit": [50 / 21],
    "is_frequent_visitor": [1]
})
pred_high = model.predict(scaler.transform(new_user_high))
print(f"高参与度用户预测: {'购买' if pred_high[0] == 1 else '不购买'}")

print("\n" + "=" * 80)
print("完成! 总用时: ~25 分钟")
print("=" * 80)

# ============================================================================
# 面试官可能的后续问题
# ============================================================================

print("\n" + "=" * 80)
print("面试官可能的后续问题:")
print("=" * 80)

questions = """
Q1: "为什么选择 RandomForest 而不是 Logistic Regression?"
A1: RandomForest 能捕捉非线性关系和特征交互，不需要手动设计交互项。
    而且对特征尺度不敏感，更容易调参。Logistic Regression 更适合线性可分的问题。

Q2: "如果数据量很大 (百万级)，你会怎么优化?"
A2: 1. 用 LightGBM 或 XGBoost (更快)
    2. 特征采样和数据采样
    3. 增量学习 (online learning)
    4. 分布式训练 (Spark MLlib)

Q3: "Precision 和 Recall 哪个更重要?"
A3: 取决于业务场景:
    - 如果推送成本高 (发邮件、打电话)，优先 Precision (减少误报)
    - 如果错过用户损失大 (高价值客户)，优先 Recall (减少漏报)
    - FareHarbor 可能更关心 Precision，避免骚扰不感兴趣的用户

Q4: "如何处理新特征 (比如新增'用户评分')?"
A4: 1. 重新训练模型 (包含新特征)
    2. 用 A/B 测试验证新模型是否更好
    3. 如果是在线系统，需要更新特征工程 pipeline

Q5: "模型上线后如何监控?"
A5: 1. 监控预测分布 (是否偏移)
    2. 监控业务指标 (转化率、收入)
    3. 定期重新训练 (数据漂移)
    4. 设置告警 (预测延迟、错误率)
"""

print(questions)

print("\n" + "=" * 80)
print("关键要点总结:")
print("=" * 80)

summary = """
✅ 做到的:
1. 清晰的思路: 理解数据 → 特征工程 → 训练 → 评估 → 分析
2. 边想边说: 每一步都解释为什么这么做
3. 特征工程: 创建有意义的新特征
4. 正确的评估: 用 train/test split，计算多个指标
5. 复杂度分析: 说出时间和空间复杂度
6. 边界测试: 测试极端情况
7. 改进建议: 展示对 ML 工程的理解

⚠️ 注意事项:
1. 不要跳过数据探索 (EDA)
2. 不要忘记标准化特征
3. 不要只看 accuracy (类别不平衡时会误导)
4. 不要忘记设置 random_state (可复现)
5. 不要在测试集上 fit scaler (数据泄露)

💡 加分项:
1. 主动讨论业务场景 (FareHarbor 的定价优化)
2. 提出改进方向 (超参数调优、更多特征)
3. 考虑生产环境 (监控、A/B 测试)
4. 测试边界情况 (工程师思维)
"""

print(summary)
