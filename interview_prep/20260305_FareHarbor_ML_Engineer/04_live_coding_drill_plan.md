# Live Coding Drill Plan - FareHarbor ML Engineer
**Interview Date**: 2026-03-05
**Focus**: Python fundamentals + ML production patterns + pricing optimization

## Critical Insight from Past Failures
**Springer Nature failure (2026-02-27)**: Couldn't answer Python basics in live coding.
**Root cause**: Lack of muscle memory for core concepts.
**Fix**: Zero-AI drill, hand-write code, 10-second response time.

---

## Part 1: Python Fundamentals (P0 Priority)
**Time**: 30 minutes tonight, 15 minutes tomorrow morning
**Method**: Hand-write on paper, NO AI, explain out loud

### Core Concepts to Drill
1. **Decorators**
   ```python
   # Function decorator
   def timer(func):
       def wrapper(*args, **kwargs):
           start = time.time()
           result = func(*args, **kwargs)
           print(f"{func.__name__} took {time.time()-start:.2f}s")
           return result
       return wrapper

   # Class decorator
   def singleton(cls):
       instances = {}
       def get_instance(*args, **kwargs):
           if cls not in instances:
               instances[cls] = cls(*args, **kwargs)
           return instances[cls]
       return get_instance
   ```

2. **Generators & Iterators**
   ```python
   # Generator function
   def fibonacci(n):
       a, b = 0, 1
       for _ in range(n):
           yield a
           a, b = b, a + b

   # Generator expression
   squares = (x**2 for x in range(10))

   # Custom iterator
   class Countdown:
       def __init__(self, start):
           self.current = start
       def __iter__(self):
           return self
       def __next__(self):
           if self.current <= 0:
               raise StopIteration
           self.current -= 1
           return self.current + 1
   ```

3. **Context Managers**
   ```python
   # Class-based
   class DatabaseConnection:
       def __enter__(self):
           self.conn = connect_to_db()
           return self.conn
       def __exit__(self, exc_type, exc_val, exc_tb):
           self.conn.close()
           return False  # Don't suppress exceptions

   # Function-based
   from contextlib import contextmanager
   @contextmanager
   def timer_context():
       start = time.time()
       yield
       print(f"Elapsed: {time.time()-start:.2f}s")
   ```

4. **List/Dict Comprehensions & Functional Programming**
   ```python
   # List comprehension with condition
   evens = [x for x in range(20) if x % 2 == 0]

   # Dict comprehension
   word_lengths = {word: len(word) for word in ["hello", "world"]}

   # Nested comprehension (flatten 2D list)
   matrix = [[1,2], [3,4], [5,6]]
   flat = [item for row in matrix for item in row]

   # map/filter/reduce
   from functools import reduce
   numbers = [1, 2, 3, 4, 5]
   doubled = list(map(lambda x: x*2, numbers))
   evens = list(filter(lambda x: x%2==0, numbers))
   product = reduce(lambda x,y: x*y, numbers)
   ```

5. **Classes & OOP**
   ```python
   # Property decorator
   class Temperature:
       def __init__(self, celsius):
           self._celsius = celsius

       @property
       def fahrenheit(self):
           return self._celsius * 9/5 + 32

       @fahrenheit.setter
       def fahrenheit(self, value):
           self._celsius = (value - 32) * 5/9

   # __slots__ for memory optimization
   class Point:
       __slots__ = ['x', 'y']
       def __init__(self, x, y):
           self.x = x
           self.y = y

   # Abstract base class
   from abc import ABC, abstractmethod
   class Model(ABC):
       @abstractmethod
       def predict(self, X):
           pass
   ```

---

## Part 2: ML Production Patterns
**Time**: 45 minutes tonight
**Focus**: Code patterns you'll actually write in the interview

