# Deribit 项目 - 傻瓜式面试拆解

## 🧘 先深呼吸 - 你其实有准备

**你可能会被问到的问题**: 10-15个技术问题
**你需要完全准备好的**: 3-5个核心问题
**其他可以诚实承认的**: 剩下的问题

**核心策略**: 证明你理解原理 + 诚实承认局限 + 展示学习意愿

---

## 📚 模块一: 项目概述 (必考! 必须背熟)

### 问题: "Tell me about this crypto options system on your resume."

**回答模板** (背诵版本，1.5-2分钟):

```
这是我最近半年的个人学习项目。

背景是我在VU Amsterdam读AI硕士期间，对强化学习和不确定性量化
做了研究，想把这方面的理解应用到交易系统中。

系统有三个模块：

第一，定价引擎。我自己实现了Black-Scholes模型，
包括完整的希腊字母计算和隐含波动率求解器。

第二，策略模块。基于edge的做市策略框架，
计算买卖价差、判断交易信号。

第三，风险管理。多层风控框架，包括希腊字母限制、回撤控制。

目前接入了Deribit的测试网，在做纸面交易验证。

我要强调的是，这是一个学习项目，目的是验证我对期权理论的
理解，而不是真正的生产系统。
```

**背诵检查点**:
- [ ] 三个模块能说清楚
- [ ] 最后强调"学习项目"和"纸面交易"
- [ ] 控制在2分钟内

**可能的追问1**: "Why options? Why not futures or spot?"

**回答**:
```
Two reasons:

First, I have some background in options from my Baiquan days,
though that was equity options, not crypto.

Second, options pricing has beautiful mathematical structure -
the whole framework of Black-Scholes, Greeks, volatility surface.
As someone with engineering background, I find it elegant.

Also, options force you to think about risk in a structured way
through Greeks, which appeals to my systematic mindset.
```

**可能的追问2**: "Why Deribit specifically?"

**回答**:
```
Deribit is the largest crypto options exchange by volume,
and they have a well-documented API and a testnet.

For a learning project, having access to real market data
(even on testnet) is valuable compared to just using historical data.

Also, crypto options are interesting because of the high volatility
and 24/7 trading - different dynamics from traditional markets.
```

---

## 📚 模块二: Black-Scholes (必考基础)

### 问题: "Explain Black-Scholes to me."

**极简版本** (30秒):
```
Black-Scholes is a mathematical model for pricing European options.

It assumes the underlying asset price follows a geometric Brownian motion
with constant volatility.

The key inputs are: current price, strike price, time to maturity,
risk-free rate, and volatility.

The output is the theoretical fair price of the option.
```

**标准版本** (1分钟):
```
Black-Scholes models the price of a European option.

The core assumption is that the underlying stock price follows
a log-normal distribution - specifically, geometric Brownian motion.

The famous formula for a call option is:
C = S₀ × N(d₁) - K × e^(-rT) × N(d₂)

Where:
- S₀ is current stock price
- K is strike price  
- T is time to maturity
- r is risk-free rate
- σ is volatility
- N() is the cumulative distribution function of standard normal

d₁ and d₂ are calculated from these parameters.

The model assumes constant volatility, no dividends, efficient markets,
and the ability to continuously hedge.
```

**手写公式准备** (如果要求写下来):
```
Call option price: C = S₀N(d₁) - Ke^(-rT)N(d₂)

where:
d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T

N(x) = cumulative distribution function of standard normal
```

**关键假设** (必须知道):
1. Underlying follows geometric Brownian motion
2. Constant volatility
3. No dividends (or known constant dividend yield)
4. Efficient markets (no arbitrage)
5. Can continuously hedge
6. Constant risk-free rate

---

### 问题: "What are the limitations of Black-Scholes, especially for crypto?"

