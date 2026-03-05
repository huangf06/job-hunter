# ML 面试速查表 - 打印版
**适用场景**: Live Coding 技术面试 | 最后更新: 2026-03-05

---

## 1. 数据加载与探索

### CSV 文件操作
```python
import pandas as pd
import numpy as np

# 读取 CSV
df = pd.read_csv('data.csv')
df = pd.read_csv('data.csv', sep=';', encoding='utf-8')  # 自定义分隔符

# 基础检查（必做！）
df.shape                    # (行数, 列数)
df.head(10)                 # 前 10 行
df.tail()                   # 后 5 行
df.info()                   # 数据类型 + 非空计数
df.describe()               # 数值列统计
df.columns                  # 列名列表
df.dtypes                   # 每列数据类型

# 缺失值处理
df.isnull().sum()           # 每列缺失值数量
df.dropna()                 # 删除含缺失值的行
df.fillna(0)                # 填充为 0
df.fillna(df.mean())        # 填充为均值
df['col'].fillna(method='ffill')  # 前向填充

# 数据类型转换
df['col'] = df['col'].astype(int)
df['date'] = pd.to_datetime(df['date'])

# 数据筛选
df[df['age'] > 30]          # 条件筛选
df[df['city'].isin(['NYC', 'LA'])]  # 多值筛选
df.query('age > 30 and city == "NYC"')  # SQL 风格

# 数据排序
df.sort_values('age', ascending=False)
df.sort_values(['city', 'age'], ascending=[True, False])
```

### 常用 Pandas 操作
```python
# 分组聚合
df.groupby('city')['sales'].mean()
df.groupby('city').agg({'sales': ['mean', 'sum'], 'age': 'max'})

# 合并数据
pd.concat([df1, df2], axis=0)  # 纵向拼接
pd.merge(df1, df2, on='id', how='left')  # 左连接

# 应用函数
df['new_col'] = df['col'].apply(lambda x: x * 2)
df['new_col'] = df.apply(lambda row: row['a'] + row['b'], axis=1)
```

---

## 2. 特征工程

### 数值特征
```python
# 标准化（必须！聚类/距离算法）
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)  # 训练集 fit
X_test_scaled = scaler.transform(X_test)  # 测试集只 transform

# 归一化（Min-Max Scaling）
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)  # 缩放到 [0, 1]

# 对数变换（处理偏态分布）
df['log_price'] = np.log1p(df['price'])  # log(1+x)，避免 log(0)

# 分箱（Binning）
df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 60, 100],
                         labels=['child', 'young', 'middle', 'senior'])
```

### 类别特征
```python
# One-Hot Encoding
df_encoded = pd.get_dummies(df, columns=['city', 'gender'])

# Label Encoding（有序类别）
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['city_encoded'] = le.fit_transform(df['city'])

# 手动映射
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
```

### 时间特征
```python
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
df['days_since'] = (pd.Timestamp.now() - df['date']).dt.days
```

### 常用特征工程思路
```python
# 1. 比率特征
df['price_per_sqft'] = df['price'] / df['sqft']
df['conversion_rate'] = df['conversions'] / df['visits']

# 2. 差值特征
df['price_diff'] = df['price'] - df['competitor_price']
df['price_vs_avg'] = df['price'] / df.groupby('city')['price'].transform('mean')

# 3. 交互特征
df['price_x_sqft'] = df['price'] * df['sqft']

# 4. 聚合特征
df['city_avg_price'] = df.groupby('city')['price'].transform('mean')
df['user_total_spend'] = df.groupby('user_id')['amount'].transform('sum')

# 5. 时间衰减
df['urgency'] = np.exp(-df['days_until'] / 7)  # 指数衰减

# 6. 排名特征
df['price_rank'] = df.groupby('city')['price'].rank(ascending=False)
```

---

## 3. 模型选择

### 监督学习 - 分类

