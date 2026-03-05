# Live Coding 记忆卡片 - 3 小时速成

## 监督学习：动态定价 (20 分钟)

### 核心逻辑（3 句话）
1. 生成数据：价格 ↑ → 转化 ↓，紧迫性/稀缺性 → 转化 ↑
2. 关键特征：`price_vs_comp`, `urgency = exp(-days/7)`, `scarcity = 1-capacity`
3. 优化目标：遍历价格，找 `max(price × P(conversion))`

### 必记代码片段
```python
# 特征工程
df['price_vs_comp'] = (df['price'] - df['competitor_price']) / df['competitor_price']
df['urgency'] = np.exp(-df['days_advance'] / 7)
df['scarcity'] = 1 - df['capacity_left']

# 模型
from sklearn.ensemble import GradientBoostingClassifier
model = GradientBoostingClassifier(n_estimators=100, max_depth=4)
model.fit(X_train_scaled, y_train)

# 优化
for price in prices:
    prob = model.predict_proba(X_scaled)[0, 1]
    revenue = price * prob
```

### 面试要点
- **为什么 GradientBoosting?** 捕捉非线性（价格敏感度因场景而异）
- **生产化?** A/B 测试新价格，监控转化率漂移
- **扩展?** Multi-armed bandit 在线学习

---

## 无监督学习：客户聚类 (20 分钟)

### 核心逻辑（3 句话）
1. 生成 4 类客户：Budget/Premium/Value/Spontaneous
2. 关键特征：`lifetime_value = spend × frequency`, `urgency = exp(-days/10)`
3. K-Means 聚类 → 每个簇对应不同定价策略

### 必记代码片段
```python
# 特征工程
df['lifetime_value'] = df['avg_spend'] * df['frequency']
df['urgency'] = np.exp(-df['days_advance'] / 10)

# 聚类
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=42)
labels = kmeans.fit_predict(X_scaled)

# 评估
from sklearn.metrics import silhouette_score
score = silhouette_score(X_scaled, labels)  # 越高越好
```

### 面试要点
- **为什么标准化?** 不同量纲（价格 vs 频率）会主导距离
- **如何选 k?** Silhouette Score + 业务可操作性
- **定价策略?** 高敏感→折扣，低敏感→溢价，临时→动态

---

## 时间分配（总 20-25 分钟）

| 步骤 | 时间 | 关键动作 |
|------|------|----------|
| 数据生成 | 5 min | 合成数据，展示业务理解 |
| 特征工程 | 5 min | 2-3 个核心特征 |
| 模型训练 | 5 min | 标准流程，不调参 |
| 业务应用 | 5 min | 优化/分析，口头描述结果 |
| 讨论 | 5 min | 生产化、A/B 测试 |

---

## 通用技巧

### 开场白（30 秒）
"我理解这个问题是 [业务目标]。我计划：
1. 生成合成数据模拟 [场景]
2. 工程化 [2-3 个特征]
3. 训练 [模型] 并评估
4. 应用到 [业务优化]
可以吗？"

### 边写边说
- "我现在生成数据，核心逻辑是..."
- "这个特征捕捉了 [业务含义]"
- "我选 [模型] 因为 [原因]"

### 遇到 Bug
1. 不慌，说 "让我 debug 一下"
2. 用 `print(df.head())` 检查数据
3. 检查形状 `X.shape`, `y.shape`
4. 面试官通常会提示

### 没时间了
- 跳过可视化，口头描述："这里我会画一个 price-revenue 曲线"
- 跳过评估，直接说："生产环境我会用 AUC 和交叉验证"

---

## 最后检查（面试前 10 分钟）

### 监督学习
- [ ] 记住 3 个特征：`price_vs_comp`, `urgency`, `scarcity`
- [ ] 记住优化循环：`for price in prices: revenue = price * prob`
- [ ] 记住面试点：GradientBoosting, A/B 测试, 漂移监控

### 无监督学习
- [ ] 记住 2 个特征：`lifetime_value`, `urgency`
- [ ] 记住必须标准化：`StandardScaler()`
- [ ] 记住 4 类客户：Budget/Premium/Value/Spontaneous
- [ ] 记住评估：`silhouette_score`

---

## 心态

- **简单 > 完美**: 能跑的简单代码 > 复杂但有 bug 的代码
- **沟通 > 代码**: 展示思维过程比写完所有代码重要
- **业务 > 算法**: 强调业务价值（收入优化、客户体验）

**你已经准备好了！深呼吸，相信自己 💪**