### Pattern 1: Feature Engineering Pipeline
```python
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self, date_col='timestamp'):
        self.date_col = date_col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        # Time-based features
        X['hour'] = pd.to_datetime(X[self.date_col]).dt.hour
        X['day_of_week'] = pd.to_datetime(X[self.date_col]).dt.dayofweek
        X['is_weekend'] = X['day_of_week'].isin([5, 6]).astype(int)

        # Lag features
        X['price_lag_1'] = X['price'].shift(1)
        X['price_rolling_7d'] = X['price'].rolling(7).mean()

        return X

# Usage in pipeline
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor

pipeline = Pipeline([
    ('features', FeatureEngineer()),
    ('scaler', StandardScaler()),
    ('model', GradientBoostingRegressor())
])
```

### Pattern 2: Model Serving with Caching
```python
from functools import lru_cache
import pickle
import redis

class ModelServer:
    def __init__(self, model_path, cache_size=1000):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        self.redis_client = redis.Redis(host='localhost', port=6379)

    @lru_cache(maxsize=1000)
    def _get_features(self, user_id, item_id):
        # Expensive feature lookup
        return self._fetch_from_db(user_id, item_id)

    def predict(self, user_id, item_id):
        # Check cache
        cache_key = f"pred:{user_id}:{item_id}"
        cached = self.redis_client.get(cache_key)
        if cached:
            return float(cached)

        # Compute prediction
        features = self._get_features(user_id, item_id)
        prediction = self.model.predict([features])[0]

        # Cache result (TTL 1 hour)
        self.redis_client.setex(cache_key, 3600, str(prediction))
        return prediction
```

### Pattern 3: A/B Testing Framework
```python
import hashlib
from enum import Enum

class Variant(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"

class ABTest:
    def __init__(self, experiment_name, treatment_ratio=0.5):
        self.experiment_name = experiment_name
        self.treatment_ratio = treatment_ratio

    def assign_variant(self, user_id):
        # Deterministic assignment based on hash
        hash_input = f"{self.experiment_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 100) / 100.0

        return Variant.TREATMENT if bucket < self.treatment_ratio else Variant.CONTROL

    def log_event(self, user_id, event_type, value):
        variant = self.assign_variant(user_id)
        # Log to analytics system
        print(f"User {user_id} | Variant: {variant.value} | Event: {event_type} | Value: {value}")

# Usage
test = ABTest("dynamic_pricing_v1", treatment_ratio=0.5)
variant = test.assign_variant("user_123")
if variant == Variant.TREATMENT:
    price = dynamic_pricing_model.predict(features)
else:
    price = baseline_price
test.log_event("user_123", "purchase", price)
```

---

## Part 3: Pricing/Revenue Optimization Problems
**Time**: 30 minutes tonight
**Focus**: Domain-specific algorithms for FareHarbor

### Problem 1: Multi-Armed Bandit (Epsilon-Greedy)
```python
import numpy as np

class EpsilonGreedyBandit:
    def __init__(self, n_arms, epsilon=0.1):
        self.n_arms = n_arms
        self.epsilon = epsilon
        self.counts = np.zeros(n_arms)  # Number of times each arm pulled
        self.values = np.zeros(n_arms)  # Average reward for each arm

    def select_arm(self):
        if np.random.random() < self.epsilon:
            # Explore: random arm
            return np.random.randint(self.n_arms)
        else:
            # Exploit: best arm so far
            return np.argmax(self.values)

    def update(self, arm, reward):
        self.counts[arm] += 1
        n = self.counts[arm]
        # Incremental average
        self.values[arm] = ((n - 1) / n) * self.values[arm] + (1 / n) * reward

# Usage for dynamic pricing
bandit = EpsilonGreedyBandit(n_arms=5, epsilon=0.1)  # 5 price points
price_options = [50, 60, 70, 80, 90]

for customer in customers:
    arm = bandit.select_arm()
    price = price_options[arm]
    purchased = show_price_and_check_purchase(customer, price)
    reward = price if purchased else 0
    bandit.update(arm, reward)
```