**回答模板**:
```
There are several limitations:

First, constant volatility assumption. In reality, volatility changes
over time and has clustering effects. In crypto, this is even more
extreme - you can have 5% daily moves regularly.

Second, the log-normal distribution assumption. Crypto has fat tails -
extreme moves happen more often than the normal distribution predicts.

Third, Black-Scholes assumes continuous trading, but crypto is
24/7 with potential liquidity gaps.

Fourth, BS doesn't account for jumps. Crypto can have sudden gaps
based on news or whale movements.

For my project, I use standard BS but I'm aware of these limitations.
I know more advanced models exist - like jump-diffusion models or
stochastic volatility models - but I haven't implemented them yet.
```

**加分点** (可以说，但别被追问太深):
- "Heston model has stochastic volatility and closed-form solution"
- "Jump-diffusion models like Merton's add Poisson jumps"

**如果被追问**: "Tell me more about Heston model."

**回答**:
```
I know Heston allows volatility to be random rather than constant.
The volatility follows its own stochastic process - mean-reverting.

The model has closed-form solution using characteristic functions
and Fourier transform, but I haven't implemented it.

I understand the concept but not the mathematical details of
the implementation.
```

---

## 📚 模块三: 希腊字母 (必考! 重点准备)

### 问题: "Explain the Greeks."

**极简版本** (背诵):
```
Delta: Sensitivity of option price to underlying price change.
       Like a probability of expiring in-the-money.

Gamma: Sensitivity of Delta to underlying price change.
       How fast Delta changes. Highest at ATM, near expiration.

Theta: Time decay. Option loses value as time passes.
       Usually negative for long options.

Vega: Sensitivity to volatility. Options gain value when
      volatility increases.

Rho: Sensitivity to interest rates. Usually less important.
```

**详细版本**:

**Delta**:
```
Delta = ∂V/∂S

For call options: Delta between 0 and 1 (typically 0 to 0.5 for OTM, 0.5 for ATM, 0.5 to 1 for ITM)
For put options: Delta between -1 and 0

Intuition: If Delta is 0.6, a $1 increase in stock price
causes approximately $0.60 increase in call option price.

At expiration, Delta approaches 1 for deep ITM calls, 0 for deep OTM.
```

**Gamma**:
```
Gamma = ∂²V/∂S² = ∂Delta/∂S

Same for calls and puts.

Highest when ATM and near expiration.
This is the risk - your Delta changes fastest when you're ATM near expiry.

In my system, I monitor Gamma exposure and set limits.
```

**Theta**:
```
Theta = ∂V/∂t

Usually negative for long options (you lose value as time passes).

Accelerates near expiration - the "theta decay" is fastest
in the last month, especially the last week.

For crypto options with high IV, theta can be substantial.
```

**Vega**:
```
Vega = ∂V/∂σ

Higher for longer-dated options.

In crypto, vega risk is huge because volatility can change rapidly.
A 10% change in IV can mean significant P&L for an options portfolio.
```

---

### 问题: "How do you calculate Greeks in your system?"

**回答**:
```
I use the closed-form analytical solutions from Black-Scholes.

For example:
- Delta_call = N(d₁)
- Gamma = N'(d₁) / (S × σ × √T)
- Vega = S × N'(d₁) × √T

Where N' is the standard normal PDF.

I also did some sanity checks using finite differences
(numerical differentiation) to verify my analytical calculations.

For a small ΔS, (V(S+ΔS) - V(S-ΔS)) / (2×ΔS) should approximate Delta.
This helped me catch some bugs in my implementation.
```

**如果真的被问公式推导**:
```
I'm honest - I implemented the standard formulas from textbooks,
but I haven't done the full mathematical derivation from first principles.

I understand the intuition - for example, why Delta of call is N(d₁):
it relates to the risk-neutral probability of the option expiring ITM.

But the full derivation using Itô's lemma and PDEs - I know the outline
but not the details.
```

---

## 📚 模块四: 隐含波动率 (IV)

### 问题: "How do you calculate implied volatility?"

