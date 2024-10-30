from app import create_app, db
from app.models import Staff
from app.routes import init_routes
from datetime import datetime

app = create_app()
#init_routes(app)

if __name__ == '__main__':
    app.run(debug=True) 