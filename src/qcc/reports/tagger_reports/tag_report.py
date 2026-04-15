"""Core utilities for tag-level reports."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional

from qcc.domain.tagassignment import TagAssignment
from qcc.domain.characteristic import Characteristic
from qcc.domain.tagger import Tagger
from qcc.domain.enums import TagValue
from qcc.metrics.agreement import AgreementMetrics

import statistics


@dataclass
class TagReportRow:
    comment_id: str
    characteristic_id: str
    num_taggers_could_set: int
    num_yes: int
    num_no: int
    num_skipped: int
    cohens_kappa: Optional[float]
    krippendorffs_alpha: Optional[float]
    aggregate_tagger_reliability: Optional[float]

    def to_csv_row(self):
        return [
            self.comment_id,
            self.characteristic_id,
            self.num_taggers_could_set,
            self.num_yes,
            self.num_no,
            self.num_skipped,
            self.cohens_kappa,
            self.krippendorffs_alpha,
            self.aggregate_tagger_reliability,
        ]


def group_by_comment(assignments: List[TagAssignment]) -> Dict[str, List[TagAssignment]]:
    groups: Dict[str, List[TagAssignment]] = defaultdict(list)

    for assignment in assignments or []:
        cid = getattr(assignment, "comment_id", None)
        if cid is None:
            comment_obj = getattr(assignment, "comment", None)
            cid = getattr(comment_obj, "id", None) if comment_obj is not None else None
        if cid is None:
            continue
        groups[str(cid)].append(assignment)

    return dict(groups)


def group_by_characteristic(assignments: List[TagAssignment]) -> Dict[str, List[TagAssignment]]:
    groups: Dict[str, List[TagAssignment]] = defaultdict(list)

    for assignment in assignments or []:
        char_id = getattr(assignment, "characteristic_id", None)
        if char_id is None:
            char_obj = getattr(assignment, "characteristic", None)
            char_id = getattr(char_obj, "id", None) if char_obj is not None else None

        if char_id is None:
            continue

        groups[str(char_id)].append(assignment)

    return dict(groups)


def group_by_comment_and_characteristic(
    assignments: List[TagAssignment],
) -> Dict[Tuple[str, str], List[TagAssignment]]:
    groups: Dict[Tuple[str, str], List[TagAssignment]] = defaultdict(list)

    for assignment in assignments or []:
        cid = getattr(assignment, "comment_id", None)
        if cid is None:
            comment_obj = getattr(assignment, "comment", None)
            cid = getattr(comment_obj, "id", None) if comment_obj is not None else None

        char_id = getattr(assignment, "characteristic_id", None)
        if char_id is None:
            char_obj = getattr(assignment, "characteristic", None)
            char_id = getattr(char_obj, "id", None) if char_obj is not None else None

        if cid is None or char_id is None:
            continue

        groups[(str(cid), str(char_id))].append(assignment)

    return dict(groups)


def taggers_who_touched_comment(assignments_for_comment: List[TagAssignment]) -> Set[str]:
    tagger_ids: Set[str] = set()

    for assignment in assignments_for_comment or []:
        tid = getattr(assignment, "tagger_id", None)
        if tid is None:
            tagger_obj = getattr(assignment, "tagger", None)
            tid = getattr(tagger_obj, "id", None) if tagger_obj is not None else None

        if tid is not None:
            tagger_ids.add(str(tid))

    return tagger_ids

def count_yes_no(assignments: List[TagAssignment]) -> Tuple[int, int]:
    yes = 0
    no = 0

    for assignment in assignments or []:
        v = getattr(assignment, "value", None)
        if v == TagValue.YES:
            yes += 1
        elif v == TagValue.NO:
            no += 1

    return yes, no

def alpha_for_item(
    assignments: List[TagAssignment],
    characteristic: Characteristic,
) -> Optional[float]:
    
    if not assignments:
        return None

    taggers = taggers_who_touched_comment(assignments)
    if len(taggers) < 2:
        return None

    metrics = AgreementMetrics()
    return metrics.krippendorffs_alpha(assignments, characteristic)

def kappa_for_item(
    assignments: List[TagAssignment],
    characteristic: Characteristic,
) -> Optional[float]:
    if not assignments:
        return None

    taggers = taggers_who_touched_comment(assignments)
    if len(taggers) < 2:
        return None

    metrics = AgreementMetrics()
    return metrics.cohens_kappa(assignments, characteristic)

def tag_reliability_calculation(
    assignments: List[TagAssignment],
    value: TagValue,
) -> Optional[float]:

    if not assignments:
        return None

    taggers_for_comment = taggers_who_touched_comment(assignments)

    if len(taggers_for_comment) == 0:
        return None

    # Compute agreement matrix
    pairwise_matrix = AgreementMetrics.agreement_matrix(assignments)

    # Build reliability dict
    reliability: Dict[str, float] = {}

    for tagger in taggers_for_comment:

        kappas = pairwise_matrix.get(tagger, [])

        if kappas:
            reliability[tagger] = statistics.mean(kappas)
        else:
            reliability[tagger] = 0.5  # fallback default

    # Identify taggers assigning this value
    taggers_assigning_tag = {

        str(a.tagger_id)

        for a in assignments

        if a.value == value
    }

    if not taggers_assigning_tag:
        return 0.0

    agreement_fraction = (
        len(taggers_assigning_tag)
        / len(taggers_for_comment)
    )

    weighted_vote_numerator = sum(
        reliability[tagger]
        for tagger in taggers_assigning_tag
    )

    weighted_vote_denominator = sum(

        reliability[tagger]

        for tagger in taggers_for_comment
    )

    if weighted_vote_denominator == 0:
        return None

    weighted_vote = (
        weighted_vote_numerator
        / weighted_vote_denominator
    )

    return agreement_fraction * weighted_vote