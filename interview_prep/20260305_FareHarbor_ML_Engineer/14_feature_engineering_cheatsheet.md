# 特征工程万能套路 - 面试速查表

**核心思想**：特征工程不是创新，是套路！

面试中 90% 的特征工程都可以用这 6 个套路解决。

---

## 套路 1: 组合特征（最常用）

**公式**：两个相关特征相乘或相除

### 模板

```python
# 乘法组合 (表示"总量")
data["total_engagement"] = data["num_visits"] * data["avg_session_time"]

# 除法组合 (表示"效率"或"比率")
data["price_per_visit"] = data["price"] / (data["num_visits"] + 1)  # +1 避免除零
data["conversion_rate"] = data["purchases"] / (data["views"] + 1)
```

### 何时使用

- 看到两个相关的数值特征
- 例子：访问次数 + 停留时间 → 总参与度
- 例子：价格 + 访问次数 → 价格敏感度

### 面试话术

> "我注意到 num_visits 和 avg_session_time 都反映用户参与度，我把它们相乘创建一个 engagement_score，这样能更全面地衡量用户兴趣。"

---

## 套路 2: 二值化（阈值特征）

**公式**：数值特征 > 阈值 → 0/1

### 模板

```python
# 基于中位数
data["is_high_value"] = (data["price"] > data["price"].median()).astype(int)

# 基于均值
data["is_frequent_visitor"] = (data["num_visits"] > data["num_visits"].mean()).astype(int)

# 基于业务阈值
data["is_premium"] = (data["price"] > 100).astype(int)
```

### 何时使用

- 数值特征有明显的"高/低"分界
- 例子：访问次数 → 高频/低频用户
- 例子：价格 → 高价/低价商品

### 面试话术

> "我创建一个二值特征 is_frequent_visitor，区分高频和低频用户，因为这两类用户的购买行为可能不同。"

---

## 套路 3: 分桶（Binning）

**公式**：连续特征 → 离散区间

### 模板

```python
# 等宽分桶
data["age_group"] = pd.cut(data["age"], bins=[0, 30, 50, 100], labels=["young", "middle", "senior"])

# 等频分桶
data["price_quartile"] = pd.qcut(data["price"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])
```

### 何时使用

- 连续特征有非线性关系
- 例子：年龄 → 年龄段（年轻人和老年人行为不同）
- 例子：价格 → 价格区间

### 面试话术

> "我把年龄分成几个区间，因为不同年龄段的用户可能有不同的购买模式，这比直接用连续的年龄值更能捕捉这种非线性关系。"

---

## 套路 4: 时间特征（如果有时间戳）

**公式**：从时间戳提取多个维度

### 模板

```python
# 基础时间特征
data["hour"] = pd.to_datetime(data["timestamp"]).dt.hour
data["day_of_week"] = pd.to_datetime(data["timestamp"]).dt.dayofweek
data["month"] = pd.to_datetime(data["timestamp"]).dt.month

# 二值时间特征
data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
data["is_business_hours"] = data["hour"].between(9, 17).astype(int)

# 周期性特征 (高级)
data["hour_sin"] = np.sin(2 * np.pi * data["hour"] / 24)
data["hour_cos"] = np.cos(2 * np.pi * data["hour"] / 24)
```

### 何时使用

- 数据有时间戳
- 例子：购买时间 → 小时、星期几、是否周末

### 面试话术

> "我从时间戳提取了 hour 和 day_of_week，因为用户在不同时间段的购买行为可能不同，比如周末可能更活跃。"

---

## 套路 5: 聚合特征（如果有分组）

**公式**：按某个维度聚合统计

### 模板

```python
# 按用户聚合
user_stats = data.groupby("user_id").agg({
    "purchase_amount": ["mean", "sum", "count"],
    "num_visits": "max"
}).reset_index()

# 按类别聚合
category_avg_price = data.groupby("category")["price"].mean()
data["price_vs_category_avg"] = data["price"] / data["category"].map(category_avg_price)
```

### 何时使用

- 数据有分组结构（用户、类别、地区）
- 例子：用户历史购买 → 平均订单金额、购买频率

### 面试话术

> "我计算了每个用户的历史平均购买金额，这能反映用户的消费能力，对预测很有帮助。"

---

