"""
Bond Pricing & Yield Calculator
--------------------------------
Core idea: a bond's price is the present value of all its future cash flows
(coupon payments plus the face value returned at maturity), discounted at the
market yield.

    Price = sum( C / (1 + y/f)^t ) + F / (1 + y/f)^n

    F = face value, C = coupon per period, y = annual yield,
    f = payments per year, n = total number of periods
"""

import argparse


# ----------------------------------------------------------------------
# Validation helper
# ----------------------------------------------------------------------
def _num_periods(years, freq):
    """Total number of coupon periods, validated."""
    if freq not in (1, 2, 4, 12):
        raise ValueError("freq must be 1, 2, 4 or 12 payments per year")
    if years <= 0:
        raise ValueError("years to maturity must be positive")
    n = round(years * freq)
    if n < 1:
        raise ValueError("bond must have at least one payment period")
    return n


# ----------------------------------------------------------------------
# Core calculations
# ----------------------------------------------------------------------
def bond_price(face, coupon_rate, ytm, years, freq=2):
    """Price of a bond given its yield to maturity (all rates as decimals)."""
    n = _num_periods(years, freq)
    coupon = face * coupon_rate / freq
    r = ytm / freq  # yield per period

    price = 0.0
    for t in range(1, n + 1):
        price += coupon / (1 + r) ** t  # PV of each coupon
    price += face / (1 + r) ** n        # PV of principal
    return price


def current_yield(face, coupon_rate, price):
    """Annual coupon income divided by the bond's market price."""
    if price <= 0:
        raise ValueError("price must be positive")
    return face * coupon_rate / price


def classify(price, face, tol=1e-6):
    """Is the bond trading at a premium, discount or par?"""
    if abs(price - face) <= tol:
        return "par"
    return "premium" if price > face else "discount"


def yield_to_maturity(face, coupon_rate, price, years, freq=2,
                      tol=1e-10, max_iter=200):
    """
    Solve for YTM using bisection.
    Bond price falls as yield rises, so we can repeatedly halve the
    search interval until the computed price matches the market price.
    """
    if price <= 0:
        raise ValueError("price must be positive")

    low, high = 0.0, 1.0
    # Price at 0% yield is the largest possible (sum of undiscounted cash flows)
    if price > bond_price(face, coupon_rate, low, years, freq) + 1e-9:
        raise ValueError("price too high: implies a negative yield")

    # Widen the upper bound until it brackets the answer
    while bond_price(face, coupon_rate, high, years, freq) > price:
        high *= 2
        if high > 1000:
            raise ValueError("could not bracket the yield")

    for _ in range(max_iter):
        mid = (low + high) / 2
        if bond_price(face, coupon_rate, mid, years, freq) > price:
            low = mid   # price too high -> yield must be higher
        else:
            high = mid
        if high - low < tol:
            break
    return (low + high) / 2


def durations(face, coupon_rate, ytm, years, freq=2):
    """
    Macaulay duration (years) and modified duration.
    Duration measures how sensitive the bond price is to yield changes.
    """
    n = _num_periods(years, freq)
    coupon = face * coupon_rate / freq
    r = ytm / freq
    price = bond_price(face, coupon_rate, ytm, years, freq)

    weighted = 0.0
    for t in range(1, n + 1):
        cash_flow = coupon + (face if t == n else 0)
        weighted += t * cash_flow / (1 + r) ** t

    macaulay = weighted / price / freq
    modified = macaulay / (1 + r)
    return macaulay, modified


# ----------------------------------------------------------------------
# Plot (optional, needs matplotlib)
# ----------------------------------------------------------------------
def plot_price_yield(face, coupon_rate, years, freq=2, ytm=None, save_path=None):
    """Plot bond price against yield to show their inverse relationship."""
    import matplotlib.pyplot as plt

    yields = [i / 1000 for i in range(5, 201)]  # 0.5% to 20%
    prices = [bond_price(face, coupon_rate, y, years, freq) for y in yields]

    plt.figure(figsize=(8, 5))
    plt.plot([y * 100 for y in yields], prices, label="Bond price")
    plt.axhline(face, color="grey", linestyle="--", label="Face value (par)")
    plt.axvline(coupon_rate * 100, color="green", linestyle=":",
                label=f"Coupon rate ({coupon_rate * 100:.2f}%)")
    if ytm is not None:
        p = bond_price(face, coupon_rate, ytm, years, freq)
        plt.scatter([ytm * 100], [p], color="red", zorder=5,
                    label=f"Your bond ({ytm * 100:.2f}%, {p:.2f})")
    plt.xlabel("Yield to maturity (%)")
    plt.ylabel("Bond price")
    plt.title("Bond Price vs Yield")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Plot saved to {save_path}")
    else:
        plt.show()


# ----------------------------------------------------------------------
# Command line interface
# ----------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        description="Bond pricing and yield calculator. "
                    "Give --ytm to compute price, or --price to compute YTM.")
    p.add_argument("--face", type=float, default=1000, help="face value (default 1000)")
    p.add_argument("--coupon", type=float, required=True,
                   help="annual coupon rate in %% (e.g. 7 for 7%%)")
    p.add_argument("--years", type=float, required=True, help="years to maturity")
    p.add_argument("--freq", type=int, default=2, choices=[1, 2, 4, 12],
                   help="coupon payments per year (default 2)")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--ytm", type=float, help="market yield in %%")
    group.add_argument("--price", type=float, help="market price (to solve for YTM)")
    p.add_argument("--plot", action="store_true", help="show price vs yield plot")
    p.add_argument("--save-plot", metavar="FILE", help="save the plot to a file")
    return p


def main():
    args = build_parser().parse_args()
    coupon_rate = args.coupon / 100

    if args.ytm is not None:
        ytm = args.ytm / 100
        price = bond_price(args.face, coupon_rate, ytm, args.years, args.freq)
    else:
        price = args.price
        ytm = yield_to_maturity(args.face, coupon_rate, price, args.years, args.freq)

    cy = current_yield(args.face, coupon_rate, price)
    mac, mod = durations(args.face, coupon_rate, ytm, args.years, args.freq)

    print("\n=== Bond Summary ===")
    print(f"Face value         : {args.face:,.2f}")
    print(f"Coupon rate        : {args.coupon:.2f}% ({args.freq}x per year)")
    print(f"Years to maturity  : {args.years}")
    print(f"Yield to maturity  : {ytm * 100:.4f}%")
    print(f"Price              : {price:,.2f}")
    print(f"Trading at         : {classify(price, args.face)}")
    print(f"Current yield      : {cy * 100:.4f}%")
    print(f"Macaulay duration  : {mac:.4f} years")
    print(f"Modified duration  : {mod:.4f}")

    if args.plot or args.save_plot:
        plot_price_yield(args.face, coupon_rate, args.years, args.freq,
                         ytm=ytm, save_path=args.save_plot)


if __name__ == "__main__":
    main()
