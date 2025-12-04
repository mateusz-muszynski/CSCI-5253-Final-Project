## Create a test fixture so that tests can simply use `nlp`

# tests/conftest.py
import pytest
from nlp_service import NLPService

@pytest.fixture
def nlp():
    return NLPService()

# from unittest.mock import MagicMock, patch
# from fastapi.testclient import TestClient
# import api

# @pytest.fixture
# def client():
#     # Patch all service dependencies on import
#     with patch.object(api, "db", MagicMock()), \
#          patch.object(api, "translation_service", MagicMock()), \
#          patch.object(api, "nlp_service", MagicMock()), \
#          patch.object(api, "pubsub", MagicMock()):
        
#         return TestClient(api.app)
