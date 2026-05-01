/**
 * TechNest UI Controller
 * Handles data fetching from SQLAlchemy backend and dynamic UI updates
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    loadDashboard();

    // Handle the Order Form submission
    const orderForm = document.getElementById('order-form');
    if (orderForm) {
        orderForm.addEventListener('submit', handleOrderSubmission);
    }

    // Handle the Restock Form submission (inventory.html)
    const restockForm = document.getElementById('restock-form');
    if (restockForm) {
        restockForm.addEventListener('submit', handleRestockSubmission);
    }
});

/**
 * Fetches product and order data from the Flask API
 */
async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();

        // 1. Render the Product Catalog (technest.html)
        renderCatalog(data.catalog);

        // 2. Populate Order Dropdown (technest.html)
        populateOrderDropdown(data.catalog);

        // 3. Populate Restock Dropdown (inventory.html)
        populateRestockDropdown(data.catalog);

        // 4. Render Order Table (orders.html - if on that page)
        renderOrdersTable(data.orders);

        // 5. Render Payments Table (orders.html and inventory.html)
        renderPaymentsTable(data.orders);

        // 6. Render Activity Log
        renderActivityLog(data.activity);

        // 7. Update Stats (if elements exist)
        updateStats(data);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        const catalog = document.getElementById('catalog');
        if (catalog) catalog.innerHTML = '<p class="subtle">Unable to load products. Check server connection.</p>';
    }
}

/**
 * Injects product cards into the catalog div
 */
