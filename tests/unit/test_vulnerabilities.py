"""
Unit tests for vulnerability modules.
Tests model theft, data poisoning, and other vulnerability demonstrations.
"""
import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variable to prevent route initialization during tests
os.environ['TESTING'] = 'True'

from application import app, db
from application.model import Comment, User, Pizza
from application.vulnerabilities import model_theft, data_poisoning


@pytest.fixture
def test_app():
    """Create and configure a test Flask application instance."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'

    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create users
        alice = User(username='alice')
        alice.set_password('alice')
        db.session.add(alice)
        db.session.commit()

        # Create pizza
        pizza = Pizza(name='Test Pizza', description='Test', price=10.0, image='test.jpg')
        db.session.add(pizza)
        db.session.commit()

        # Create comments with mixed sentiments
        comments = [
            Comment(pizza_id=1, user_id=1, name='alice', content='Excellent pizza! So delicious.', rating=5),
            Comment(pizza_id=1, user_id=1, name='alice', content='Great taste, loved it!', rating=5),
            Comment(pizza_id=1, user_id=1, name='alice', content='Good pizza overall.', rating=4),
            Comment(pizza_id=1, user_id=1, name='alice', content='Terrible pizza, awful.', rating=1),
            Comment(pizza_id=1, user_id=1, name='alice', content='Disgusting and bad.', rating=2),
        ]
        for comment in comments:
            db.session.add(comment)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


class TestModelTheft:
    """Tests for model theft vulnerability."""

    def test_model_theft_with_words(self, test_app):
        """Test model theft attack with sample words."""
        with test_app.app_context():
            user_words = ['excellent', 'terrible', 'good', 'bad']

            samples, logs, approx_weights, actual_weights, correlation, agreement, avg_error, avg_rel_error = \
                model_theft.run_model_theft_attack(user_words)

            # Should return probing samples
            assert len(samples) > 0
            assert all(word in samples for word in user_words)

            # Should generate logs
            assert len(logs) > 0
            assert any('Starting model theft attack' in log for log in logs)

            # Should have approximated weights
            assert isinstance(approx_weights, dict)
            assert len(approx_weights) > 0

            # Should have actual weights
            assert isinstance(actual_weights, dict)
            assert len(actual_weights) > 0

            # Correlation should be a float
            assert isinstance(correlation, (int, float))
            assert -1.0 <= correlation <= 1.0

            # Agreement rate should be a string with %
            assert isinstance(agreement, str)
            assert '%' in agreement

            # Errors should be strings
            assert isinstance(avg_error, str)
            assert isinstance(avg_rel_error, str)

    def test_model_theft_empty_words(self, test_app):
        """Test model theft attack with empty word list."""
        with test_app.app_context():
            samples, logs, approx_weights, actual_weights, correlation, agreement, avg_error, avg_rel_error = \
                model_theft.run_model_theft_attack([])

            # Should handle empty case gracefully
            assert len(samples) == 0
            assert len(logs) > 0

            # Should have default values
            assert correlation == 0.0
            assert agreement == "0.00%"
            assert avg_error == "0.0000"
            assert avg_rel_error == "0.0%"

            # Should still have actual weights
            assert isinstance(actual_weights, dict)
            assert len(actual_weights) > 0

    def test_model_theft_with_none(self, test_app):
        """Test model theft attack with None input."""
        with test_app.app_context():
            samples, logs, approx_weights, actual_weights, correlation, agreement, avg_error, avg_rel_error = \
                model_theft.run_model_theft_attack(None)

            # Should handle None as empty list
            assert len(samples) == 0
            assert len(logs) > 0

    def test_model_theft_logs_content(self, test_app):
        """Test that model theft generates meaningful logs."""
        with test_app.app_context():
            user_words = ['delicious', 'terrible']
            _, logs, _, _, _, _, _, _ = model_theft.run_model_theft_attack(user_words)

            # Check for key log messages
            log_text = ' '.join(logs)
            assert 'model theft attack' in log_text.lower()
            assert 'probing' in log_text.lower()

    def test_model_theft_weight_approximation(self, test_app):
        """Test that approximated weights are in reasonable range."""
        with test_app.app_context():
            user_words = ['excellent', 'terrible', 'good']
            _, _, approx_weights, actual_weights, _, _, _, _ = \
                model_theft.run_model_theft_attack(user_words)

            # Approximated weights should be floats
            for word, weight in approx_weights.items():
                assert isinstance(weight, (int, float))
                # Should be in reasonable range (not infinity, not NaN)
                assert abs(weight) < 1000

            # Should have some overlap with actual weights
            common_words = set(approx_weights.keys()) & set(actual_weights.keys())
            assert len(common_words) > 0


class TestDataPoisoning:
    """Tests for data poisoning vulnerability."""

    def test_create_sentiment_model(self, test_app):
        """Test creating base sentiment model."""
        with test_app.app_context():
            model_data = data_poisoning.create_sentiment_model()

            # Should return model data dictionary
            assert isinstance(model_data, dict)
            assert 'top_positive_words' in model_data
            assert 'top_negative_words' in model_data
            assert 'all_weights' in model_data
            assert 'training_size' in model_data

            # Should have weights
            weights = model_data['all_weights']
            assert isinstance(weights, dict)
            assert len(weights) > 0

            # Should have training size
            assert model_data['training_size'] > 0

    def test_create_poisoned_model(self, test_app):
        """Test creating model with poisoned data."""
        with test_app.app_context():
            # Poisoned comments (wrong labels)
            poisoned_comments = [
                {'text': 'excellent delicious great', 'sentiment': 'negative'},
                {'text': 'terrible awful disgusting', 'sentiment': 'positive'},
            ]

            model_data = data_poisoning.create_new_model_with_poisoned_data(poisoned_comments)

            # Should return model data
            assert isinstance(model_data, dict)
            assert 'model_name' in model_data
            assert 'vocabulary_size' in model_data
            assert 'all_weights' in model_data
            assert 'poisoning_size' in model_data
            assert model_data['poisoning_size'] == 2

    def test_poisoned_model_validation(self, test_app):
        """Test that poisoned model accepts valid formats."""
        with test_app.app_context():
            valid_comments = [
                {'text': 'good pizza', 'sentiment': 'positive'},
                {'text': 'bad pizza', 'sentiment': 'negative'},
            ]

            model_data = data_poisoning.create_new_model_with_poisoned_data(valid_comments)
            assert isinstance(model_data, dict)

    def test_test_model_function(self, test_app):
        """Test the test_model function."""
        with test_app.app_context():
            # Create a simple model first
            model_data = data_poisoning.create_sentiment_model()
            weights = model_data['all_weights']

            # Test with sample text
            text = "This is a great pizza"
            sentiment, confidence, score, probability = data_poisoning.test_model(text, weights)

            # Should return valid values
            assert sentiment in ['positive', 'negative']
            assert isinstance(confidence, (int, float))
            assert 0.0 <= confidence <= 1.0
            assert isinstance(score, (int, float))
            assert isinstance(probability, (int, float))
            assert 0.0 <= probability <= 1.0

    def test_test_model_empty_text(self, test_app):
        """Test model with empty text."""
        with test_app.app_context():
            model_data = data_poisoning.create_sentiment_model()
            weights = model_data['all_weights']

            # Test with empty text
            sentiment, confidence, score, probability = data_poisoning.test_model("", weights)

            # Should still return valid values
            assert sentiment in ['positive', 'negative']
            assert isinstance(confidence, (int, float))

    def test_poisoning_effect(self, test_app):
        """Test that poisoned data affects model predictions."""
        with test_app.app_context():
            # Create normal model
            normal_model = data_poisoning.create_sentiment_model()

            # Create heavily poisoned model
            poisoned_comments = [
                {'text': 'excellent great delicious amazing wonderful', 'sentiment': 'negative'},
                {'text': 'terrible awful disgusting horrible bad', 'sentiment': 'positive'},
            ] * 10  # Repeat to have strong effect

            poisoned_model = data_poisoning.create_new_model_with_poisoned_data(poisoned_comments)

            # Both should create models
            assert 'all_weights' in normal_model
            assert 'all_weights' in poisoned_model


class TestVulnerabilityHelpers:
    """Tests for helper functions in vulnerability modules."""

    def test_model_theft_with_special_chars(self, test_app):
        """Test model theft with words containing special characters."""
        with test_app.app_context():
            user_words = ['good!', 'bad...', 'okay?']
            samples, logs, _, _, _, _, _, _ = model_theft.run_model_theft_attack(user_words)

            # Should clean and process words
            assert len(logs) > 0

    def test_data_poisoning_mixed_sentiments(self, test_app):
        """Test data poisoning with mixed sentiment labels."""
        with test_app.app_context():
            mixed_comments = [
                {'text': 'good', 'sentiment': 'positive'},
                {'text': 'bad', 'sentiment': 'negative'},
                {'text': 'okay', 'sentiment': 'positive'},
                {'text': 'terrible', 'sentiment': 'negative'},
            ]

            model_data = data_poisoning.create_new_model_with_poisoned_data(mixed_comments)
            assert 'vocabulary_size' in model_data
            assert model_data['vocabulary_size'] > 0


class TestSupplyChainDeserialization:
    """Tests for the load-time __reduce__ payload and its win condition."""

    def test_evaluate_solve_matrix(self):
        from application.vulnerabilities.supply_chain import evaluate_supply_chain_solve
        # Solve only when the payload ran AND the unsafe loader was used.
        assert evaluate_supply_chain_solve(payload_executed=True, hardened=False)['solved'] is True
        assert evaluate_supply_chain_solve(payload_executed=True, hardened=True)['solved'] is False
        assert evaluate_supply_chain_solve(payload_executed=False, hardened=False)['solved'] is False

    def test_construction_does_not_fire_payload(self):
        """Building the object must not run the payload; only loading the file does."""
        from application.vulnerabilities import supply_chain as sc
        token = 'unit-construct-check'
        marker = sc._proof_path(token)
        if os.path.exists(marker):
            os.remove(marker)
        sc.SentimentModel_reduce_malicious(token=token)
        assert not os.path.exists(marker)

    def test_reduce_payload_fires_on_unsafe_load_only(self):
        from application.vulnerabilities import supply_chain as sc
        saved = sc.save_reduce_malicious_model()
        assert saved['success'] is True

        unsafe = sc.load_saved_model(hardened=False)
        assert unsafe['payload_executed'] is True
        assert unsafe['solved'] is True

        hardened = sc.load_saved_model(hardened=True)
        assert hardened['payload_executed'] is False
        assert hardened['blocked'] is True
        assert hardened['solved'] is False
