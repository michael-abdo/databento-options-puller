# 🔍 How It Works - Visual Guide

## 📊 The Rolling 15-Delta Strategy

```
Month 1 (December)              Month 2 (January)              Month 3 (February)
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ First Trading   │            │ First Trading   │            │ First Trading   │
│ Day: Dec 1      │            │ Day: Jan 3      │            │ Day: Feb 1      │
│                 │            │                 │            │                 │
│ Target: Feb     │            │ Target: Mar     │            │ Target: Apr     │
│ (M+2)           │            │ (M+2)           │            │ (M+2)           │
│                 │            │                 │            │                 │
│ Find 15-delta   │            │ Find 15-delta   │            │ Find 15-delta   │
│ Strike: $2.78   │            │ Strike: $2.45   │            │ Strike: $2.70   │
│                 │            │                 │            │                 │
│ ► OHF2 C27800   │            │ ► OHG2 C24500   │            │ ► OHH2 C27000   │
└─────────────────┘            └─────────────────┘            └─────────────────┘
        │                              │                              │
        └──────────────────────────────┴──────────────────────────────┘
                                       │
                                       ▼
                              📄 OUTPUT CSV FILE
```

## 🎯 What is Delta?

```
Stock Price Movement vs Option Price Movement
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    High Delta (0.80)
Futures ▲ $1.00 ─────────────────────► Option ▲ $0.80

                    15-Delta (0.15)  ← We target this!
Futures ▲ $1.00 ─────► Option ▲ $0.15

                    Low Delta (0.05)
Futures ▲ $1.00 ──► Option ▲ $0.05
```

## 📈 The Process Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Date Check  │     │ 2. Find Target  │     │ 3. Get Options  │
│                 │     │                 │     │                 │
│ Is it first     │ YES │ Current: Dec    │     │ Fetch all Mar   │
│ trading day? ───┼────►│ Target: Feb     │────►│ call options    │
│                 │     │ (M+2)           │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 6. Track Daily  │     │ 5. Select Best  │     │ 4. Calculate    │
│                 │     │                 │     │    Deltas       │
│ Pull prices     │     │ Pick strike     │     │                 │
│ until next   ◄─┼─────┤ closest to   ◄──┼─────┤ For each strike │
│ month's roll    │     │ 0.15 delta      │     │ find the delta  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 📅 Timeline Example

```
December 2021                          January 2022
─────────────────────────────────────────────────────────────►
│                                      │
Dec 1: Buy OHF2 C27800                Jan 3: Buy OHG2 C24500
       (Feb expiry, $2.78 strike)            (Mar expiry, $2.45 strike)
│                                      │
├──────── Track OHF2 daily ───────────┤
                                       ├──── Track OHG2 daily ────►
```

## 💾 Output Format Explained

```csv
timestamp,OHF2 C27800,OHG2 C24500,OHH2 C27000
12/1/21,0.12,,,              ← OHF2 starts (Dec roll)
12/2/21,0.11,,,
12/5/21,0.11,2.6,,           ← OHG2 appears (overlapping)
...
1/3/22,,4.11,1.80,           ← OHH2 starts (Jan roll)
```

Each column represents one 15-delta option that was selected on a roll date.

## 🔄 Why M+2 Expiration?

```
Current Month    M+1 (Too Close)    M+2 (Just Right)    M+3 (Too Far)
December ────────► January ─────────► February ─────────► March
                      ❌                  ✅                 ❌
                   (Too little         (Optimal          (Too much
                   time value)         liquidity)        uncertainty)
```

## 🎲 Why 15-Delta?

```
Delta Range    Probability ITM    Use Case
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
50-delta         ~50%            At-the-money hedging
25-delta         ~25%            Moderate protection
15-delta         ~15%            Income generation ← Our target!
5-delta          ~5%             Tail risk protection
```

15-delta options provide a good balance of:
- Premium income (not too cheap)
- Low exercise risk (85% chance of expiring worthless)
- Decent liquidity (actively traded)

## 🚀 Ready to Start?

Now that you understand how it works:

1. **Try it out**: Run `python quick_example.py`
2. **Learn more**: Read [GETTING_STARTED.md](GETTING_STARTED.md)
3. **Dive deep**: Check [docs/guides/DOCUMENTATION.md](docs/guides/DOCUMENTATION.md)

---

The system automates all of this complexity into a simple command! 🎉