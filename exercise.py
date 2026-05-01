from __future__ import annotations
from datetime import datetime
from models import db, Product, Order, ActivityLog

def get_catalog_snapshot() -> list[dict[str, str]]:
    """Retrieves all products and prints debug info to the terminal."""
    try:
        products = Product.query.all()
        print(f"\n📦 DATABASE QUERY: get_catalog_snapshot")
        print(f"   Table: {Product.__tablename__}")
        print(f"   Products found: {len(products)}")
        
        catalog = [
            {
                'id': p.id,
                'name': p.name,
                'brand': p.brand,
                'price': f"{p.price:.2f}",
                'stock': str(p.stock),
                'description': p.description if hasattr(p, 'description') else "",
            }
            for p in products
        ]
        print(f"✓ Catalog snapshot ready ({len(catalog)} items)")
        return catalog
        
    except Exception as e:
        print(f"❌ DATABASE ERROR in get_catalog_snapshot: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_product(product_id: str) -> dict[str, str] | None:
    """Fetches a single product by its ID."""
    try:
        p = Product.query.get(product_id)
        if p:
            return {
                'id': p.id,
                'name': p.name,
                'brand': p.brand,
                'price': f"{p.price:.2f}",
                'stock': str(p.stock),
                'description': getattr(p, 'description', ""),
            }
        print(f"⚠️ Product {product_id} not found")
        return None
    except Exception as e:
        print(f"❌ ERROR fetching product {product_id}: {e}")
        return None

def adjust_stock(product_id: str, quantity_delta: int) -> dict[str, str]:
    """Increases or decreases stock and commits changes."""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            print(f"❌ Product {product_id} not found")
            return {'status': 'Failed', 'message': 'Product not found'}

        new_stock = product.stock + quantity_delta
        
        if new_stock < 0:
            print(f"❌ Cannot set stock to {new_stock} (negative). Current: {product.stock}, Delta: {quantity_delta}")
            return {
                'status': 'Failed', 
                'message': 'Insufficient stock', 
                'remaining_stock': str(product.stock)
            }

        product.stock = new_stock
        print(f"📊 Stock adjustment: {product.name}: {product.stock - quantity_delta} → {product.stock}")
        db.session.commit()
        
        return {
            'status': 'Success',
            'product_name': product.name,
            'remaining_stock': str(product.stock),
        }
    except Exception as e:
        print(f"❌ ERROR adjusting stock: {e}")
        db.session.rollback()
        return {'status': 'Failed', 'message': str(e)}

def record_order(
    order_id: str,
    customer_name: str,
    product_id: str,
    product_name: str,
    quantity: int,
    unit_price: float,
    total_amount: float,
    inventory_status: str,
    payment_status: str, # Added to match microservice logic
    order_status: str,
    message: str,
) -> None:
    """Saves a new order record to the MySQL orders table."""
    try:
        new_order = Order(
            id=order_id,
            customer_name=customer_name,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            total_amount=total_amount,
            payment_status=payment_status,
            status=order_status,
            message=message
        )
        db.session.add(new_order)
        db.session.commit()
        
        # Log the order placement after order is saved
        log_entry = ActivityLog(
            action="Order Placed",
            details=f"Order #{order_id} for {customer_name}"
        )
        db.session.add(log_entry)
        db.session.commit()
        print(f"✓ Order {order_id} saved successfully")
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR recording order: {e}")
        raise

def append_activity(action: str, details: str) -> None:
    """Logs system activity to the activity_log table."""
    log_entry = ActivityLog(
        action=action,
        details=details
    )
    db.session.add(log_entry)
    db.session.commit()

def get_dashboard_snapshot() -> dict[str, list[dict]]:
    """Gathers data for the dashboard with safe date handling."""
    try:
        print("\n📊 Fetching dashboard snapshot...")
        
        # Fetching data for all 3 tables
        try:
            orders = Order.query.order_by(Order.timestamp.desc()).limit(15).all()
            print(f"   Found {len(orders)} orders")
        except Exception as e:
            print(f"   ⚠️ Error fetching orders: {e}")
            orders = []
        
        try:
            activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(20).all()
            print(f"   Found {len(activity)} activity logs")
        except Exception as e:
            print(f"   ⚠️ Error fetching activity: {e}")
            activity = []
        
        def safe_date(date_val):
            if hasattr(date_val, 'isoformat'):
                return date_val.isoformat()
            return str(date_val) if date_val else ""

        result = {
            'catalog': get_catalog_snapshot(),
            'orders': [
                {
                    'id': o.id,
                    'timestamp': safe_date(o.timestamp),
                    'customer_name': o.customer_name,
                    'product_name': o.product_name,
                    'quantity': str(o.quantity),
                    'total_amount': f"{o.total_amount:.2f}",
                    'order_status': o.status,
                    'payment_status': getattr(o, 'payment_status', 'Pending')
                } for o in orders
            ],
            'activity': [
                {
                    'timestamp': safe_date(a.timestamp),
                    'action': a.action,
                    'details': a.details
                } for a in activity
            ]
        }
        print(f"✓ Dashboard snapshot ready")
        return result
        
    except Exception as e:
        print(f"❌ DASHBOARD SNAPSHOT ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Return minimal valid data
        return {
            'catalog': get_catalog_snapshot(), 
            'orders': [], 
            'activity': []
        }