function renderCatalog(products) {
    const catalogContainer = document.getElementById('catalog');
    if (!catalogContainer) return;

    if (!products || products.length === 0) {
        catalogContainer.innerHTML = '<p class="subtle">No products currently available.</p>';
        return;
    }

    catalogContainer.innerHTML = products.map(product => {
        // Assuming your images are named by ID: 101.jpg, 102.jpg, etc.
        const imagePath = `/static/phones/${product.id}.jpg`;

        return `
            <div class="panel product-card" onclick="selectProduct('${product.id}', '${product.name}', '${product.brand}', '${product.price}', '${product.stock}')">
                <div class="product-image-container" style="text-align: center; margin-bottom: 15px;">
                    <img src="${imagePath}" 
                         alt="${product.name}" 
                         onerror="this.src='/static/phones/default.jpg'" 
                         style="max-width: 120px; height: auto; border-radius: 12px;">
                </div>
                <div class="product-info">
                    <h3>${product.name}</h3>
                    <p class="subtle">${product.brand}</p>
                    <div class="price">$${parseFloat(product.price).toFixed(2)}</div>
                    <div class="focus-meta">
                        <span class="pill">Stock: ${product.stock}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Handles clicking a product card to open the order form
 * REVISED: Added logic to update the focus image
 */
function selectProduct(id, name, brand, price, stock) {
    const layerTwo = document.getElementById('layer-two');
    if (!layerTwo) return;

    // Show the order section
    layerTwo.classList.remove('hidden');

    // Update the "Focus" preview section
    document.getElementById('focus-name').innerText = name;
    document.getElementById('focus-brand').innerText = brand;
    document.getElementById('focus-price').innerText = `$${parseFloat(price).toFixed(2)}`;
    document.getElementById('focus-stock').innerText = `Stock: ${stock}`;
    document.getElementById('focus-id').innerText = `ID: ${id}`;

    // FIX: Update the image in the focus section
    const focusImg = document.querySelector('.product-focus img') || document.querySelector('#layer-two img');
    if (focusImg) {
        focusImg.src = `/static/phones/${id}.jpg`;
        focusImg.onerror = () => { focusImg.src = '/static/phones/default.jpg'; };
    }

    // Set the dropdown to match the clicked product
    const orderSelect = document.getElementById('order-product');
    if (orderSelect) orderSelect.value = id;

    // Smooth scroll to form
    layerTwo.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Populates the <select> element in the order form
 */
function populateOrderDropdown(products) {
    const select = document.getElementById('order-product');
    if (!select) return;

    select.innerHTML = products.map(p => 
        `<option value="${p.id}">${p.name} (${p.brand})</option>`
    ).join('');
}

/**
 * Handles the POST request to place an order
 * REVISED: Added dashboard refresh to update stock and order history instantly
 */
async function handleOrderSubmission(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/place_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            // Provide success feedback
            alert("Order Successful! Your items have been reserved.");

            // Move to Confirmation Layer
            document.getElementById('layer-two').classList.add('hidden');
            document.getElementById('layer-three').classList.remove('hidden');
            
            // Update Confirmation Details
            document.getElementById('confirm-order-id').innerText = `Order: ${result.order_id}`;
            document.getElementById('confirm-product').innerText = `Product ID: ${payload.product_id}`;
            document.getElementById('confirm-qty').innerText = `Qty: ${payload.quantity}`;
            document.getElementById('confirm-title').innerText = "Order Successful!";

            // REFRESH DATA: This updates the Catalog stock and Orders table in real-time
            loadDashboard();
            
            // Navigate to orders page after 2 seconds
            setTimeout(() => {
                window.location.href = '/orders';
            }, 2000);
        } else {
            alert('Order failed: ' + result.message);
        }
    } catch (error) {
        console.error('Order submission error:', error);
        alert('Server error while placing order.');
    }
}

/**
 * Updates the inventory/orders tables if on the management pages
 */
function renderOrdersTable(orders) {
    const tableBody = document.getElementById('orders-body');
    if (!tableBody || !orders) return;

    tableBody.innerHTML = orders.map(o => `
        <tr>
            <td>${o.id}</td>
            <td>${o.customer_name}</td>
            <td>${o.product_name}</td>
            <td>${o.quantity}</td>
            <td>$${parseFloat(o.total_amount).toFixed(2)}</td>
            <td><span class="pill">${o.order_status}</span></td>
        </tr>
    `).join('');
}

/**
 * Renders the payments table with order data
 */
function renderPaymentsTable(orders) {
    const tableBody = document.getElementById('payments-body');
    if (!tableBody || !orders) return;

    tableBody.innerHTML = orders.map(o => `
        <tr>
            <td>${o.id}</td>
            <td>${o.customer_name}</td>
            <td>$${parseFloat(o.total_amount).toFixed(2)}</td>
            <td><span class="pill" style="background-color: ${o.payment_status === 'Paid' ? '#22c55e' : '#f59e0b'};">${o.payment_status}</span></td>
            <td>${o.order_status}</td>
        </tr>
    `).join('');
}

/**
 * Renders the activity log
 */
function renderActivityLog(activities) {
    const activityList = document.getElementById('activity-list');
    if (!activityList || !activities) return;

    if (activities.length === 0) {
        activityList.innerHTML = '<p class="subtle">No activity logged yet.</p>';
        return;
    }

    activityList.innerHTML = activities.map(a => `
        <div style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong>${a.action}</strong>
                <span class="subtle" style="font-size: 0.85em;">${new Date(a.timestamp).toLocaleString()}</span>
            </div>
            <p class="subtle" style="margin: 4px 0 0 0;">${a.details}</p>
        </div>
    `).join('');
}

function updateStats(data) {
    const prodCount = document.getElementById('catalog-count');
    if (prodCount) prodCount.innerText = data.catalog.length;
    
    const orderCount = document.getElementById('order-count');
    if (orderCount) orderCount.innerText = data.orders.length;
}

/**
 * Populates product select for restock form
 */
function populateRestockDropdown(products) {
    const select = document.getElementById('restock-product');
    if (!select) return;

    select.innerHTML = products.map(p => 
        `<option value="${p.id}">${p.name} (${p.brand})</option>`
    ).join('');
}

/**
 * Handles the restock form submission
 */
async function handleRestockSubmission(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/restock_inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            const messageDiv = document.getElementById('restock-message');
            messageDiv.innerHTML = `<span style="color: green;">✓ ${result.message}</span>`;
            messageDiv.style.display = 'block';
            
            // Refresh dashboard to show updated stock
            loadDashboard();
            
            // Reset form
            e.target.reset();
            
            // Clear message after 3 seconds
            setTimeout(() => {
                messageDiv.innerHTML = '';
                messageDiv.style.display = 'none';
            }, 3000);
        } else {
            const messageDiv = document.getElementById('restock-message');
            messageDiv.innerHTML = `<span style="color: red;">✗ ${result.message}</span>`;
            messageDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Restock submission error:', error);
        const messageDiv = document.getElementById('restock-message');
        messageDiv.innerHTML = '<span style="color: red;">✗ Server error while restocking.</span>';
        messageDiv.style.display = 'block';
    }
}