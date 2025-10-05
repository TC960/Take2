"""
WebSocket Keystroke Analysis Module
Processes real-time keystroke data and streams analysis results
"""

import json
import time
import sys
import pathlib

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from pd_keystroke_rules import features_from_session, RobustBaseline, evaluate_rules, load_baseline_table


class KeystrokeAnalyzer:
    """
    Real-time keystroke analyzer that processes streaming keystroke data
    """

    def __init__(self, baseline_dir="baseline_store"):
        self.baseline_dir = baseline_dir
        self.baseline_model = None
        self.session_data = {
            "holds": [],
            "flights": [],
            "chars": [],
            "backspaces": 0,
            "n_press": 0,
            "n_rel": 0
        }
        self.press_times = {}
        self.last_release_time = None

        # Load baseline if available
        try:
            df_base = load_baseline_table(baseline_dir)
            if df_base is not None and not df_base.empty:
                self.baseline_model = RobustBaseline()
                self.baseline_model.fit(df_base)
        except Exception as e:
            print(f"[KeystrokeAnalyzer] No baseline loaded: {e}")

    def process_keystroke(self, event_type: str, key: str, timestamp: float):
        """
        Process a single keystroke event

        Args:
            event_type: "press" or "release"
            key: The key character
            timestamp: Event timestamp in seconds

        Returns:
            Dict with current metrics
        """
        if event_type == "press":
            # Calculate flight time from last release
            if self.last_release_time is not None:
                flight_time = max(0.0, timestamp - self.last_release_time)
                self.session_data["flights"].append(flight_time)

            self.press_times[key] = timestamp
            self.session_data["n_press"] += 1
            self.session_data["chars"].append(key)

            # Track backspaces
            if key in ("Backspace", "Delete"):
                self.session_data["backspaces"] += 1

        elif event_type == "release":
            # Calculate hold time
            if key in self.press_times:
                hold_time = max(0.0, timestamp - self.press_times[key])
                self.session_data["holds"].append(hold_time)
                del self.press_times[key]

            self.last_release_time = timestamp
            self.session_data["n_rel"] += 1

        # Calculate current features
        return self.get_current_metrics()

    def get_current_metrics(self):
        """Get current typing metrics"""
        if len(self.session_data["holds"]) < 5:
            # Not enough data yet
            return {
                "status": "collecting",
                "keystrokes": self.session_data["n_press"],
                "message": "Building baseline data..."
            }

        # Calculate features
        features = features_from_session(self.session_data)

        result = {
            "status": "analyzing",
            "keystrokes": self.session_data["n_press"],
            "features": features
        }

        # If we have a baseline model, evaluate rules
        if self.baseline_model:
            try:
                rz = self.baseline_model.rz(features)
                eval_result = evaluate_rules(features, rz)

                result.update({
                    "score": eval_result["score_0to1"],
                    "band": eval_result["band"],
                    "rules_fired": len(eval_result["rules_fired"]),
                    "total_rules": 7,
                    "robust_z": {k: float(v) for k, v in rz.items()}
                })
            except Exception as e:
                result["baseline_error"] = str(e)

        return result

    def finalize_session(self):
        """Get final analysis of the session"""
        features = features_from_session(self.session_data)

        final_result = {
            "timestamp": time.time(),
            "features": features,
            "session_data": {
                "total_keystrokes": self.session_data["n_press"],
                "total_releases": self.session_data["n_rel"],
                "backspaces": self.session_data["backspaces"]
            }
        }

        # Evaluate with baseline if available
        if self.baseline_model:
            try:
                rz = self.baseline_model.rz(features)
                eval_result = evaluate_rules(features, rz)

                final_result.update({
                    "score_0to1": eval_result["score_0to1"],
                    "band": eval_result["band"],
                    "rules_fired": eval_result["rules_fired"],
                    "robust_z": {k: float(v) for k, v in rz.items()}
                })
            except Exception as e:
                final_result["baseline_error"] = str(e)
        else:
            final_result["note"] = "No baseline model available. Features extracted only."

        return final_result
