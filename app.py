from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime
import json
import os
import io
import MySQLdb.cursors  
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


app.config['MYSQL_HOST'] = Config.MYSQL_HOST
app.config['MYSQL_USER'] = Config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = Config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = Config.MYSQL_DB
app.config['MYSQL_PORT'] = Config.MYSQL_PORT

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user[0], user[1])  
    return None


def get_db_connection():
    return mysql.connection

def generate_bill_number():
    today = datetime.datetime.now()
    return f"BILL{today.strftime('%Y%m%d%H%M%S')}"


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
    
        if len(username) < 4 or len(username) > 20:
            flash('Username must be between 4-20 characters', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        cur = mysql.connection.cursor()
        
    
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            flash('Username already exists', 'danger')
            cur.close()
            return render_template('register.html')
        
   
        password_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                   (username, password_hash))
        mysql.connection.commit()
        cur.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     cur = mysql.connection.cursor()    
#     today = datetime.datetime.now().date()
#     cur.execute("SELECT SUM(final_amount) FROM bills WHERE DATE(created_at) = %s", (today,))
#     today_sales = cur.fetchone()[0] or 0    
#     month_start = datetime.datetime.now().replace(day=1).date()
#     cur.execute("SELECT SUM(final_amount) FROM bills WHERE DATE(created_at) >= %s", (month_start,))
#     monthly_sales = cur.fetchone()[0] or 0
    
  
#     cur.execute("SELECT COUNT(*) FROM products")
#     total_products = cur.fetchone()[0]
    

#     cur.execute("SELECT COUNT(*) FROM bills")
#     total_bills = cur.fetchone()[0]
    

#     cur.execute("""
#         SELECT b.id, b.bill_number, c.name, b.final_amount, b.created_at 
#         FROM bills b 
#         LEFT JOIN customers c ON b.customer_id = c.id 
#         ORDER BY b.created_at DESC 
#         LIMIT 5
#     """)
#     recent_bills = cur.fetchall()
    
#     cur.close()
    
