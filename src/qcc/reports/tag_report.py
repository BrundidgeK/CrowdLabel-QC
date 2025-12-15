"""Core utilities for tag-level reports.

This module provides lightweight helper functions for grouping and
analyzing tag assignments. It intentionally contains no I/O or
CSV/export logic — those live in higher layers of the reporting system.
"""

from __future__ import annotations  # future annotations

from collections import defaultdict  # dict grouping
from typing import Dict, List, Tuple, Set, Optional  # type hints

from qcc.domain.tagassignment import TagAssignment  # import assignments
from qcc.domain.characteristic import Characteristic  # import characteristic
from qcc.domain.enums import TagValue  # import tag values
from qcc.metrics.agreement import AgreementMetrics, LatestLabelPercentAgreement  # add import

# NOTE:
# This module provides compute-only helper functions for tag-level reporting.
# It intentionally does NOT define a row data structure or perform any I/O.
# Higher-level report generators are expected to:
# - call these helpers to compute values
# - write results directly to their chosen output stream (CSV, JSON, etc.)



def group_by_comment(assignments: List[TagAssignment]) -> Dict[str, List[TagAssignment]]:
    """Group assignments by comment_id (string key).

    This function focuses on IDs only — it will look for a ``comment_id``
    attribute on the assignment and fall back to assignment.comment.id if a comment object is present. 
    Assignments missing any comment id are skipped.
    """  # fixed incomplete docstring

    groups: Dict[str, List[TagAssignment]] = defaultdict(list)  # init grouping dict

    for assignment in assignments or []:  # iterate assignments
        cid = getattr(assignment, "comment_id", None)  # try direct comment_id
        if cid is None:  # not found directly
            comment_obj = getattr(assignment, "comment", None)  # get attached comment
            cid = getattr(comment_obj, "id", None) if comment_obj is not None else None  # fallback to attached id
        if cid is None:  # skip if still missing
            continue  # skip this assignment
        groups[str(cid)].append(assignment)  # add to group

    return dict(groups)  # convert to dict


def group_by_comment_and_characteristic(
    assignments: List[TagAssignment],
) -> Dict[Tuple[str, str], List[TagAssignment]]:
    """Group assignments by (comment_id, characteristic_id) tuple of strings.

    This is explicitly ID-focused and does not attempt to create any
    placeholder domain objects. If either id is missing the assignment is
    skipped.
    """

    groups: Dict[Tuple[str, str], List[TagAssignment]] = defaultdict(list)  # init grouping dict

    for assignment in assignments or []:  # iterate assignments
        cid = getattr(assignment, "comment_id", None)  # try direct comment_id
        if cid is None:  # not found directly
            comment_obj = getattr(assignment, "comment", None)  # get attached comment
            cid = getattr(comment_obj, "id", None) if comment_obj is not None else None  # fallback to attached id
        char_id = getattr(assignment, "characteristic_id", None)  # try direct characteristic_id
        if char_id is None:  # not found directly
            char_obj = getattr(assignment, "characteristic", None)  # get attached characteristic
            char_id = getattr(char_obj, "id", None) if char_obj is not None else None  # fallback to attached id

        if cid is None or char_id is None:  # skip if either is missing
            continue  # skip this assignment

        groups[(str(cid), str(char_id))].append(assignment)  # add to group

    return dict(groups)  # convert to dict


def taggers_who_touched_comment(assignments_for_comment: List[TagAssignment]) -> Set[str]:
    """Return set of tagger_id strings of taggers who tagged this comment.

    This function strictly returns IDs and does not construct or return
    Tagger objects.
    """

    tagger_ids: Set[str] = set()  # init tagger id set
    for assignment in assignments_for_comment or []:  # iterate assignments
        tid = getattr(assignment, "tagger_id", None)  # try direct tagger_id
        if tid is None:  # not found directly
            tagger_obj = getattr(assignment, "tagger", None)  # get attached tagger
            tid = getattr(tagger_obj, "id", None) if tagger_obj is not None else None  # fallback to attached id
        if tid is not None:  # if tagger id found
            tagger_ids.add(str(tid))  # add to set

    return tagger_ids  # return collected ids


def count_yes_no(assignments: List[TagAssignment]) -> Tuple[int, int]:
    """Return (#YES, #NO) based on TagValue.YES and TagValue.NO.

    Non-YES/NO values are ignored.
    """

    yes = 0  # init yes count
    no = 0  # init no count

    for assignment in assignments or []:  # iterate assignments
        v = getattr(assignment, "value", None)  # get tag value
        if v == TagValue.YES:  # check if yes
            yes += 1  # increment yes
        elif v == TagValue.NO:  # check if no
            no += 1  # increment no

    return yes, no  # return counts


def alpha_for_item(assignments: List[TagAssignment], characteristic: Characteristic) -> Optional[float]:
    """Return Krippendorff’s alpha for a single (comment, characteristic).

    Uses :class:`qcc.metrics.agreement.AgreementMetrics`. If fewer than two
    distinct taggers participated on this item the function returns ``None``
    to signify alpha is not defined.
    """

    if not assignments:  # check if empty
        return None  # no data

    taggers = taggers_who_touched_comment(assignments)  # get tagger ids
    if len(taggers) < 2:  # need at least 2 taggers
        return None  # alpha undefined

    metrics = AgreementMetrics()  # create metrics calculator
    return metrics.krippendorffs_alpha(assignments, characteristic)  # compute alpha


def percent_agreement_for_item(assignments: List[TagAssignment], characteristic: Characteristic) -> Optional[float]:  # new helper
    """Return percent agreement for a single (comment, characteristic).

    Uses LatestLabelPercentAgreement to compute percent agreement and
    returns a value rounded to 3 decimals and clamped to [0.0, 1.0].
    """  # docstring for percent agreement

    if not assignments:  # return None if empty
        return None  # empty fallback

    taggers = taggers_who_touched_comment(assignments)  # get unique taggers
    if len(taggers) < 2:  # need at least two taggers
        return None  # not enough taggers

    pla = LatestLabelPercentAgreement()  # create percent-agreement calculator
    pa = pla.percent_agreement(assignments, characteristic)  # compute percent agreement
    # clamp to [0.0, 1.0]
    if pa is None:  # handle None result
        return None  # propagate None
    pa_clamped = max(0.0, min(1.0, float(pa)))  # clamp value
    return round(pa_clamped, 3)  # round and return


def cohens_kappa_for_item(assignments: List[TagAssignment], characteristic: Characteristic) -> Optional[float]:  # new helper
    """Return Cohen's kappa for a single (comment, characteristic).

    Uses LatestLabelPercentAgreement to compute Cohen's kappa and returns
    a value rounded to 3 decimals (no clamping).
    """  # docstring for kappa

    if not assignments:  # return None if empty
        return None  # empty fallback

    taggers = taggers_who_touched_comment(assignments)  # get unique taggers
    if len(taggers) < 2:  # need at least two taggers
        return None  # not enough taggers

    pla = LatestLabelPercentAgreement()  # create percent-agreement calculator
    k = pla.cohens_kappa(assignments, characteristic)  # compute kappa
    if k is None:  # handle None result
        return None  # propagate None
    return round(float(k), 3)  # round and return
