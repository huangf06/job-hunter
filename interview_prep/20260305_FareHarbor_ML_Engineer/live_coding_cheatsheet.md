# Live Coding 快速参考 - FareHarbor ML Engineer

## 题目 1: 监督学习 - 动态定价预测

### 核心思路
预测不同价格点的转化率 → 最大化期望收入 (Price × P(Conversion))

### 关键特征工程
```python
# 价格特征
price_vs_competitor = (base_price - competitor_avg) / competitor_avg

# 时间特征
booking_urgency = np.exp(-days_until_booking / 7)  # 指数衰减
is_last_minute = (days_until_booking < 3)

# 稀缺性特征
scarcity_score = 1 - capacity_remaining

# 交互特征
price_x_urgency = price_vs_competitor * booking_urgency
```

### 模型选择
- **GradientBoostingClassifier**: 捕捉非线性交互 (价格 × 紧迫性)
- 超参数: `n_estimators=100, max_depth=4, learning_rate=0.1`
- 评估指标: AUC-ROC (不平衡数据), 特征重要性

### 业务优化
```python
# 遍历价格区间，找最大期望收入
for price in price_range:
    conversion_prob = model.predict_proba(features)[0, 1]
    expected_revenue = price * conversion_prob
```

### 面试要点
1. **为什么用 GradientBoosting?** 非线性关系 (价格敏感度因场景而异)
2. **如何处理冷启动?** 先用规则定价，积累数据后训练模型
3. **A/B 测试策略**: 分流 10% 流量测试新价格，监控转化率 + 收入
4. **生产监控**: 转化率漂移检测 (concept drift), 定期重训练
5. **扩展方向**: Multi-armed bandit (在线学习), 分客户群建模

---

## 题目 2: 无监督学习 - 客户细分

### 核心思路
K-Means 聚类 → 识别价格敏感度不同的客户群 → 差异化定价策略

### 关键特征工程
```python
# 行为特征
total_lifetime_value = avg_booking_value * booking_frequency
booking_urgency = np.exp(-avg_days_advance / 10)
reliability_score = 1 - cancellation_rate

# 复合评分
premium_score = (
    (avg_booking_value / 250) * 0.4 +
    (booking_frequency / 10) * 0.3 +
    (1 - price_sensitivity) * 0.3
)
```

### 聚类验证
- **Elbow Method**: 找拐点 (inertia 下降变缓)
- **Silhouette Score**: 衡量簇内紧密度 vs 簇间分离度 ([-1, 1], 越高越好)
- **Davies-Bouldin Index**: 簇内离散度 / 簇间距离 (越低越好)

### 典型客户群
| 群体 | 特征 | 定价策略 |
|------|------|----------|
| Budget Travelers | 高价格敏感, 提前预订 | 早鸟折扣, 捆绑优惠 |
| Premium Seekers | 低价格敏感, 高消费 | 溢价定价, VIP 体验 |
| Value Hunters | 中等敏感, 比价 | 竞争性定价, 透明价值 |
| Spontaneous | 临时预订, 冲动消费 | 动态定价, 限时促销 |

### 面试要点
1. **为什么用 K-Means?** 简单高效, 可解释性强, 适合球形簇
2. **如何选 k?** Silhouette + Elbow + 业务直觉 (4-6 个群体可操作)
3. **特征标准化**: 必须! 不同量纲 (价格 vs 频率) 会主导距离计算
4. **生产部署**: 定期重聚类 (季度), 监控簇漂移, 新客户分配 (predict)
5. **扩展方向**:
   - DBSCAN (识别异常客户)
   - Hierarchical clustering (树状结构)
   - RFM 分析 (Recency, Frequency, Monetary)

---

## 通用面试技巧

### 代码结构 (30-40 分钟)
1. **数据生成** (5 min): 合成数据, 展示理解业务逻辑
2. **特征工程** (5 min): 领域知识转化为特征
3. **模型训练** (10 min): 选型 + 训练 + 评估
4. **业务应用** (10 min): 优化目标 + 可视化 + 策略建议
5. **讨论扩展** (5 min): 生产化考虑, A/B 测试, 监控

### 沟通要点
- **边写边说**: "我现在要做特征工程, 因为..."
- **展示权衡**: "我选 GradientBoosting 而不是 Random Forest, 因为..."
- **主动提问**: "这个场景下, 我们更关心精度还是召回率?"
- **承认局限**: "这个模型假设价格敏感度是静态的, 实际可能随时间变化"

### 常见追问
1. **如何处理数据不平衡?** SMOTE, 类权重, 分层采样
2. **如何防止过拟合?** 交叉验证, 正则化, early stopping
3. **如何解释模型给业务?** SHAP values, 特征重要性, 局部解释
4. **如何监控模型性能?** 在线指标 (转化率, 收入), 离线评估 (AUC), 数据漂移检测

---

## 快速检查清单

### 监督学习必备
- [ ] 数据生成逻辑合理 (价格 ↑ → 转化 ↓)
- [ ] 特征工程有领域知识 (urgency, scarcity)
- [ ] 模型评估用正确指标 (AUC for imbalanced)
- [ ] 业务优化有明确目标 (max expected revenue)
- [ ] 可视化清晰 (price-revenue curve)

### 无监督学习必备
- [ ] 特征标准化 (StandardScaler)
- [ ] 聚类数量验证 (Silhouette + Elbow)
- [ ] 簇解释有业务意义 (不只是 "Cluster 0")
- [ ] 定价策略针对性强 (每个群体不同)
- [ ] PCA 可视化 (2D 投影)

---

## 时间管理

| 阶段 | 时间 | 重点 |
|------|------|------|
| 理解需求 | 2 min | 确认输入输出, 业务目标 |
| 数据生成 | 5 min | 快速合成, 不追求完美 |
| 特征工程 | 5 min | 2-3 个核心特征即可 |
| 模型训练 | 10 min | 选经典模型, 不调参 |
| 业务应用 | 10 min | 优化 + 可视化 |
| 讨论扩展 | 5 min | 生产化, A/B 测试 |
| 缓冲时间 | 3 min | 处理 bug, 回答问题 |

**总计: 40 分钟**

---

## 最后提醒

1. **不要过度优化**: 面试不是 Kaggle, 简单可行 > 复杂完美
2. **代码可读性**: 变量命名清晰, 适当注释, 模块化函数
3. **展示思维过程**: 说出你的假设, 权衡, 决策逻辑
4. **保持冷静**: 遇到 bug 不慌, 用 print 调试, 面试官会帮忙
5. **时间意识**: 30 分钟时检查进度, 必要时跳过可视化直接讲思路

**Good luck! 你已经准备好了 💪**