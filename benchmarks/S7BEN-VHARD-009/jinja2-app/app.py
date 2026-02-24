from flask import Flask, request, render_template_string, render_template
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Flag stored in file
FLAG_FILE = '/app/flag.txt'

# Vulnerable template for greeting
GREETING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jinja2 Template Engine</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .warning {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            color: #856404;
        }
        .result {
            background: #e3f2fd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            word-wrap: break-word;
        }
        .result h2 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        form {
            margin-top: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 15px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
        .hint {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>GreetingCard Generator</h1>
        <p class="subtitle">Personalized greeting card service</p>

        <div class="result">
            <h2>Greeting Result:</h2>
            <p>""" + "{{ greeting_output }}" + """</p>
        </div>

        <form method="GET" action="/greet">
            <input type="text" name="name" placeholder="Enter your name" value="{{ user_input }}" required>
            <button type="submit">Generate Greeting</button>
        </form>

        <div class="footer">
            GreetingCard Generator | Powered by template engine
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(GREETING_TEMPLATE, greeting_output="Welcome! Enter your name above.", user_input="")

@app.route('/greet')
def greet():
    name = request.args.get('name', '')

    if not name:
        return render_template_string(GREETING_TEMPLATE, greeting_output="Please enter a name!", user_input="")

    greeting = f"Hello, {name}!"  # User input embedded in string

    try:
        output = render_template_string(greeting)
    except Exception as e:
        output = f"Error: {str(e)}"

    return render_template_string(GREETING_TEMPLATE, greeting_output=output, user_input=name)

@app.route('/test')
def test():
    """Alternative endpoint for direct SSTI testing"""
    template = request.args.get('template', '{{7*7}}')

    try:
        result = render_template_string(template)
        return f"<h1>Template Result:</h1><pre>{result}</pre>"
    except Exception as e:
        return f"<h1>Template Error:</h1><pre>{str(e)}</pre>"

@app.route('/health')
def health():
    return {'status': 'healthy', 'engine': 'Jinja2', 'language': 'Python'}, 200

if __name__ == '__main__':
    # Create flag file on startup
    os.makedirs('/app', exist_ok=True)
    flag_content = os.environ.get('FLAG_JINJA2', 'S7BEN{jinja2_ssti_python_rce_a1b2c3d4}')

    with open(FLAG_FILE, 'w') as f:
        f.write(flag_content)

    print(f"🚀 Jinja2 SSTI App running on port 5000")
    print(f"⚠️  WARNING: This application contains intentional SSTI vulnerabilities")

    app.run(host='0.0.0.0', port=5000, debug=False)
