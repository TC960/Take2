import time
import argparse
import pathlib
import json
import math
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation, iqr
from pynput import keyboard

# --- Keyboard side maps for rough asymmetry ---
LEFT_HAND = set(list("`12345qwertasdfgzxcvb"))
RIGHT_HAND = set(list("67890-=[]\\yuiophjklnm,.'/"))

# ---------- Recorder ----------
class KeystrokeRecorder:
    def __init__(self):
        self.press_t = {}
        self.holds = []
        self.flights = []
        self.chars = []
        self.backspaces = 0
        self.last_release = None
        self.n_press = 0
        self.n_rel = 0

    def _on_press(self, key):
        t = time.perf_counter()
        try: k = key.char.lower() if hasattr(key, "char") and key.char else str(key)
        except: k = str(key)
        if self.last_release is not None:
            self.flights.append(max(0.0, t - self.last_release))
        self.press_t[k] = t
        self.n_press += 1
        self.chars.append(k)
        if k in ("\\x08", "Key.backspace"):
            self.backspaces += 1

    def _on_release(self, key):
        t = time.perf_counter()
        try: k = key.char.lower() if hasattr(key, "char") and key.char else str(key)
        except: k = str(key)
        if k in self.press_t:
            self.holds.append(max(0.0, t - self.press_t[k]))
            del self.press_t[k]
        self.last_release = t
        self.n_rel += 1

    def capture(self, duration_sec=60):
        print(f"\nType for {duration_sec}s… (ESC won’t stop; timer will)")
        listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        listener.start()
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < duration_sec and listener.is_alive():
            time.sleep(0.05)
        listener.stop()
        return {
            "holds": self.holds,
            "flights": self.flights,
            "chars": self.chars,
            "backspaces": self.backspaces,
            "n_press": self.n_press,
            "n_rel": self.n_rel
        }

# ---------- Feature engineering ----------
def stats(arr, pfx):
    arr = np.asarray(arr, float)
    arr = arr[np.isfinite(arr)]
    out = {}
    if arr.size == 0:
        for k in ["mean","std","median","iqr","mad","cv","p95","p99","min","max"]:
            out[f"{pfx}_{k}"] = np.nan
        return out
    out[f"{pfx}_mean"] = float(np.mean(arr))
    out[f"{pfx}_std"] = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    out[f"{pfx}_median"] = float(np.median(arr))
    out[f"{pfx}_iqr"] = float(iqr(arr)) if arr.size > 1 else 0.0
    out[f"{pfx}_mad"] = float(median_abs_deviation(arr)) if arr.size > 1 else 0.0
    out[f"{pfx}_cv"] = float((np.std(arr, ddof=1)/np.mean(arr))) if arr.size>1 and np.mean(arr)>0 else 0.0
    out[f"{pfx}_p95"] = float(np.percentile(arr, 95))
    out[f"{pfx}_p99"] = float(np.percentile(arr, 99))
    out[f"{pfx}_min"] = float(np.min(arr))
    out[f"{pfx}_max"] = float(np.max(arr))
    return out

def features_from_session(s):
    f = {}
    f.update(stats(s["holds"], "hold"))
    f.update(stats(s["flights"], "flight"))

    flights = np.asarray(s["flights"], float)
    flights = flights[np.isfinite(flights)]
    f["pause_rate_p95"] = float(np.mean(flights >= np.percentile(flights, 95))) if flights.size else np.nan

    left = sum(1 for k in s["chars"] if len(k)==1 and k in LEFT_HAND)
    right = sum(1 for k in s["chars"] if len(k)==1 and k in RIGHT_HAND)
    total_lr = left + right
    f["prop_left"] = float(left/total_lr) if total_lr else np.nan
    f["prop_right"] = float(right/total_lr) if total_lr else np.nan
    f["lr_imbalance_abs"] = float(abs(left-right)/total_lr) if total_lr else np.nan

    total_chars = sum(1 for k in s["chars"] if len(k)==1)
    est_duration = sum(s["holds"]) + sum(s["flights"])
    f["chars_per_sec"] = float(total_chars/est_duration) if est_duration>0 else np.nan
    f["backspace_per_100chars"] = float(100.0 * s["backspaces"] / max(1, total_chars))

    f["n_chars"] = int(total_chars)
    f["n_press"] = int(s["n_press"])
    f["n_rel"] = int(s["n_rel"])
    return f

