"""
Integration tests for API endpoints.
Tests the main API routes for sentiment analysis, model theft, data poisoning, and DoS simulation.
"""
import json


class TestSentimentAnalysisAPI:
    """Tests for sentiment analysis API endpoints."""

    def test_analyze_sentiment_positive(self, client):
        """Test sentiment analysis with positive text."""
        response = client.post(
            '/analyze_sentiment',
            json={'text': 'This pizza is amazing and delicious!'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sentiment' in data
        assert 'confidence' in data
        assert data['sentiment'] in ['positive', 'negative']

    def test_analyze_sentiment_negative(self, client):
        """Test sentiment analysis with negative text."""
        response = client.post(
            '/analyze_sentiment',
            json={'text': 'This pizza is terrible and disgusting.'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sentiment' in data
        assert 'confidence' in data

    def test_analyze_sentiment_empty_text(self, client):
        """Test sentiment analysis with empty text."""
        response = client.post(
            '/analyze_sentiment',
            json={'text': ''}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_sentiment_no_text(self, client):
        """Test sentiment analysis with no text field."""
        response = client.post(
            '/analyze_sentiment',
            json={}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_api_sentiment_analysis(self, client):
        """Test the /api/sentiment endpoint."""
        response = client.post(
            '/api/sentiment',
            json={'text': 'Great pizza with excellent service!'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'result' in data
        assert 'sentiment' in data['result']
        assert 'confidence' in data['result']
        assert 'probabilities' in data['result']
        assert 'model_info' in data

    def test_api_sentiment_missing_field(self, client):
        """Test /api/sentiment with missing text field."""
        response = client.post(
            '/api/sentiment',
            json={}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'message' in data


class TestModelTheftAPI:
    """Tests for model theft vulnerability demonstration."""

    def test_generate_sentiment_model(self, client):
        """Test model weight exposure endpoint."""
        response = client.get('/generate_sentiment_model')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'model_name' in data
        assert 'vocabulary_size' in data
        assert 'intercept' in data
        assert 'top_positive_words' in data
        assert 'top_negative_words' in data
        assert 'all_weights' in data
        assert isinstance(data['all_weights'], dict)

    def test_model_theft_attack(self, client):
        """Test model theft attack simulation."""
        response = client.post(
            '/api/model-theft',
            json={'user_words': ['great', 'terrible', 'delicious', 'awful']}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'samples' in data
        assert 'logs' in data
        assert 'approximated_weights' in data
        assert 'actual_weights' in data
        assert 'correlation' in data

    def test_model_theft_empty_words(self, client):
        """Test model theft with empty word list."""
        response = client.post(
            '/api/model-theft',
            json={'user_words': []}
        )

        assert response.status_code == 200
        # Should still return data even with empty words


class TestDataPoisoningAPI:
    """Tests for training data poisoning demonstration."""

    def test_train_poisoned_model(self, client):
        """Test training a model with poisoned data."""
        poisoned_comments = [
            {'text': 'delicious pizza', 'sentiment': 'negative'},  # Poisoned: positive text labeled negative
            {'text': 'terrible pizza', 'sentiment': 'positive'},   # Poisoned: negative text labeled positive
        ]

        response = client.post(
            '/api/train-poisoned-model',
            json={'comments': poisoned_comments}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'model_name' in data
        assert 'vocabulary_size' in data
        assert 'all_weights' in data

    def test_train_poisoned_model_invalid_format(self, client):
        """Test training with invalid comment format."""
        invalid_comments = [
            {'text': 'test'},  # Missing sentiment
        ]

        response = client.post(
            '/api/train-poisoned-model',
            json={'comments': invalid_comments}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_train_poisoned_model_invalid_sentiment(self, client):
        """Test training with invalid sentiment value."""
        invalid_comments = [
            {'text': 'test', 'sentiment': 'neutral'},  # Invalid sentiment
        ]

        response = client.post(
            '/api/train-poisoned-model',
            json={'comments': invalid_comments}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_test_poisoned_model(self, client):
        """Test the poisoned model testing endpoint."""
        response = client.post(
            '/api/test-poisoned-model',
            json={
                'text': 'delicious pizza',
                'weights': {'delicious': 0.5, 'pizza': 0.3}
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sentiment' in data
        assert 'confidence' in data
        assert 'score' in data
        assert 'probability' in data

    def test_test_poisoned_model_no_weights(self, client):
        """Test poisoned model with no weights provided."""
        response = client.post(
            '/api/test-poisoned-model',
            json={'text': 'test pizza'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestDoSSimulationAPI:
    """Tests for DoS attack simulation endpoint."""

    def test_llm_query_basic(self, client):
        """Test basic LLM query."""
        response = client.post(
            '/api/llm-query',
            json={'prompt': 'Tell me about your pizzas'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
        assert 'tokens_used' in data
        assert 'model' in data
        assert 'processing_time' in data
        assert 'server_load' in data
        assert 'rate_limits' in data

    def test_llm_query_no_prompt(self, client):
        """Test LLM query without prompt."""
        response = client.post(
            '/api/llm-query',
            json={}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_llm_query_server_load_tracking(self, client):
        """Test that server load increases with multiple requests."""
        # Make first request
        response1 = client.post('/api/llm-query', json={'prompt': 'test1'})
        data1 = json.loads(response1.data)
        initial_load = data1['server_load']['requests_last_minute']

        # Make second request
        response2 = client.post('/api/llm-query', json={'prompt': 'test2'})
        data2 = json.loads(response2.data)
        second_load = data2['server_load']['requests_last_minute']

        # Load should increase
        assert second_load >= initial_load

    def test_llm_query_pizza_keywords(self, client):
        """Test that pizza-related queries get relevant responses."""
        response = client.post(
            '/api/llm-query',
            json={'prompt': 'What pizzas do you have?'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'pizza' in data['response'].lower() or 'menu' in data['response'].lower()


class TestSupplyChainAPI:
    """Tests for supply chain vulnerability demonstrations."""

    def test_save_js_malicious_model(self, client):
        """Test saving JavaScript malicious model."""
        response = client.post('/save-js-malicious-model')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data

    def test_save_bash_malicious_model(self, client):
        """Test saving bash malicious model."""
        response = client.post('/save-bash-malicious-model')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data

    def test_load_bash_malicious_model(self, client):
        """Test loading bash malicious model (demonstrates supply chain attack)."""
        response = client.post('/load-bash-malicious-model')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data
        assert 'message' in data
        assert 'warning' in data

    def test_demo_malicious_model_page(self, client):
        """JS malicious model demo page loads after training the model."""
        response = client.get('/demo-malicious-model')

        assert response.status_code == 200
        assert b'Error demonstrating malicious model' not in response.data
