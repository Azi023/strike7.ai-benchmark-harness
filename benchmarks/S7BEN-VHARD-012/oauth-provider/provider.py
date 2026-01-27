#!/usr/bin/env python3
"""
Mock OAuth Provider for S7BEN-VHARD-012
Simulates Google OAuth flow
"""

from flask import Flask, request, redirect, render_template_string
import secrets

app = Flask(__name__)

@app.route('/authorize')
def authorize():
    """OAuth authorization endpoint"""
    state = request.args.get('state', '')
    redirect_uri = request.args.get('redirect_uri', '')

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock Google OAuth</title>
        <style>
            body {{ font-family: Arial; max-width: 500px; margin: 100px auto;
                   padding: 30px; text-align: center; }}
            .oauth-box {{ border: 1px solid #ddd; padding: 30px; border-radius: 8px; }}
            button {{ background: #4285f4; color: white; padding: 12px 30px;
                     border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
        </style>
    </head>
    <body>
        <div class="oauth-box">
            <h2>🔐 Google OAuth</h2>
            <p>Authorize application to access your account?</p>
            <p><small>State: {state}</small></p>
            <form action="/authorize/grant" method="POST">
                <input type="hidden" name="state" value="{state}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <button type="submit">✓ Allow</button>
            </form>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/authorize/grant', methods=['POST'])
def grant():
    """Grant authorization and redirect back"""
    state = request.form.get('state', '')
    redirect_uri = request.form.get('redirect_uri', '')

    # Generate authorization code
    code = secrets.token_hex(16)

    # Redirect back to app with code and state
    callback_url = f"{redirect_uri}?code={code}&state={state}"
    return redirect(callback_url)

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    print("[+] Mock OAuth Provider starting on http://0.0.0.0:8092")
    app.run(host='0.0.0.0', port=8092, debug=False)
