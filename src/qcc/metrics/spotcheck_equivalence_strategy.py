from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class SpotCheckEquivalenceStrategy:
    """Strategy template for Spot Check Equivalence (SCE) reliability.

    This implementation is intentionally lightweight:
    - Sensitivity is modeled as coverage (how many items the tagger touched).
    - Measurement integrity is modeled as majority agreement on shared items.
    - SCE combines both into a [0,1] reliability-style score.
    """

    tagassignments: List[Any]
    config: Optional[Dict[str, Any]] = None

    # -------------------------
    # Internal helpers (pure)
    # -------------------------

    def _cfg(self, key: str, default: Any) -> Any:
        if self.config is None:
            return default
        return self.config.get(key, default)

    def _clamp01(self, x: float) -> float:
        if x < 0.0:
            return 0.0
        if x > 1.0:
            return 1.0
        return x

    def _tagger_id(self, tagger: Any) -> Any:
        return getattr(tagger, "id", tagger)

    def _assignment_tagger(self, ta: Any) -> Any:
        t = getattr(ta, "tagger", None)
        if t is not None:
            return t
        return getattr(ta, "tagger_id", None)

    def _assignment_value(self, ta: Any) -> Any:
        # Prefer normalized "value"; fall back to "tag.value" if present.
        v = getattr(ta, "value", None)
        if v is not None:
            return v
        tag_obj = getattr(ta, "tag", None)
        return getattr(tag_obj, "value", None) if tag_obj is not None else None

    def _item_key(self, ta: Any) -> Optional[Tuple[str, str]]:
        # Item = (comment_id, characteristic_id), best-effort extraction
        cid = getattr(ta, "comment_id", None)
        if cid is None:
            cobj = getattr(ta, "comment", None)
            cid = getattr(cobj, "id", None) if cobj is not None else None

        chid = getattr(ta, "characteristic_id", None)
        if chid is None:
            chobj = getattr(ta, "characteristic", None)
            chid = getattr(chobj, "id", None) if chobj is not None else None

        if cid is None or chid is None:
            return None
        return (str(cid), str(chid))

    def _assignments_for_tagger(self, tagger: Any) -> List[Any]:
        tid = self._tagger_id(tagger)
        out: List[Any] = []
        for ta in self.tagassignments or []:
            t = self._assignment_tagger(ta)
            if t is None:
                continue
            if self._tagger_id(t) == tid:
                out.append(ta)
        return out

    def _group_by_item(self) -> Dict[Tuple[str, str], List[Any]]:
        groups: Dict[Tuple[str, str], List[Any]] = {}
        for ta in self.tagassignments or []:
            key = self._item_key(ta)
            if key is None:
                continue
            groups.setdefault(key, []).append(ta)
        return groups

    def _majority_value_excluding(self, tas: List[Any], exclude_tagger: Any) -> Optional[Any]:
        """Return majority value among tas excluding exclude_tagger (ties -> None)."""
        exclude_id = self._tagger_id(exclude_tagger)
        counts: Dict[Any, int] = {}

        for ta in tas:
            t = self._assignment_tagger(ta)
            if t is None or self._tagger_id(t) == exclude_id:
                continue
            v = self._assignment_value(ta)
            if v is None:
                continue
            counts[v] = counts.get(v, 0) + 1

        if not counts:
            return None

        # Find top count; if tie, return None
        best_val = None
        best_count = -1
        tie = False
        for v, c in counts.items():
            if c > best_count:
                best_val = v
                best_count = c
                tie = False
            elif c == best_count:
                tie = True

        return None if tie else best_val

    # -------------------------
    # Core metrics
    # -------------------------

    def sensitivity(self, tagger: Any) -> float:
        """Coverage-based sensitivity in [0,1].

        Interpretation:
        - If a tagger touched more of the available (comment, characteristic) items,
          their reliability score is more "responsive" to effort changes because
          there is more evidence.
        """
        groups = self._group_by_item()
        total_items = len(groups)
        if total_items == 0:
            return 0.0

        mine = self._assignments_for_tagger(tagger)

        touched: Dict[Tuple[str, str], bool] = {}
        for ta in mine:
            key = self._item_key(ta)
            if key is not None:
                touched[key] = True

        coverage = len(touched) / float(total_items)
        return self._clamp01(coverage)

    def measurement_integrity(self, tagger: Any) -> float:
        """Majority-agreement integrity in [0,1].

        Interpretation:
        - For each item the tagger labeled, compare their label to the
          majority label from other taggers on the same item.
        - The integrity score is the fraction of comparable items where
          the tagger matches the majority.
        """
        groups = self._group_by_item()
        mine = self._assignments_for_tagger(tagger)
        if not mine:
            return 0.0

        comparable = 0
        matches = 0

        for ta in mine:
            key = self._item_key(ta)
            if key is None:
                continue

            peers = groups.get(key, [])
            majority = self._majority_value_excluding(peers, exclude_tagger=tagger)
            my_val = self._assignment_value(ta)

            # Only score items where a majority exists (no tie, at least 1 peer)
            if majority is None or my_val is None:
                continue

            comparable += 1
            if my_val == majority:
                matches += 1

        if comparable == 0:
            return 0.0

        return self._clamp01(matches / float(comparable))

    def spot_check_equivalence(self, tagger: Any) -> float:
        """Weighted combination of sensitivity and integrity in [0,1]."""
        w_sens = float(self._cfg("weight_sensitivity", 0.4))
        w_int = float(self._cfg("weight_integrity", 0.6))

        # Normalize weights if they don't sum to 1
        total_w = w_sens + w_int
        if total_w <= 0:
            w_sens, w_int = 0.4, 0.6
            total_w = 1.0

        w_sens /= total_w
        w_int /= total_w

        s = self.sensitivity(tagger)
        mi = self.measurement_integrity(tagger)
        return self._clamp01((w_sens * s) + (w_int * mi))

    # -------------------------
    # Aggregation / reporting
    # -------------------------

    def summary_report(self) -> Dict[Any, Dict[str, float]]:
        """Compute sensitivity, integrity, and SCE for each tagger present."""
        taggers: Dict[Any, Any] = {}

        for ta in self.tagassignments or []:
            t = self._assignment_tagger(ta)
            if t is None:
                continue
            tid = self._tagger_id(t)
            taggers[tid] = t

        out: Dict[Any, Dict[str, float]] = {}
        for tid, t in taggers.items():
            sens = self.sensitivity(t)
            integ = self.measurement_integrity(t)
            sce = self.spot_check_equivalence(t)
            out[tid] = {
                "sensitivity": float(sens),
                "measurement_integrity": float(integ),
                "sce": float(sce),
            }

        return out
