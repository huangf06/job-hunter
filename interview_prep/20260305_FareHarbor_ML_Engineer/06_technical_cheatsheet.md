# Technical Cheatsheet - Quick Reference

## Python One-Liners

### List Operations
```python
# Flatten 2D list
flat = [item for row in matrix for item in row]

# Remove duplicates (preserve order)
unique = list(dict.fromkeys(items))

# Group by key
from itertools import groupby
grouped = {k: list(v) for k, v in groupby(sorted(data, key=lambda x: x['key']), key=lambda x: x['key'])}

# Zip with default
from itertools import zip_longest
pairs = list(zip_longest(a, b, fillvalue=0))
```

### Dict Operations
```python
# Merge dicts (Python 3.9+)
merged = d1 | d2

# Invert dict
inverted = {v: k for k, v in d.items()}

# Default dict
from collections import defaultdict
counts = defaultdict(int)

# Counter
from collections import Counter
freq = Counter(items)
```

### Functional Programming
```python
# Map/filter/reduce
from functools import reduce
doubled = list(map(lambda x: x*2, nums))
evens = list(filter(lambda x: x%2==0, nums))
product = reduce(lambda x,y: x*y, nums)

# Partial application
from functools import partial
multiply_by_2 = partial(lambda x, y: x * y, 2)
```

---

## NumPy/Pandas Quick Hits

### NumPy
```python
import numpy as np

# Array creation
arr = np.arange(10)
zeros = np.zeros((3, 4))
ones = np.ones((2, 3))
identity = np.eye(3)

# Indexing
arr[arr > 5]  # Boolean indexing
arr[[0, 2, 4]]  # Fancy indexing

# Operations
np.mean(arr, axis=0)
np.std(arr)
np.argmax(arr)
np.where(arr > 5, 1, 0)  # Conditional

# Broadcasting
arr + 10  # Add scalar to all elements
```

### Pandas
```python
import pandas as pd

# DataFrame creation
df = pd.DataFrame({'A': [1,2,3], 'B': [4,5,6]})

# Selection
df['A']  # Column
df.loc[0]  # Row by label
df.iloc[0]  # Row by position
df[df['A'] > 1]  # Boolean indexing

# Operations
df.groupby('A').agg({'B': ['mean', 'sum']})
df.merge(df2, on='key', how='left')
df.pivot_table(values='B', index='A', aggfunc='mean')

# Time series
df['date'] = pd.to_datetime(df['date'])
df.set_index('date').resample('D').mean()
```

---

## Scikit-Learn Patterns

### Pipeline
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', RandomForestClassifier())
])
pipe.fit(X_train, y_train)
```

### Cross-Validation
```python
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='f1')
```

### Grid Search
```python
from sklearn.model_selection import GridSearchCV
params = {'n_estimators': [100, 200], 'max_depth': [5, 10]}
grid = GridSearchCV(model, params, cv=5)
grid.fit(X_train, y_train)
best_model = grid.best_estimator_
```

---

## SQL Quick Reference

### Common Queries
```sql
-- Window functions
SELECT user_id, revenue,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date) as rn,
       SUM(revenue) OVER (PARTITION BY user_id) as total_revenue
FROM transactions;

-- CTEs
WITH daily_stats AS (
    SELECT date, COUNT(*) as cnt, AVG(price) as avg_price
    FROM bookings
    GROUP BY date
)
SELECT * FROM daily_stats WHERE cnt > 100;

-- Joins
SELECT a.*, b.name
FROM orders a
LEFT JOIN customers b ON a.customer_id = b.id;
```

---

## Time Complexity Cheatsheet

| Operation | List | Dict | Set |
|-----------|------|------|-----|
| Access | O(1) | O(1) | - |
| Search | O(n) | O(1) | O(1) |
| Insert | O(1)* | O(1) | O(1) |
| Delete | O(n) | O(1) | O(1) |

*Amortized for list append

### Common Algorithms
- Binary search: O(log n)
- Merge sort: O(n log n)
- Quick sort: O(n log n) average, O(n²) worst
- Hash table: O(1) average, O(n) worst

---

## ML Metrics

### Classification
```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)
auc = roc_auc_score(y_true, y_proba)
```

### Regression
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

mse = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)
```

---

## Debugging Checklist

When code doesn't work:
1. **Print shapes**: `print(X.shape, y.shape)`
2. **Check types**: `print(type(x), x.dtype)`
3. **Inspect first few**: `print(df.head())`
4. **Look for NaNs**: `print(df.isnull().sum())`
5. **Check ranges**: `print(df.describe())`
6. **Verify indices**: `print(df.index)`

---

## Interview Mantras

1. **Clarify first**: "Just to confirm, you want me to..."
2. **Think out loud**: "I'm considering two approaches..."
3. **Start simple**: "Let me start with a brute force solution..."
4. **Test as you go**: "Let me test this with [1, 2, 3]..."
5. **Ask for hints**: "I'm stuck on X, could you give me a hint?"

---

## Breathing Technique (4-7-8)
When nervous:
1. Inhale through nose for 4 seconds
2. Hold breath for 7 seconds
3. Exhale through mouth for 8 seconds
4. Repeat 3 times

**You've got this!**
