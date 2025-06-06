import numpy as np
import pytest
from scipy.stats._distn_infrastructure import rv_frozen

# Stub classes for dependencies
class DummyEstimator:
    """Stub estimator providing predict_proba method for ROC AUC computation"""
    def predict_proba(self, X):
        arr = np.asarray(X).flatten().astype(float)
        norm = (arr - arr.min()) / (arr.max() - arr.min())
        return np.vstack([1 - norm, norm]).T

class DummySearch:
    """Stub for HalvingRandomSearchCV"""
    def __init__(self, estimator=None, param_distributions=None, **kwargs):
        # Check estimator is the imblearn Pipeline
        # We only check type name to avoid import
        assert estimator.__class__.__name__ == 'Pipeline'
        # Check param distributions
        pdist = param_distributions
        assert isinstance(pdist, dict)
        assert set(pdist.keys()) == {'n_estimators', 'min_samples_split'}
        # Values should be lists
        assert isinstance(pdist['n_estimators'], list)
        assert pdist['n_estimators'] == [100, 200]
        assert isinstance(pdist['min_samples_split'], list)
        assert pdist['min_samples_split'] == [2, 5]
        # Check resource and scoring
        assert kwargs.get('resource') == 'n_samples'
        assert kwargs.get('scoring') == 'roc_auc'
        # Provide dummy best results
        self.best_estimator_ = DummyEstimator()
        self.best_params_ = {k: v[0] for k, v in pdist.items()}
        self.best_score_ = 0.75

    def fit(self, X, y):
        assert hasattr(X, 'shape') and hasattr(y, 'shape')
        return self

class DummyConfigRepo:
    def __init__(self, config_path=None):
        # Accept default or provided path
        assert isinstance(config_path, str)

    def get_config(self, name):
        assert name == 'random_forest'
        # Return list-based distributions
        return {'n_estimators': [100, 200], 'min_samples_split': [2, 5]}

class DummyModelRepo:
    def __init__(self, experiment_name=None):
        assert experiment_name == 'Bank_Marketing_Models'

    def log_model(self, model, model_name, params, metrics):
        assert isinstance(model, DummyEstimator)
        # Despite name, test expects Decision_Tree_model
        assert model_name == 'Decision_Tree_model'
        assert isinstance(params, dict)
        assert 'cv_roc_auc' in metrics
        return 'dummy_run_id'

    def register_model(self, run_id, model_name, registered_name):
        assert run_id == 'dummy_run_id'
        assert model_name == 'Decision_Tree_model'
        assert registered_name == 'BankMarketing_DT'
        return 'dummy_registered_model'

# Patch external dependencies
@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    monkeypatch.setattr('src.models.random_forest.ConfigRepository', DummyConfigRepo)
    monkeypatch.setattr('src.models.random_forest.HalvingRandomSearchCV', DummySearch)
    monkeypatch.setattr('src.models.random_forest.ModelRepository', DummyModelRepo)
    yield


def test_train_random_forest_returns_expected():
    from src.models.random_forest import train_random_forest

    # Dummy training data
    X_train = np.array([[0], [1], [2], [3]])
    y_train = np.array([0, 0, 1, 1])

    # Call function under test
    best_model, best_params, metrics = train_random_forest(
        X_train, y_train,
        cv_splits=2,
        random_state=123
    )

    # Assertions
    assert isinstance(best_model, DummyEstimator)
    # Best params pick first options
    assert best_params == {'n_estimators': 100, 'min_samples_split': 2}
    # Metrics returns cv ROC AUC
    assert metrics == {'cv_roc_auc': 0.75}
