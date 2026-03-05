# ML 面试核心速查表 (2 页打印版)
**Live Coding 必备 | 字体: 8-9pt | 双栏打印**

---

## 1. 数据加载 (必记 5 行)

```python
import pandas as pd, numpy as np
df = pd.read_csv('data.csv')
df.shape, df.isnull().sum()  # 形状 + 缺失值
df.fillna(df.mean())          # 填充缺失值
df.groupby('city')['sales'].agg(['mean', 'sum'])  # 分组聚合
```

---

## 2. 特征工程 (6 种核心模式)

```python
# 标准化（K-Means/KNN/SVM 必须！）
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)  # 训练集 fit
X_test_scaled = scaler.transform(X_test)  # 测试集只 transform

# 类别编码
pd.get_dummies(df, columns=['city'])  # One-Hot
df['is_weekend'] = (df['day'] >= 5).astype(int)  # 手动

# 6 种特征工程
df['ratio'] = df['a'] / df['b']                    # 1. 比率
df['diff'] = df['price'] - df['competitor']        # 2. 差值
df['interact'] = df['price'] * df['sqft']          # 3. 交互
df['city_avg'] = df.groupby('city')['price'].transform('mean')  # 4. 聚合
df['urgency'] = np.exp(-df['days'] / 7)            # 5. 时间衰减
df['log_price'] = np.log1p(df['price'])            # 6. 对数变换
```

---

## 3. 模型 (3 个必会)

### Logistic Regression (基线)
```python
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(C=1.0, class_weight='balanced', max_iter=1000)
```

### Random Forest (通用)
```python
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(
    n_estimators=100, max_depth=10, min_samples_split=20,
    class_weight='balanced', random_state=42, n_jobs=-1
)
```

### Gradient Boosting (最强)
```python
from sklearn.ensemble import GradientBoostingClassifier
model = GradientBoostingClassifier(
    n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42
)
```

### K-Means (聚类)
```python
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
labels = kmeans.fit_predict(X_scaled)  # 必须标准化！
```

---

## 4. 训练流程 (标准 5 步)

```python
from sklearn.model_selection import train_test_split

# 1. 划分
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2. 标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 3. 训练
model.fit(X_train_scaled, y_train)

# 4. 预测
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

# 5. 评估
from sklearn.metrics import roc_auc_score
auc = roc_auc_score(y_test, y_pred_proba)
```

---

## 5. Metrics (必记公式)

### 分类 (4 个核心)
```python
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score
)

# Precision = TP / (TP + FP)  "我说的对不对"
precision = precision_score(y_true, y_pred)

# Recall = TP / (TP + FN)  "我找全了没"
recall = recall_score(y_true, y_pred)

# F1 = 2 × P × R / (P + R)  "又对又全"
f1 = f1_score(y_true, y_pred)

# AUC-ROC: 正样本分数 > 负样本的概率
# 0.8+ 良好, 0.9+ 优秀
auc = roc_auc_score(y_true, y_pred_proba)
```

### 聚类 (2 个核心)
```python
from sklearn.metrics import silhouette_score, davies_bouldin_score

# Silhouette: 样本与簇匹配度, >0.5 良好
silhouette = silhouette_score(X_scaled, labels)

# Davies-Bouldin: 簇分离度, <1.0 良好
db = davies_bouldin_score(X_scaled, labels)
```

---

## 6. 不平衡数据 (3 种方法)

```python
# 方法 1: 类权重
model = RandomForestClassifier(class_weight='balanced')

# 方法 2: SMOTE 过采样
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_res, y_res = smote.fit_resample(X_train, y_train)

# 方法 3: 调整阈值
threshold = 0.3  # 降低阈值 → 提高 Recall
y_pred = (y_pred_proba > threshold).astype(int)
```

---

## 7. 特征重要性

```python
importance = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print(importance.head(5))
```

---

## 8. 交叉验证 & 调参

```python
# 交叉验证
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
print(f"Mean AUC: {scores.mean():.3f}")

# 网格搜索
from sklearn.model_selection import GridSearchCV
param_grid = {'n_estimators': [50, 100], 'max_depth': [5, 10]}
grid = GridSearchCV(model, param_grid, cv=5, scoring='roc_auc')
grid.fit(X_train, y_train)
print(grid.best_params_, grid.best_score_)
```

---

## 9. 面试高频问题 (5 个)

**Q1: 为什么标准化？**
A: K-Means/KNN/SVM 基于距离，不同量纲会主导聚类。StandardScaler: (x-mean)/std

**Q2: Precision vs Recall？**
A: 误报代价高 → 高 Precision（营销）；漏报代价高 → 高 Recall（欺诈检测）

**Q3: 如何防止过拟合？**
A: 交叉验证、正则化、减少复杂度（max_depth）、增加数据

**Q4: AUC 为什么比 Accuracy 好？**
A: 不受阈值和类别不平衡影响，衡量排序能力

**Q5: 如何选择模型？**
A: 基线 Logistic → 通用 Random Forest → 最强 Gradient Boosting

---

## 10. 记忆口诀

### Metrics
- **Precision**: "我说的对不对"
- **Recall**: "我找全了没"
- **F1**: "又对又全"
- **AUC**: "排序能力" (0.8+ 良好, 0.9+ 优秀)

### 标准化规则
- **必须**: K-Means, KNN, SVM
- **不需要**: Random Forest, Gradient Boosting

### 模型选择
- **快速基线**: Logistic Regression
- **通用强模型**: Random Forest
- **精度最高**: Gradient Boosting

### 特征工程 6 式
比率、差值、交互、聚合、衰减、对数

---

## 11. 时间管理 (40 分钟)

| 阶段 | 时间 | 动作 |
|------|------|------|
| 理解 | 2 min | 确认输入输出 |
| 加载 | 3 min | CSV + 缺失值 |
| 特征 | 5 min | 2-3 个核心特征 |
| 训练 | 10 min | 选模型 + 评估 |
| 应用 | 10 min | 优化 + 策略 |
| 讨论 | 5 min | 生产化 |
| 缓冲 | 5 min | Debug |

---

## 12. 常用 Import

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    silhouette_score, davies_bouldin_score
)
```

---

**打印设置**: A4 双栏 | 字体 8-9pt | 行距 1.0 | 页边距 1cm
**使用建议**: 面试前 10 分钟快速浏览，面试中放旁边作参考