### Problem 2: Demand Forecasting
```python
from sklearn.ensemble import GradientBoostingRegressor
import pandas as pd

def train_demand_model(historical_data):
    """
    Predict demand based on price, day of week, seasonality
    """
    # Feature engineering
    df = historical_data.copy()
    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['month'] = pd.to_datetime(df['date']).dt.month
    df['is_holiday'] = df['date'].isin(holidays).astype(int)

    # Lag features
    df['demand_lag_7'] = df['demand'].shift(7)
    df['demand_rolling_14'] = df['demand'].rolling(14).mean()

    features = ['price', 'day_of_week', 'month', 'is_holiday',
                'demand_lag_7', 'demand_rolling_14']
    X = df[features].dropna()
    y = df.loc[X.index, 'demand']

    model = GradientBoostingRegressor(n_estimators=100, max_depth=5)
    model.fit(X, y)
    return model

def optimize_price(demand_model, cost, price_range):
    """
    Find price that maximizes revenue
    """
    best_revenue = 0
    best_price = None

    for price in price_range:
        features = build_features(price)  # Current context
        predicted_demand = demand_model.predict([features])[0]
        revenue = (price - cost) * predicted_demand

        if revenue > best_revenue:
            best_revenue = revenue
            best_price = price

    return best_price, best_revenue
```

### Problem 3: Contextual Bandit (Thompson Sampling)
```python
import numpy as np
from scipy.stats import beta

class ThompsonSamplingBandit:
    def __init__(self, n_arms):
        self.n_arms = n_arms
        # Beta distribution parameters (successes, failures)
        self.alpha = np.ones(n_arms)  # Prior: Beta(1,1) = Uniform
        self.beta_param = np.ones(n_arms)

    def select_arm(self):
        # Sample from posterior distribution
        samples = [np.random.beta(self.alpha[i], self.beta_param[i])
                   for i in range(self.n_arms)]
        return np.argmax(samples)

    def update(self, arm, reward):
        # reward is 0 or 1 (purchase or not)
        if reward == 1:
            self.alpha[arm] += 1
        else:
            self.beta_param[arm] += 1

# Usage with context (user features)
class ContextualBandit:
    def __init__(self, n_arms, n_features):
        self.bandits = {}  # One bandit per context bucket
        self.n_arms = n_arms
        self.n_features = n_features

    def _get_context_key(self, features):
        # Discretize continuous features into buckets
        return tuple(np.digitize(features, bins=[0.33, 0.67]))

    def select_arm(self, features):
        key = self._get_context_key(features)
        if key not in self.bandits:
            self.bandits[key] = ThompsonSamplingBandit(self.n_arms)
        return self.bandits[key].select_arm()

    def update(self, features, arm, reward):
        key = self._get_context_key(features)
        self.bandits[key].update(arm, reward)
```

---

## Part 4: Common Interview Questions (Rapid Fire)
**Practice**: Answer each in <30 seconds

### Python Basics
1. **What's the difference between `==` and `is`?**
   - `==` compares values, `is` compares object identity (memory address)
   - `a == b` checks if contents are equal
   - `a is b` checks if they're the same object

2. **Explain the GIL (Global Interpreter Lock)**
   - Mutex that protects Python objects, prevents multiple threads from executing Python bytecode simultaneously
   - Makes single-threaded programs fast, but limits multi-threading for CPU-bound tasks
   - Use multiprocessing for CPU-bound parallelism, threading for I/O-bound

3. **What are `*args` and `**kwargs`?**
   - `*args`: variable positional arguments (tuple)
   - `**kwargs`: variable keyword arguments (dict)
   - Used for flexible function signatures

4. **Mutable vs Immutable types?**
   - Immutable: int, float, str, tuple, frozenset
   - Mutable: list, dict, set, custom objects
   - Matters for default arguments: `def f(x=[]):` is a bug!

