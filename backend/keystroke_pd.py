import time
import sys
import json
import math
import argparse
import pathlib
from collections import defaultdict, deque

import numpy as np
import pandas as pd
from pynput import keyboard
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from joblib import dump, load
from scipy.stats import iqr, median_abs_deviation

# ---------------------------
# Utility: left/right hand sets (approx for asymmetry)
# ---------------------------
LEFT_HAND_KEYS = set(list("`12345qwertasdfgzxcvb"))
RIGHT_HAND_KEYS = set(list("67890-=[]\\yuiophjklnm,.'/"))

# ---------------------------
# Keystroke Recorder
# ---------------------------
class KeystrokeRecorder:
    """
    Records press/release timestamps for each key. Computes:
    - hold times per key (press -> release)
    - flight times (release -> next press)
    Also counts backspaces and pauses.
    """
    def __init__(self):
        self.press_times = {}              # key -> last press timestamp
        self.hold_times = []               # seconds
        self.flight_times = []             # seconds
        self.char_stream = []              # for analysis (keys typed)
        self.backspace_count = 0
        self.last_release_time = None
        self.n_presses = 0
        self.n_releases = 0
        self._listener = None
        self._running = False

    def _on_press(self, key):
        t = time.perf_counter()
        try:
            k = key.char.lower() if hasattr(key, "char") and key.char else str(key)
        except:
            k = str(key)

        # flight time: time since last release to this press
        if self.last_release_time is not None:
            self.flight_times.append(max(0.0, t - self.last_release_time))

        self.press_times[k] = t
        self.n_presses += 1
        self.char_stream.append(k)

        # backspace
        if k in ("\\x08", "Key.backspace"):
            self.backspace_count += 1

    def _on_release(self, key):
        t = time.perf_counter()
        try:
            k = key.char.lower() if hasattr(key, "char") and key.char else str(key)
        except:
            k = str(key)

        if k in self.press_times:
            hold = max(0.0, t - self.press_times[k])
            self.hold_times.append(hold)
            del self.press_times[k]

        self.last_release_time = t
        self.n_releases += 1

        # ESC to stop
        if key == keyboard.Key.esc:
            return False

    def start(self, duration_sec=None, prompt=True):
        """
        Start capture. If duration_sec is given, auto-stop after that many seconds.
        Otherwise, press ESC to stop.
        """
        if prompt:
            print("\n[Typing] Start typing. Press ESC to stop." if duration_sec is None
                  else f"\n[Typing] Start typing. Auto-stops in {duration_sec}s.")

        self._running = True
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()
        t0 = time.perf_counter()

        try:
            if duration_sec is None:
                self._listener.join()
            else:
                while time.perf_counter() - t0 < duration_sec and self._listener.is_alive():
                    time.sleep(0.05)
                self._listener.stop()
        finally:
            self._running = False

    def to_dataframe(self):
        # Return a raw summary dataframe
        return pd.DataFrame({
            "hold_times": pd.Series(self.hold_times),
            "flight_times": pd.Series(self.flight_times),
        })

