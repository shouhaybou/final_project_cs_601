import sqlite3
from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
from typing import List

class Item(BaseModel):
    name: str
    price: float
    
class Customer(BaseModel):
    name: str
    phone: str
    
class Order(BaseModel):
    id:int
    timestamp:int
    name: str
    phone: str
    notes: str
    items : List[Item]
    
class ItemCreate(BaseModel):
    name:str
    price: float
    
class OrderCreate(BaseModel):
    name: str
    phone: str
    notes: str
    items : List[ItemCreate]
    
connection = sqlite3.connect("db.sqlite")
cursor = connection.cursor()
app = FastAPI()

# read Items
@app.get("/items/{item_id}")
async def read_item(item_id):
    result = cursor.execute("SELECT * FROM items WHERE id=?;", (item_id,))
    item = result.fetchone()
    if item == None:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "id": item[0],
        "name": item[1],
        "price": item[2],
    }
# read customers
@app.get("/customers/{customer_id}")
async def read_customer(customer_id):
    result = cursor.execute("SELECT * FROM customers WHERE id=?;", (customer_id,))
    customer = result.fetchone()
    if customer == None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "id":customer[0],
        "name": customer[1],
        "phone": customer[2],
    }
# create items
@app.post("/items/")
async def create_item(item: Item):
    name = item.name
    price = item.price
    
    cursor.execute("INSERT INTO items (name, price) VALUES (?,?);", (name, price))
    connection.commit()
    return {
        "id": cursor.lastrowid,
        "name": name,
        "price": price,
        }

# delete items
@app.delete("/items/{item_id}")
async def delete_item(item_id):
    cursor.execute("DELETE FROM items WHERE id=?;", (item_id,))
    connection.commit()
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="Item not found")
    return

# update item
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    cursor.execute("UPDATE items SET name=?, price=? WHERE id=?;", (item.name, item.price, item_id))
    connection.commit()
    return{
        "id": item_id,
        "name": item.name,
        "price": item.price,
    }
    
# create customers
@app.post("/customers/")
async def create_customer(customer: Customer):
    name = customer.name
    phone = customer.phone
    
    cursor.execute("INSERT INTO customers (name, phone) VALUES (?,?);", (name, phone))
    connection.commit()
    return {
        "id": cursor.lastrowid,
        "name": name,
        "phone": phone,
        }

# update customers
@app.put("/customers/{customer_id}")
async def update_customer(customer_id: int, customer: Customer):
    cursor.execute("UPDATE customers SET name=?, phone=? WHERE id=?;", (customer.name, customer.phone, customer_id))
    connection.commit()
    return{
        "id": customer_id,
        "name": customer.name,
        "phone": customer.phone,
    }
    
# delete customers
@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id):
    cursor.execute("DELETE FROM customers WHERE id=?;", (customer_id,))
    connection.commit()
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="customer not found")
    return
    
    
# read orders
@app.get("/orders/{order_id}", response_model=Order)
async def read_order(order_id: int):
    
    cursor.execute("""
        SELECT orders.id, orders.timestamp, customers.name, customers.phone, orders.notes 
        FROM orders
        JOIN customers ON orders.cust_id = customers.id
        WHERE orders.id = ?
    """, (order_id,))
    order = cursor.fetchone()
    
    if order is None:
        
        raise HTTPException(status_code=404, detail="Order not found")
    
    cursor.execute("""
        SELECT items.name, items.price
        FROM item_list
        JOIN items ON item_list.item_id = items.id
        WHERE item_list.order_id = ?
    """, (order_id,))
    items = cursor.fetchall()
    
    order_items = [{"name": item[0], "price": item[1]} for item in items]
    
    
    
    return {
        "id": order[0],
        "timestamp": order[1],
        "name": order[2],
        "phone": order[3],
        "notes": order[4],
        "items": order_items
    }

