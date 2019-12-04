import os


def pytest_addoption(parser):
    parser.addoption(
        '--visible', action='store_true',
        default=False, help='Show browser when running tests')


def pytest_configure(config):
    if config.getoption('visible'):
        os.environ['GOCEPT_SELENIUM_HEADLESS'] = 'false'
    else:
        os.environ['GOCEPT_SELENIUM_HEADLESS'] = 'true'
