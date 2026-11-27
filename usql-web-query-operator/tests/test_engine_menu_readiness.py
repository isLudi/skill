from unittest import TestCase
from unittest.mock import MagicMock,patch
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from _shared.errors import UsageError
from usql_web_query.engine import _click_engine_menu_item

class EngineMenuReadiness(TestCase):
    def test_delayed_option_is_awaited_before_single_click(self):
        frame=MagicMock();item=frame.locator.return_value.filter.return_value.last
        item.count.return_value=0
        with patch('usql_web_query.engine.get_sql_frame',return_value=frame):
            _click_engine_menu_item(MagicMock(),r'^Presto[_-]lakehouse$')
        item.wait_for.assert_called_once_with(state='visible',timeout=10_000)
        item.click.assert_called_once()
        item.count.assert_not_called()

    def test_missing_option_never_clicks_or_falls_back_to_another_engine(self):
        frame=MagicMock();item=frame.locator.return_value.filter.return_value.last
        item.wait_for.side_effect=TimeoutError('not visible')
        with patch('usql_web_query.engine.get_sql_frame',return_value=frame):
            with self.assertRaises(UsageError):_click_engine_menu_item(MagicMock(),r'^Presto$')
        item.click.assert_not_called()
