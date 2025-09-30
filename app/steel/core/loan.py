from dataclasses import dataclass

@dataclass
class LoanInput:
    principal: float
    apr_pct: float
    term_months: int
    extra_monthly_payment: float = 0.0

def amortize(inp: LoanInput):
    r = inp.apr_pct/100/12
    P = inp.principal
    n = inp.term_months
    pmt = (P/n) if r == 0 else P * (r * (1+r)**n) / ((1+r)**n - 1)
    pmt += inp.extra_monthly_payment
    bal = P
    sched = []
    for m in range(1, n+1):
        interest = bal * r
        principal = min(pmt - interest, bal)
        bal = max(bal - principal, 0.0)
        sched.append({"month": m, "payment": round(pmt,2), "interest": round(interest,2),
                      "principal": round(principal,2), "balance": round(bal,2)})
        if bal <= 1e-6:
            break
    total_interest = round(sum(x["interest"] for x in sched), 2)
    return {"payment": round(pmt,2), "months": len(sched), "total_interest": total_interest, "schedule": sched}
