from flask import render_template, request, redirect, url_for, jsonify, session, flash, Response, stream_with_context
import os
import math
import time
import requests
import random
import json
from datetime import datetime
from sqlalchemy.exc import OperationalError

import application
from application.model import Pizza, Comment, User, Order, RoutingFlag

from application.vulnerabilities import data_poisoning
from application.vulnerabilities import model_theft
from application import sentiment_model


from application.vulnerabilities.ollama_indirect_prompt_injection import chat_with_ollama_indirect, decode_qr, UPLOAD_FOLDER
from application.vulnerabilities.openai_indirect_prompt_injection import chat_with_openai_indirect_prompt_injection
from application.provider_config import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    api_response_model_type,
    cloud_api_key_valid,
    cloud_provider_prefix,
    get_openai_api_key,
    llm_ui_snapshot,
    resolve_provider,
)
from werkzeug.utils import secure_filename

OLLAMA_BASE_URL = OLLAMA_HOST
_DB_READY_CHECKED = False


def _ollama_status_snapshot() -> tuple[bool, list[str], str | None]:
    """Best-effort Ollama status probe without side effects."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=4)
        if response.status_code != 200:
            return False, [], f"status={response.status_code}"
        models_data = response.json()
        models = [model.get("name", "") for model in models_data.get("models", []) if model.get("name")]
        return True, models, None
    except Exception as e:
        return False, [], str(e)


def _ollama_unavailable_message(feature_name: str) -> str:
    return (
        f"Ollama is unavailable for {feature_name}. "
        "Start Ollama (Lab Setup -> Setup Ollama) and retry."
    )


def _ollama_remote_gate_enabled() -> bool:
    """Skip live Ollama HTTP probes under pytest / Flask test client (monkeypatch targets)."""
    if (os.environ.get("TESTING") or "").strip().lower() in {"1", "true", "yes"}:
        return False
    try:
        from flask import current_app, has_request_context

        if has_request_context() and getattr(current_app, "testing", False):
            return False
    except RuntimeError:
        pass
    return True


def _seed_minimum_app_data() -> None:
    """Ensure essential DB objects exist so root/login never hard-fail."""
    application.db.create_all()

    if Pizza.query.count() == 0:
        pizzas = [
            Pizza(name='Margherita', description='Classic pizza with tomato sauce, mozzarella, and basil', price=9.99, image='margherita.jpg'),
            Pizza(name='Pepperoni', description='Pizza topped with tomato sauce, mozzarella, and pepperoni slices', price=11.99, image='pepperoni.jpg'),
            Pizza(name='Veggie Supreme', description='Loaded with bell peppers, onions, mushrooms, olives, and tomatoes', price=12.99, image='veggie.jpg'),
        ]
        for pizza in pizzas:
            application.db.session.add(pizza)
        application.db.session.commit()

    if User.query.filter_by(username='alice').first() is None:
        alice = User(username='alice')
        alice.set_password('alice')
        application.db.session.add(alice)
    if User.query.filter_by(username='bob').first() is None:
        bob = User(username='bob')
        bob.set_password('bob')
        application.db.session.add(bob)
    application.db.session.commit()

    if RoutingFlag.query.filter_by(username="alice").first() is None:
        application.db.session.add(RoutingFlag(username="alice", flag_code="RT-ALICE7A"))
    if RoutingFlag.query.filter_by(username="bob").first() is None:
        application.db.session.add(RoutingFlag(username="bob", flag_code="RT-BOB9F2"))
    application.db.session.commit()


def _ensure_db_ready() -> None:
    """Self-heal local runtime if DB tables are missing."""
    global _DB_READY_CHECKED
    if _DB_READY_CHECKED:
        return
    try:
        Pizza.query.limit(1).all()
        User.query.limit(1).all()
        RoutingFlag.query.limit(1).all()
        _DB_READY_CHECKED = True
    except OperationalError:
        application.db.session.rollback()
        _seed_minimum_app_data()
        _DB_READY_CHECKED = True


@application.app.before_request
def _before_request_ensure_db_ready():
    _ensure_db_ready()




# Create tables and initialize sample data
# Skip initialization during testing
if not os.environ.get('TESTING'):
    with application.app.app_context():
        application.db.create_all()

        # Only add sample data if the pizza table is empty
        if Pizza.query.count() == 0:
            pizzas = [
                Pizza(
                    name='Margherita',
                    description='Classic pizza with tomato sauce, mozzarella, and basil',
                    price=9.99,
                    image='margherita.jpg'
                ),
                Pizza(
                    name='Pepperoni',
                    description='Pizza topped with tomato sauce, mozzarella, and pepperoni slices',
                    price=11.99,
                    image='pepperoni.jpg'
                ),
                Pizza(
                    name='Veggie Supreme',
                    description='Loaded with bell peppers, onions, mushrooms, olives, and tomatoes',
                    price=12.99,
                    image='veggie.jpg'
                ),
                Pizza(
                    name='Hawaiian',
                    description='Ham and pineapple pizza with tomato sauce and mozzarella',
                    price=10.99,
                    image='hawaiian.jpg'
                ),
                Pizza(
                    name='BBQ Chicken',
                    description='BBQ sauce base with chicken, red onions, and mozzarella',
                    price=13.99,
                    image='bbq_chicken.jpg'
                ),
            ]

            for pizza in pizzas:
                application.db.session.add(pizza)

            application.db.session.commit()

            # Add sample comments with a good mix of positive and negative sentiments
            comments = [
                # Margherita comments
                Comment(pizza_id=1, name='Mike', content='Best pizza ever! The basil was so fresh and the sauce was perfect.', rating=5),
                Comment(pizza_id=1, name='Sarah', content='Love the fresh basil! Simple but delicious.', rating=4),
                Comment(pizza_id=1, name='Miguel', content='Classic Margherita done right. The cheese was fantastic.', rating=5),
                Comment(pizza_id=1, name='Laura', content='A bit too basic for my taste, but well executed.', rating=3),
                Comment(pizza_id=1, name='Thomas', content='The crust was undercooked and too soggy in the middle.', rating=2),
                
                # Pepperoni comments
                Comment(pizza_id=2, name='Mike', content='Perfect amount of pepperoni! Crispy and not too greasy.', rating=5),
                Comment(pizza_id=2, name='Emily', content='Delicious pepperoni and the cheese was melted perfectly.', rating=4),
                Comment(pizza_id=2, name='Robert', content='The pepperoni was tasty but too spicy for me.', rating=3),
                Comment(pizza_id=2, name='Jessica', content='My go-to pizza, always reliable and tasty.', rating=5),
                Comment(pizza_id=2, name='Daniel', content='Too greasy and the crust was burnt on the edges.', rating=2),
                
                # Veggie Supreme comments
                Comment(pizza_id=3, name='Emma', content='So many veggies, delicious! Great flavor combination.', rating=4),
                Comment(pizza_id=3, name='Noah', content='Fresh veggies and excellent sauce. Would order again!', rating=5),
                Comment(pizza_id=3, name='Mike', content='The vegetables were fresh but there was too much sauce.', rating=3),
                Comment(pizza_id=3, name='William', content='As a vegetarian, this is my favorite! Amazing taste.', rating=5),
                Comment(pizza_id=3, name='Olivia', content='Boring and bland. The vegetables seemed frozen, not fresh.', rating=1),
                
                # Hawaiian comments
                Comment(pizza_id=4, name='David', content='Pineapple on pizza is controversial but I love it! Sweet and savory perfection.', rating=5),
                Comment(pizza_id=4, name='Ava', content='The ham was excellent quality and paired well with the pineapple.', rating=4),
                Comment(pizza_id=4, name='James', content='Pineapple has no place on pizza. Disgusting combination.', rating=1),
                Comment(pizza_id=4, name='Isabella', content='Classic Hawaiian done well. Good balance of sweet and salty.', rating=4),
                Comment(pizza_id=4, name='Ethan', content='The ham was dry and the pineapple was too sour.', rating=2),
                
                # BBQ Chicken comments
                Comment(pizza_id=5, name='Mia', content='The BBQ sauce was amazing! Chicken was tender and juicy.', rating=5),
                Comment(pizza_id=5, name='Benjamin', content='Great flavor but a bit too much sauce for my taste.', rating=3),
                Comment(pizza_id=5, name='Charlotte', content='Perfect balance of flavors. The onions added a nice touch.', rating=5),
                Comment(pizza_id=5, name='Lucas', content='My favorite pizza! The BBQ sauce is unique and delicious.', rating=5),
                Comment(pizza_id=5, name='Amelia', content='Terrible pizza. The chicken was dry and the sauce was too sweet.', rating=1),
            ]
            
            for comment in comments:
                application.db.session.add(comment)
                
            application.db.session.commit()
    
        # Create users if they don't exist
        if User.query.count() == 0:
            alice = User(username='alice')
            alice.set_password('alice')
            
            bob = User(username='bob')
            bob.set_password('bob')
            
            application.db.session.add(alice)
            application.db.session.add(bob)
            application.db.session.commit()

        if RoutingFlag.query.count() == 0:
            application.db.session.add(RoutingFlag(username="alice", flag_code="RT-ALICE7A"))
            application.db.session.add(RoutingFlag(username="bob", flag_code="RT-BOB9F2"))
            application.db.session.commit()

# Authentication routes
@application.app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@application.app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Routes
@application.app.route('/')
def index():
    pizzas = Pizza.query.all()
    return render_template('index.html', pizzas=pizzas)

@application.app.route('/basics')
def basics():
    return render_template('basics.html')

@application.app.route('/model-theft')
def model_theft_main():
    return render_template('model_theft.html')

@application.app.route('/api/model-theft', methods=['POST'])
def model_theft_attack():
    user_words = request.json.get("user_words", [])
    probing_samples, logs, approximated_weights, model_weights, correlation, agreement_rate_str, avg_error_str, avg_rel_error_str = model_theft.run_model_theft_attack(user_words)
    
    return jsonify({
        "samples": probing_samples,
        "logs": logs,
        "approximated_weights": approximated_weights,
        "actual_weights": model_weights,
        "correlation": correlation,
        "agreement_rate": agreement_rate_str,
        "avg_error": avg_error_str,
        "avg_rel_error": avg_rel_error_str
    })

@application.app.route('/supply-chain')
def supply_chain():
    return render_template('supply_chain.html')

@application.app.route('/insecure-plugin')
def insecure_plugin():
    """Page demonstrating insecure plugin design with client-side API tokens"""
    return render_template('insecure_plugin.html')

@application.app.route('/sensitive-info')
def sensitive_info():
    """Page demonstrating sensitive information disclosure vulnerabilities in LLMs"""
    return render_template('sensitive_info.html')

@application.app.route('/training-data-leak/huggingface', methods=['POST'])
def test_huggingface_leakage():
    """API endpoint for testing HuggingFace model for training data leakage"""
    from training_data_leakage import huggingface_leak_endpoint
    return huggingface_leak_endpoint()

@application.app.route('/training-data-leak/openai', methods=['POST'])
def test_openai_leakage():
    """API endpoint for testing OpenAI model for training data leakage"""
    try:
        from application.vulnerabilities.openai_sensitive_data_leakage import query_rag_system_openai, detect_sensitive_info
        
        data = request.get_json()
        user_query = data.get('query', '')
        
        # Use OpenAI API key from session instead of user input
        api_token = get_openai_api_key(session)
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': '',
                'has_leakage': False,
                'leaked_info': []
            }), 400
        
        # If no API token provided, return clear error message
        if not api_token:
            return jsonify({
                'response': llm_ui_snapshot()['missing_key_error'],
                'has_leakage': False,
                'leaked_info': [],
                'model_type': 'error'
            })
        
        # Query the OpenAI RAG system with the provided API key
        response, success = query_rag_system_openai(user_query, api_token)
        
        if not success:
            return jsonify({
                'error': response,
                'response': '',
                'has_leakage': False,
                'leaked_info': [],
                'model_type': 'real'
            }), 500
        
        # Detect sensitive information in the response
        leaked_info = detect_sensitive_info(response)
        has_leakage = len(leaked_info) > 0
        
        return jsonify({
            'response': response,
            'has_leakage': has_leakage,
            'leaked_info': leaked_info,
            'model_type': 'real'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': '',
            'has_leakage': False,
            'leaked_info': []
        }), 500

@application.app.route('/training-data-leak/ollama', methods=['POST'])
def test_ollama_leakage():
    """API endpoint for testing Ollama model for training data leakage"""
    try:
        from application.vulnerabilities.ollama_sensitive_data_leakage import query_rag_system, detect_sensitive_info
        if _ollama_remote_gate_enabled():
            available, _, _ = _ollama_status_snapshot()
            if not available:
                msg = _ollama_unavailable_message("training-data-leak/ollama")
                return jsonify(
                    {
                        'response': msg,
                        'has_leakage': False,
                        'leaked_info': [],
                        'model_type': 'error',
                        'ollama_available': False,
                    }
                )

        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': '',
                'has_leakage': False,
                'leaked_info': []
            }), 400
        
        # Query the RAG system
        response, success = query_rag_system(user_query)
        
        if not success:
            return jsonify({
                'error': 'Error querying model',
                'response': response,
                'has_leakage': False,
                'leaked_info': []
            }), 500
        
        # Detect sensitive information in the response
        leaked_info = detect_sensitive_info(response)
        has_leakage = len(leaked_info) > 0
        
        return jsonify({
            'response': response,
            'has_leakage': has_leakage,
            'leaked_info': leaked_info,
            'model_type': 'real',
            'model': 'ollama'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': '',
            'has_leakage': False,
            'leaked_info': []
        }), 500

@application.app.route('/update-rag-ollama', methods=['POST'])
def update_rag_ollama():
    """API endpoint for updating the RAG system with latest comments"""
    try:
        from application.vulnerabilities.ollama_sensitive_data_leakage import initialize_rag_system
        
        # Reinitialize the RAG system with latest data
        success = initialize_rag_system()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'RAG system updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update RAG system'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating RAG system: {str(e)}'
        }), 500

@application.app.route('/update-rag-misinformation', methods=['POST'])
def update_rag_misinformation():
    """API endpoint for updating the misinformation RAG system with latest comments"""
    try:
        from application.vulnerabilities.ollama_misinformation import initialize_rag_system

        # Reinitialize the RAG system with latest data
        success = initialize_rag_system()

        if success:
            return jsonify({
                'success': True,
                'message': 'Misinformation RAG system updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update misinformation RAG system'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating misinformation RAG system: {str(e)}'
        }), 500

@application.app.route('/update-rag-openai', methods=['POST'])
def update_rag_openai():
    """API endpoint for updating the OpenAI RAG system with latest comments"""
    try:
        from application.vulnerabilities.openai_sensitive_data_leakage import initialize_rag_system

        # Reinitialize the RAG system with latest data
        success = initialize_rag_system()

        if success:
            return jsonify({
                'success': True,
                'message': 'OpenAI RAG system updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update OpenAI RAG system'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating OpenAI RAG system: {str(e)}'
        }), 500

@application.app.route('/update-rag-openai-misinfo', methods=['POST'])
def update_rag_openai_misinfo():
    """API endpoint for updating the OpenAI misinformation RAG system with latest comments"""
    try:
        from application.vulnerabilities.openai_misinformation import initialize_rag_system

        # Reinitialize the RAG system with latest data
        success = initialize_rag_system()

        if success:
            return jsonify({
                'success': True,
                'message': 'OpenAI misinformation RAG system updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update OpenAI misinformation RAG system'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating OpenAI misinformation RAG system: {str(e)}'
        }), 500

@application.app.route('/chat-with-pizza-assistant', methods=['POST'])
def chat_with_pizza_assistant():
    """API endpoint for the pizza assistant chat - using insecure plugin design"""
    try:
        # Get data from request
        data = request.get_json()
        message = data.get('message', '')
        
        # Get API token - note it's not needed with our local model but kept for UI consistency
        api_token =session.get('openai_api_token')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Import the conversational model plugin system
        from application.vulnerabilities.ollama_insecure_plugin import chat_with_llm
        
        # The vulnerability: Directly passing user message to the LLM+plugin system
        # where the LLM can control function execution
        response = chat_with_llm(message, api_token)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@application.app.route('/chat-with-pizza-assistant-direct-prompt-injection', methods=['POST'])
def chat_with_pizza_assistant_direct_prompt():
    """API endpoint for the pizza assistant chat - using insecure plugin design"""
    try:
        # Get data from request
        data = request.get_json()
        message = data.get('message', '')
        level = data.get("level", "1")  # default to level 1
        escalation_stage = data.get("escalation_stage")
        history = data.get("history")

        if not message:
            return jsonify({'error': 'No message provided'}), 400

        if _ollama_remote_gate_enabled():
            available, _, _ = _ollama_status_snapshot()
            if not available:
                return jsonify(
                    {
                        'response': _ollama_unavailable_message("direct prompt injection"),
                        'model_type': 'error',
                        'ollama_available': False,
                    }
                )

        if escalation_stage is not None:
            from application.vulnerabilities.direct_prompt_escalation import run_escalation_ollama

            try:
                stage_i = int(escalation_stage)
            except (TypeError, ValueError):
                return jsonify({'error': 'escalation_stage must be an integer 0-9'}), 400
            response, esc_meta = run_escalation_ollama(
                message, stage_i, history=history, model_name=OLLAMA_MODEL
            )
            return jsonify({"response": response, "escalation_meta": esc_meta})

        from application.vulnerabilities.ollama_direct_prompt_injection import chat_with_ollama_direct_prompt_injection

        response = chat_with_ollama_direct_prompt_injection(message, level=level, model_name=OLLAMA_MODEL)

        return jsonify({'response': response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _parse_openai_style_messages(messages):
    """Strip system roles; last user content is the active prompt; prior turns are history."""
    if not messages:
        return "", None
    clean: list[dict] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "")).lower().strip()
        if role == "system":
            continue
        if role in ("user", "assistant"):
            clean.append({"role": role, "content": str(m.get("content", ""))})
    if not clean:
        return "", None
    last = clean[-1]
    if last.get("role") != "user":
        return "", clean
    prior = clean[:-1] if len(clean) > 1 else None
    return str(last.get("content", "")), prior


@application.app.route("/api/lab/direct-prompt-escalation/stages", methods=["GET"])
def api_direct_prompt_escalation_stages():
    from application.vulnerabilities.direct_prompt_escalation import escalation_stage_metadata

    return jsonify({"stages": escalation_stage_metadata()})


@application.app.route("/v1/lab/chat/completions", methods=["POST"])
def lab_chat_completions_openai_shape():
    """
    OpenAI-shaped completions for scanner-style clients (local Ollama backend).
    Requires JSON field ``pwnzz_escalation_stage`` (0-9). Optional ``pwnzz_history``.
    """
    try:
        from application.vulnerabilities.direct_prompt_escalation import (
            openai_style_completion_response,
            run_escalation_ollama,
        )

        data = request.get_json(silent=True) or {}
        messages = data.get("messages") or []
        stage_raw = data.get("pwnzz_escalation_stage")
        if stage_raw is None:
            return jsonify(
                {"error": "pwnzz_escalation_stage (integer 0-9) is required for this lab endpoint."}
            ), 400
        try:
            stage_i = int(stage_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "pwnzz_escalation_stage must be an integer 0-9"}), 400

        user_msg, hist_from_messages = _parse_openai_style_messages(messages)
        history = data.get("pwnzz_history")
        if history is None:
            history = hist_from_messages
        if not user_msg:
            return jsonify({"error": "messages must include at least one user turn"}), 400

        text, esc_meta = run_escalation_ollama(
            user_msg, stage_i, history=history, model_name=OLLAMA_MODEL
        )
        body = openai_style_completion_response(text)
        body["pwnzz_escalation_meta"] = esc_meta
        return jsonify(body)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@application.app.route('/chat-with-openai-plugin', methods=['POST'])
def chat_with_openai_plugin():
    """API endpoint for the OpenAI-based insecure plugin demo"""
    try:
        # Get data from request
        data = request.get_json()
        message = data.get('message', '')
        
        # Use OpenAI API key from session instead of user input
        openai_api_key = get_openai_api_key(session)
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        if not openai_api_key:
            return jsonify({'error': llm_ui_snapshot()['missing_key_error']}), 400
        
        # Import the OpenAI insecure plugin
        from application.vulnerabilities.openai_insecure_plugin import chat_with_openai
        
        # VULNERABLE: Directly using user-provided API key with the configured cloud LLM
        response = chat_with_openai(message, openai_api_key)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.app.route('/demo-malicious-model')
def demo_malicious_model():
    """
    This route demonstrates how a malicious model can inject code when instantiated
    in a Flask application context.
    """
    try:
        # Import the model class (this would simulate using a library/package in a real scenario)
        from application.vulnerabilities.supply_chain import SentimentModel_JS_malicious
        
        # Create an instance of the model - this will trigger the malicious code in __init__
        # The model's __init__ method hooks into Flask's response system
        model = SentimentModel_JS_malicious()
        model.train()
        print(model.get_model_info())
        
        # Return a simple page - the model will inject its JavaScript into the response
        return render_template('demo_vulnerable.html', 
                               message="Model instantiated - inspect the page source to see the injected JavaScript")
    except Exception as e:
        return f"Error demonstrating malicious model: {str(e)}"

@application.app.route('/load-bash-malicious-model', methods=['POST'])
def load_bash_malicious_model():
    """
    This route demonstrates how a malicious model can execute OS commands when instantiated.
    This is extremely dangerous and shows supply chain attack risks.
    """
    try:
        # Import the bash malicious model class
        from application.vulnerabilities.supply_chain import SentimentModel_bash_malicious
        
        # Create an instance of the model - this will trigger OS command execution
        model = SentimentModel_bash_malicious()
        
        # Return information about what commands were executed
        return jsonify({
            'success': True,
            'message': 'Malicious bash model loaded successfully',
            'commands_executed': model.executed_commands,
            'warning': 'This demonstrates how malicious models can execute arbitrary system commands!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error loading malicious bash model: {str(e)}'
        }), 500

@application.app.route('/save-js-malicious-model', methods=['POST'])
def save_js_malicious_model():
    """Save the JavaScript malicious model as a pickle file."""
    try:
        from application.vulnerabilities.supply_chain import save_js_malicious_model
        result = save_js_malicious_model()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving JS model: {str(e)}'
        }), 500

@application.app.route('/save-bash-malicious-model', methods=['POST'])
def save_bash_malicious_model():
    """Save the bash malicious model as a pickle file."""
    try:
        from application.vulnerabilities.supply_chain import save_bash_malicious_model
        result = save_bash_malicious_model()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving bash model: {str(e)}'
        }), 500
    
@application.app.route('/data-poisoning')
def data_poisoning_main():
    model_data=data_poisoning.create_sentiment_model()
    
    return render_template('data_poisoning.html', model_data=model_data)


@application.app.route('/data-poisoning/catering-rag')
def catering_rag_poisoning_page():
    """Corporate catering vector / RAG poisoning lab (LLM04-adjacent scenario)."""
    return render_template('catering_rag_poisoning.html')


@application.app.route('/agentic-tools')
def agentic_tools():
    """Catering agentic SQL / tool routing lab (RAG sibling lives on data poisoning)."""
    return render_template('agentic_tools.html')

@application.app.route('/dos-attack')
def dos_attack():
    """
    Renders the LLM DoS Simulation page.
    This page shows how an attacker can overwhelm LLM services with requests.
    """
    return render_template('dos_attack.html')

@application.app.route('/real-dos-attack')
def real_dos_attack():
    """
    Renders the LLM DoS Attack page with real attack functionality.
    This page demonstrates both simulated and real DoS attacks,
    along with secure implementation using rate limiting.
    """
    return render_template('dos_attack.html')

@application.app.route('/pizza/<int:pizza_id>')
def pizza_detail(pizza_id):
    pizza = Pizza.query.get_or_404(pizza_id)
    return render_template('pizza_detail.html', pizza=pizza)

@application.app.route('/add_comment/<int:pizza_id>', methods=['POST'])
def add_comment(pizza_id):
    if 'user_id' not in session:
        flash('You need to be logged in to add a comment.')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(session.get('user_id'))
    name=user.username
    content = request.form.get('content')
    rating = request.form.get('rating')
    
    if name and content and rating:
        comment = Comment(
            pizza_id=pizza_id,
            user_id=session.get('user_id'),
            name=name,
            content=content,
            rating=int(rating)
        )
        application.db.session.add(comment)
        application.db.session.commit()
        print("Comment added successfully.")
    
    return redirect(url_for('pizza_detail', pizza_id=pizza_id))

@application.app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user is logged in and owns the comment
    if 'user_id' not in session or comment.user_id != session['user_id']:
        flash('You can only delete your own comments.')
        return redirect(url_for('pizza_detail', pizza_id=comment.pizza_id))
    
    pizza_id = comment.pizza_id
    application.db.session.delete(comment)
    application.db.session.commit()
    flash('Comment deleted successfully.')
    
    return redirect(url_for('pizza_detail', pizza_id=pizza_id))

@application.app.route('/order/<int:pizza_id>', methods=['POST'])
def order_pizza(pizza_id):
    if 'user_id' not in session:
        flash('You need to be logged in to place an order.')
        return redirect(url_for('login'))
    
    pizza = Pizza.query.get_or_404(pizza_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity < 1:
        flash('Quantity must be at least 1.')
        return redirect(url_for('pizza_detail', pizza_id=pizza_id))
    
    total_price = pizza.price * quantity
    
    order = Order(
        user_id=session['user_id'],
        pizza_id=pizza_id,
        quantity=quantity,
        total_price=total_price
    )
    
    application.db.session.add(order)
    application.db.session.commit()
    flash(f'Order placed successfully! {quantity} x {pizza.name} - Total: ${total_price:.2f}', 'success')
    
    return redirect(url_for('pizza_detail', pizza_id=pizza_id))

@application.app.route('/orders')
def my_orders():
    if 'user_id' not in session:
        flash('You need to be logged in to view your orders.', 'error')
        return redirect(url_for('login'))
    
    user_orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


@application.app.route('/order-access/ollama', methods=['POST'])
def test_ollama_order_access():
    """Test Ollama model accessing user orders"""
    try:
        from application.vulnerabilities.ollama_order_access import query_ollama_with_orders, detect_order_access
        
        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': '',
                'has_access_violation': False,
                'accessed_info': []
            }), 400
        
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({
                'response': "You need to be logged in to access order information.",
                'has_access_violation': False,
                'accessed_info': [],
                'model_type': 'ollama'
            })
        
        # Query Ollama model with order access
        response, success = query_ollama_with_orders(user_query)
        
        if not success:
            return jsonify({
                'error': 'Error querying model',
                'response': response,
                'has_access_violation': False,
                'accessed_info': [],
                'model_type': 'ollama'
            }), 500
        
        # Detect if order information was accessed
        accessed_info = detect_order_access(response)
        has_access_violation = len(accessed_info) > 0
        
        return jsonify({
            'response': response,
            'has_access_violation': has_access_violation,
            'accessed_info': accessed_info,
            'model_type': 'ollama'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': '',
            'has_access_violation': False,
            'accessed_info': []
        }), 500

@application.app.route('/order-access/openai', methods=['POST'])
def test_openai_order_access():
    """Test OpenAI model accessing user orders"""
    try:
        from application.vulnerabilities.openai_order_access import query_openai_with_orders, detect_order_access
        
        data = request.get_json()
        user_query = data.get('query', '')
        
        # Use OpenAI API key from session instead of user input
        api_token = get_openai_api_key(session)
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': '',
                'has_access_violation': False,
                'accessed_info': []
            }), 400
        
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({
                'response': "You need to be logged in to access order information.",
                'has_access_violation': False,
                'accessed_info': [],
                'model_type': api_response_model_type()
            })
        
        # If no API token, return error
        if not api_token:
            return jsonify({
                'response': llm_ui_snapshot()['missing_key_error'],
                'has_access_violation': False,
                'accessed_info': [],
                'model_type': 'error'
            })
        
        # Query OpenAI model with order access
        response, success = query_openai_with_orders(user_query, api_token)
        
        if not success:
            return jsonify({
                'error': response,
                'response': '',
                'has_access_violation': False,
                'accessed_info': [],
                'model_type': 'real'
            }), 500
        
        # Detect if order information was accessed
        accessed_info = detect_order_access(response)
        has_access_violation = len(accessed_info) > 0
        
        return jsonify({
            'response': response,
            'has_access_violation': has_access_violation,
            'accessed_info': accessed_info,
            'model_type': 'real'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': '',
            'has_access_violation': False,
            'accessed_info': []
        }), 500

@application.app.route('/excessive-agency')
def excessive_agency():
    """Page demonstrating excessive agency vulnerabilities in LLMs"""
    return render_template('excessive_agency.html')

@application.app.route('/excessive-agency/ollama', methods=['POST'])
def test_ollama_excessive_agency():
    """Test Ollama model with excessive agency"""
    try:
        from application.vulnerabilities.ollama_excessive_agency import place_order
        
        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': 'Please provide a query to test.'
            }), 400
        
        # Use the place_order function to process the user query
        response = place_order(user_query)
        
        return jsonify({
            'response': response,
            'model_type': 'real'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': f'Error processing order: {str(e)}'
        }), 500

@application.app.route('/excessive-agency/openai', methods=['POST'])
def test_openai_excessive_agency():
    """Test OpenAI model with excessive agency"""
    try:
        from application.vulnerabilities.openai_excessive_agency import place_order
        
        data = request.get_json()
        user_query = data.get('query', '')
        api_token = get_openai_api_key(session)
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': 'Please provide a query to test.'
            }), 400
            
        if not api_token:
            return jsonify({
                'response': llm_ui_snapshot()['excessive_agency_token_error'],
                'model_type': 'error'
            })
        
        # Use the place_order function to process the user query
        response = place_order(user_query, api_token)
        
        return jsonify({
            'response': response,
            'model_type': 'real'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': f'Error processing order: {str(e)}'
        }), 500

@application.app.route('/misinformation')
def misinformation():
    """Page demonstrating misinformation vulnerabilities in LLMs"""
    return render_template('misinformation.html')

@application.app.route('/glossary')
def glossary():
    """Glossary page with AI, LLM, and security terms"""
    return render_template('glossary.html')

# Lab Setup Routes
@application.app.route('/save-openai-api-key', methods=['POST'])
def save_openai_api_key():
    """Save cloud LLM API key to session (OpenAI/Gemini/etc via LiteLLM route)."""
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key', '').strip()
        provider_hint = (data.get('provider') or '').strip()
        model_hint = (data.get('model') or '').strip()
        # Backward-compatible default for existing clients calling /save-openai-api-key.
        if not provider_hint and not model_hint:
            provider_hint = "openai"
        effective_prefix = cloud_provider_prefix(provider_hint=provider_hint, model_hint=model_hint)
        
        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})
        
        if not cloud_api_key_valid(api_key, provider_hint=provider_hint, model_hint=model_hint):
            guidance = (
                "OpenAI-style keys usually start with sk-."
                if effective_prefix == "openai"
                else "Use your configured provider key (for Gemini/Vertex, use the API key from AI Studio/Vertex)."
            )
            error_msg = (
                "Invalid API key format. OpenAI keys typically start with sk-"
                if effective_prefix == "openai"
                else f"Invalid API key format for provider '{effective_prefix}'. Check your key and try again."
            )
            return jsonify(
                {
                    'success': False,
                    'error': error_msg,
                    'provider_prefix': effective_prefix,
                    'guidance': guidance,
                }
            )
        
        # Store in session
        session['openai_api_key'] = api_key
        session['cloud_provider_prefix'] = effective_prefix
        return jsonify(
            {
                'success': True,
                'message': 'API key saved successfully',
                'provider_prefix': effective_prefix,
                'provider_name': llm_ui_snapshot()['provider_name'],
            }
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@application.app.route('/check-openai-api-key')
def check_openai_api_key():
    """Check if OpenAI API key is saved in session"""
    has_key = get_openai_api_key(session) != ''
    return jsonify(
        {
            'has_key': has_key,
            'llm_ui': llm_ui_snapshot(),
            'provider_prefix': session.get('cloud_provider_prefix') or cloud_provider_prefix(),
        }
    )

@application.app.route('/setup-ollama', methods=['POST'])
def setup_ollama():
    """Setup Ollama using the existing ollama_setup.py"""
    try:
        from application.ollama_setup import ensure_ollama_running, check_and_pull_model, model_name

        # Ensure Ollama is running (will attempt to start if not)
        if not ensure_ollama_running(base_url=OLLAMA_BASE_URL):
            return jsonify({
                'success': False,
                'error': 'Ollama could not be started. Please check if Ollama is installed or start it manually from https://ollama.ai'
            })

        # Pull the default model
        success = check_and_pull_model(model_name, base_url=OLLAMA_BASE_URL)
        model_list=" , ".join(model_name)
        if success:
            return jsonify({
                'success': True,
                'message': f'Ollama setup completed! Model {model_list} is ready to use.'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to pull model {model_list}. Please check your internet connection and try again.'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Setup error: {str(e)}'})

@application.app.route('/setup-ollama-stream', methods=['GET'])
def setup_ollama_stream():
    """Setup Ollama with Server-Sent Events for real-time progress updates"""
    def generate():
        try:
            from application.ollama_setup import ensure_ollama_running, check_and_pull_model_with_progress, model_name

            # Initial status
            yield f"data: {json.dumps({'status': 'Starting Ollama service...', 'progress': 5})}\n\n"

            # Ensure Ollama is running
            if not ensure_ollama_running(base_url=OLLAMA_BASE_URL):
                yield f"data: {json.dumps({'status': 'error', 'error': 'Ollama could not be started. Please check if Ollama is installed or start it manually from https://ollama.ai'})}\n\n"
                return

            yield f"data: {json.dumps({'status': 'Ollama service started', 'progress': 10})}\n\n"

            # Pull models with progress updates
            for progress_update in check_and_pull_model_with_progress(model_name, base_url=OLLAMA_BASE_URL):
                # Scale progress from 10-100
                scaled_progress = 10 + (progress_update['progress'] * 0.9)
                progress_update['progress'] = scaled_progress
                yield f"data: {json.dumps(progress_update)}\n\n"

                # If there's an error, stop
                if progress_update.get('status') == 'error':
                    return

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': f'Setup error: {str(e)}'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })

@application.app.route('/check-ollama-status')
def check_ollama_status():
    """Check current Ollama status"""
    try:
        available, models, err = _ollama_status_snapshot()
        return jsonify({'available': available, 'models': models, 'error': err})
            
    except Exception as e:
        return jsonify({'available': False, 'models': [], 'error': str(e)})

@application.app.route('/misinformation/ollama', methods=['POST'])
def test_ollama_misinformation():
    """Test Ollama model for misinformation using comments"""
    try:
        from application.vulnerabilities.ollama_misinformation import query_ollama_for_misinformation
        if _ollama_remote_gate_enabled():
            available, _, _ = _ollama_status_snapshot()
            if not available:
                return jsonify(
                    {
                        'response': _ollama_unavailable_message("misinformation/ollama"),
                        'has_misinformation': False,
                        'misinformation_detected': [],
                        'model_type': 'error',
                        'ollama_available': False,
                    }
                )

        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': '',
                'has_misinformation': False,
                'misinformation_detected': []
            }), 400
        
        # Query Ollama model using comment system
        response, success = query_ollama_for_misinformation(user_query)
        
        if not success:
            return jsonify({
                'error': 'Error querying model',
                'response': response,
                'has_misinformation': False,
                'misinformation_detected': [],
                'model_type': 'ollama'
            }), 500
        
        return jsonify({
            'response': response,
            'has_misinformation': False,
            'misinformation_detected': [],
            'model_type': 'ollama'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': '',
            'has_misinformation': False,
            'misinformation_detected': []
        }), 500

@application.app.route('/misinformation/openai', methods=['POST'])
def test_openai_misinformation():
    """Test OpenAI model for misinformation using comments"""
    try:
        from application.vulnerabilities.openai_misinformation import query_openai_for_misinformation

        data = request.get_json()
        user_query = data.get('query', '')

        # Get API token from session
        api_token = get_openai_api_key(session)

        if not user_query:
            return jsonify({
                'error': 'No query provided',
                'response': '',
                'has_misinformation': False,
                'misinformation_detected': []
            }), 400

        # If no API token, return error
        if not api_token:
            return jsonify({
                'response': llm_ui_snapshot()['misinformation_connect_hint'],
                'has_misinformation': False,
                'misinformation_detected': [],
                'model_type': 'error'
            })
        
        # Query OpenAI model using comment system
        response, success = query_openai_for_misinformation(user_query, api_token)
        
        if not success:
            return jsonify({
                'error': response,
                'response': '',
                'has_misinformation': False,
                'misinformation_detected': [],
                'model_type': 'real'
            }), 500
        
        return jsonify({
            'response': response,
            'has_misinformation': False,
            'misinformation_detected': [],
            'model_type': 'real'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'response': '',
            'has_misinformation': False,
            'misinformation_detected': []
        }), 500

# @application.app.route('/ask', methods=['POST'])
# def ask_llm():
#     prompt = request.form.get('prompt', '')
#     response = llm.generate_response(prompt)
#     return jsonify({'response': response})

@application.app.route('/generate_sentiment_model')
def generate_sentiment_model():
    """
    Generate a sentiment analysis model using model.py and return its weights.
    This demonstrates model theft vulnerability by exposing the model's internals.
    """
    
    
    # Access the trained model and vectorizer from model.py
   
    sentences, labels,vectorizer, model = sentiment_model.create_model()
    
    # Get the vocabulary from the vectorizer
    vocabulary = vectorizer.get_feature_names_out()
    
    # Get the coefficients (weights) from the model
    coefficients = model.coef_[0]
    
    # Sort words by importance (absolute value of coefficients)
    word_importance = [(word, float(coef)) for word, coef in zip(vocabulary, coefficients)]
    sorted_word_importance = sorted(word_importance, key=lambda x: abs(x[1]), reverse=True)
    
    # Get intercept
    intercept = float(model.intercept_[0])
    
    # Create model data
    model_data = {
        "model_name": "Sentiment Analysis Model",
        "version": "1.0",
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "description": "A logistic regression model for sentiment analysis",
        "model_type": "Logistic Regression",
        "training_data": {
            "sentences": sentences,
            "labels": labels
        },
        "vocabulary_size": len(vocabulary),
        "intercept": intercept,
        "top_positive_words": [(word, coef) for word, coef in sorted_word_importance if coef > 0][:10],
        "top_negative_words": [(word, coef) for word, coef in sorted_word_importance if coef < 0][:10],
        "all_weights": {word: float(coef) for word, coef in sorted_word_importance}
    }
    
    return jsonify(model_data)

@application.app.route('/analyze_sentiment', methods=['POST'])
def analyze_sentiment():
    """
    Analyze the sentiment of input text using the model from sentiment_model.py.
    This demonstrates how the stolen model could be used for inference.
    Used by the web interface.
    """
    # Get input text from request
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Import the model from model.py
    from application import sentiment_model
    sentences, labels,vectorizer, model = sentiment_model.create_model()

    
    # Vectorize the input text
    text_vector = vectorizer.transform([text])
    
    # Get the prediction (0 = negative, 1 = positive)
    prediction = model.predict(text_vector)[0]
    
    # Get confidence score (probability of the predicted class)
    probabilities = model.predict_proba(text_vector)[0]
    confidence = probabilities[prediction]
    
    # Return the prediction
    sentiment = "positive" if prediction == 1 else "negative"
    
    return jsonify({
        'text': text,
        'sentiment': sentiment,
        'confidence': float(confidence)
    })

@application.app.route('/api/sentiment', methods=['POST'])
def api_sentiment_analysis():
    """
    API endpoint for sentiment analysis.
    Accepts JSON with a 'text' field and returns sentiment analysis results.
    This endpoint allows programmatic access to the model.
    """
    try:
        # Get input data from request
        data = request.get_json()
        
        # Check if request contains the required fields
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Request must include a text field',
                'example': {
                    'text': 'Your text to analyze'
                }
            }), 400
        
        text = data['text']

        # Import the model from model.py and create/get the model
        from application import sentiment_model
        sentences, labels, vectorizer, model = sentiment_model.create_model()

        # Vectorize the input text
        text_vector = vectorizer.transform([text])
        
        # Get the prediction (0 = negative, 1 = positive)
        prediction = model.predict(text_vector)[0]
        
        # Get confidence scores (probabilities of each class)
        probabilities = model.predict_proba(text_vector)[0]
        
        # Prepare the response
        result = {
            'status': 'success',
            'input': text,
            'result': {
                'sentiment': 'positive' if prediction == 1 else 'negative',
                'confidence': float(probabilities[prediction]),
                'probabilities': {
                    'positive': float(probabilities[1]),
                    'negative': float(probabilities[0])
                }
            },
            'model_info': {
                'name': 'Sentiment Analysis Model',
                'version': '1.0',
                'type': 'logistic_regression'
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.app.route('/api/train-poisoned-model', methods=['POST'])
def train_poisoned_model():
    """
    Trains a sentiment analysis model using existing comments data
    and additional user-provided comments (data poisoning attack).
    """
    try:
        # Get user comments from the request
        data = request.get_json()
        user_comments = data.get('comments', [])
        
        # Validate user input
        if not isinstance(user_comments, list):
            return jsonify({'error': 'Comments must be a list of objects'}), 400
            
        for comment in user_comments:
            if not isinstance(comment, dict) or 'text' not in comment or 'sentiment' not in comment:
                return jsonify({'error': 'Each comment must have text and sentiment properties'}), 400
                
            if comment['sentiment'] not in ['positive', 'negative']:
                return jsonify({'error': 'Sentiment must be either "positive" or "negative"'}), 400
        
        model_data=data_poisoning.create_new_model_with_poisoned_data(user_comments)
        
        return jsonify(model_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.app.route('/api/test-poisoned-model', methods=['POST'])
def test_poisoned_model():
    """
    Test the poisoned model with a new text input
    """
    try:
        # Get the test text and model parameters
        data = request.get_json()
        text = data.get('text', '')
        weights = data.get('weights', {})
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        if not weights:
            return jsonify({'error': 'No model weights provided'}), 400
        
        sentiment, confidence, score, probability=data_poisoning.test_model(text, weights)
        return jsonify({
            'sentiment': sentiment,
            'confidence': float(confidence),
            'score': float(score),
            'probability': float(probability)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@application.app.route("/api/catering-rag/reset", methods=["POST"])
def api_catering_rag_reset():
    from application.vulnerabilities import catering_rag_lab as catering_rag_lab

    catering_rag_lab.reset_corpus()
    return jsonify({"ok": True})


@application.app.route("/api/catering-rag/upload-doc", methods=["POST"])
def api_catering_rag_upload_doc():
    from application.vulnerabilities import catering_rag_lab as catering_rag_lab

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    allowed = {".txt", ".md", ".csv", ".json", ".log"}
    if ext and ext not in allowed:
        return jsonify({"error": f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(allowed))}"}), 400

    try:
        raw = file.read()
        text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": f"Could not read uploaded file: {e}"}), 400

    trusted = str(request.form.get("trusted", "")).lower() in ("1", "true", "yes", "on")
    if not text.strip():
        return jsonify({"error": "Uploaded file is empty"}), 400

    try:
        out = catering_rag_lab.ingest_custom_document(filename, text, trusted=trusted)
        return jsonify(out)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@application.app.route("/api/catering-rag/query", methods=["POST"])
def api_catering_rag_query():
    from application.vulnerabilities import catering_rag_lab as catering_rag_lab

    data = request.get_json(silent=True) or {}
    q = (data.get("query") or data.get("q") or "").strip()
    if not q:
        return jsonify({"error": "query required"}), 400
    hardened = bool(data.get("hardened"))
    preferred = (data.get("provider") or "auto").strip().lower()
    api_token = get_openai_api_key(session)
    provider = resolve_provider(preferred=preferred, has_openai_key=bool(api_token))
    model_name = data.get("model") or (OLLAMA_MODEL if provider == "ollama" else None)
    out = catering_rag_lab.answer_catering_query(
        q,
        hardened=hardened,
        model_name=model_name,
        api_key=(api_token if provider == "openai" else None),
    )
    out["model_type"] = "ollama" if provider == "ollama" else api_response_model_type()
    out["provider"] = provider
    return jsonify(out)


@application.app.route("/api/catering-sql/chat", methods=["POST"])
def api_catering_sql_chat():
    from application.vulnerabilities.catering_sql_tool_lab import run_catering_sql_chat

    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"error": "message required"}), 400
    try:
        level = int(data.get("level", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "level must be an integer 0-4"}), 400
    hardened = bool(data.get("hardened"))
    attacker = (session.get("username") or data.get("attacker_username") or "alice").lower()
    preferred = (data.get("provider") or "auto").strip().lower()
    api_token = get_openai_api_key(session)
    provider = resolve_provider(preferred=preferred, has_openai_key=bool(api_token))
    model_name = data.get("model") or (OLLAMA_MODEL if provider == "ollama" else None)
    history = data.get("history")
    if history is not None and not isinstance(history, list):
        return jsonify({"error": "history must be a list of {role, content} objects"}), 400
    try:
        out = run_catering_sql_chat(
            msg,
            level=level,
            hardened=hardened,
            attacker_username=attacker,
            model_name=model_name,
            api_key=(api_token if provider == "openai" else None),
            history=history if isinstance(history, list) else None,
        )
        out["model_type"] = "ollama" if provider == "ollama" else api_response_model_type()
        out["provider"] = provider
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@application.app.route("/promotion-photo")
def promotion_photo():
    return render_template("promotion_photo.html")


@application.app.route("/promotion-photo-claim")
def promotion_photo_claim_page():
    return redirect(url_for("promotion_photo"), code=302)


@application.app.route("/api/promotion-photo/claim", methods=["POST"])
def api_promotion_photo_claim():
    from application.vulnerabilities.promotion_indirect_injection import process_promotion_photo

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(path)
    hardened = str(request.form.get("hardened", "")).lower() in ("1", "true", "yes", "on")
    preferred = (request.form.get("provider") or "auto").strip().lower()
    api_token = get_openai_api_key(session)
    provider = resolve_provider(preferred=preferred, has_openai_key=bool(api_token))
    try:
        out = process_promotion_photo(
            path,
            hardened=hardened,
            model_name=(OLLAMA_MODEL if provider == "ollama" else None),
            api_key=(api_token if provider == "openai" else None),
        )
        out["model_type"] = "ollama" if provider == "ollama" else api_response_model_type()
        out["provider"] = provider
        return jsonify(out)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


@application.app.route("/customer-support-safety")
def customer_support_safety_page():
    from application.vulnerabilities.toxicity_support_lab import ONBOARDING_ASSISTANT_PRIMER

    return render_template(
        "customer_support_safety.html",
        support_onboarding_assistant=ONBOARDING_ASSISTANT_PRIMER,
    )


@application.app.route("/api/customer-support-safety/chat", methods=["POST"])
def api_customer_support_safety_chat():
    from application.vulnerabilities.toxicity_support_lab import chat_support_lab

    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"error": "message required"}), 400
    guarded = bool(data.get("guarded"))
    history = data.get("history")
    if history is not None and not isinstance(history, list):
        return jsonify({"error": "history must be a list of {role, content} objects"}), 400
    preferred = (data.get("provider") or "auto").strip().lower()
    api_token = get_openai_api_key(session)
    provider = resolve_provider(preferred=preferred, has_openai_key=bool(api_token))
    model_name = data.get("model") or (OLLAMA_MODEL if provider == "ollama" else None)
    out = chat_support_lab(
        msg,
        guarded=guarded,
        model_name=model_name,
        api_key=(api_token if provider == "openai" else None),
        history=history,
    )
    out["model_type"] = "ollama" if provider == "ollama" else api_response_model_type()
    out["provider"] = provider
    return jsonify(out)


# Define API endpoint for the LLM DoS simulation demonstration
@application.app.route('/api/llm-query', methods=['POST'])
def llm_query():
   
    """
    API endpoint for querying a simulated model without rate limiting.
    This endpoint is intentionally vulnerable to DoS attacks by having no rate limits
    and demonstrates service degradation under heavy load.
    """
    try:
        # Get the prompt from the request
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400

        prompt = data.get('prompt')


        # Track request timestamps in a global variable to simulate server load
        if not hasattr(application.app, 'request_history'):
            application.app.request_history = []

        # Add current timestamp to request history
        current_time = time.time()
        application.app.request_history.append(current_time)

        # Clean up old requests (older than 60 seconds)
        application.app.request_history = [t for t in application.app.request_history if current_time - t < 60]

        # Calculate recent request count and rate
        request_count = len(application.app.request_history)

        # Simulate exponential degradation based on request volume
        # This mimics how real systems behave under heavy load
        base_delay = 0.2  # Base processing time

        if request_count > 5:
            # Add delay that grows exponentially with request volume
            # Formula: delay = base_delay * e^(request_count/scaling_factor)
            scaling_factor = 500  # Controls how quickly delay increases
            load_factor = math.exp(request_count / scaling_factor)

            # Add random variance for realism (±20%)
            variance = 0.2 * random.uniform(-1, 1)

            # Calculate total delay
            processing_delay = base_delay * load_factor * (1 + variance)

            # Cap at a reasonable maximum to prevent extremely long waits
            processing_delay = min(processing_delay, 8.0)

            # Add simulated processing delay
            time.sleep(processing_delay)

            # Simulate occasional server errors under heavy load
            error_probability = min(0.01 * (request_count / 20), 0.25)  # Max 25% error rate

            if random.random() < error_probability:
                error_types = [
                    (503, "Service temporarily unavailable due to high load"),
                    (429, "Too many requests, please try again later"),
                    (500, "Internal server error - LLM worker process crashed"),
                    (504, "Gateway timeout - LLM inference took too long")
                ]
                status_code, error_message = random.choice(error_types)
                return jsonify({'error': error_message}), status_code
        else:
            # Normal processing for low request volumes
            processing_delay = base_delay + random.uniform(0, 0.3)
            time.sleep(processing_delay)

        # For demo purposes, simulate LLM response
        pizza_terms = ["pizza", "dough", "cheese", "tomato", "toppings", "oven", "slice", "crust"]
        has_pizza_term = any(term in prompt.lower() for term in pizza_terms)

        # Simulate how response quality might degrade under load
        # Generate different response quality based on server load
        if request_count > 50:
            # Very degraded response (low quality/truncated)
            responses = [
                "Sorry, I can only provide limited responses due to high system load.",
                "System under heavy load. Please try again later.",
                "High server utilization detected. Response shortened to conserve resources.",
                "Abbreviated response due to resource constraints: Pizza shop serves various pizza types.",
                "*Model running in emergency low-resource mode*"
            ]
            response = random.choice(responses)
        elif request_count > 30:
            # Slightly degraded response (shorter, less detailed)
            if "introduce yourself" in prompt.lower() or "who are you" in prompt.lower():
                response = "I'm an AI assistant for PwnzzAI Shop. Currently operating in reduced capacity mode."
            elif "help" in prompt.lower() or "assist" in prompt.lower():
                response = "I can answer basic questions about our pizza menu. What would you like to know?"
            elif "menu" in prompt.lower() or "pizzas" in prompt.lower():
                response = "Our menu: Margherita, Pepperoni, Veggie, Hawaiian, and BBQ Chicken. Note: System under load, providing brief response."
            elif has_pizza_term:
                response = f"We offer quality pizzas with premium ingredients. {random.choice(pizza_terms).capitalize()} is important to our process."
            else:
                response = "How can I assist with your pizza order? (Note: System experiencing high demand)"
        else:
            # Normal high-quality response
            if "introduce yourself" in prompt.lower() or "who are you" in prompt.lower():
                response = "I'm a simulated LLM API for the Pizza Paradise demo application. I'm designed to demonstrate Denial of Service vulnerabilities in LLM systems."
            elif "help" in prompt.lower() or "assist" in prompt.lower():
                response = "I can assist with pizza ordering, provide information about our menu, or answer general questions about the Pizza Paradise shop. How can I help you today?"
            elif "menu" in prompt.lower() or "pizzas" in prompt.lower():
                response = "Our menu includes Margherita, Pepperoni, Veggie Supreme, Hawaiian, and BBQ Chicken pizzas. Each is made with fresh ingredients and our signature dough."
            elif has_pizza_term:
                response = f"Our pizzas are made with the finest ingredients, including homemade dough, premium cheese, and fresh toppings. The {random.choice(pizza_terms)} is particularly important to our quality standards."
            else:
                response = "Thank you for your message. Is there anything specific about our pizza offerings you'd like to know? Our chefs are experts in traditional and innovative pizza recipes."

        # Add a random suffix to make each response unique
        # This helps demonstrate token usage in a DoS attack
        if request_count <= 30:  # Only add suffix for normal responses
            random_suffix = f" Our priority is customer satisfaction and quality ingredients. Order reference: #{random.randint(10000, 99999)}."
            response += random_suffix

        # Calculate token usage (approx.) for demonstration purposes
        tokens_used = len(response.split()) * 1.3  # Rough approximation: ~1.3 tokens per word

        # Set unrealistically high token limits (intentionally vulnerable)
        max_tokens_per_minute = 1000000  # Set to extremely high value to demonstrate no rate limiting
        max_tokens_per_day = 1000000000  # Unrealistically high - no effective limit

        # Calculate approximate response time based on load (for display purposes)
        display_processing_time = processing_delay * (0.7 + 0.3 * random.random())  # Add some variance

        # Return response with server load metrics
        return jsonify({
            'response': response,
            'tokens_used': int(tokens_used),
            'model': 'gpt2-simulated',
            'processing_time': display_processing_time,  # Simulated processing time in seconds
            'server_load': {
                'requests_last_minute': request_count,
                'load_factor': min(request_count / 30, 1.0),  # 0.0-1.0 scale representing load
            },
            'rate_limits': {
                'max_tokens_per_minute': max_tokens_per_minute,  # Intentionally high/unlimited
                'max_tokens_per_day': max_tokens_per_day,        # Intentionally high/unlimited
                'remaining_tokens': max_tokens_per_minute - 100   # Always shows plenty remaining
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.app.route('/chat-with-openai-dos', methods=['POST'])
def chat_with_openai_dos():
    """API endpoint for the OpenAI-based DoS attack demo - simple chat functionality"""
    try:
        # Get data from request
        data = request.get_json()
        message = data.get('message', '')
        
        # Use OpenAI API key from session instead of user input
        openai_api_key = get_openai_api_key(session)
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        if not openai_api_key:
            return jsonify({'error': llm_ui_snapshot()['missing_key_error']}), 400
        
        # Import the OpenAI DoS module
        from application.vulnerabilities.openai_dos import chat_with_openai
        
        # Call the simple chat function
        response = chat_with_openai(message, openai_api_key)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.app.route('/chat-with-openai-plugin-direct-prompt', methods=['POST'])
def chat_with_openai_plugin_direct_prompt():
    """
    API endpoint for the OpenAI Pizza Assistant plugin.
    This demonstrates direct prompt injection against GPT models.
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        level = data.get('level', '1')
        escalation_stage = data.get("escalation_stage")
        history = data.get("history")

        # Use OpenAI API key from session instead of user input
        api_token = get_openai_api_key(session)

        if not message:
            return jsonify({'error': 'No message provided'}), 400

        if not api_token:
            return jsonify({'error': llm_ui_snapshot()['missing_key_error']}), 400

        if escalation_stage is not None:
            from application.vulnerabilities.direct_prompt_escalation import run_escalation_openai

            try:
                stage_i = int(escalation_stage)
            except (TypeError, ValueError):
                return jsonify({'error': 'escalation_stage must be an integer 0-9'}), 400
            response, esc_meta = run_escalation_openai(
                message, stage_i, history=history, api_token=api_token
            )
            return jsonify({"response": response, "escalation_meta": esc_meta})

        from application.vulnerabilities.openai_direct_prompt_injection import chat_with_openai_direct_prompt_injection

        response = chat_with_openai_direct_prompt_injection(message, api_token, level)

        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@application.app.route('/chat-with-ollama-dos', methods=['POST'])