5. **What's a closure?**
   - Function that captures variables from enclosing scope
   - Example: decorator functions, factory functions
   ```python
   def make_multiplier(n):
       def multiply(x):
           return x * n  # 'n' is captured
       return multiply
   ```

### ML/Data Science
1. **Bias-variance tradeoff?**
   - Bias: error from wrong assumptions (underfitting)
   - Variance: error from sensitivity to training data (overfitting)
   - Goal: minimize total error = bias² + variance + irreducible error

2. **Precision vs Recall?**
   - Precision: TP / (TP + FP) — "Of predicted positives, how many are correct?"
   - Recall: TP / (TP + FN) — "Of actual positives, how many did we find?"
   - F1 = harmonic mean of both

3. **How do you handle imbalanced data?**
   - Resampling: oversample minority, undersample majority
   - Class weights in loss function
   - Evaluation: use precision-recall curve, not accuracy
   - SMOTE for synthetic samples

4. **Explain gradient boosting**
   - Ensemble method: train models sequentially
   - Each model corrects errors of previous models
   - Fits new model to residuals (gradient of loss)
   - XGBoost, LightGBM, CatBoost are implementations

5. **What's regularization?**
   - Penalty term added to loss function to prevent overfitting
   - L1 (Lasso): sparse weights, feature selection
   - L2 (Ridge): small weights, smooth models
   - Dropout: randomly disable neurons during training

---

## Part 5: System Design (ML Pipeline)
**Time**: 20 minutes tonight
**Scenario**: Design a real-time pricing recommendation system

### Architecture
```
┌─────────────┐
│   Client    │
│  (booking)  │
└──────┬──────┘
       │ HTTP request (user_id, activity_id, timestamp)
       ▼
┌─────────────────────────────────────────┐
│         API Gateway (FastAPI)           │
│  - Authentication                       │
│  - Rate limiting                        │
│  - Request validation                   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│      Pricing Service (Python)           │
│  - Feature fetching (Redis cache)      │
│  - Model inference                      │
│  - A/B test assignment                  │
│  - Logging (Kafka)                      │
└──────┬──────────────────────────────────┘
       │
       ├──────────────┬──────────────┬─────────────┐
       ▼              ▼              ▼             ▼
┌──────────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐
│  Redis   │   │ Model    │   │ Feature  │  │  Kafka   │
│  Cache   │   │ Registry │   │  Store   │  │  Logs    │
└──────────┘   └──────────┘   └──────────┘  └──────────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │  Offline     │
                                            │  Training    │
                                            │  Pipeline    │
                                            └──────────────┘
```

### Key Components to Discuss
1. **Feature Store**: Pre-computed features (user history, activity popularity)
2. **Model Registry**: Versioned models, A/B test variants
3. **Caching**: Redis for hot features, reduce latency
4. **Monitoring**: Track prediction latency, model drift, revenue metrics
5. **Fallback**: If model fails, return rule-based price

### Code Sketch (FastAPI endpoint)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import pickle

app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379)

class PricingRequest(BaseModel):
    user_id: str
    activity_id: str
    timestamp: str

@app.post("/predict_price")
async def predict_price(request: PricingRequest):
    try:
        # 1. Get features from cache
        features = get_features(request.user_id, request.activity_id)

        # 2. A/B test assignment
        variant = ab_test.assign_variant(request.user_id)
        model = load_model(variant)

        # 3. Predict
        price = model.predict([features])[0]

        # 4. Log event
        log_prediction(request, price, variant)

        return {"price": float(price), "variant": variant}

    except Exception as e:
        # Fallback to rule-based pricing
        return {"price": get_baseline_price(request.activity_id), "variant": "fallback"}
