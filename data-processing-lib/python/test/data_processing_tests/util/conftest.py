import pytest

def pytest_addoption(parser):
    parser.addoption("--s3_url", action="store")

@pytest.fixture(scope='session')
def s3_url(request):
    s3_value = request.config.option.s3_url
    if s3_value is None:
        pytest.skip()
    return s3_value