#     return render_template('dashboard.html', 
#                          today_sales=today_sales,
#                          monthly_sales=monthly_sales,
#                          total_products=total_products,
#                          total_bills=total_bills,
#                          recent_bills=recent_bills)
@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()

    # --- Weekly Sales (Last 7 Days) ---
    cur.execute("""
        SELECT DATE(created_at) AS day, COALESCE(SUM(final_amount), 0)
        FROM bills
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY day ASC
    """)
    weekly_sales = cur.fetchall()

    import datetime
    today = datetime.date.today()
    labels = []
    sales = []
    for i in range(6, -1, -1):  # last 7 days
        day = today - datetime.timedelta(days=i)
        labels.append(day.strftime("%a"))  # Mon, Tue, ...
        amount = 0.0
        for r in weekly_sales:
            if str(r[0]) == str(day):
                amount = float(r[1])
                break
        sales.append(amount)

    # --- Stock Availability (Top 10 products) ---
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT name, stock FROM products WHERE stock > 0 ORDER BY stock DESC LIMIT 10
    """)
    stock_data = cur.fetchall()
    stock_labels = [row[0] for row in stock_data]
    stock_values = [row[1] for row in stock_data]

    # --- Dashboard Cards ---
    cur.execute("SELECT SUM(final_amount) FROM bills WHERE DATE(created_at) = CURDATE()")
    today_sales = cur.fetchone()[0] or 0

    month_start = today.replace(day=1)
    cur.execute("SELECT SUM(final_amount) FROM bills WHERE DATE(created_at) >= %s", (month_start,))
    monthly_sales = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bills")
    total_bills = cur.fetchone()[0]

    cur.execute("""
        SELECT b.id, b.bill_number, c.name, b.final_amount, b.created_at
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        ORDER BY b.created_at DESC
        LIMIT 5
    """)
    recent_bills = cur.fetchall()
    cur.close()

    # Debug check (optional)
    print("Weekly Labels:", labels)
    print("Weekly Sales:", sales)
    print("Stock Labels:", stock_labels)
    print("Stock Values:", stock_values)

    return render_template(
        'dashboard.html',
        today_sales=today_sales,
        monthly_sales=monthly_sales,
        total_products=total_products,
        total_bills=total_bills,
        recent_bills=recent_bills,
        labels=labels,
        sales=sales,
        stock_labels=stock_labels,
        stock_values=stock_values
    )

@app.route('/products')
@login_required
def products():
    search = request.args.get('search', '')
    cur = mysql.connection.cursor()
    
    if search:
        cur.execute("SELECT * FROM products WHERE name LIKE %s", (f'%{search}%',))
    else:
        cur.execute("SELECT * FROM products")
    
    products = cur.fetchall()
    cur.close()
    return render_template('products.html', products=products, search=search)

@app.route('/products/add', methods=['POST'])
@login_required
def add_product():
    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form['stock'])
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)", 
                (name, price, stock))
    mysql.connection.commit()
    cur.close()
    
    flash('Product added successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/products/edit/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form['stock'])
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE products SET name = %s, price = %s, stock = %s WHERE id = %s", 
                (name, price, stock, product_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Product updated successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/products/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    cur = mysql.connection.cursor()

    if search:
        cur.execute(
            "SELECT id, name, phone, email, address, created_at "
            "FROM customers WHERE name LIKE %s OR phone LIKE %s",
            (f'%{search}%', f'%{search}%')
        )
    else:
        cur.execute("SELECT id, name, phone, email, address, created_at FROM customers")

    rows = cur.fetchall()
    cur.close()


    customers = []
    for c in rows:
        customers.append({
            "id": c[0],
            "name": c[1],
            "phone": c[2],
            "email": c[3],
            "address": c[4],
            "created_at": c[5].strftime("%Y-%m-%d")
        })

    return render_template('customers.html', customers=customers, search=search)

@app.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)", 
                (name, phone, email, address))
    mysql.connection.commit()
    cur.close()
    
    flash('Customer added successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/edit/<int:customer_id>', methods=['POST'])
@login_required
def edit_customer(customer_id):
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE customers SET name = %s, phone = %s, email = %s, address = %s WHERE id = %s", 
                (name, phone, email, address, customer_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Customer updated successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:customer_id>')
@login_required
def delete_customer(customer_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))


@app.route('/billing')
@login_required
def billing():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE stock > 0")
    products = cur.fetchall()
    
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    
    cur.close()
    return render_template('billing.html', products=products, customers=customers)

@app.route('/billing/create', methods=['POST'])
@login_required
def create_bill():
    data = request.get_json()
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    payment_method = data.get('payment_method', 'Cash')
    

    subtotal = sum(item['quantity'] * item['price'] for item in items)
    gst_amount = subtotal * 0.18  # 18% GST
    final_amount = subtotal + gst_amount
    
    cur = mysql.connection.cursor()
    
   
    bill_number = generate_bill_number()
    cur.execute("""
        INSERT INTO bills (customer_id, bill_number, total_amount, gst_amount, final_amount, payment_method) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (customer_id, bill_number, subtotal, gst_amount, final_amount, payment_method))
    
    bill_id = cur.lastrowid
    
   
    for item in items:
        cur.execute("""
            INSERT INTO bill_items (bill_id, product_id, quantity, unit_price, total_price) 
            VALUES (%s, %s, %s, %s, %s)
        """, (bill_id, item['product_id'], item['quantity'], item['price'], item['quantity'] * item['price']))
        
        cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s", 
                   (item['quantity'], item['product_id']))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'success': True, 'bill_id': bill_id, 'bill_number': bill_number})
    
