from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_oauth(app):
    from src.shared.config import settings

    oauth.init_app(app)

    if settings.GOOGLE_CLIENT_ID:
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url=(
                "https://accounts.google.com/.well-known/openid-configuration"
            ),
            client_kwargs={"scope": "openid email profile"},
        )
