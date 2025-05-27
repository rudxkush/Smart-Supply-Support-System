from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, make_response
import sqlite3
import os
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'smart_supply_support_system'

# Database setup
DATABASE_PATH = 'database/4s_database.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    
    # Create Requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        auto_tag TEXT NOT NULL,
        status TEXT NOT NULL,
        submitted_time TIMESTAMP NOT NULL,
        fulfilled_time TIMESTAMP,
        vendor_name TEXT,
        solution TEXT,
        estimated_delivery TEXT,
        forwarded_to_production INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create Status_Logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS status_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (request_id) REFERENCES requests (id)
    )
    ''')
    
    # Create Inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE NOT NULL,
        quantity INTEGER NOT NULL,
        status TEXT NOT NULL
    )
    ''')
    
    # Insert sample inventory items if they don't exist
    sample_inventory = [
        ('Product A', 50, 'In Stock'),
        ('Product B', 25, 'In Stock'),
        ('Product C', 0, 'Out of Stock'),
        ('Product D', 10, 'Low Stock')
    ]
    
    for item in sample_inventory:
        try:
            cursor.execute('INSERT INTO inventory (item_name, quantity, status) VALUES (?, ?, ?)', item)
        except sqlite3.IntegrityError:
            # Item already exists
            pass
    
    # Insert default users if they don't exist
    default_users = [
        ('sales', generate_password_hash('sales123', method='pbkdf2:sha256'), 'Sales Executive'),
        ('warehouse', generate_password_hash('warehouse123', method='pbkdf2:sha256'), 'Warehouse Officer'),
        ('production', generate_password_hash('production123', method='pbkdf2:sha256'), 'Production Planner'),
        ('support', generate_password_hash('support123', method='pbkdf2:sha256'), 'Support Agent')
    ]
    
    for user in default_users:
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', user)
        except sqlite3.IntegrityError:
            # User already exists
            pass
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def auto_tag_request(message, role):
    """Auto-tag a request based on message content and user role"""
    message = message.lower()
    
    # Sales Executive tags
    if role == 'Sales Executive':
        if 'urgent' in message or 'immediate' in message:
            return 'Urgent Delivery'
        elif 'stock' in message or 'inventory' in message or 'available' in message:
            return 'Stock Check'
        else:
            return 'Sales Request'
    
    # Warehouse Officer tags
    elif role == 'Warehouse Officer':
        if 'confirm' in message or 'availability' in message:
            return 'Stock Confirmation'
        elif 'ship' in message or 'deliver' in message:
            return 'Shipment'
        else:
            return 'Warehouse Request'
    
    # Production Planner tags
    elif role == 'Production Planner':
        if 'delay' in message:
            return 'Delay Report'
        elif 'schedule' in message:
            return 'Production Schedule'
        else:
            return 'Production Request'
    
    # Support Agent tags
    elif role == 'Support Agent':
        if 'complaint' in message:
            return 'Customer Complaint'
        elif 'service' in message:
            return 'Service Request'
        else:
            return 'Support Request'
    
    return 'General Request'

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session data
    session.clear()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            # Store user info in session
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            
            # Set a cookie to indicate successful login
            response = redirect(url_for('dashboard', role=user['role'], user_id=user['id']))
            response.set_cookie('logged_in', 'true', max_age=3600)  # 1 hour expiry
            return response
        else:
            flash('Invalid username or password')
    
    # Set cache control headers to prevent caching of login page
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/dashboard/<role>/<int:user_id>')
def dashboard(role, user_id):
    # Check if user is logged in
    if not session.get('logged_in'):
        flash('Please log in to access this page')
        return redirect(url_for('login'))
    
    # Check if the user is accessing their own dashboard
    if session.get('user_id') != user_id or session.get('role') != role:
        flash('Unauthorized access')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    # Get requests relevant to the user's role
    if role in ['Sales Executive', 'Warehouse Officer', 'Production Planner', 'Support Agent']:
        # For regular users, show their own requests
        my_requests = conn.execute(
            'SELECT * FROM requests WHERE user_id = ? ORDER BY submitted_time DESC', 
            (user_id,)
        ).fetchall()
        
        # For Warehouse Officer, also show stock check requests, in-transit items, and stock updates
        if role == 'Warehouse Officer':
            pending_requests = conn.execute(
                'SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id '
                'WHERE (r.auto_tag IN ("Stock Check", "Urgent Delivery", "Stock Update") '
                'AND r.status IN ("Submitted", "In Transit", "Notification")) '
                'ORDER BY r.submitted_time ASC'
            ).fetchall()
        # For Production Planner, show requests forwarded from sales/warehouse
        elif role == 'Production Planner':
            pending_requests = conn.execute(
                'SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id '
                'WHERE r.forwarded_to_production = 1 AND r.status = "Forwarded to Production" '
                'ORDER BY r.submitted_time ASC'
            ).fetchall()
        else:
            pending_requests = []
            
        # Get inventory status for display
        inventory = conn.execute('SELECT * FROM inventory ORDER BY item_name').fetchall()
        
        # Get notifications count for the navbar
        notifications_count = 0
        if role == 'Warehouse Officer':
            notifications = conn.execute(
                'SELECT COUNT(*) as count FROM requests '
                'WHERE user_id = ? AND auto_tag = "Stock Update" AND status = "Notification"',
                (user_id,)
            ).fetchone()
            if notifications:
                notifications_count = notifications['count']
    else:
        # Invalid role
        conn.close()
        return redirect(url_for('login'))
    
    conn.close()
    return render_template('dashboard.html', role=role, user_id=user_id, 
                          my_requests=my_requests, pending_requests=pending_requests,
                          inventory=inventory, notifications_count=notifications_count)