@app.route('/createbill', methods=['POST'])
def createbill_api():
    data = request.get_json()
    
    customer = data.get('customer_id')
    payment = data.get('payment_method')
    discounttype = data.get('discount_type')
    discountvalue = data.get('discount_value')
    gsttype = data.get('gst_type')
    subtotal = data.get('subtotal')
    discountamount = data.get('discount_amount')
    cgst = data.get('cgst')
    sgst = data.get('sgst')
    igst = data.get('igst')
    finaltotal = data.get('final_total')
    items = data.get('items')
    
    status = 'Completed'  # Mark as completed for generated bills
    
    try:
        cursor = mysql.connection.cursor()
        
        # Generate bill number
        bill_number = generate_bill_number()
        
        # Calculate GST amount
        gst_amount = float(cgst or 0) + float(sgst or 0) + float(igst or 0)
        
        # Insert into bills table
        cursor.execute("""
            INSERT INTO bills (customer_id, bill_number, total_amount, discount_type, 
                             discount_value, discount_amount, gst_type, cgst_amount, 
                             sgst_amount, igst_amount, gst_amount, final_amount, payment_method)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (customer, bill_number, subtotal, discounttype, discountvalue,
              discountamount, gsttype, cgst, sgst, igst, gst_amount, finaltotal, payment))
        
        billid = cursor.lastrowid
        
        # Insert bill items with correct column names
        for item in items:
            cursor.execute("""
                INSERT INTO bill_items (bill_id, product_id, quantity, unit_price, total_price)
                VALUES (%s,%s,%s,%s,%s)
            """, (billid, item['product_id'], item['qty'],
                  item['price'], item['total']))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'status': 'success', 'bill_id': billid})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route("/createbill.html")
def createbill_success_page():
    return render_template("createbill.html")



# @app.route('/invoices')
# @login_required
# def invoices():
#     cur = mysql.connection.cursor()
#     cur.execute("""
#         SELECT b.id, b.bill_number, c.name, b.final_amount, b.created_at 
#         FROM bills b 
#         LEFT JOIN customers c ON b.customer_id = c.id 
#         ORDER BY b.created_at DESC
#     """)
#     invoices = cur.fetchall()
#     cur.close()
#     return render_template('invoices.html', invoices=invoices)

@app.route('/invoices')
@login_required
def invoices():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.id, b.bill_number, c.name, 
               b.total_amount, b.gst_amount, b.final_amount, 
               b.payment_method, b.created_at
        FROM bills b 
        LEFT JOIN customers c ON b.customer_id = c.id 
        ORDER BY b.created_at DESC
    """)
    invoices = cur.fetchall()
    cur.close()
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoices/<int:bill_id>')
@login_required
def invoice_detail(bill_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.*, c.name, c.phone, c.email, c.address 
        FROM bills b 
        LEFT JOIN customers c ON b.customer_id = c.id 
        WHERE b.id = %s
    """, (bill_id,))
    bill = cur.fetchone()
    cur.execute("""
        SELECT bi.*, p.name 
        FROM bill_items bi 
        JOIN products p ON bi.product_id = p.id 
        WHERE bi.bill_id = %s
    """, (bill_id,))
    items = cur.fetchall()
    
    cur.close()
    
    return render_template('invoice_detail.html', bill=bill, items=items)

@app.route('/invoices/<int:bill_id>/pdf', methods=['GET', 'POST'])

