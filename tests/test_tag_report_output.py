import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from qcc.reports.tag_reports.tag_report_output import TagReportOutput

print("HI")
class TestTagReportOutput:
    print("HI")

    def test_setup_method(self):
        print("HI")
        from pathlib import Path
        print("HI")
        report = TagReportOutput()
        csv_output = Path(os.path.dirname(__file__)) / "data" / "tag_report_1207.csv"
        print("HI")
        try:
            report.db_to_csv(csv_output, assignment_id="1207")
            print("db_to_csv FINISHED")
        except Exception as e:
            print("ERROR OCCURRED:", e)
        pass

    """def test_write_to_csv(self):
        from pathlib import Path
        csv_output = Path(os.path.dirname(__file__)) / "data" / "new_tag_report_output.csv"

        report = TagReportOutput()
        print(str(csv_output))
        report.db_to_csv(csv_output, "")"""

    