```

---

## Part 6: Behavioral Prep (Quick Hits)
**Time**: 15 minutes tonight
**Method**: Pick 3 stories from bullet_library, practice 2-min delivery

### Story 1: Technical Challenge (GLP Credit Scoring)
**Situation**: Needed to build credit scoring model for 200K+ users with sparse data
**Task**: Design model that balances precision (avoid bad loans) and recall (approve good users)
**Action**:
- Engineered 50+ features from transaction history
- Used gradient boosting with class weights for imbalance
- Implemented SHAP for explainability (regulatory requirement)
**Result**: 15% reduction in default rate, 92% precision, deployed to production

### Story 2: Production Issue (Baiquan Factor Engine)
**Situation**: Factor calculation pipeline failing silently, causing stale data
**Task**: Debug and fix without disrupting live trading
**Action**:
- Added comprehensive logging and monitoring
- Implemented circuit breaker pattern
- Set up alerting for data freshness
**Result**: 99.9% uptime, caught 3 data quality issues before they hit production

### Story 3: Collaboration (Ele.me A/B Testing)
**Situation**: Product team wanted to test new recommendation algorithm
**Task**: Design experiment that's statistically valid and doesn't hurt revenue
**Action**:
- Worked with PM to define success metrics
- Implemented multi-armed bandit for adaptive allocation
- Set up real-time dashboards for monitoring
**Result**: 8% lift in CTR, rolled out to 100% traffic

---

## Part 7: Pre-Interview Checklist (Tomorrow Morning)
**Time**: 30 minutes before interview

### Technical Warm-Up (15 min)
- [ ] Write a decorator from scratch (no looking)
- [ ] Implement a generator for Fibonacci
- [ ] Code a simple A/B test assignment function
- [ ] Explain bias-variance tradeoff out loud

### Environment Setup (5 min)
- [ ] Test webcam and microphone
- [ ] Close all unnecessary tabs/apps
- [ ] Have Python REPL open for quick testing
- [ ] Water, notebook, pen ready

### Mental Prep (10 min)
- [ ] Review 3 STAR stories
- [ ] Read FareHarbor mission statement
- [ ] Deep breathing: 4-7-8 technique
- [ ] Remind yourself: "I've built production ML systems. I can do this."

---

## Part 8: During Interview - Communication Protocol

### When Given a Problem
1. **Clarify requirements** (2 min)
   - "What's the expected input/output format?"
   - "Are there performance constraints?"
   - "Should I optimize for readability or efficiency?"

2. **Think out loud** (throughout)
   - "I'm thinking we could use a dictionary here because..."
   - "Let me consider edge cases: empty input, negative numbers..."
   - "I'm going to start with a brute force approach, then optimize"

3. **Write clean code** (during)
   - Use meaningful variable names
   - Add comments for complex logic
   - Test with example inputs as you go

4. **Handle getting stuck** (if needed)
   - "I'm not sure about X, but here's my reasoning..."
   - "Could you give me a hint about Y?"
   - "Let me try a different approach..."

### Red Flags to Avoid
- ❌ Jumping straight to code without clarifying
- ❌ Silent coding for 5+ minutes
- ❌ Giving up when stuck
- ❌ Not testing your code
- ❌ Defensive/dismissive when given feedback

---

## Part 9: Post-Interview Action
**IMMEDIATELY after interview** (within 1 hour):
- [ ] Create `09_post_interview_notes.md`
- [ ] Record: What questions were asked?
- [ ] Record: How did I answer?
- [ ] Record: What did I struggle with?
- [ ] Record: Interviewer's reactions/feedback
- [ ] Record: What would I do differently?

**This is CRITICAL for the feedback loop!**

---

## Resources
- Python docs: https://docs.python.org/3/
- Scikit-learn docs: https://scikit-learn.org/
- Multi-armed bandits: https://en.wikipedia.org/wiki/Multi-armed_bandit
- FareHarbor careers: https://fareharbor.com/careers/

## Final Thoughts
You've built production ML systems at GLP and Baiquan. You've handled real-world data, deployed models, and solved business problems. The interview is just showing them what you already know how to do.

**Confidence comes from preparation. You've got this.**