@login_required
def generate_pdf(bill_id):
    cur = mysql.connection.cursor()
    

    cur.execute("""
        SELECT b.*, c.name, c.phone, c.email, c.address 
        FROM bills b 
        LEFT JOIN customers c ON b.customer_id = c.id 
        WHERE b.id = %s
    """, (bill_id,))
    bill = cur.fetchone()
    

    cur.execute("""
        SELECT bi.*, p.name 
        FROM bill_items bi 
        JOIN products p ON bi.product_id = p.id 
        WHERE bi.bill_id = %s
    """, (bill_id,))
    items = cur.fetchall()
    
    cur.close()

    import decimal

    if not bill:
        flash('Bill not found', 'danger')
        return redirect(url_for('invoices'))

    bill = list(bill)


    for i, v in enumerate(bill):
        if isinstance(v, decimal.Decimal):
            try:
                bill[i] = float(v)
            except Exception:
                pass
        elif isinstance(v, str):
            s = v.strip().replace(',', '')
            if s.replace('.', '', 1).lstrip('-').isdigit():
                try:
                    bill[i] = float(s)
                except Exception:
                    pass

   
    created_at = None
    for val in bill:
        if isinstance(val, datetime.datetime):
            created_at = val
            break
        if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
            created_at = datetime.datetime.combine(val, datetime.time.min)
            break
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                try:
                    created_at = datetime.datetime.strptime(val, fmt)
                    break
                except Exception:
                    continue
            if created_at:
                break

  
    if created_at is None:
        for val in bill:
            try:
                if isinstance(val, (int, float)) and float(val) > 1e9:
                    created_at = datetime.datetime.fromtimestamp(float(val))
                    break
                if isinstance(val, decimal.Decimal) and float(val) > 1e9:
                    created_at = datetime.datetime.fromtimestamp(float(val))
                    break
            except Exception:
                continue

    if created_at is None:
        created_at = datetime.datetime.now()

 
    while len(bill) <= 7:
        bill.append(None)
    bill[7] = created_at

    for idx in (3, 4, 5):
        if idx < len(bill):
            try:
                bill[idx] = float(bill[idx]) if bill[idx] is not None else 0.0
            except Exception:
                bill[idx] = 0.0

    #
    processed_items = []
    for it in items:
        row = list(it)
        for j, val in enumerate(row):
            if isinstance(val, decimal.Decimal):
                try:
                    row[j] = float(val)
                except Exception:
                    pass
            elif isinstance(val, str):
                s = val.strip().replace(',', '')
                if s.replace('.', '', 1).lstrip('-').isdigit():
                    try:
                        if s.isdigit() or (s.lstrip('-').isdigit()):
                            row[j] = int(s)
                        else:
                            row[j] = float(s)
                    except Exception:
                        pass
        processed_items.append(row)
    
    items = processed_items

    # Create PDF using ReportLab
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='Right', alignment=2))

    elements.append(Paragraph("SHOP BILLING SYSTEM", styles['Title']))
    elements.append(Paragraph("TAX INVOICE", styles['Heading1']))
    elements.append(Spacer(1, 12))

    company_data = [
        [Paragraph("<b>From:</b>", styles['Normal']), 
         Paragraph("<b>Invoice Details:</b>", styles['Normal'])],
        [Paragraph("Shop Billing System<br/>"
                  "123 College Street<br/>"
                  "Academic City, AC 12345<br/>"
                  "Phone: (555) 123-4567<br/>"
                  "Email: shop@college.edu", styles['Normal']),
         Paragraph(f"Bill No: {bill[2]}<br/>"
                  f"Date: {bill[7].strftime('%B %d, %Y')}<br/>"
                  f"Time: {bill[7].strftime('%I:%M %p')}<br/>"
                  f"Payment Method: {bill[6]}", styles['Normal'])]
    ]
    
    company_table = Table(company_data, colWidths=[3*inch, 3*inch])
    company_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 12))

    customer_name = bill[8] if bill[8] else "Walk-in Customer"
    elements.append(Paragraph(f"<b>Bill To:</b> {customer_name}", styles['Normal']))
    if bill[9]:
        elements.append(Paragraph(f"Phone: {bill[9]}", styles['Normal']))
    if bill[10]:
        elements.append(Paragraph(f"Email: {bill[10]}", styles['Normal']))
    if bill[11]:
        elements.append(Paragraph(f"Address: {bill[11]}", styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    
    data = [['Item', 'Product', 'Unit Price (₹)', 'Qty', 'Total (₹)']]
    
    #  Corrected indexes: product name = item[6], total price = item[5]
    for i, item in enumerate(items, 1):
        data.append([
            str(i),
            item[6],                 # product name
            f"₹{item[4]:.2f}",       # unit price
            str(item[3]),            # quantity
            f"₹{item[5]:.2f}"        # total price
        ])

    data.append(['', '', '', 'Subtotal:', f"₹{bill[3]:.2f}"])
    data.append(['', '', '', 'GST (18%):', f"₹{bill[4]:.2f}"])
    data.append(['', '', '', '<b>Grand Total:</b>', f"<b>₹{bill[5]:.2f}</b>"])
    
    items_table = Table(data, colWidths=[0.5*inch, 2.5*inch, 1.2*inch, 0.8*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ALIGN', (-2, -3), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 24))
    
  
    elements.append(Paragraph("Thank you for your business!", styles['Heading2']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Terms & Conditions: Goods once sold cannot be returned or exchanged unless defective. "
                            "This is a computer generated invoice.", styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                            styles['Normal']))
    
  
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f"invoice_{bill[2]}.pdf",
        as_attachment=True,
        mimetype='application/pdf'
    )

@app.route('/invoices/<int:bill_id>/print')
@login_required
def print_invoice(bill_id):
    cur = mysql.connection.cursor()
    

    cur.execute("""
        SELECT b.*, c.name, c.phone, c.email, c.address 
        FROM bills b 
        LEFT JOIN customers c ON b.customer_id = c.id 
        WHERE b.id = %s
    """, (bill_id,))
    bill = cur.fetchone()
    

    cur.execute("""
        SELECT bi.*, p.name 
        FROM bill_items bi 
        JOIN products p ON bi.product_id = p.id 
        WHERE bi.bill_id = %s
    """, (bill_id,))
    items = cur.fetchall()
    
    cur.close()
    
    import decimal
 
    if not bill:
        flash('Bill not found', 'danger')
        return redirect(url_for('invoices'))

    bill = list(bill)


    for i, v in enumerate(bill):
        if isinstance(v, decimal.Decimal):
            try:
                bill[i] = float(v)
            except Exception:
                pass
        elif isinstance(v, str):
            s = v.strip().replace(',', '')
            if s.replace('.', '', 1).lstrip('-').isdigit():
                try:
                    bill[i] = float(s)
                except Exception:
                    pass


    created_at = None
    for val in bill:
        if isinstance(val, datetime.datetime):
            created_at = val
            break
        if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
            created_at = datetime.datetime.combine(val, datetime.time.min)
            break
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                try:
                    created_at = datetime.datetime.strptime(val, fmt)
                    break
                except Exception:
                    continue
            if created_at:
                break

    if created_at is None:
        for val in bill:
            if isinstance(val, (int, float, decimal.Decimal)):
                try:
                    if float(val) > 1e9:
                        created_at = datetime.datetime.fromtimestamp(float(val))
                        break
                except Exception:
                    continue

    if created_at is None:
        created_at = datetime.datetime.now()

    while len(bill) <= 7:
        bill.append(None)
    bill[7] = created_at


    for idx in (3, 4, 5):
        if idx < len(bill):
            try:
                bill[idx] = float(bill[idx]) if bill[idx] is not None else 0.0
            except Exception:
                bill[idx] = 0.0
    processed_items = []
    for it in items:
        row = list(it)
        for j, val in enumerate(row):
            if isinstance(val, decimal.Decimal):
                try:
                    row[j] = float(val)
                except Exception:
                    pass
            elif isinstance(val, str):
                s = val.strip().replace(',', '')
                if s.replace('.', '', 1).lstrip('-').isdigit():
                    try:
                        if s.isdigit() or (s.lstrip('-').isdigit()):
                            row[j] = int(s)
                        else:
                            row[j] = float(s)
                    except Exception:
                        pass
        processed_items.append(row)

    items = processed_items
    return render_template('invoice_print.html', bill=bill, items=items)



@app.route('/api/products')
@login_required
def api_products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, price, stock FROM products WHERE stock > 0")
    products = cur.fetchall()
    cur.close()
    
    products_list = []
    for product in products:
        products_list.append({
            'id': product[0],
            'name': product[1],
            'price': float(product[2]),
            'stock': product[3]
        })
    
    return jsonify(products_list)



@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, price, stock FROM products WHERE name LIKE %s", (f'%{query}%',))
    rows = cur.fetchall()
    cur.close()

    products = []
    for r in rows:
        products.append({
            "id": r[0],
            "name": r[1],
            "price": float(r[2]),
            "stock": r[3]
        })

    return jsonify(products)


import MySQLdb.cursors  

@app.route('/api/product/lookup')
@login_required
def api_product_lookup():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    rows = []
    if q.isdigit():
        cur.execute("SELECT id, name, price, stock FROM products WHERE id = %s", (q,))
        row = cur.fetchone()
        if row:
            rows = [row]
        else:
            rows = []
    else:

        cur.execute("""
            SELECT id, name, price, stock
            FROM products
            WHERE name LIKE %s
            ORDER BY name ASC
            LIMIT 10
        """, (f"%{q}%",))
        rows = cur.fetchall()

    cur.close()

    result = []
    for r in rows or []:
        result.append({
            "id": int(r["id"]),
            "name": r["name"],
            "price": float(r["price"]),
            "stock": int(r["stock"]),
        })
    return jsonify(result)


@app.route('/api/customers')
@login_required
def api_customers():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, phone, email, address FROM customers ORDER BY name")
    customers = cur.fetchall()
    cur.close()
    return jsonify(customers)

@app.route('/api/bill/<int:bill_id>/items/count')
@login_required
def bill_items_count(bill_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as item_count FROM bill_items WHERE bill_id = %s", (bill_id,))
    result = cur.fetchone()
    cur.close()
    return jsonify({'item_count': result['item_count']})

@app.route('/api/customer/<int:customer_id>/stats')
@login_required
def customer_stats(customer_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as total_bills FROM bills WHERE customer_id = %s", (customer_id,))
    bill_count = cur.fetchone()['total_bills']
    cur.execute("SELECT COALESCE(SUM(final_amount), 0) as total_spent FROM bills WHERE customer_id = %s", (customer_id,))
    total_spent = cur.fetchone()['total_spent']
    
    cur.close()
    
    return jsonify({
        'total_bills': bill_count,
        'total_spent': float(total_spent)
    })

@app.route('/api/billing/stats')
@login_required
def billing_stats():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as today_bills FROM bills WHERE DATE(created_at) = CURDATE()")
    today_bills = cur.fetchone()['today_bills']
    cur.execute("SELECT COUNT(*) as low_stock FROM products WHERE stock < 5")
    low_stock = cur.fetchone()['low_stock']
    
    cur.close()
    
    return jsonify({
        'today_bills': today_bills,
        'low_stock': low_stock
    })


@app.route('/api/customers/quick-add', methods=['POST'])
@login_required
def quick_add_customer():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone', '')
        email = data.get('email', '')
        address = data.get('address', '')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'})
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                   (name, phone, email, address))
        customer_id = cur.lastrowid
        mysql.connection.commit()
        cur.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cur.fetchone()
        cur.close()
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer['id'],
                'name': customer['name'],
                'phone': customer['phone'],
                'email': customer['email'],
                'address': customer['address']
            }
        })
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route("/confirm-payment/<int:bill_id>")
@login_required
def confirm_payment(bill_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT payment_method FROM bills WHERE id=%s", (bill_id,))
    pay = cur.fetchone()
    cur.close()

    if not pay:
        return "Invalid Bill ID"

    return render_template("confirm.html", bill_id=bill_id, payment_method=pay[0])
@app.route('/complete-payment/<int:bill_id>', methods=['POST'])
@login_required
def complete_payment(bill_id):
    upi_id = request.form.get("upi_id")
    card_number = request.form.get("card_number")
    card_name = request.form.get("card_name")

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE bills 
        SET status='Completed',
            upi_id=%s,
            card_number=%s,
            card_name=%s
        WHERE id=%s
    """, (upi_id, card_number, card_name, bill_id))

    mysql.connection.commit()
    cursor.close()

    return redirect(f"/invoices/{bill_id}/print")


@app.route('/savedraft', methods=['POST'])
def save_draft():
    data = request.get_json()

    customer_id = data.get("customer_id")
    payment_method = data.get("payment_method")
    discount_type = data.get("discount_type")
    discount_value = data.get("discount_value")
    gst_type = data.get("gst_type")

    subtotal = data.get("subtotal")
    discount_amount = data.get("discount_amount")
    cgst = data.get("cgst")
    sgst = data.get("sgst")
    igst = data.get("igst")
    final_total = data.get("final_total")

    items = data.get("items")

    # DRAFT STATUS
    status = "Payment Pending"

    # Save to bills table
    cursor = mysql.connection.cursor()
    
    # Generate bill number
    bill_number = generate_bill_number()
    
    # Calculate GST amount
    gst_amount = float(cgst or 0) + float(sgst or 0) + float(igst or 0)
    
    cursor.execute("""
        INSERT INTO bills 
        (customer_id, bill_number, total_amount, discount_type, discount_value, discount_amount,
         gst_type, cgst_amount, sgst_amount, igst_amount, gst_amount, final_amount, payment_method)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        customer_id, bill_number, subtotal, discount_type, discount_value, discount_amount,
        gst_type, cgst, sgst, igst, gst_amount, final_total, payment_method
    ))
    bill_id = cursor.lastrowid

    # Save bill items
    for item in items:
        cursor.execute("""
            INSERT INTO bill_items (bill_id, product_id, quantity, unit_price, total_price)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            bill_id,
            item['product_id'],
            item['qty'],
            item['price'],
            item['total']
        ))

    mysql.connection.commit()
    cursor.close()

    return jsonify({"status":"success", "bill_id": bill_id})

@app.route('/savedraft', methods=['POST'])
def savedraft():
    data = request.get_json()
    
    customerid = data.get('customer_id')
    paymentmethod = data.get('payment_method')
    discounttype = data.get('discount_type')
    discountvalue = data.get('discount_value')
    gsttype = data.get('gst_type')
    subtotal = data.get('subtotal')
    discountamount = data.get('discount_amount')
    cgst = data.get('cgst')
    sgst = data.get('sgst')
    igst = data.get('igst')
    finaltotal = data.get('final_total')
    items = data.get('items')
    
    status = 'Draft'  # Mark as draft
    
    try:
        cursor = mysql.connection.cursor()
        
        # Insert into bills table with Draft status
        cursor.execute("""
            INSERT INTO bills (customerid, paymentmethod, discounttype, discountvalue, 
                             gsttype, subtotal, discountamount, cgst, sgst, igst, 
                             finaltotal, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (customerid, paymentmethod, discounttype, discountvalue, gsttype, 
              subtotal, discountamount, cgst, sgst, igst, finaltotal, status))
        
        billid = cursor.lastrowid
        
        # Insert bill items - Use correct column name 'productname'
        for item in items:
            cursor.execute("""
                INSERT INTO billitems (billid, productid, productname, price, qty, total)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (billid, item['product_id'], item['product_name'], 
                  item['price'], item['qty'], item['total']))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'status': 'success', 'bill_id': billid})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400


# Search products by barcode
@app.route('/api/products/barcode/<barcode>')
@login_required
def search_product_by_barcode(barcode):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE barcode = %s AND stock > 0", (barcode,))
    product = cur.fetchone()
    cur.close()
    
    if product:
        return jsonify({
            'success': True,
            'product': {
                'id': product['id'],
                'name': product['name'],
                'price': float(product['price']),
                'stock': product['stock']
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Product not found'})

if __name__ == '__main__':
    app.run(debug=True,port=3000)
