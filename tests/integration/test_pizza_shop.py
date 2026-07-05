"""
Integration tests for core pizza shop functionality.
Tests browsing, commenting, ordering, and basic CRUD operations.
"""

class TestPizzaBrowsing:
    """Tests for browsing pizzas."""

    def test_home_page_loads(self, client):
        """Test that home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'pizza' in response.data.lower()

    def test_home_page_shows_pizzas(self, client):
        """Test that pizzas are displayed on home page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Margherita' in response.data or b'margherita' in response.data.lower()

    def test_pizza_detail_page(self, client):
        """Test viewing individual pizza details."""
        response = client.get('/pizza/1')
        assert response.status_code == 200
        # Should show pizza details
        assert b'pizza' in response.data.lower()

    def test_pizza_detail_nonexistent(self, client):
        """Test viewing non-existent pizza returns 404."""
        response = client.get('/pizza/9999')
        assert response.status_code == 404

    def test_basics_page(self, client):
        """Test that basics/lab setup page loads."""
        response = client.get('/basics')
        assert response.status_code == 200


class TestComments:
    """Tests for pizza comments functionality."""

    def test_add_comment_authenticated(self, authenticated_client):
        """Test adding a comment when logged in."""
        response = authenticated_client.post(
            '/add_comment/1',
            data={
                'content': 'This is a test comment',
                'rating': '5'
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        # Comment should appear on page
        assert b'test comment' in response.data.lower()

    def test_add_comment_unauthenticated(self, client):
        """Test that unauthenticated users cannot add comments."""
        response = client.post(
            '/add_comment/1',
            data={
                'content': 'Test comment',
                'rating': '5'
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'log in' in response.data.lower()

    def test_add_comment_missing_fields(self, authenticated_client):
        """Test adding comment with missing required fields."""
        response = authenticated_client.post(
            '/add_comment/1',
            data={'content': 'Test'},  # Missing rating
            follow_redirects=True
        )

        # Should redirect back to pizza page
        assert response.status_code == 200

    def test_delete_own_comment(self, authenticated_client):
        """Test deleting own comment."""
        # First add a comment
        authenticated_client.post(
            '/add_comment/1',
            data={'content': 'Comment to delete', 'rating': '4'}
        )

        # Get the comment ID (in real scenario, you'd parse it from response)
        # For now, we'll test with existing comment ID 1
        response = authenticated_client.post(
            '/delete_comment/1',
            follow_redirects=True
        )

        assert response.status_code == 200

    def test_delete_others_comment(self, authenticated_client):
        """Test that users cannot delete other users' comments."""
        # Try to delete comment ID 2 (owned by bob, logged in as alice)
        response = authenticated_client.post(
            '/delete_comment/2',
            follow_redirects=True
        )

        assert response.status_code == 200
        # Should show error message
        assert b'own' in response.data.lower() or b'cannot' in response.data.lower()


class TestOrdering:
    """Tests for pizza ordering functionality."""

    def test_order_pizza_authenticated(self, authenticated_client):
        """Test ordering pizza when logged in."""
        response = authenticated_client.post(
            '/order/1',
            data={'quantity': '2'},
            follow_redirects=True
        )

        assert response.status_code == 200
        # Should show success message
        assert b'success' in response.data.lower() or b'order' in response.data.lower()

    def test_order_pizza_unauthenticated(self, client):
        """Test that unauthenticated users cannot order."""
        response = client.post(
            '/order/1',
            data={'quantity': '1'},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'log in' in response.data.lower()

    def test_order_invalid_quantity(self, authenticated_client):
        """Test ordering with invalid quantity."""
        response = authenticated_client.post(
            '/order/1',
            data={'quantity': '0'},
            follow_redirects=True
        )

        assert response.status_code == 200
        # Should show error about invalid quantity
        assert b'quantity' in response.data.lower() or b'error' in response.data.lower()

    def test_order_nonexistent_pizza(self, authenticated_client):
        """Test ordering non-existent pizza."""
        response = authenticated_client.post(
            '/order/9999',
            data={'quantity': '1'}
        )

        assert response.status_code == 404

    def test_view_orders(self, authenticated_client):
        """Test viewing user's orders."""
        response = authenticated_client.get('/orders')

        assert response.status_code == 200
        assert b'order' in response.data.lower()

    def test_view_orders_unauthenticated(self, client):
        """Test that unauthenticated users cannot view orders."""
        response = client.get('/orders', follow_redirects=True)

        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'log in' in response.data.lower()


class TestVulnerabilityPages:
    """Tests for vulnerability demonstration pages."""

    def test_model_theft_page(self, client):
        """Test model theft demonstration page loads."""
        response = client.get('/model-theft')
        assert response.status_code == 200

    def test_supply_chain_page(self, client):
        """Test supply chain vulnerability page loads."""
        response = client.get('/supply-chain')
        assert response.status_code == 200

    def test_data_poisoning_page(self, client):
        """Test data poisoning page loads."""
        response = client.get('/data-poisoning')
        assert response.status_code == 200

    def test_catering_rag_poisoning_page(self, client):
        """Test corporate catering RAG lab page loads."""
        response = client.get('/data-poisoning/catering-rag')
        assert response.status_code == 200

    def test_dos_attack_page(self, client):
        """Test DoS attack demonstration page loads."""
        response = client.get('/dos-attack')
        assert response.status_code == 200

    def test_insecure_plugin_page(self, client):
        """Test insecure plugin page loads."""
        response = client.get('/insecure-plugin')
        assert response.status_code == 200

    def test_sensitive_info_page(self, client):
        """Test sensitive information disclosure page loads."""
        response = client.get('/sensitive-info')
        assert response.status_code == 200

    def test_excessive_agency_page(self, client):
        """Test excessive agency page loads."""
        response = client.get('/excessive-agency')
        assert response.status_code == 200

    def test_agentic_tools_page(self, client):
        """Test agentic tools / SQL lab page loads."""
        response = client.get('/agentic-tools')
        assert response.status_code == 200

    def test_misinformation_page(self, client):
        """Test misinformation page loads."""
        response = client.get('/misinformation')
        assert response.status_code == 200

    def test_direct_prompt_injection_page(self, client):
        """Test direct prompt injection page loads."""
        response = client.get('/direct-prompt-injection')
        assert response.status_code == 200

    def test_direct_prompt_injection_nav_hierarchy_and_deep_links(self, client):
        """DPI nav exposes Baseline and Guardrail ladder as separate routes."""
        response = client.get('/direct-prompt-injection')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'id="dpi-lab"' in html
        assert '/direct-prompt-injection"' in html or "/direct-prompt-injection'" in html
        assert '/direct-prompt-injection/guardrail-ladder' in html
        assert 'const DPI_MODE = "baseline"' in html
        assert 'id="dpi-baseline-wrap-ollama"' in html
        assert '>Baseline<' in html
        assert '>Guardrail ladder<' in html

        guardrail = client.get('/direct-prompt-injection/guardrail-ladder')
        assert guardrail.status_code == 200
        guardrail_html = guardrail.data.decode()
        assert 'const DPI_MODE = "escalation"' in guardrail_html
        assert 'id="dpi-escalation-wrap-ollama"' in guardrail_html

    def test_indirect_prompt_injection_page(self, client):
        """Test indirect prompt injection page loads."""
        response = client.get('/indirect-prompt-injection')
        assert response.status_code == 200

    def test_glossary_page(self, client):
        """Test glossary page loads."""
        response = client.get('/glossary')
        assert response.status_code == 200
