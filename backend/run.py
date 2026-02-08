import os
from app import app

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host="0.0.0.0", port=port)