**回答模板**:
```
IV is the volatility value that makes the Black-Scholes price
equal to the observed market price.

Since there's no closed-form solution to invert BS,
I use numerical methods.

Specifically, I use bisection method (binary search):

1. Start with a range, say sigma_low = 0.001, sigma_high = 5.0
2. Calculate BS price at midpoint
3. If model price < market price, volatility needs to be higher
   (because higher vol increases option price)
4. Adjust range and repeat
5. Stop when |model_price - market_price| < epsilon (e.g., 1e-6)
   or after max iterations (e.g., 100)

This is robust but slower than Newton-Raphson.

I tried Newton-Raphson but had convergence issues with extreme
market prices, so I stuck with bisection for reliability.
```

**可能的追问**: "What is the volatility smile?"

**回答**:
```
Volatility smile refers to the pattern where IV varies with strike price.

In theory, if BS assumptions held, IV should be constant across strikes.
But in reality, you often see:
- Lower strikes (OTM puts) have higher IV (crash protection)
- ATM has lower IV
- Higher strikes may have slightly higher IV

Plotting IV against strike gives a "smile" or "smirk" pattern.

For crypto, this effect is often very pronounced due to
tail risk and demand for downside protection.

My current implementation uses a single IV per option,
but I know more sophisticated approaches model the full surface.
```

**可能的追问**: "How do you use IV in your trading strategy?"

**回答**:
```
My simple approach:

1. Calculate theoretical price using some reference IV
2. Compare to market price
3. If market IV is significantly higher than my reference,
   the option might be overpriced (selling opportunity)
4. If market IV is lower, might be buying opportunity

But I want to be clear - this is very naive.

Proper vol trading requires:
- Understanding vol term structure (different expiries)
- Understanding vol skew (different strikes)
- Forecasting realized vol vs trading implied vol

I haven't implemented these more sophisticated approaches yet.
```

---

## 📚 模块五: 风险管理 (诚实承认局限)

### 问题: "Tell me about your risk management."

**回答模板**:
```
I implemented a multi-layer framework, but I want to be transparent -
this is based on textbook knowledge, not proven in live trading.

Layer 1 - Position limits:
- Maximum position size per trade (e.g., 2% of capital)
- Maximum total portfolio exposure (e.g., 20% of capital)

Layer 2 - Greeks limits:
- Delta limit: net delta exposure capped
- Gamma monitoring: alerts when gamma is concentrated
- Vega limit: cap on volatility exposure

Layer 3 - Drawdown controls:
- Daily loss limit (e.g., stop trading if down 5% in a day)
- Maximum drawdown limit (e.g., 20% from peak)
- Consecutive loss limits

Layer 4 - Kelly-inspired sizing:
- Adjust position size based on perceived edge and volatility
- Higher IV = smaller positions

What I DON'T have (and know I need):
- Stress testing for extreme scenarios
- Correlation risk across multiple positions
- Liquidity risk modeling
- Proper backtesting of the risk rules themselves
```

**可能的追问**: "How do you hedge Delta?"

**⚠️ 关键问题 - 诚实回答**:
```
This is a gap in my current system.

In theory, Delta hedging means buying or selling the underlying asset
to offset the option's Delta exposure.

For example, if I have a call option with Delta 0.6,
to be Delta-neutral I would need to short 0.6 units of the underlying.

In my current implementation, I only monitor Delta exposure
and set alerts, but I don't automatically execute the hedge trades.

The reasons:
1. Capital constraints - this is a learning project with limited funds
2. Complexity of implementing continuous hedging
3. In testnet, the price dynamics don't reflect real market impact

I know proper Delta hedging is crucial for options market making,
and this is something I want to learn more about.
```

**可能的追问**: "What's Kelly Criterion and how did you use it?"

**回答**:
```
Kelly Criterion is a formula for optimal bet sizing:
f = (bp - q) / b

Where:
- f = fraction of capital to bet
- b = odds received (profit potential)
- p = probability of winning
- q = probability of losing (1-p)

In my system, I didn't use the full formula literally.

Instead, I used the principle: size positions based on perceived edge
and adjust for volatility.

Higher confidence in the trade = larger position
Higher IV (more uncertainty) = smaller position

But this is a simplified heuristic, not rigorous Kelly optimization.
```

---

## 📚 模块六: 技术实现 (简单诚实)

### 问题: "What's your tech stack?"

