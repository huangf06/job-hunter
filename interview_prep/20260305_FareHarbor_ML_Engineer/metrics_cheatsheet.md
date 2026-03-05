# ML Metrics 速查表 - 面试必备

## 监督学习 Metrics（分类问题）

### 混淆矩阵基础
```
              预测: 负类    预测: 正类
实际: 负类      TN          FP  ← 误报 (Type I Error)
实际: 正类      FN  ←漏报   TP
                ↓
         (Type II Error)
```

### 核心 Metrics

| Metric | 公式 | 含义 | 何时用 | 范围 |
|--------|------|------|--------|------|
| **Accuracy** | (TP+TN) / 总数 | 整体准确率 | ⚠️ 数据平衡时 | [0, 1] |
| **Precision** | TP / (TP+FP) | 预测为正的准确性 | 误报代价高 | [0, 1] |
| **Recall** | TP / (TP+FN) | 找出所有正样本的能力 | 漏报代价高 | [0, 1] |
| **F1 Score** | 2×P×R / (P+R) | P 和 R 的调和平均 | 平衡 P 和 R | [0, 1] |
| **AUC-ROC** | ROC 曲线下面积 | 整体区分能力 | 评估模型质量 | [0.5, 1] |

### 详细解释

#### 1. Accuracy（准确率）
```python
accuracy = (TP + TN) / (TP + TN + FP + FN)
```
- **优点**: 直观易懂
- **缺点**: 数据不平衡时会误导
- **例子**: 95% 样本为负类，全预测负类也有 95% 准确率
- **面试答**: "Accuracy 在不平衡数据时不可靠，应该看 Precision/Recall"

#### 2. Precision（精确率/查准率）
```python
precision = TP / (TP + FP)
```
- **含义**: 预测为正的样本中，真正为正的比例
- **业务**: "我预测会流失的客户，有多少真的流失了？"
- **高 Precision**: 减少误报，避免浪费资源
- **例子**: 垃圾邮件分类（不想误杀正常邮件）
- **面试答**: "Precision 关注预测为正的质量，适合误报代价高的场景"

#### 3. Recall（召回率/查全率）
```python
recall = TP / (TP + FN)
```
- **含义**: 真正为正的样本中，被预测出来的比例
- **业务**: "真正流失的客户，我识别出了多少？"
- **高 Recall**: 减少漏报，不错过重要样本
- **例子**: 疾病诊断（不能漏诊）、欺诈检测
- **面试答**: "Recall 关注找全所有正样本，适合漏报代价高的场景"

#### 4. F1 Score
```python
f1 = 2 × (precision × recall) / (precision + recall)
```
- **含义**: Precision 和 Recall 的调和平均数
- **为什么用调和平均**: 惩罚极端值（一个很高一个很低）
- **何时用**: Precision 和 Recall 都重要，且数据不平衡
- **面试答**: "F1 平衡了 Precision 和 Recall，适合不平衡数据"

#### 5. AUC-ROC
```python
from sklearn.metrics import roc_auc_score
auc = roc_auc_score(y_true, y_pred_proba)
```
- **ROC 曲线**: TPR (Recall) vs FPR，不同阈值下的表现
- **AUC**: ROC 曲线下面积
- **含义**: 随机正样本排在随机负样本前面的概率
- **范围**: [0.5, 1.0]
  - 0.5 = 随机猜测
  - 0.7-0.8 = 一般
  - 0.8-0.9 = 良好
  - 0.9-1.0 = 优秀
- **优点**: 不受阈值影响，不受类别不平衡影响
- **面试答**: "AUC 衡量模型整体区分能力，是评估模型质量的金标准"

### Precision vs Recall 权衡

```
阈值 ↑ → Precision ↑, Recall ↓  (更保守，只预测很确定的)
阈值 ↓ → Precision ↓, Recall ↑  (更激进，宁可错杀不放过)
```

**业务场景选择**:
- **高 Precision**: 营销活动（避免骚扰客户）、推荐系统（避免推荐垃圾）
- **高 Recall**: 欺诈检测（不能漏）、疾病筛查（不能漏诊）
- **平衡**: 客户流失预测（既要准又要全）

---

## 无监督学习 Metrics（聚类问题）

### 核心 Metrics

| Metric | 公式 | 含义 | 越大越好/越小越好 | 典型值 |
|--------|------|------|-------------------|--------|
| **Inertia** | Σ dist² | 簇内紧密度 | 越小越好 | 看 Elbow |
| **Silhouette** | (b-a)/max(a,b) | 样本与簇匹配度 | 越大越好 | >0.5 良好 |
| **Davies-Bouldin** | 簇内/簇间 | 簇分离度 | 越小越好 | <1.0 良好 |
| **Calinski-Harabasz** | 簇间/簇内 | 方差比 | 越大越好 | 越高越好 |

### 详细解释

#### 1. Inertia（簇内平方和）
```python
inertia = kmeans.inertia_
```
- **公式**: Σ (样本到其簇中心的距离²)
- **含义**: 簇内紧密度，越小说明簇越紧密
- **问题**: 随 k 增大单调递减（k=n 时为 0）
- **用途**: 画 Elbow 曲线找拐点
- **面试答**: "Inertia 单独看没意义，要结合 Elbow Method 找拐点"

