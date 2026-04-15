import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from qcc.reports.tag_reports.tag_report_output import TagReportOutput

class TestTagReportOutput:

    def setup_method(self):
        # set up
        pass

    def test_write_to_csv(self):
        from pathlib import Path
        csv_output = Path(os.path.dirname(__file__)) / "data" / "new_tag_report_output.csv"

        report = TagReportOutput()
        print(str(csv_output))
        report.db_to_csv(csv_output, "")

    