## 套路 6: 交互特征（高级）

**公式**：两个特征的乘积（捕捉交互效应）

### 模板

```python
# 数值 × 数值
data["price_age_interaction"] = data["price"] * data["age"]

# 数值 × 类别 (one-hot 后)
data["price_premium_interaction"] = data["price"] * data["is_premium"]
```

### 何时使用

- 两个特征有交互效应
- 例子：价格 × 年龄（年轻人对价格更敏感）

### 面试话术

> "我创建了 price 和 age 的交互特征，因为不同年龄段对价格的敏感度可能不同。"

---

## 🎯 面试中的决策树

**拿到数据后，按这个顺序思考**：

```
1. 有没有两个相关的数值特征？
   → 是：用套路 1 (组合特征)

2. 有没有数值特征可以分"高/低"？
   → 是：用套路 2 (二值化)

3. 有没有时间戳？
   → 是：用套路 4 (时间特征)

4. 有没有明显的非线性关系？
   → 是：用套路 3 (分桶)

5. 有没有分组结构？
   → 是：用套路 5 (聚合特征)

6. 还有时间吗？
   → 是：用套路 6 (交互特征)
```

---

## 📋 FareHarbor 面试的特征工程模板

**假设数据有这些字段**：
- user_id, age, num_visits, avg_session_time, viewed_reviews, price, purchased

**标准特征工程（5分钟内完成）**：

```python
# 套路 1: 组合特征
data["engagement_score"] = data["num_visits"] * data["avg_session_time"] / 1000

# 套路 1: 比率特征
data["price_per_visit"] = data["price"] / (data["num_visits"] + 1)

# 套路 2: 二值化
data["is_frequent_visitor"] = (data["num_visits"] > data["num_visits"].median()).astype(int)

# 如果有时间，加一个交互特征
data["price_engagement_interaction"] = data["price"] * data["engagement_score"]
```

**话术**：
> "我创建了 3 个新特征：
> 1. engagement_score 结合访问次数和停留时间，衡量用户参与度
> 2. price_per_visit 衡量价格相对于用户兴趣的比值
> 3. is_frequent_visitor 区分高频和低频用户"

---

## ⚠️ 面试中的注意事项

### ✅ 做到的

1. **先说再做**："我打算创建 engagement_score，因为..."
2. **解释合理性**："这个特征能捕捉用户参与度"
3. **处理边界**：除法加 +1 避免除零
4. **不要过度**：2-3 个特征足够，不要创建 10 个

### ❌ 避免

1. ❌ 不解释直接写代码
2. ❌ 创建没有业务意义的特征（比如 age² 没有解释）
3. ❌ 忘记处理除零、缺失值
4. ❌ 创建太多特征（时间不够）

---

## 💡 万能回答模板

**如果面试官问："你为什么创建这个特征？"**

**模板**：
> "我创建 [特征名] 是因为 [业务逻辑]。具体来说，[原始特征A] 和 [原始特征B] 都反映了 [某个概念]，但单独看可能不够全面。通过 [组合方式]，我们能更好地捕捉 [目标行为]。"

**例子**：
> "我创建 engagement_score 是因为用户参与度。具体来说，num_visits 和 avg_session_time 都反映了用户兴趣，但单独看可能不够全面。通过相乘，我们能更好地捕捉真正感兴趣的用户（既访问多，又停留久）。"

---

## 🚀 今晚练习方法

**不要背代码，背套路！**

1. **看一遍 6 个套路**（10 分钟）
2. **拿到数据后，问自己**：
   - 有没有两个相关特征？→ 套路 1
   - 有没有可以分高/低的？→ 套路 2
   - 有没有时间戳？→ 套路 4
3. **练习话术**（5 分钟）
   - "我创建 X 是因为..."
   - "这个特征能捕捉..."

---

## 🎯 关键要点

1. **特征工程不是创新，是套路**
2. **90% 的面试题用 6 个套路就够了**
3. **重点是解释合理性，不是特征数量**
4. **2-3 个特征足够，不要贪多**
5. **先说再做，边做边解释**

**记住**：面试官不期待你发明新算法，他们期待你能用标准方法解决实际问题。

**你已经有 6 年经验了，这些套路你肯定用过，只是需要唤醒记忆！** 💪