# create order
@app.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate):


    # Insert or find customer
    cursor.execute("SELECT id FROM customers WHERE name=? AND phone=?;", (order.name, order.phone))
    customer = cursor.fetchone()
    if customer is not None:
        cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?);", (order.name, order.phone))
        cust_id = cursor.lastrowid
    else:
        cust_id = customer[0]
    
    # Insert order with automatic timestamp
    cursor.execute("INSERT INTO orders (cust_id, notes) VALUES (?, ?);", (cust_id, order.notes))
    order_id = cursor.lastrowid
    
    # Insert items
    for item in order.items:
        cursor.execute("SELECT id FROM items WHERE name=? AND price=?;", (item.name, item.price))
        item_record = cursor.fetchone()
        if item_record is None:
            cursor.execute("INSERT INTO items (name, price) VALUES (?, ?);", (item.name, item.price))
            item_id = cursor.lastrowid
        else:
            item_id = item_record[0]
        cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);", (order_id, item_id))

    connection.commit()

    # Retrieve the created order details
    cursor.execute("""
        SELECT orders.id, orders.timestamp, customers.name, customers.phone, orders.notes 
        FROM orders
        JOIN customers ON orders.cust_id = customers.id
        WHERE orders.id = ?
    """, (order_id,))
    created_order = cursor.fetchone()
    print(created_order)
    
    cursor.execute("""
        SELECT items.name, items.price
        FROM item_list
        JOIN items ON item_list.item_id = items.id
        WHERE item_list.order_id = ?
    """, (order_id,))
    items = cursor.fetchall()
    
    order_items = [{"name": item[0], "price": item[1]} for item in items]
    
    
    return {
        "id": created_order[0],
        "timestamp": created_order[1],
        "name": created_order[2],
        "phone": created_order[3],
        "notes": created_order[4],
        "items": order_items
    }
# delete order
@app.delete("/orders/{order_id}")
async def delete_order(order_id):
    cursor.execute("DELETE FROM customers WHERE id=?;", (order_id,))
    connection.commit()
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="order not found")
    return

# Update order
@app.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: int, order_update: OrderCreate):
    # Check if the order exists
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Find or create customer
    cursor.execute("SELECT id FROM customers WHERE name=? AND phone=?", (order_update.name, order_update.phone))
    customer = cursor.fetchone()
    if customer:
        cust_id = customer[0]
    else:
        cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (order_update.name, order_update.phone))
        cust_id = cursor.lastrowid

    # Update order with new customer ID and notes
    cursor.execute("UPDATE orders SET cust_id = ?, notes = ? WHERE id = ?", (cust_id, order_update.notes, order_id))

    # Remove existing items
    cursor.execute("DELETE FROM item_list WHERE order_id = ?", (order_id,))

    # Insert updated items
    for item in order_update.items:
        cursor.execute("SELECT id FROM items WHERE name=? AND price=?", (item.name, item.price))
        item_record = cursor.fetchone()
        if item_record:
            item_id = item_record[0]
        else:
            cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (item.name, item.price))
            item_id = cursor.lastrowid
        cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?)", (order_id, item_id))

    connection.commit()

    # Retrieve updated order details
    cursor.execute("""
        SELECT orders.id, orders.timestamp, customers.name, customers.phone, orders.notes 
        FROM orders
        JOIN customers ON orders.cust_id = customers.id
        WHERE orders.id = ?
    """, (order_id,))
    updated_order = cursor.fetchone()
    
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")

    cursor.execute("""
        SELECT items.name, items.price
        FROM item_list
        JOIN items ON item_list.item_id = items.id
        WHERE item_list.order_id = ?
    """, (order_id,))
    items = cursor.fetchall()

    order_items = [{"name": item[0], "price": item[1]} for item in items]

    return {
        "id": updated_order[0],
        "timestamp": updated_order[1],
        "name": updated_order[2],
        "phone": updated_order[3],
        "notes": updated_order[4],
        "items": order_items
    }