#### Logistic Regression（基线模型）
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    C=1.0,              # 正则化强度（越小越强）
    max_iter=1000,      # 最大迭代次数
    class_weight='balanced',  # 处理不平衡数据
    random_state=42
)
model.fit(X_train, y_train)
y_pred_proba = model.predict_proba(X_test)[:, 1]
```
**优点**: 快速、可解释、概率输出
**缺点**: 只能学习线性关系
**适用**: 基线模型、特征线性可分

#### Random Forest（通用强模型）
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,       # 树的数量
    max_depth=10,           # 树的最大深度
    min_samples_split=20,   # 分裂所需最小样本数
    min_samples_leaf=10,    # 叶子节点最小样本数
    class_weight='balanced',
    random_state=42,
    n_jobs=-1               # 并行
)
model.fit(X_train, y_train)
```
**优点**: 鲁棒、处理非线性、特征重要性
**缺点**: 慢、内存占用大
**适用**: 表格数据、特征重要性分析

#### Gradient Boosting（最强表格模型）
```python
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,      # 学习率（越小越保守）
    max_depth=4,            # 树深度（3-5 常用）
    min_samples_split=20,
    subsample=0.8,          # 样本采样比例
    random_state=42
)
model.fit(X_train, y_train)
```
**优点**: 精度最高、处理复杂非线性
**缺点**: 易过拟合、训练慢
**适用**: Kaggle、生产环境（调参后）

### 监督学习 - 回归
```python
# Linear Regression
from sklearn.linear_model import LinearRegression
model = LinearRegression()

# Ridge Regression（L2 正则化）
from sklearn.linear_model import Ridge
model = Ridge(alpha=1.0)

# Random Forest Regressor
from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor(n_estimators=100, max_depth=10)
```

### 无监督学习 - 聚类

#### K-Means（最常用）
```python
from sklearn.cluster import KMeans

kmeans = KMeans(
    n_clusters=4,       # 聚类数
    random_state=42,
    n_init=10,          # 初始化次数（选最好的）
    max_iter=300        # 最大迭代次数
)
labels = kmeans.fit_predict(X_scaled)  # 必须标准化！

# 预测新样本
new_labels = kmeans.predict(X_new_scaled)
```
**优点**: 快速、简单、可扩展
**缺点**: 需要指定 k、假设球形簇
**适用**: 客户细分、图像压缩

#### DBSCAN（基于密度）
```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(
    eps=0.5,            # 邻域半径
    min_samples=5       # 核心点最小样本数
)
labels = dbscan.fit_predict(X_scaled)
```
**优点**: 自动发现簇数、识别异常点
**缺点**: 参数敏感
**适用**: 异常检测、非球形簇

---

## 4. 模型评估指标

### 分类指标

#### 混淆矩阵
```python
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel()

#              预测: 0    预测: 1
# 实际: 0        TN        FP  ← 误报
# 实际: 1        FN  ←漏报  TP
```

#### 核心指标
```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)

# Accuracy（准确率）- 数据平衡时用
accuracy = accuracy_score(y_true, y_pred)
# 公式: (TP + TN) / 总数

# Precision（精确率）- 误报代价高时用
precision = precision_score(y_true, y_pred)
# 公式: TP / (TP + FP)
# 含义: 预测为正的样本中，真正为正的比例

# Recall（召回率）- 漏报代价高时用
recall = recall_score(y_true, y_pred)
# 公式: TP / (TP + FN)
# 含义: 真正为正的样本中，被预测出来的比例

# F1 Score（平衡 P 和 R）
f1 = f1_score(y_true, y_pred)
# 公式: 2 × P × R / (P + R)

# AUC-ROC（最重要！）
auc = roc_auc_score(y_true, y_pred_proba)
# 含义: 随机正样本分数高于随机负样本的概率
# 范围: [0.5, 1.0]，0.8+ 良好，0.9+ 优秀

# 完整报告
print(classification_report(y_true, y_pred))
```