# ---------------------------
# Feature Extraction
# ---------------------------
class FeatureExtractor:
    """
    Produces a feature vector inspired by keystroke-PD literature:
    - Hold time stats: mean, std, median, IQR, MAD, CV
    - Flight time stats: same
    - Pause features: p95/p99 of flights as 'pauses'
    - Asymmetry: proportion of left vs right keys; difference in average hold by side
    - Error rate: backspaces per 100 chars
    - Overall speed: chars per second
    """
    def __init__(self):
        pass

    @staticmethod
    def _basic_stats(arr, prefix):
        arr = np.asarray(arr, dtype=float)
        arr = arr[np.isfinite(arr)]
        feats = {}
        if arr.size == 0:
            for name in ["mean","std","median","iqr","mad","cv","p95","p99","min","max"]:
                feats[f"{prefix}_{name}"] = np.nan
            return feats

        feats[f"{prefix}_mean"]   = float(np.mean(arr))
        feats[f"{prefix}_std"]    = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
        feats[f"{prefix}_median"] = float(np.median(arr))
        feats[f"{prefix}_iqr"]    = float(iqr(arr)) if arr.size > 1 else 0.0
        feats[f"{prefix}_mad"]    = float(median_abs_deviation(arr)) if arr.size > 1 else 0.0
        feats[f"{prefix}_cv"]     = float((np.std(arr, ddof=1)/np.mean(arr))) if np.mean(arr) > 0 and arr.size > 1 else 0.0
        feats[f"{prefix}_p95"]    = float(np.percentile(arr, 95))
        feats[f"{prefix}_p99"]    = float(np.percentile(arr, 99))
        feats[f"{prefix}_min"]    = float(np.min(arr))
        feats[f"{prefix}_max"]    = float(np.max(arr))
        return feats

    @staticmethod
    def _side_masks(char_stream):
        left = 0
        right = 0
        for k in char_stream:
            if len(k) == 1:  # single character key
                if k in LEFT_HAND_KEYS:
                    left += 1
                elif k in RIGHT_HAND_KEYS:
                    right += 1
        total = left + right
        return left, right, total

    def extract(self, recorder: KeystrokeRecorder):
        feats = {}
        # Stats
        feats.update(self._basic_stats(recorder.hold_times, "hold"))
        feats.update(self._basic_stats(recorder.flight_times, "flight"))

        # Derived “pause” measures from long flights
        flights = np.asarray(recorder.flight_times, dtype=float)
        flights = flights[np.isfinite(flights)]
        if flights.size > 0:
            long_pause_thr = np.percentile(flights, 95)
            feats["pause_rate_p95"] = float(np.mean(flights >= long_pause_thr))
        else:
            feats["pause_rate_p95"] = np.nan

        # Asymmetry proxies
        left, right, total_lr = self._side_masks(recorder.char_stream)
        feats["prop_left"] = float(left / total_lr) if total_lr else np.nan
        feats["prop_right"] = float(right / total_lr) if total_lr else np.nan
        feats["lr_imbalance_abs"] = float(abs((left - right) / total_lr)) if total_lr else np.nan

        # Backspace / error proxy
        total_chars = sum(1 for k in recorder.char_stream if len(k) == 1)
        feats["backspace_per_100chars"] = float(100.0 * recorder.backspace_count / max(1, total_chars))

        # Speed (approx): chars per second over the session
        if recorder.n_releases > 1 and recorder.last_release_time is not None:
            # rough duration from first to last release
            # (We don't have a first timestamp saved directly; approximate via hold + flights)
            est_duration = sum(recorder.hold_times) + sum(recorder.flight_times)
        else:
            est_duration = np.nan
        feats["chars_per_sec"] = float(total_chars / est_duration) if (est_duration and est_duration > 0) else np.nan

        # Counts
        feats["n_chars"] = int(total_chars)
        feats["n_presses"] = int(recorder.n_presses)
        feats["n_releases"] = int(recorder.n_releases)

        return feats

# ---------------------------
# Model Wrapper
# ---------------------------
class PDKeystrokeModel:
    """
    Two operation modes:
    - Supervised: load scikit-learn Pipeline (StandardScaler + Classifier) from pd_keystroke_model.joblib
        -> pipeline.predict_proba(X)[..., 1] used as 'risk'
    - Unsupervised: one-class SVM trained on user's baseline feature vectors
        -> negative decision_function(X) as 'risk' (higher = more abnormal)
    """
    def __init__(self, model_path="pd_keystroke_model.joblib", baseline_dir="baseline_sessions"):
        self.model_path = pathlib.Path(model_path)
        self.baseline_dir = pathlib.Path(baseline_dir)
        self.supervised_pipeline = None
        self.unsupervised_pipeline = None

        if self.model_path.exists():
            try:
                self.supervised_pipeline = load(self.model_path)
                print(f"[Model] Loaded supervised pipeline from {self.model_path}")
            except Exception as e:
                print(f"[Model] Could not load supervised pipeline: {e}")

        # Prepare unsupervised pipeline
        self.unsupervised_pipeline = Pipeline([
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
            ("ocsvm", OneClassSVM(kernel="rbf", gamma="scale", nu=0.05))
        ])

    def _features_to_df(self, feats_dict):
        return pd.DataFrame([feats_dict]).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    def _load_baseline(self):
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        paths = sorted(self.baseline_dir.glob("baseline_features_*.csv"))
        dfs = []
        for p in paths:
            try:
                dfs.append(pd.read_csv(p))
            except Exception:
                pass
        if not dfs:
            return None
        # Union of columns is handled by concat; fillna then
        df = pd.concat(dfs, ignore_index=True, sort=False).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return df

    def fit_unsupervised(self):
        df = self._load_baseline()
        if df is None or df.empty:
            raise RuntimeError("No baseline features found. Run --mode collect_baseline first.")
        self.unsupervised_pipeline.fit(df.values)
        print(f"[Model] Unsupervised OneClassSVM fitted on {len(df)} baseline sessions.")

    def predict(self, feats_dict):
        X = self._features_to_df(feats_dict)

        # Prefer supervised if available
        if self.supervised_pipeline is not None:
            try:
                # Probabilities (class 1 = PD-like) if available; else decision_function
                if hasattr(self.supervised_pipeline, "predict_proba"):
                    proba = self.supervised_pipeline.predict_proba(X.values)[:, -1]
                    return float(proba[0]), "supervised_proba"
                elif hasattr(self.supervised_pipeline, "decision_function"):
                    score = self.supervised_pipeline.decision_function(X.values)
                    # Map to 0-1 via sigmoid for a "risk-like" number
                    risk = 1.0 / (1.0 + np.exp(-score))
                    return float(risk[0]), "supervised_decision"
            except Exception as e:
                print(f"[Model] Supervised inference failed: {e}")

        # Fall back to unsupervised
        self.fit_unsupervised()
        # OneClassSVM: higher decision_function => more normal; we invert to make "risk"
        df = self._features_to_df(feats_dict)
        norm_score = self.unsupervised_pipeline.decision_function(df.values)[0]
        # Convert to a 0..1 risk-like measure by ranking relative to baseline margin assumptions
        # Simple transform: risk = sigmoid(-(score - median_baseline_score))
        # But we don't have baseline scores cached here; use a heuristic:
        risk = 1.0 / (1.0 + math.exp(norm_score))  # invert and squash
        return float(risk), "unsupervised_ocsvm"

