from typing import Dict, Iterable, Protocol
from collections import defaultdict
from ..domain.enums import TagValue


class AbstractDetectionAlgorithm(Protocol):
    def detect_patterns(self, tag_assignments: Iterable["TagAssignment"]) -> Dict[str, int]:
        ...

class ContiguousDetectionAlgorithm(AbstractDetectionAlgorithm):
    def detect_patterns(self, tag_assignments, substring_length = 12):
        assignment_sequence = list(self.build_sequence_str(tag_assignments))
        sub_start = 0
        track_4 = defaultdict(list)

        while sub_start < len(assignment_sequence) - (substring_length - 1):
            cur_sub = "".join(assignment_sequence[sub_start : sub_start + substring_length])
        
            first_pattern = cur_sub[0:4]
            # expected = first_pattern * 3
            expected = first_pattern * (substring_length // len(first_pattern))
            if cur_sub == expected:
                track_4[first_pattern].append(sub_start)
                sub_start += substring_length
            else:
                sub_start += 1
        
        for length_4_occurrences in track_4.values():
            for start_pos in length_4_occurrences:
                assignment_sequence[start_pos: start_pos + substring_length] = "#"
        
        sub_start = 0
        track_3 = defaultdict(list)

        while sub_start < len(assignment_sequence) - (substring_length - 1):
            cur_sub = "".join(assignment_sequence[sub_start : sub_start + substring_length])
            if "#" in cur_sub:
                sub_start += substring_length
                continue
            else:
                first_pattern = cur_sub[0:3]
                # expected = first_pattern * 4
                expected = first_pattern * (substring_length // len(first_pattern))
                if cur_sub == expected:
                    track_3[first_pattern].append(sub_start)
                    sub_start += substring_length
                else:
                    sub_start += 1
        
        all_detected_patterns = {}
        for pattern, occurences in track_4.items():
            all_detected_patterns[pattern] = len(occurences)
        for pattern, occurences in track_3.items():
            all_detected_patterns[pattern] = len(occurences)

        return all_detected_patterns
    
    def build_sequence_str(self, assignments: "list[TagAssignment]") -> str:
        """Function takes in a list of tag assignments, and then returns a sequence string consisting of the first character of the tag value
        for each tag assignment

        The sequence string created allows for simpler pattern detection, since then the re module can be utilized.

        Args:
            assignments (List[TagAssignment]): _description_

        Returns:
            str: sequence_str in the format "YNYN" etc.
        """
        tokens: list[str] = []
        for assignment in assignments:
            value = getattr(assignment, "value", None)
            if value == TagValue.YES:
                tokens.append("Y")
            elif value == TagValue.NO:
                tokens.append("N")

        return "".join(tokens)