#### ROC 曲线
```python
from sklearn.metrics import roc_curve
import matplotlib.pyplot as plt

fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)

plt.plot(fpr, tpr, label=f'AUC={auc:.2f}')
plt.plot([0, 1], [0, 1], 'k--', label='Random')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.legend()
plt.show()
```

### 回归指标
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# MSE（均方误差）
mse = mean_squared_error(y_true, y_pred)

# RMSE（均方根误差）- 与目标同单位
rmse = np.sqrt(mse)

# MAE（平均绝对误差）- 对异常值鲁棒
mae = mean_absolute_error(y_true, y_pred)

# R² Score（决定系数）
r2 = r2_score(y_true, y_pred)
# 范围: (-∞, 1]，1 为完美，0 为均值预测
```

### 聚类指标
```python
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score,
    calinski_harabasz_score
)

# Silhouette Score（最常用）
silhouette = silhouette_score(X_scaled, labels)
# 范围: [-1, 1]，>0.5 良好，>0.7 优秀
# 含义: 样本与自己簇的匹配度

# Davies-Bouldin Index
db = davies_bouldin_score(X_scaled, labels)
# 范围: [0, +∞)，<1.0 良好，越小越好
# 含义: 簇内离散度 / 簇间距离

# Calinski-Harabasz Index
ch = calinski_harabasz_score(X_scaled, labels)
# 范围: [0, +∞)，越大越好
# 含义: 簇间方差 / 簇内方差

# Inertia（用于 Elbow Method）
inertia = kmeans.inertia_
# 含义: 簇内平方和，越小越好（但看拐点）
```

---

## 5. 模型训练流程

### 标准流程
```python
from sklearn.model_selection import train_test_split

# 1. 划分数据
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,      # 测试集比例
    random_state=42,
    stratify=y          # 分层采样（保持类别比例）
)

# 2. 标准化（如果需要）
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 3. 训练模型
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# 4. 预测
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

# 5. 评估
auc = roc_auc_score(y_test, y_pred_proba)
print(f"AUC: {auc:.3f}")
```

### 交叉验证
```python
from sklearn.model_selection import cross_val_score

# K-Fold 交叉验证
scores = cross_val_score(
    model, X, y,
    cv=5,               # 5 折
    scoring='roc_auc'   # 评估指标
)
print(f"Mean AUC: {scores.mean():.3f} (+/- {scores.std():.3f})")
```

### 网格搜索（调参）
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [10, 20, 50]
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")
print(f"Best AUC: {grid_search.best_score_:.3f}")

best_model = grid_search.best_estimator_
```

---

## 6. 常用技巧

### 处理不平衡数据
```python
# 方法 1: 类权重
model = RandomForestClassifier(class_weight='balanced')

# 方法 2: 过采样（SMOTE）
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# 方法 3: 欠采样
from imblearn.under_sampling import RandomUnderSampler
rus = RandomUnderSampler(random_state=42)
X_resampled, y_resampled = rus.fit_resample(X_train, y_train)

# 方法 4: 调整阈值
threshold = 0.3  # 降低阈值提高 Recall
y_pred = (y_pred_proba > threshold).astype(int)
```

### 特征重要性
```python
# Random Forest / Gradient Boosting
importance = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(importance.head(10))

# 可视化
import matplotlib.pyplot as plt
importance.head(10).plot(x='feature', y='importance', kind='barh')
plt.show()
```

### 保存和加载模型
```python
import joblib

# 保存
joblib.dump(model, 'model.pkl')
joblib.dump(scaler, 'scaler.pkl')

# 加载
model = joblib.load('model.pkl')
scaler = joblib.load('scaler.pkl')
```

---

## 7. 面试常见问题

### Q1: 如何处理缺失值？
**A**:
- 数值: 均值/中位数填充，或预测填充
- 类别: 众数填充，或新增 "Unknown" 类别
- 时间序列: 前向/后向填充
- 删除: 缺失率 >50% 的列，或缺失关键特征的行