@app.route('/submit_request/<role>/<int:user_id>', methods=['GET', 'POST'])
def submit_request(role, user_id):
    # Check if user is logged in
    if not session.get('logged_in'):
        flash('Please log in to access this page')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form['message']
        # Use the tag selected from the dropdown instead of auto-tagging
        selected_tag = request.form['tag']
        status = 'Submitted'
        submitted_time = datetime.datetime.now()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        estimated_delivery = None
        forwarded_to_production = 0
        
        # For Sales Executive requests, check inventory automatically
        if role == 'Sales Executive':
            # Get quantity from form
            quantity = request.form.get('quantity', '1')
            try:
                quantity = int(quantity)
            except ValueError:
                quantity = 1
                
            # Check if this is a new product request
            product_name = request.form.get('product', '')
            if product_name == 'new_product':
                # Get new product name
                new_product_name = request.form.get('new_product_name', '')
                if new_product_name:
                    product_name = new_product_name
                    # Add new product to inventory as Out of Stock
                    try:
                        cursor.execute(
                            'INSERT INTO inventory (item_name, quantity, status) VALUES (?, ?, ?)',
                            (new_product_name, 0, 'Out of Stock')
                        )
                        conn.commit()
                        # Forward to production automatically
                        status = 'Forwarded to Production'
                        forwarded_to_production = 1
                        estimated_delivery = "New product awaiting production"
                        message += f"\n\nRequested NEW product: {new_product_name}, Quantity: {quantity}"
                    except sqlite3.Error as e:
                        # Handle database error
                        flash(f"Error adding new product: {e}")
            
            # If no product selected or found, try to extract from message
            if not product_name or product_name == '':
                for word in message.split():
                    # Check if this word matches any product in inventory
                    product = conn.execute('SELECT * FROM inventory WHERE item_name LIKE ?', 
                                          ('%' + word + '%',)).fetchone()
                    if product:
                        product_name = product['item_name']
                        break
            
            # Add product name and quantity to message if it was selected from dropdown
            if product_name and product_name not in message and product_name != 'new_product':
                message += f"\n\nRequested product: {product_name}, Quantity: {quantity}"
            
            if product_name and product_name != 'new_product' and product_name != '':
                # Check if product is in stock with sufficient quantity
                inventory_item = conn.execute('SELECT * FROM inventory WHERE item_name = ?', 
                                            (product_name,)).fetchone()
                
                if inventory_item and inventory_item['status'] == 'In Stock' and inventory_item['quantity'] >= quantity:
                    # Product is available in sufficient quantity
                    status = 'In Transit'
                    # Set estimated delivery to 4 days from now
                    delivery_date = datetime.datetime.now() + datetime.timedelta(days=4)
                    estimated_delivery = f"Will arrive by {delivery_date.strftime('%Y-%m-%d')}"
                    
                    # Update inventory quantity
                    cursor.execute(
                        'UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?',
                        (quantity, product_name)
                    )
                    
                    # Check if stock is now low
                    remaining = inventory_item['quantity'] - quantity
                    if remaining <= 10 and remaining > 0:
                        cursor.execute(
                            'UPDATE inventory SET status = ? WHERE item_name = ?',
                            ('Low Stock', product_name)
                        )
                    elif remaining <= 0:
                        cursor.execute(
                            'UPDATE inventory SET status = ?, quantity = 0 WHERE item_name = ?',
                            ('Out of Stock', product_name)
                        )
                        
                elif inventory_item:
                    # Product exists but not enough in stock, forward to production
                    status = 'Forwarded to Production'
                    forwarded_to_production = 1
                    estimated_delivery = "Awaiting production schedule"
        
        # Insert the request with the selected tag and inventory status
        cursor.execute('''
            INSERT INTO requests (user_id, role, message, auto_tag, status, submitted_time, 
                                estimated_delivery, forwarded_to_production)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, role, message, selected_tag, status, submitted_time, 
             estimated_delivery, forwarded_to_production))
        
        request_id = cursor.lastrowid
        
        # Log the status
        cursor.execute('''
            INSERT INTO status_logs (request_id, status, timestamp)
            VALUES (?, ?, ?)
        ''', (request_id, status, submitted_time))
        
        conn.commit()
        conn.close()
        
        flash('Request submitted successfully!')
        return redirect(url_for('dashboard', role=role, user_id=user_id))
    
    # For GET requests, fetch inventory items to display in the form
    conn = get_db_connection()
    inventory_items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    
    return render_template('submit_request.html', role=role, user_id=user_id, inventory_items=inventory_items)

@app.route('/update_request/<int:request_id>', methods=['POST'])
def update_request(request_id):
    new_status = request.form['status']
    timestamp = datetime.datetime.now()
    
    # Get role and user_id from query parameters
    current_user_role = request.args.get('role')
    current_user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current request details
    request_details = conn.execute('SELECT * FROM requests WHERE id = ?', (request_id,)).fetchone()
    
    if not request_details:
        flash('Request not found.')
        conn.close()
        return redirect(url_for('dashboard', role=current_user_role, user_id=current_user_id))
    
    estimated_delivery = request_details['estimated_delivery']
    forwarded_to_production = request_details['forwarded_to_production']
    
    # Handle status updates with specific logic
    if new_status == 'Fulfilled':
        cursor.execute('''
            UPDATE requests SET status = ?, fulfilled_time = ?
            WHERE id = ?
        ''', (new_status, timestamp, request_id))
    elif new_status == 'In Transit':
        # Set estimated delivery to 4 days from now if not already set
        if not estimated_delivery:
            delivery_date = datetime.datetime.now() + datetime.timedelta(days=4)
            estimated_delivery = f"Will arrive by {delivery_date.strftime('%Y-%m-%d')}"
            
        cursor.execute('''
            UPDATE requests SET status = ?, estimated_delivery = ?
            WHERE id = ?
        ''', (new_status, estimated_delivery, request_id))
    elif new_status == 'Forwarded to Production':
        # Mark as forwarded to production
        cursor.execute('''
            UPDATE requests SET status = ?, forwarded_to_production = 1, estimated_delivery = ?
            WHERE id = ?
        ''', (new_status, "Awaiting production schedule", request_id))
    elif new_status == 'Production Complete':
        # When production is complete, update inventory and mark request as ready for shipment
        cursor.execute('''
            UPDATE requests SET status = 'Ready for Shipment', estimated_delivery = ?
            WHERE id = ?
        ''', (f"Ready for shipment on {(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')}", request_id))
        
        # Extract product name and quantity from message
        product_name = None
        quantity = 10  # Default production quantity
        
        # First try to find "Requested product:" in the message
        message_lines = request_details['message'].split('\n')
        for line in message_lines:
            if "Requested product:" in line:
                parts = line.split(',')
                if len(parts) > 0:
                    product_part = parts[0].strip()
                    product_name = product_part.replace("Requested product:", "").strip()
                
                # Try to extract quantity
                if len(parts) > 1 and "Quantity:" in parts[1]:
                    try:
                        qty_str = parts[1].replace("Quantity:", "").strip()
                        quantity = int(qty_str)
                    except ValueError:
                        quantity = 10
                break
        
        # If not found in formatted message, try word matching
        if not product_name:
            for word in request_details['message'].split():
                # Check if this word matches any product in inventory
                product = conn.execute('SELECT * FROM inventory WHERE item_name LIKE ?', 
                                      ('%' + word + '%',)).fetchone()
                if product:
                    product_name = product['item_name']
                    break
                
        if product_name:
            # Update inventory to show item is now in stock with produced quantity
            cursor.execute('''
                UPDATE inventory SET quantity = quantity + ?, status = 'In Stock'
                WHERE item_name = ?
            ''', (quantity, product_name))
    else:
        cursor.execute('''
            UPDATE requests SET status = ?
            WHERE id = ?
        ''', (new_status, request_id))
    
    # Log the status change
    cursor.execute('''
        INSERT INTO status_logs (request_id, status, timestamp)
        VALUES (?, ?, ?)
    ''', (request_id, new_status, timestamp))
    
    conn.commit()
    
    # Get the role of the user who is updating the request
    current_user_role = request.args.get('role')
    current_user_id = request.args.get('user_id')
    
    # If role/user_id not provided in args, get from request data
    if not current_user_role or not current_user_id:
        request_data = conn.execute('SELECT user_id, role FROM requests WHERE id = ?', (request_id,)).fetchone()
        if request_data:
            current_user_role = current_user_role or request_data['role']
            current_user_id = current_user_id or request_data['user_id']
        else:
            current_user_role = current_user_role or 'Warehouse Officer'
            current_user_id = current_user_id or '1'
    
    conn.close()
    
    flash('Request updated successfully!')
    return redirect(url_for('dashboard', role=current_user_role, user_id=current_user_id))

@app.route('/vendor_login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        request_id = request.form['request_id']
        
        conn = get_db_connection()
        request_details = conn.execute(
            'SELECT * FROM requests WHERE id = ? AND auto_tag IN ("Customer Complaint", "Service Request", "Support Request")',
            (request_id,)
        ).fetchone()
        conn.close()
        
        if request_details:
            return redirect(url_for('vendor_update', request_id=request_id))
        else:
            flash('Invalid request ID or not a support request.')
    
    return render_template('vendor_login.html')

@app.route('/vendor_update/<int:request_id>', methods=['GET'])
def vendor_update(request_id):
    conn = get_db_connection()
    request_details = conn.execute('SELECT * FROM requests WHERE id = ?', (request_id,)).fetchone()
    conn.close()
    
    if not request_details:
        flash('Request not found.')
        return redirect(url_for('vendor_login'))
    
    return render_template('vendor_update.html', request_details=request_details)

@app.route('/vendor_update_submit/<int:request_id>', methods=['POST'])
def vendor_update_submit(request_id):
    vendor_name = request.form['vendor_name']
    solution = request.form['solution']
    timestamp = datetime.datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update the request with vendor information and mark as fulfilled
    cursor.execute('''
        UPDATE requests 
        SET status = 'Fulfilled', 
            fulfilled_time = ?,
            vendor_name = ?,
            solution = ?
        WHERE id = ?
    ''', (timestamp, vendor_name, solution, request_id))
    
    # Log the status change
    cursor.execute('''
        INSERT INTO status_logs (request_id, status, timestamp)
        VALUES (?, ?, ?)
    ''', (request_id, 'Fulfilled by Vendor: ' + vendor_name, timestamp))
    
    conn.commit()
    conn.close()
    
    flash('Support request updated successfully!')
    return redirect(url_for('vendor_login'))

@app.route('/add_inventory/<role>/<int:user_id>', methods=['GET', 'POST'])
def add_inventory(role, user_id):
    if role not in ['Warehouse Officer', 'Production Planner']:
        flash('Access denied. Only Warehouse Officers and Production Planners can manage inventory.')
        return redirect(url_for('dashboard', role=role, user_id=user_id))
    
    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = int(request.form['quantity'])
        status = request.form['status']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO inventory (item_name, quantity, status) VALUES (?, ?, ?)',
                (item_name, quantity, status)
            )
            conn.commit()
            flash(f'Inventory item "{item_name}" added successfully!')
        except sqlite3.IntegrityError:
            flash(f'Error: Product "{item_name}" already exists in inventory.')
        finally:
            conn.close()
        
        return redirect(url_for('add_inventory', role=role, user_id=user_id))
    
    # GET request - show inventory form and current inventory
    conn = get_db_connection()
    inventory = conn.execute('SELECT * FROM inventory ORDER BY item_name').fetchall()
    conn.close()
    
    return render_template('add_inventory.html', role=role, user_id=user_id, inventory=inventory)

@app.route('/update_inventory/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    role = request.args.get('role')
    user_id = request.args.get('user_id')
    
    if role not in ['Warehouse Officer', 'Production Planner']:
        flash('Access denied. Only Warehouse Officers and Production Planners can manage inventory.')
        return redirect(url_for('dashboard', role=role, user_id=user_id))
    
    quantity = int(request.form['quantity'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current item details
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
    
    if item:
        # Update quantity and determine status
        status = item['status']
        if quantity > 10:
            status = 'In Stock'
        elif quantity > 0:
            status = 'Low Stock'
        else:
            status = 'Out of Stock'
        
        cursor.execute(
            'UPDATE inventory SET quantity = ?, status = ? WHERE id = ?',
            (quantity, status, item_id)
        )
        conn.commit()
        flash(f'Inventory for "{item["item_name"]}" updated successfully!')
    else:
        flash('Error: Inventory item not found.')
    
    conn.close()
    return redirect(url_for('add_inventory', role=role, user_id=user_id))

@app.route('/reports')
def reports():
    conn = get_db_connection()
    
    # Get request counts by type
    request_types = conn.execute('''
        SELECT auto_tag, COUNT(*) as count
        FROM requests
        GROUP BY auto_tag
        ORDER BY count DESC
    ''').fetchall()
    
    # Get average fulfillment time
    avg_fulfillment = conn.execute('''
        SELECT auto_tag, 
               AVG(JULIANDAY(fulfilled_time) - JULIANDAY(submitted_time)) * 24 as avg_hours
        FROM requests
        WHERE fulfilled_time IS NOT NULL
        GROUP BY auto_tag
    ''').fetchall()
    
    # Get SLA breaches (requests taking more than 2 days)
    sla_breaches = conn.execute('''
        SELECT id, role, auto_tag, message, 
               JULIANDAY(fulfilled_time) - JULIANDAY(submitted_time) as days
        FROM requests
        WHERE fulfilled_time IS NOT NULL
          AND (JULIANDAY(fulfilled_time) - JULIANDAY(submitted_time)) > 2
        ORDER BY days DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('reports.html', 
                          request_types=request_types,
                          avg_fulfillment=avg_fulfillment,
                          sla_breaches=sla_breaches)

@app.route('/export_data')
def export_data():
    conn = get_db_connection()
    
    # Get all requests with user information
    all_requests = conn.execute('''
        SELECT r.id, u.username, r.role, r.message, r.auto_tag, r.status,
               r.submitted_time, r.fulfilled_time, r.estimated_delivery,
               r.vendor_name, r.solution, r.forwarded_to_production,
               CASE 
                   WHEN r.fulfilled_time IS NOT NULL THEN 
                       ROUND((JULIANDAY(r.fulfilled_time) - JULIANDAY(r.submitted_time)) * 24, 2)
                   ELSE NULL
               END as hours_to_fulfill
        FROM requests r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.submitted_time DESC
    ''').fetchall()
    
    # Get inventory data
    inventory = conn.execute('SELECT * FROM inventory ORDER BY item_name').fetchall()
    
    conn.close()
    
    # Convert requests to list of dicts for JSON export
    requests_list = []
    for r in all_requests:
        requests_list.append({
            'id': r['id'],
            'username': r['username'],
            'role': r['role'],
            'message': r['message'],
            'auto_tag': r['auto_tag'],
            'status': r['status'],
            'submitted_time': r['submitted_time'],
            'fulfilled_time': r['fulfilled_time'],
            'estimated_delivery': r['estimated_delivery'],
            'vendor_name': r['vendor_name'],
            'solution': r['solution'],
            'forwarded_to_production': r['forwarded_to_production'],
            'hours_to_fulfill': r['hours_to_fulfill']
        })
    
    # Convert inventory to list of dicts
    inventory_list = []
    for item in inventory:
        inventory_list.append({
            'id': item['id'],
            'item_name': item['item_name'],
            'quantity': item['quantity'],
            'status': item['status']
        })
    
    # Return combined data
    return jsonify({
        'requests': requests_list,
        'inventory': inventory_list
    })

if __name__ == '__main__':
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Initialize the database
    init_db()
    
    app.run(debug=True)