# coding: utf-8
"""Paired significance tests without scipy, which is not a dependency here.

Implements the two tests the evaluation reports and nothing else:

    t_sf2(t, df)   two-tailed p-value for Student's t, via the regularized
                   incomplete beta function (continued fraction, Numerical
                   Recipes form)
    sign_test(w,l) exact two-tailed binomial test at p = 0.5, ties dropped

Verified against known values in `if __name__ == "__main__"` below, so the
substitute for scipy is itself checked rather than trusted.
"""
import math

_TINY = 1e-300


def _betacf(a, b, x, itmax=300, eps=3e-16):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _TINY:
        d = _TINY
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betai(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lb = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
          + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lb) * _betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """Two-tailed p-value for Student's t with df degrees of freedom."""
    return betai(0.5 * df, 0.5, df / (df + t * t))


def sign_test(wins, losses):
    """Exact two-tailed binomial test at p = 0.5. Ties are dropped."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


def z_for(two_tailed_p, df=10 ** 6):
    """The t value whose two-tailed p equals the given one. Used for power."""
    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_sf2(mid, df) > two_tailed_p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def n_for_power(effect_size, alpha=0.05, power=0.80):
    """Paired-sample size for a given Cohen's d, normal approximation."""
    return math.ceil(((z_for(alpha) + z_for(2 * (1 - power))) / effect_size) ** 2)


if __name__ == "__main__":
    cases = [
        ("t_sf2(2.41, 38)", t_sf2(2.41, 38), 0.0209),
        ("t_sf2(2.95, 38)", t_sf2(2.95, 38), 0.0054),
        ("t_sf2(2.00,  1)", t_sf2(2.00, 1), 0.2952),
        ("t_sf2(1.96, 1e6)", t_sf2(1.96, 10 ** 6), 0.0500),
        ("t_sf2(0.00, 10)", t_sf2(0.00, 10), 1.0000),
        ("sign_test(29, 10)", sign_test(29, 10), 0.003378),
        ("sign_test(30,  9)", sign_test(30, 9), 0.001065),
        ("sign_test(5, 5)", sign_test(5, 5), 1.0000),
        ("sign_test(10, 0)", sign_test(10, 0), 0.001953),
    ]
    bad = 0
    for name, got, want in cases:
        ok = abs(got - want) < 1e-4
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'} {name:20} {got:.4f}  expected {want:.4f}")
    print(f"\n{len(cases) - bad}/{len(cases)} reference values reproduced")
    raise SystemExit(1 if bad else 0)
