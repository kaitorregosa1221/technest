from flask import Flask, render_template, request, jsonify
from models import db, Product, Order, ActivityLog
import exercise
import requests
import uuid

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:DuleJPNTwuXlEOmknQPyWlZuoYOYvWlB@switchyard.proxy.rlwy.net:44466/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- PAGE ROUTES ---
@app.route('/')
def hero():
    return render_template('hero.html')

@app.route('/technest')
def technest():
    return render_template('technest.html')

@app.route('/orders')
def orders_page():
    return render_template('orders.html')

@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html')

# --- DATA API ROUTES ---
@app.route('/api/dashboard')
def get_dashboard():
    """Fetch all dashboard data (products, orders, activities)"""
    try:
        # This fetches live data from the DB for both orders and inventory
        data = exercise.get_dashboard_snapshot()
        return jsonify(data)
    except Exception as e:
        print(f"❌ ERROR in get_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "Failed",
            "message": f"Error loading dashboard: {str(e)}",
            "catalog": [],
            "orders": [],
            "activity": []
        }), 500

@app.route('/restock_inventory', methods=['POST'])
def restock_inventory():
    """Endpoint to restock a product"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        
        print(f"\n📝 Restock Request: Product={product_id}, Qty=+{quantity}")
        
        # Validate
        if not product_id or quantity <= 0:
            print(f"❌ Invalid input: product_id={product_id}, quantity={quantity}")
            return jsonify({"status": "Failed", "message": "Invalid product or quantity"}), 400
        
        # Update inventory
        result = exercise.adjust_stock(product_id, quantity)
        
        if result['status'] == 'Success':
            print(f"✓ Restock successful: {result['product_name']} +{quantity} units")
            # Log the restock
            log_entry = ActivityLog(
                action="Restock",
                details=f"Added {quantity} units to {result['product_name']}"
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                "status": "Success",
                "message": f"Restocked {result['product_name']}",
                "remaining_stock": result['remaining_stock']
            }), 200
        
        print(f"❌ Restock failed: {result}")
        return jsonify(result), 400
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in restock_inventory: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "Failed", "message": f"Server error: {str(e)}"}), 500

@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        qty = int(data.get('quantity'))
        customer = data.get('customer_name')

        print(f"\n📝 New Order Request: Product={product_id}, Qty={qty}, Customer={customer}")

        # 1. Check if product exists and has stock
        product = exercise.get_product(product_id)
        if not product:
            print(f"❌ Product {product_id} not found")
            return jsonify({"status": "Failed", "message": "Product not found"}), 404
        
        if int(product['stock']) < qty:
            print(f"❌ Insufficient stock for {product_id}. Available: {product['stock']}, Requested: {qty}")
            return jsonify({"status": "Failed", "message": "Insufficient stock"}), 400

        # 2. Update Inventory (directly via adjust_stock function)
        print(f"📦 Adjusting inventory for {product_id} by -{qty}")
        inventory_result = exercise.adjust_stock(product_id, -qty)
        
        if inventory_result['status'] != 'Success':
            print(f"❌ Inventory update failed: {inventory_result}")
            return jsonify({"status": "Failed", "message": "Inventory update failed"}), 400
        
        # 3. Generate Order Details
        order_id = str(uuid.uuid4())[:8]
        total = float(product['price']) * qty
        
        print(f"💾 Recording order {order_id}: {qty}x {product['name']} = ${total}")
        
        # 4. Save to Database (Ensures it appears on the Orders page)
        exercise.record_order(
            order_id=order_id,
            customer_name=customer,
            product_id=product['id'],
            product_name=product['name'],
            quantity=qty,
            unit_price=float(product['price']),
            total_amount=total,
            inventory_status="Confirmed",
            payment_status="Pending",
            order_status="Processing",
            message="Order created via Web UI"
        )
        
        print(f"✅ Order {order_id} completed successfully!")
        
        return jsonify({
            "status": "Success", 
            "order_id": order_id, 
            "product_name": product['name'],
            "total": total
        })
    
    except Exception as e:
        print(f"❌ CRITICAL ERROR in place_order: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "Failed", "message": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist
    app.run(port=5000, debug=True)