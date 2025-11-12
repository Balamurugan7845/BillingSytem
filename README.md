## 🧾 Shop Billing System (Flask + MySQL)

A **complete billing and invoicing management system** built with **Flask**, **MySQL**, and **Bootstrap UI**.
Includes:

* User login/register with Flask-Login
* Product, Customer, and Billing Management
* Invoice generation (PDF + Print)
* Sales Dashboard with charts
* Save Draft & Confirm Payment system

---

### ⚙️ Tech Stack

| Component      | Technology           |
| -------------- | -------------------- |
| Backend        | Python Flask         |
| Database       | MySQL                |
| Frontend       | HTML5, Bootstrap, JS |
| ORM            | Flask-MySQLdb        |
| Authentication | Flask-Login          |
| PDF Generation | ReportLab            |

---

## 🪜 1. Clone or Download

```bash
git clone https://github.com/Balamurugan7845/BillingSytem.git
cd <your-repo>
```

---

## ⚙️ 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate      # (Windows)
# or
source venv/bin/activate   # (Linux/Mac)
```

---

## 📦 3. Install Required Packages

```bash
pip install -r requirements.txt
```

> **If you don’t have a `requirements.txt` yet**, create one:

```bash
Flask
Flask-MySQLdb
Flask-Login
Werkzeug
mysql-connector-python
reportlab
python-dotenv
WTForms
Flask-WTF
xhtml2pdf
```

---

## 🗄️ 4. Configure Database

Create a MySQL database named (for example) `shop_billing`:

```sql
CREATE DATABASE shop_billing;
USE shop_billing;
```

Now create the required tables:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2),
    stock INT DEFAULT 0,
    barcode VARCHAR(100)
);

CREATE TABLE bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    bill_number VARCHAR(50),
    total_amount DECIMAL(10,2),
    discount_type VARCHAR(50),
    discount_value DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    gst_type VARCHAR(50),
    cgst_amount DECIMAL(10,2),
    sgst_amount DECIMAL(10,2),
    igst_amount DECIMAL(10,2),
    gst_amount DECIMAL(10,2),
    final_amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    upi_id VARCHAR(100),
    card_number VARCHAR(100),
    card_name VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE bill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    FOREIGN KEY (bill_id) REFERENCES bills(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

---

## ⚙️ 5. Configure `config.py`

Create a `config.py` file in the root directory:

```python
class Config:
    SECRET_KEY = 'your-secret-key'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'your_mysql_password'
    MYSQL_DB = 'shop_billing'
    MYSQL_PORT = 3306
```

---

## 🚀 6. Run Flask App

In VS Code terminal:

```bash
python app.py
```

or

```bash
flask run
```

The app will run on:

> **[http://127.0.0.1:3000](http://127.0.0.1:3000)**

---

## 🔑 Default Login (if you added one manually)

You can insert an admin user directly into MySQL:

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash('admin123'))
```

Then add it to the database:

```sql
INSERT INTO users (username, password_hash) VALUES ('admin', '<paste_generated_hash>');
```

---

## 🧠 Features Overview
```
✅ User Login / Registration
✅ Dashboard with Weekly Sales Chart
✅ Manage Products and Customers
✅ Create Bills and Generate PDF Invoices
✅ Save Draft Bills (Payment Pending)
✅ Confirm Payment with UPI / Card
✅ Print Invoice
✅ REST API for AJAX product and customer lookups
```
---

## 📁 Folder Structure

```
project/
├── app.py
├── config.py
├── requirements.txt
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── products.html
    ├── customers.html
    ├── billing.html
    ├── invoices.html
    ├── invoice_detail.html
    ├── invoice_print.html
```

---

## 🧾 Example PDF Output

The system generates **professional tax invoices** in PDF format using **ReportLab**.
<img width="1886" height="863" alt="image" src="https://github.com/user-attachments/assets/5117eb9e-fef7-4d7f-a5ba-859cfdeb4ab3" />


---

## 🧰 Troubleshooting

| Issue                                | Fix                                                       |
| ------------------------------------ | --------------------------------------------------------- |
| `ModuleNotFoundError: flask_mysqldb` | `pip install Flask-MySQLdb`                               |
| `Access denied for user`             | Check your MySQL username/password in `config.py`         |
| PDF not downloading                  | Ensure `reportlab` is installed (`pip install reportlab`) |
| Port conflict                        | Change `app.run(port=3000)` to another port               |

---

## 🧑‍💻 Author

**Balamurugan S**
📧 [balamurugansundarraj07@gmail.com](mailto:balamurugansundarraj07@gmail.com)

💻 Flask Developer

---

