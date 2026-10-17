def evaluate_predictions(y_test, probs, classes, th_long=0.35, th_short=0.564,
                         short_zero=False):
    idx_short = list(classes).index(0) if 0 in list(classes) else None
    idx_long = list(classes).index(2) if 2 in list(classes) else None
    
    p_short = probs[:, idx_short] if idx_short is not None else np.zeros(len(probs))
    p_long = probs[:, idx_long] if idx_long is not None else np.zeros(len(probs))
    
    preds = []
    for i in range(len(p_short)):
        if short_zero:
            if p_long[i] > th_long:
                preds.append(2)
            else:
                preds.append(1)
        else:
            if idx_short is not None and p_short[i] > th_short:
                preds.append(0)
            elif p_long[i] > th_long:
                preds.append(2)
            else:
                preds.append(1)
    preds = np.array(preds)
    profit = 0.0
    n_trades = 0
    n_wins = 0
    n_opposite = 0
    n_long_trades = 0
    n_short_trades = 0
    for i in range(len(preds)):
        actual = y_test.iloc[i] if hasattr(y_test, 'iloc') else y_test[i]
        pred = preds[i]
        if pred == 1:
            continue
        n_trades += 1
        if pred == 2:
            n_long_trades += 1
            if actual == 2:
                profit += 2.0
                n_wins += 1
            elif actual == 0:
                profit -= 1.0
                n_opposite += 1
            else:
                profit -= 1.0
        elif pred == 0:
            n_short_trades += 1
            if actual == 0:
                profit += 2.0
                n_wins += 1
            elif actual == 2:
                profit -= 1.0
                n_opposite += 1
            else:
                profit -= 1.0
    win_rate = n_wins / n_trades * 100 if n_trades > 0 else 0
    opp_rate = n_opposite / n_trades * 100 if n_trades > 0 else 0
    return {
        'n_trades': n_trades,
        'n_wins': n_wins,
        'n_opposite': n_opposite,
        'n_long': n_long_trades,
        'n_short': n_short_trades,
        'win_rate': round(win_rate, 1),
        'opposite_rate': round(opp_rate, 1),
        'profit': round(profit, 2),
        'avg_per_trade': round(profit / n_trades, 3) if n_trades > 0 else 0,
        'predictions': preds,
    }