# ---------- Robust baseline model ----------
class RobustBaseline:
    """
    Stores per-feature robust center & scale from personal baseline:
      center = median, scale = MAD (fall back to IQR or std or epsilon)
    """
    def __init__(self):
        self.center = {}
        self.scale = {}
        self.features = None  # column list

    @staticmethod
    def _robust_scale(values):
        arr = np.asarray(values, float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return 0.0
        mad = median_abs_deviation(arr)
        if mad and mad > 1e-12:
            return float(mad)
        q = iqr(arr) if arr.size > 1 else 0.0
        if q and q > 1e-12:
            return float(q/1.349)  # approximate MAD from IQR
        std = np.std(arr, ddof=1) if arr.size > 1 else 0.0
        return float(std if std>1e-12 else 1.0)

    def fit(self, df: pd.DataFrame):
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        self.features = list(df.columns)
        for c in self.features:
            col = df[c].values
            self.center[c] = float(np.median(col))
            self.scale[c] = self._robust_scale(col)

    def rz(self, x_row: dict):
        """Robust z-scores for a single feature dict."""
        rz = {}
        for c in self.features:
            x = float(x_row.get(c, 0.0))
            mu = self.center.get(c, 0.0)
            s = self.scale.get(c, 1.0)
            rz[c] = (x - mu) / s
        return rz

# ---------- Deterministic rules ----------
def evaluate_rules(feats: dict, rz: dict):
    """
    Rules are written to capture PD-leaning patterns reported in literature:
      - slower & more variable timing (hold/flight)
      - more long pauses
      - reduced overall speed
      - increased left-right imbalance (asymmetry)
      - elevated error repair (backspace rate)
    Thresholds use robust z-scores against your baseline.
    """
    fired = []

    def add(rule_id, cond, detail):
        if cond:
            fired.append({"rule": rule_id, "detail": detail})

    # 1) Flight-time variability high
    add("FLIGHT_VAR_HIGH",
        rz["flight_std"] > 2.0 or rz["flight_mad"] > 2.0 or rz["flight_iqr"] > 2.0,
        {"rz_flight_std": rz.get("flight_std"), "rz_flight_mad": rz.get("flight_mad"), "rz_flight_iqr": rz.get("flight_iqr")})

    # 2) Hold-time variability high
    add("HOLD_VAR_HIGH",
        rz["hold_std"] > 2.0 or rz["hold_mad"] > 2.0 or rz["hold_iqr"] > 2.0,
        {"rz_hold_std": rz.get("hold_std"), "rz_hold_mad": rz.get("hold_mad"), "rz_hold_iqr": rz.get("hold_iqr")})

    # 3) Long pauses frequent
    add("PAUSES_HIGH",
        rz["flight_p95"] > 2.0 or rz["pause_rate_p95"] > 2.0,
        {"rz_flight_p95": rz.get("flight_p95"), "rz_pause_rate_p95": rz.get("pause_rate_p95")})

    # 4) Overall speed reduced
    add("SPEED_LOW",
        rz["chars_per_sec"] < -2.0,
        {"rz_chars_per_sec": rz.get("chars_per_sec")})

    # 5) Left-right imbalance elevated
    add("ASYMMETRY_HIGH",
        rz["lr_imbalance_abs"] > 2.0,
        {"rz_lr_imbalance_abs": rz.get("lr_imbalance_abs")})

    # 6) Error repair (backspace per 100 chars) elevated
    add("BACKSPACE_RATE_HIGH",
        rz["backspace_per_100chars"] > 2.0,
        {"rz_backspace_per_100chars": rz.get("backspace_per_100chars")})

    # 7) Central tendency slowed (median timing)
    add("TIMING_SLOWED",
        rz["hold_median"] > 1.5 or rz["flight_median"] > 1.5,
        {"rz_hold_median": rz.get("hold_median"), "rz_flight_median": rz.get("flight_median")})

    # Score = fraction of rules that fired (simple, transparent)
    total_rules = 7
    score = len(fired) / total_rules
    # Simple bands
    if score >= 4/7:
        band = "HIGH"
    elif score >= 2/7:
        band = "MODERATE"
    else:
        band = "LOW"

    return {"score_0to1": score, "band": band, "rules_fired": fired}

# ---------- Storage helpers ----------
def save_json(obj, path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[saved] {path}")

def load_baseline_table(baseline_dir):
    bdir = pathlib.Path(baseline_dir)
    bdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(bdir.glob("baseline_*.json")):
        try:
            rows.append(json.loads(p.read_text())["features"])
        except Exception:
            pass
    if not rows:
        return None
    df = pd.DataFrame(rows).replace([np.inf,-np.inf], np.nan).fillna(0.0)
    return df

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Deterministic keystroke PD-style screener (research prototype)")
    ap.add_argument("--mode", required=True, choices=["collect_baseline","screen","just_features"])
    ap.add_argument("--duration", type=int, default=60)
    ap.add_argument("--baseline_dir", type=str, default="baseline_store")
    args = ap.parse_args()

    # Capture a session
    sess = KeystrokeRecorder().capture(args.duration)
    feats = features_from_session(sess)

    # Save raw session
    out_dir = pathlib.Path("sessions")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    save_json({"timestamp": stamp, "features": feats}, out_dir / f"session_{stamp}.json")

    if args.mode == "just_features":
        print(json.dumps({"features": feats}, indent=2))
        return

    if args.mode == "collect_baseline":
        save_json({"timestamp": stamp, "features": feats}, pathlib.Path(args.baseline_dir) / f"baseline_{stamp}.json")
        print("Baseline saved. Aim for 5–10 baseline sessions at different times/days.")
        return

    # SCREEN mode: build robust baseline, compute robust z, evaluate deterministic rules
    df_base = load_baseline_table(args.baseline_dir)
    if df_base is None or df_base.empty:
        raise SystemExit("No baseline found. Run --mode collect_baseline a few times first.")

    rb = RobustBaseline()
    rb.fit(df_base)
    rz = rb.rz(feats)

    result = evaluate_rules(feats, rz)
    report = {
        "band": result["band"],
        "score_0to1": result["score_0to1"],
        "rules_fired": result["rules_fired"],
        "features": feats,
        "robust_z": {k: float(v) for k, v in rz.items()}
    }
    print(json.dumps(report, indent=2))
    save_json(report, out_dir / f"screen_{stamp}.json")

if __name__ == "__main__":
    main()