#### 2. Silhouette Score（轮廓系数）
```python
from sklearn.metrics import silhouette_score
score = silhouette_score(X_scaled, labels)
```
- **公式**: (b - a) / max(a, b)
  - a = 样本到同簇其他点的平均距离（簇内距离）
  - b = 样本到最近其他簇的平均距离（簇间距离）
- **范围**: [-1, 1]
  - +1: 样本离自己簇很近，离其他簇很远（完美）
  - 0: 样本在簇边界上（模糊）
  - -1: 样本可能分错簇了（很差）
- **典型值**: >0.5 为良好聚类
- **优点**: 最常用，直观易懂
- **面试答**: "Silhouette Score 是最常用的聚类评估指标，衡量簇的紧密度和分离度"

#### 3. Davies-Bouldin Index（DB 指数）
```python
from sklearn.metrics import davies_bouldin_score
db = davies_bouldin_score(X_scaled, labels)
```
- **公式**: (1/k) × Σ max[(σᵢ + σⱼ) / d(cᵢ, cⱼ)]
  - σᵢ = 簇 i 内样本到中心的平均距离
  - d(cᵢ, cⱼ) = 簇中心 i 和 j 的距离
- **含义**: 簇内离散度 / 簇间距离
- **范围**: [0, +∞)，越小越好
- **典型值**: <1.0 为良好聚类
- **优点**: 计算快，适合大数据
- **面试答**: "DB Index 衡量簇的分离度，越小说明簇越分离"

#### 4. Calinski-Harabasz Index（CH 指数/方差比）
```python
from sklearn.metrics import calinski_harabasz_score
ch = calinski_harabasz_score(X_scaled, labels)
```
- **公式**: (簇间方差 / 簇内方差) × [(n - k) / (k - 1)]
- **含义**: 簇间分离度 vs 簇内紧密度的比值
- **范围**: [0, +∞)，越大越好
- **优点**: 计算快，适合快速评估
- **面试答**: "CH Index 是方差比，越高说明簇分离清晰且内部紧密"

### 如何选择 k（聚类数）

```python
# 方法 1: Elbow Method
for k in range(2, 10):
    kmeans = KMeans(n_clusters=k)
    inertias.append(kmeans.inertia_)
# 画图找拐点

# 方法 2: Silhouette Score
for k in range(2, 10):
    kmeans = KMeans(n_clusters=k)
    scores.append(silhouette_score(X, kmeans.labels_))
# 选最高的 k

# 方法 3: 业务直觉
# 4-6 个客群最实用（太多难以操作）
```

---

## 面试常见问题

### Q1: 为什么不用 Accuracy？
**A**: "数据不平衡时 Accuracy 会误导。比如 95% 样本为负类，全预测负类也有 95% 准确率，但模型没有任何价值。应该用 Precision/Recall/F1。"

### Q2: Precision 和 Recall 哪个更重要？
**A**: "取决于业务场景。如果误报代价高（如营销骚扰），优先 Precision；如果漏报代价高（如欺诈检测），优先 Recall。通常用 F1 平衡两者。"

### Q3: 如何调整 Precision 和 Recall？
**A**: "调整分类阈值。降低阈值 → 提高 Recall（更激进）；提高阈值 → 提高 Precision（更保守）。默认 0.5，可根据业务调整。"

### Q4: AUC 为什么比 Accuracy 好？
**A**: "AUC 不受阈值影响，也不受类别不平衡影响，衡量模型整体区分能力。是评估模型质量的金标准。"

### Q5: 聚类为什么要标准化？
**A**: "K-Means 基于欧氏距离，不同特征量纲不同（如天数 vs 金额），大数值特征会主导聚类。StandardScaler 将所有特征缩放到同一尺度。"

### Q6: Silhouette Score 多少算好？
**A**: ">0.5 为良好聚类，>0.7 为优秀。但也要结合业务可操作性，有时 0.4-0.5 的聚类也有业务价值。"

### Q7: 如何选择聚类数 k？
**A**: "三种方法：1) Elbow Method 找 Inertia 拐点；2) Silhouette Score 选最高的 k；3) 业务直觉，4-6 个客群最实用。"

---

## 快速记忆口诀

### 监督学习
- **Precision**: "我说的对不对"（预测为正的准确性）
- **Recall**: "我找全了没"（找出所有正样本）
- **F1**: "又对又全"（平衡两者）
- **AUC**: "整体能力"（不受阈值影响）

### 无监督学习
- **Silhouette**: "我在对的群里吗"（样本与簇匹配度）
- **Davies-Bouldin**: "群之间分得开吗"（簇分离度）
- **Calinski-Harabasz**: "群内紧群间松"（方差比）

---

## 代码速查

```python
# 监督学习
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)
auc = roc_auc_score(y_true, y_pred_proba)

# 无监督学习
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score,
    calinski_harabasz_score
)

silhouette = silhouette_score(X_scaled, labels)
db = davies_bouldin_score(X_scaled, labels)
ch = calinski_harabasz_score(X_scaled, labels)
```

**面试时记住：先说含义，再说公式，最后说业务应用！**