### Q2: 为什么要标准化？
**A**:
- K-Means、KNN、SVM 等基于距离的算法必须标准化
- 不同特征量纲不同（价格 vs 年龄），大数值特征会主导
- StandardScaler: (x - mean) / std，适合正态分布
- MinMaxScaler: (x - min) / (max - min)，适合有界数据

### Q3: 如何选择模型？
**A**:
- 基线: Logistic Regression（快速、可解释）
- 表格数据: Random Forest / Gradient Boosting
- 大数据: Logistic Regression / SGD
- 可解释性: Logistic Regression / Decision Tree
- 精度优先: Gradient Boosting / XGBoost

### Q4: 如何防止过拟合？
**A**:
- 交叉验证
- 正则化（L1/L2）
- 减少模型复杂度（max_depth, min_samples_split）
- Early stopping
- 增加训练数据

### Q5: Precision vs Recall 如何选择？
**A**:
- 高 Precision: 误报代价高（营销、推荐）
- 高 Recall: 漏报代价高（欺诈检测、疾病筛查）
- 平衡: F1 Score
- 调整阈值: 降低阈值 → 提高 Recall

---

## 8. 时间管理（40 分钟面试）

| 阶段 | 时间 | 关键动作 |
|------|------|----------|
| 理解需求 | 2 min | 确认输入输出、业务目标 |
| 数据加载 | 3 min | 读 CSV、基础检查、缺失值 |
| 特征工程 | 5 min | 2-3 个核心特征 |
| 模型训练 | 10 min | 选模型、训练、评估 |
| 业务应用 | 10 min | 优化目标、可视化、策略 |
| 讨论扩展 | 5 min | 生产化、A/B 测试 |
| 缓冲 | 5 min | Debug、回答问题 |

---

## 9. 代码模板

### 监督学习模板
```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, classification_report

# 1. 加载数据
df = pd.read_csv('data.csv')
print(df.shape, df.isnull().sum())

# 2. 特征工程
df['feature1'] = df['a'] / df['b']
df['feature2'] = np.exp(-df['c'] / 7)

# 3. 准备数据
X = df[['feature1', 'feature2', ...]]
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. 标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 5. 训练
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# 6. 评估
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
print(f"AUC: {auc:.3f}")
```

### 无监督学习模板
```python
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# 1. 加载数据
df = pd.read_csv('data.csv')

# 2. 特征工程
df['feature1'] = df['a'] * df['b']
df['feature2'] = 1 / (df['c'] + 1)

# 3. 准备数据
X = df[['feature1', 'feature2', ...]]

# 4. 标准化（必须！）
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 5. 聚类
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
labels = kmeans.fit_predict(X_scaled)

# 6. 评估
silhouette = silhouette_score(X_scaled, labels)
print(f"Silhouette: {silhouette:.3f}")

# 7. 分析
df['cluster'] = labels
for i in range(4):
    cluster_data = df[df['cluster'] == i]
    print(f"Cluster {i}: {cluster_data[['feature1', 'feature2']].mean()}")
```

---

## 10. 记忆口诀

### Metrics
- **Precision**: "我说的对不对"（预测为正的准确性）
- **Recall**: "我找全了没"（找出所有正样本）
- **F1**: "又对又全"（平衡两者）
- **AUC**: "排序能力"（0.8+ 良好，0.9+ 优秀）

### 标准化
- **K-Means/KNN/SVM**: 必须标准化
- **Tree-based**: 不需要标准化
- **Linear/Logistic**: 建议标准化

### 模型选择
- **快速基线**: Logistic Regression
- **通用强模型**: Random Forest
- **精度最高**: Gradient Boosting
- **大数据**: SGD / Online Learning

---

**打印提示**: 建议双面打印，字体 9-10pt，保存为 PDF 方便查看
