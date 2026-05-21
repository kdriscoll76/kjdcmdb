import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-change-me')

# Connect to MongoDB
client = MongoClient(os.getenv('DATABASE_URL'), serverSelectionTimeoutMS=5000)
db = client['cmdb_db']
inventory = db['inventory']

def check_db_connection():
    """Verify MongoDB connection. Returns True if successful."""
    try:
        client.admin.command('ping')
        return True
    except Exception as e:
        app.logger.error(f"MongoDB connection failed: {e}")
        return False

@app.before_request
def before_request():
    """Check DB connection before each request."""
    if not check_db_connection():
        flash('Database connection failed', 'danger')

@app.route('/')
def index():
    # Get all items (include _id for delete functionality)
    items = list(inventory.find({}, {'host': 1, 'ip': 1, 'os': 1, 'status': 1, 'comment': 1}))
    return render_template('index.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        try:
            data = request.form
            # Validate required fields
            if not all([data.get('host'), data.get('ip'), data.get('status')]):
                flash('All required fields must be filled', 'warning')
                return redirect(url_for('index'))
            
            inventory.insert_one({
                'host': data['host'],
                'ip': data['ip'],
                'status': data['status'],
                'os': data.get('os', ''),
                'comment': data.get('comment', '')
            })
            flash('Asset added successfully!', 'success')
        except Exception as e:
            app.logger.error(f"Error adding asset: {e}")
            flash(f'Error adding asset: {str(e)}', 'danger')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/delete/<id>', methods=['POST'])
def delete_item(id):
    try:
        # Convert string id to ObjectId for MongoDB
        result = inventory.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            flash('Asset deleted successfully!', 'success')
        else:
            flash('Asset not found', 'warning')
    except Exception as e:
        app.logger.error(f"Error deleting asset: {e}")
        flash(f'Error deleting asset: {str(e)}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