**回答模板**:
```
Backend: Python

Key libraries:
- NumPy for numerical calculations
- scipy.stats for normal distribution functions
- WebSocket client for real-time data
- SQLite for data storage
- Redis for caching hot data

Architecture:
- Data ingestion module (WebSocket to Deribit)
- Pricing engine (Black-Scholes calculations)
- Strategy module (signal generation)
- Risk module (limits checking)
- Execution module (paper trading orders)
- Monitoring dashboard (Streamlit)

Nothing fancy - it's a simple architecture suitable for a
learning project, not production trading.
```

**可能的追问**: "What would you change for production?"

**回答**:
```
Many things:

Latency: Use C++ or Rust for hot path, not Python.
Use FPGA for tick-to-trade if doing HFT.

Database: Use proper time-series database like TimescaleDB or kdb+,
not SQLite.

Infrastructure: Distributed architecture with redundancy,
not a single process.

Risk: Real-time risk monitoring with dedicated risk servers,
not just pre-trade checks.

Testing: Much more extensive backtesting, paper trading,
and gradual rollout.

Monitoring: Professional observability stack, alerting,
automated failover.

My current system is "get it working and learn the concepts".
Production is a completely different level of engineering.
```

---

## 🆘 应急预案

### 场景1: TJ问了一个你完全不懂的问题

**话术**:
```
"I don't know the answer to that specific question.

This project has been my way of learning options pricing,
and there's clearly much more I need to learn.

What I can say is [related concept you do know],
but I haven't studied [the specific topic] in depth yet.

If I join Maverick, this is exactly the kind of thing
I want to learn from experienced traders."
```

### 场景2: TJ指出你系统的明显缺陷

**话术**:
```
"You're absolutely right, that's a significant limitation.

I'm aware of [the issue], and I know proper systems would
handle it by [correct approach].

In my defense, this is a learning project with limited scope,
but I completely agree that [the proper approach] is necessary
for production.

This is why I'm interested in joining an established firm like
Maverick - to learn how these systems are properly built."
```

### 场景3: TJ问得太深入，你需要把话题转回你有优势的领域

**话术**:
```
"That's getting into details I haven't implemented yet.

What I can say with confidence is that I understand the
fundamental principles of [topic], and I've demonstrated
my ability to implement working systems through this project.

If I may pivot slightly - one area where I do have deeper
experience is my R-Breaker strategy work at Baiquan.

That was a production system with real capital, and I learned
a lot about [related topic].

Would it be helpful if I talked about that experience?"
```

---

## 📝 面试前最后检查清单

### 必须能流利说出的 (5个):
- [ ] 项目三模块概述 (1.5分钟版本)
- [ ] Black-Scholes基本公式和假设
- [ ] 五个希腊字母的定义和直觉
- [ ] IV求解的二分查找方法
- [ ] 风险管理的多层框架

### 必须知道的 (不要犯错):
- [ ] Delta of call is between 0 and 1
- [ ] Gamma is highest ATM near expiration
- [ ] IV is backed out from market price
- [ ] You DON'T have Delta hedging implemented
- [ ] This is paper trading on testnet, not live

### 可以诚实不知道的 (3-5个):
- [ ] Stochastic volatility model implementation details
- [ ] Jump-diffusion model math
- [ ] Production market making microstructure
- [ ] Complex exotic options pricing
- [ ] Regulatory capital requirements

### 保底话术 (记住):
> *"This is a learning project. I understand the principles but haven't implemented production-grade solutions. If I join Maverick, this is what I want to learn."*

---

## 🎯 最后提醒

**你不是去证明你是期权专家** - 你是去证明:
1. 你理解期权定价的基本原理 ✅
2. 你有动手实现的能力 ✅
3. 你有自主学习的动力 ✅
4. 你诚实、不夸大 ✅

**你的真正优势在 Baiquan 的 R-Breaker 策略** - 那才是实盘、生产、有业绩的。

如果这个 Deribit 项目聊不下去了，**果断转回 Baiquan**。

**你已经准备好了。去面试吧！** 🚀
