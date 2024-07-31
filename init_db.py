import sqlite3
import json
connection = sqlite3.connect("db.sqlite")
cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers(
	id INTEGER PRIMARY KEY,
	name CHAR(64) NOT NULL,
	phone CHAR(10) NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
	id INTEGER PRIMARY KEY,
	name CHAR(64) NOT NULL,
	price REAL NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	timestamp INTEGER DEFAULT (unixepoch()),
	cust_id INT NOT NULL,
    notes TEXT
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS item_list(
    order_id NOT NULL,
    item_id NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(item_id) REFERENCES items(id)
);
""")
with open("customers.json") as f:
    customers = json.load(f)

for phone, name in customers.items():
    cursor.execute("INSERT INTO customers (name, phone) VALUES(?, ?);", (name, phone))

with open("items.json") as f:
    items = json.load(f)

for name, stats in items.items():
    price = stats["price"]
    number_of_orders = stats["orders"]
    cursor.execute("INSERT INTO items (name, price) VALUES(?, ?);", (name, price)) 
    
with open("example_orders.json") as f:
    orders = json.load(f)

for order in orders:
    # Insert or find customer
    cursor.execute("SELECT id FROM customers WHERE name=? AND phone=?;", (order["name"], order["phone"]))
    customer = cursor.fetchone()
    if customer is None:
        cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?);", (order['name'], order['phone']))
        cust_id = cursor.lastrowid
    else:
        cust_id = customer[0]
    
    # Insert order
    cursor.execute("INSERT INTO orders (timestamp, cust_id, notes) VALUES (?, ?, ?);", (order["timestamp"], cust_id, order["notes"]))
    order_id = cursor.lastrowid
    
    # Insert items in item_list
    for item in order["items"]:
        cursor.execute("SELECT id FROM items WHERE name=? AND price=?;", (item["name"], item["price"]))
        item_record = cursor.fetchone()
        if item_record is None:
            # If item doesn't exist, insert it
            cursor.execute("INSERT INTO items (name, price) VALUES (?, ?);", (item["name"], item["price"]))
            item_id = cursor.lastrowid
        else:
            item_id = item_record[0]
        cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);", (order_id, item_id))

# Commit changes
connection.commit()

# Query and print results
result = cursor.execute('''
SELECT orders.id AS order_id, orders.timestamp, customers.name, customers.phone, orders.notes, items.name AS item_name, items.price
FROM orders
JOIN customers ON orders.cust_id = customers.id
JOIN item_list ON orders.id = item_list.order_id
JOIN items ON item_list.item_id = items.id
''').fetchone()
for row in result:
    print(row)
    
connection.close()
