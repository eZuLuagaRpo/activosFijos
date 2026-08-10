""" Init module """
from .driver_manager import create_driver
from .login_page import LoginPage
from .cases_page import CasesPage
from .report_page import ReportPage
from .form_handler import FormHandler
from .response import build_response
from .xpath_builder import XPathBuilder
from .app_state import AppState
from .download_manager import DownloadManager
from . import _version
__version__ = _version.get_versions()['version']
