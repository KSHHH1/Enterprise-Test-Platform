import os
from test_platform.app import create_app, db
from flask_migrate import Migrate

from test_platform.models import Device

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
print('Models detected:', db.Model.__subclasses__())

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Device=Device) 