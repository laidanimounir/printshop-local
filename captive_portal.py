from flask import redirect, request, render_template
import config


def register_captive_portal_routes(app):
    @app.route('/hotspot-detect.html')
    @app.route('/library/test/success.html')
    def apple_captive():
        return redirect(_get_upload_url(), code=302)

    @app.route('/generate_204')
    @app.route('/mobile/status.php')
    @app.route('/check_network_status')
    def android_captive():
        return '', 204

    @app.route('/ncsi.txt')
    @app.route('/connecttest.txt')
    def windows_captive():
        return 'Microsoft NCSI', 200, {'Content-Type': 'text/plain'}

    @app.route('/success.html')
    def generic_captive():
        return redirect(_get_upload_url(), code=302)

    @app.route('/captive')
    def captive_redirect():
        return redirect(_get_upload_url(), code=302)

    @app.before_request
    def captive_portal_intercept():
        if request.host and '192.168.1' not in request.host and request.host != 'localhost:5000':
            return None
        return None


def _get_upload_url():
    return f"http://192.168.1.1:{config.SERVER_PORT}/upload/PC1"