def chat_with_ollama_dos():
    """API endpoint for the Ollama-based DoS attack demo - simple chat functionality"""
    try:
        # Get data from request
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Import the Ollama DoS module
        from application.vulnerabilities.ollama_dos import chat_with_llm
        
        # Call the chat function (no API token needed for local Ollama)
        response = chat_with_llm(message)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@application.app.route('/direct-prompt-injection')
def direct_prompt_injection():
    return render_template('direct_prompt_injection.html', dpi_mode='baseline')

@application.app.route('/direct-prompt-injection/guardrail-ladder')
def direct_prompt_injection_guardrail():
    return render_template('direct_prompt_injection.html', dpi_mode='escalation')

@application.app.route('/indirect-prompt-injection')
def indirect_prompt_injection():
    return render_template('indirect_prompt_injection.html')

@application.app.route("/upload-qr", methods=["POST"])
def upload_qr():
    print("Upload QR endpoint called")  # Debug log
    
    if "file" not in request.files:
        print("No file in request")  # Debug log
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    print(f"File received: {file.filename}")  # Debug log
    
    if file.filename == "":
        print("Empty filename")  # Debug log
        return jsonify({"error": "Empty filename"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(file_path)
    print(f"File saved to: {file_path}")  # Debug log

    qr_text = decode_qr(file_path)
    print(f"QR decoded: {qr_text}")  # Debug log
    
    if not qr_text:
        return jsonify({"error": "No QR code detected"}), 400

    model_output = chat_with_ollama_indirect(qr_text)
    print(f"Model output: {model_output}")  # Debug log
    
    return jsonify({"response": model_output, "qr_text": qr_text})


@application.app.route('/upload-qr-openai', methods=['POST'])
def upload_qr_openai():
    """Handles QR code uploads for the OpenAI model."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get the OpenAI API key from the user's session
    api_token = get_openai_api_key(session)
    if not api_token:
        return jsonify({'error': llm_ui_snapshot()['session_key_missing_short']}), 400

    # Get the injection level from the form data sent by the JavaScript
    level = request.form.get('level', '1')

    if file:
        # Securely save the file to a temporary location
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Decode the QR code text from the image file
        qr_text = decode_qr(file_path)

        # The file is no longer needed, so we remove it
        os.remove(file_path)

        if not qr_text:
            return jsonify({'error': 'Failed to decode QR code from the image.'}), 400

        # Call your function to interact with the OpenAI model
        response = chat_with_openai_indirect_prompt_injection(qr_text, api_token, level)

        return jsonify({'response': response, 'qr_text': qr_text})
            
    return jsonify({'error': 'An unknown error occurred'}), 500



if __name__ == '__main__':
    application.app.run(debug=True)