import os

TWITCH_CLIENT_ID: str = os.getenv("TWITCH_CLIENT_ID", "uimyu5s6ecbzal85atzoyz1n6q4uff")
TWITCH_REDIRECT_PORT = 13486
TWITCH_API = "https://api.twitch.tv/helix"
TWITCH_URL = "https://www.twitch.tv"
TWITCH_AUTH_REDIRECT_HTML = """
<!DOCTYPE html>
<html>
<body style="background: #0e0e10; color: #efeff1; text-align: center; padding-top: 50px; font-family: sans-serif;">
    <h2>Connecting to Streamify...</h2>
    <script>
        if (window.location.hash) {
            window.location.href = '/callback?' + window.location.hash.substring(1);
        } else {
            document.body.innerHTML = '<h2>Login canceled or failed.</h2>';
        }
    </script>
</body>
</html>
"""

TWITCH_AUTH_SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<body style="background: #0e0e10; color: #efeff1; text-align: center; padding-top: 50px; font-family: sans-serif;">
    <h2 style="color: #9146ff;">Authorization Successful!</h2>
    <p>You can close this browser tab and return to Streamify.</p>
</body>
</html>
"""
