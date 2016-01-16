from unittest.mock import patch, Mock

from tygs import utils


def test_get_project_dir():
    with patch('os.getcwd', new_callable=lambda: lambda: '/current/dir'):
        with patch('sys.argv') as argv:
            argv.__getitem__ = Mock(return_value='../path/to/wololo.py')
            cwd = utils.get_project_dir()
            assert cwd == '/current/path/to'
