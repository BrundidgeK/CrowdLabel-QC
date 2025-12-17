from typing import Dict, Iterable, Protocol
from collections import defaultdict
from ..domain.enums import TagValue


class AbstractDetectionAlgorithm(Protocol):
    def detect_patterns(self, tag_assignments: Iterable["TagAssignment"]) -> Dict[str, int]:
        ...

class ContiguousDetectionAlgorithm(AbstractDetectionAlgorithm):
    """
    Class to detect patterns when patterns are repeated contiguously for a substring of length 12. The patterns detected are either 3 continuous repititons of a length-4 pattern, or 4 continuous repitions of a length-3 pattern.
    The build_sequence_str() method is used in detect_patterns() method below to build a string that represents the entire sequence of eligible tag values (Yes or No) for tag assignments.
    The string representing the entire sequence of tag assignments is sliced into substrings of length-12 in the detect_patterns() method. It is then determined whether each length-12 substring contains 3 continuous repeats of length-4 pattern, or 4 continous repeats of length-3 patterns.


    Args:
        AbstractDetectionAlgorithm: Interface for pattern detection algorithm classes, ensures detect_patterns() method is inherited for each algorithm class
    """

    def detect_patterns(self, tag_assignments, substring_length = 12):
        """_summary_

        Args:
            tag_assignments (list[TagAssignment]): list of tag assignments to detect patterns for
            substring_length (int, optional): length of substring to check for repeats. Defaults to 12.

        Returns:
            Dict(str, int): key represents either a length-4 or length-3 pattern, the value represents how many substrings were made of entirely the pattern stored in the key
        """
        assignment_sequence = list(self.build_sequence_str(tag_assignments))
        sub_start = 0 # index representing start of substring
        track_4 = defaultdict(list) # dictionary that keeps track of all length-4 patterns repeated in all length-12 substrings

        while sub_start < len(assignment_sequence) - (substring_length - 1):
            cur_sub = "".join(assignment_sequence[sub_start : sub_start + substring_length])
        
            first_pattern = cur_sub[0:4]
            # Next line is equivalent to "expected = first_pattern * 3"
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
        track_3 = defaultdict(list) # dictionary that keeps track of all length-3 patterns repeated in all length-12 substrings

        while sub_start < len(assignment_sequence) - (substring_length - 1):
            cur_sub = "".join(assignment_sequence[sub_start : sub_start + substring_length])
            if "#" in cur_sub:
                sub_start += substring_length
                continue
            else:
                first_pattern = cur_sub[0:3]
                # Next line is equivalent to "expected = first_pattern * 4"
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

        # all length-4 and length-3 patterns detected are returned, with the number of length-12 substrings they were detected in
        return all_detected_patterns
    
    def build_sequence_str(self, assignments: "list[TagAssignment]") -> str:
        """Function takes in a list of tag assignments, and then returns a sequence string consisting of the first character of the tag value
        for each tag assignment

        The sequence string created allows for simpler pattern detection, since there are existing libraries for string searching.

        Example use case:
        If there is given a list of tag assignments such that user has tagged Yes, No, Yes, Yes, No for the assignments, then the
        return value would be "YNYYN". 

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