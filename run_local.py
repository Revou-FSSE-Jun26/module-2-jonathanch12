"""Local development entrypoint that serves the app over HTTPS using mkcert.

Why this exists
---------------
The app issues its JWT cookies with ``SameSite=None`` and (by default)
``Secure=True``. Browsers reject a ``SameSite=None`` cookie that is not also
``Secure``, so cross-origin browser testing against the API needs to happen
over HTTPS even locally. mkcert gives us a locally-trusted certificate so the
browser accepts ``https://127.0.0.1:5000`` without warnings.

This is a LOCAL DEVELOPMENT tool only. It is never used in production: on a
platform like Vercel, HTTPS is terminated at the edge and the WSGI ``app``
object is imported directly, so the dev server below is not involved.

One-time setup (machine level, not in the venv)
-----------------------------------------------
    winget install FiloSottile.mkcert   # or download the release binary
    mkcert -install                      # trust the local CA
    cd certs
    mkcert localhost 127.0.0.1           # generates the cert + key in certs/

Then, from the project root:
    python run_local.py

Plain HTTP still works the old way with ``flask run --debug`` if you ever want
it. This script only adds the HTTPS path.
"""

import glob
import os
import sys

from app import create_app

# Directory where the mkcert-generated certificate and key are expected.
CERTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")


def _find_cert_pair():
    """Locate the mkcert cert and key files inside ``certs/``.

    mkcert names its output after the hosts you pass, e.g.
    ``localhost+1.pem`` (certificate) and ``localhost+1-key.pem`` (key). We
    glob for that pattern so the exact host count does not matter: the key is
    whichever file ends in ``-key.pem`` and the cert is its ``.pem`` sibling.

    Returns a ``(cert_path, key_path)`` tuple, or ``None`` if no pair is found.
    """
    key_matches = glob.glob(os.path.join(CERTS_DIR, "*-key.pem"))
    for key_path in key_matches:
        cert_path = key_path.replace("-key.pem", ".pem")
        if os.path.exists(cert_path):
            return cert_path, key_path
    return None


def main():
    cert_pair = _find_cert_pair()

    if cert_pair is None:
        sys.stderr.write(
            "\n[run_local] No mkcert certificate found in 'certs/'.\n"
            "Generate one first (one-time setup):\n\n"
            "    winget install FiloSottile.mkcert   # if mkcert is not installed\n"
            "    mkcert -install\n"
            "    cd certs\n"
            "    mkcert localhost 127.0.0.1\n\n"
            "Then run 'python run_local.py' again.\n"
            "To run plain HTTP instead, use: flask run --debug\n\n"
        )
        sys.exit(1)

    cert_path, key_path = cert_pair
    print(f"[run_local] Serving HTTPS with cert: {os.path.basename(cert_path)}")
    print("[run_local] App available at https://127.0.0.1:5000/")

    app = create_app()
    # ssl_context as a (cert, key) tuple tells Werkzeug's dev server to serve
    # TLS using those files. host/port mirror the Flask dev defaults.
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        ssl_context=(cert_path, key_path),
    )


if __name__ == "__main__":
    main()