# ---------------------------
# Helpers
# ---------------------------
def save_features_csv(feats, out_path):
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([feats]).to_csv(out_path, index=False)
    print(f"[IO] Saved features to {out_path}")

def collect_session(duration, notes=None):
    rec = KeystrokeRecorder()
    rec.start(duration_sec=duration, prompt=True)
    feats = FeatureExtractor().extract(rec)
    meta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_sec": duration,
        "notes": notes or ""
    }
    return feats, meta

# ---------------------------
# CLI
# ---------------------------
def main():
    ap = argparse.ArgumentParser(description="Keystroke dynamics PD-style analysis (research prototype)")
    ap.add_argument("--mode", required=True, choices=["collect_baseline", "screen", "just_features"],
                    help="collect_baseline: build your baseline; screen: evaluate current session; just_features: dump features only")
    ap.add_argument("--duration", type=int, default=60, help="Typing duration in seconds (default 60)")
    ap.add_argument("--baseline_dir", type=str, default="baseline_sessions", help="Where baseline CSVs are stored")
    ap.add_argument("--model_path", type=str, default="pd_keystroke_model.joblib", help="Path to supervised pipeline (optional)")
    ap.add_argument("--notes", type=str, default="", help="Optional note to attach")
    args = ap.parse_args()

    # Collect current session
    feats, meta = collect_session(duration=args.duration, notes=args.notes)

    # Always save the session features log
    out_root = pathlib.Path("sessions")
    out_root.mkdir(parents=True, exist_ok=True)
    session_id = int(time.time())
    session_csv = out_root / f"session_{session_id}_features.csv"
    save_features_csv(feats, session_csv)

    if args.mode == "just_features":
        print(json.dumps({"meta": meta, "features": feats}, indent=2))
        return

    if args.mode == "collect_baseline":
        # Append this session to baseline store
        bdir = pathlib.Path(args.baseline_dir)
        bdir.mkdir(parents=True, exist_ok=True)
        bcsv = bdir / f"baseline_features_{session_id}.csv"
        save_features_csv(feats, bcsv)
        print("[Baseline] Stored. Collect 5–10 sessions (different times of day) for a decent baseline.")
        return

    if args.mode == "screen":
        model = PDKeystrokeModel(model_path=args.model_path, baseline_dir=args.baseline_dir)
        risk, source = model.predict(feats)
        print("\n=== Screening Result (Research Prototype) ===")
        print(f"Model source: {source}")
        print(f"Risk score (0..1, higher≈more PD-like): {risk:.3f}")
        print("Note: Thresholds depend on your model/baseline. For unsupervised mode, try flagging >0.6 as 'abnormal' and compare across repeated sessions.")
        return

if __name__ == "__main__":
    main()
