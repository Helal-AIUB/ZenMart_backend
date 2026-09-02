# Petora BD API Documentation

**Base URL:** `api/` (e.g., `https://api.petorabd.com/api/` or `http://localhost:8000/api/`)

**Authentication:** Endpoints that require authentication use the `Authorization: JWT <token>` header.

---

## Index

| # | Endpoint | Method | Who Can Use | Description |
|---|----------|--------|-------------|-------------|
| 1 | `store/collections/` | GET | Anyone | List all product collections |
| 2 | `store/products/` | GET | Anyone | List all products with search & filters |
| 3 | `store/products/<pk>/` | GET | Anyone | Get single product details |
| 4 | `store/carts/` | POST | Anyone | Create a new unique cart |
| 5 | `store/carts/<pk>/` | GET | Cart Owner | Fetch cart details and items |
| 6 | `store/carts/<pk>/items/` | POST | Cart Owner | Add a product to the cart |
| 7 | `store/carts/<cart_pk>/items/<item_pk>/` | PATCH / DELETE | Cart Owner | Update quantity or remove cart item |
| 8 | `store/coupons/` | GET / POST | Admin only | List all coupons or create a new one |
| 9 | `store/coupons/<pk>/` | GET / PATCH / DELETE | Admin only | Get, edit, or delete a coupon |
| 10| `store/coupons/validate/` | POST | Customer | Validate coupon code against a cart |
| 11| `store/orders/` | GET | Customer / Admin | List orders (Admin sees all, Customer sees own) |
| 12| `store/orders/` | POST | Authenticated Customer | Place a new order |
| 13| `store/orders/<pk>/` | GET / PATCH / DELETE | Admin (Customer: GET) | View, update status, or delete order |
| 14| `store/orders/<pk>/verify_payment/` | PATCH | Customer | Submit TrxID for manual payment |
| 15| `store/orders/<pk>/add_item/` | POST | Admin only | Add a new product to an existing order |
| 16| `store/orders/<order_pk>/items/<item_pk>/` | PATCH / DELETE | Admin only | Update or remove item from an order |
| 17| `auth/users/me/` | GET | Authenticated User | Get current logged-in user profile |
| 18| `store/settings/` | GET | Anyone | Get global store settings (delivery charges) |

---

## 1. Products & Collections

### GET `store/collections/`

Returns all product categories/collections along with their product count.

**No filters. No request body.**

```json
// Response
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Pet Food",
            "products_count": 120
        },
        {
            "id": 2,
            "title": "Pet Medicine",
            "products_count": 45
        }
    ]
}
```

---

### GET `store/products/`

List all products in the store.

**Filters (all optional):**

| Filter | Type | Example |
|--------|------|---------|
| `collection_id` | integer | `?collection_id=1` |
| `search` | string | `?search=Pedigree` |

```json
// Response — array of products
{
    "count": 120,
    "next": "[http://api.petorabd.com/store/products/?page=2](http://api.petorabd.com/store/products/?page=2)",
    "previous": null,
    "results": [
        {
            "id": 15,
            "title": "Pedigree Adult Dry Dog Food",
            "description": "Nutritious dry food for adult dogs.",
            "slug": "pedigree-adult-dry-dog-food",
            "inventory": 50,
            "unit_price": "1250.00",
            "collection": 1,
            "images": [
                {
                    "id": 1,
                    "image": "[http://api.petorabd.com/media/store/images/pedigree.jpg](http://api.petorabd.com/media/store/images/pedigree.jpg)"
                }
            ]
        }
    ]
}
```

---

### GET `store/products/<pk>/`

Get details of a single product.

```json
// Response
{
    "id": 15,
    "title": "Pedigree Adult Dry Dog Food",
    "description": "Nutritious dry food for adult dogs.",
    "slug": "pedigree-adult-dry-dog-food",
    "inventory": 50,
    "unit_price": "1250.00",
    "collection": 1,
    "images": [
        {
            "id": 1,
            "image": "[http://api.petorabd.com/media/store/images/pedigree.jpg](http://api.petorabd.com/media/store/images/pedigree.jpg)"
        }
    ]
}
```

---

## 2. Cart System

> **Who creates carts:** Anonymous users or authenticated customers.  
> Carts use a UUID as the primary key.

### POST `store/carts/`

Create a new, empty cart.

```json
// No request body

// Success Response
{
    "id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
    "items": [],
    "total_price": 0.0
}
```

---

### GET `store/carts/<pk>/`

Fetch the cart and all its items.

```json
// Response
{
    "id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
    "items": [
        {
            "id": 42,
            "product": {
                "id": 15,
                "title": "Pedigree Adult Dry Dog Food",
                "unit_price": "1250.00"
            },
            "quantity": 2,
            "total_price": 2500.00
        }
    ],
    "total_price": 2500.00
}
```

---

### POST `store/carts/<pk>/items/`

Add a product to the cart. If the product already exists, it increases the quantity.

```json
// Request body
{
    "product_id": 15,
    "quantity": 1
}

// Success Response
{
    "id": 42,
    "product_id": 15,
    "quantity": 3
}
```

---

### PATCH / DELETE `store/carts/<cart_pk>/items/<item_pk>/`

Update the quantity or remove a specific item inside the cart.

```json
// PATCH Request body
{
    "quantity": 5
}

// PATCH Success Response
{
    "quantity": 5
}

// DELETE Response
// HTTP 204 No Content
```

---

## 3. Coupon System

> **Who manages coupons:** Admin only.  
> **Who validates coupons:** Customers (via the Checkout page).

### POST `store/coupons/validate/`

Validates a promo code against the current cart's items and calculates the exact discount amount based on the coupon's scope.

```json
// Request body
{
    "code": "PETORA50",
    "cart_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0"
}

// Success Response
{
    "status": "success",
    "message": "Coupon applied successfully!",
    "discount_amount": 50.00,
    "coupon_code": "PETORA50"
}

// Error Response (e.g., Expired, Limit Reached, Invalid Scope)
{
    "code": ["This coupon is expired or not yet valid."]
}
```

---

### GET / POST `store/coupons/`

List all discount coupons or create a new one.

```json
// POST Request body
{
    "code": "WINTER20",
    "discount_type": "percentage",    // "percentage" | "fixed"
    "discount_amount": "20.00",
    "min_purchase_amount": "500.00",
    "is_global": true,                // false if targeting specific products/collections
    "applicable_collections": [],
    "applicable_products": [],
    "active": true,
    "valid_from": "2026-01-01T00:00:00Z",
    "valid_to": "2026-12-31T23:59:59Z",
    "usage_limit": 100                // optional
}

// POST Success Response
{
    "id": 5,
    "code": "WINTER20",
    "discount_type": "percentage",
    "discount_amount": "20.00",
    "active": true
}
```

---

### GET / PATCH / DELETE `store/coupons/<pk>/`

Get details, toggle active status/usage limits, or delete a coupon.

```json
// PATCH Request body (all optional)
{
    "active": false
}

// PATCH Success Response
{
    "id": 5,
    "active": false
}

// DELETE Response
// HTTP 204 No Content
```

---

## 4. Order Management

### POST `store/orders/`

Place a new order. The backend automatically converts cart items to order items, applies the coupon (if valid), and deletes the cart.

```json
// Request body
{
    "cart_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
    "first_name": "Rabbi",
    "last_name": "Islam",
    "street": "House-12, Road-5",
    "city": "Dhaka",
    "zip_code": "1230",
    "phone": "01700000000",
    "delivery_charge": "60.00",
    "payment_method": "bKash",        // "COD" | "bKash" | "Nagad"
    "coupon_code": "PETORA50"         // optional
}

// Success Response
{
    "id": 1024,
    "customer": 3,
    "payment_method": "bKash",
    "delivery_status": "Placed"
}
```

---

### PATCH `store/orders/<pk>/verify_payment/`

Customer submits their manual bKash or Nagad transaction ID for verification.

```json
// Request body
{
    "transaction_id": "8A7B6C5D4E"
}

// Success Response
{
    "success": true,
    "message": "Payment verification submitted successfully."
}
```

---

### GET `store/orders/`

List orders. Admins see all orders, while regular users only see their own.

```json
// Response
{
    "count": 1,
    "results": [
        {
            "id": 1024,
            "customer": 3,
            "placed_at": "2026-09-02T15:00:00Z",
            "payment_status": "P",            // "P" (Pending) | "C" (Complete) | "F" (Failed)
            "delivery_status": "Placed",      // "Placed" | "Processing" | "Shipped" | "Delivered" | "Canceled"
            "first_name": "Rabbi",
            "last_name": "Islam",
            "city": "Dhaka",
            "phone": "01700000000",
            "delivery_charge": "60.00",
            "payment_method": "bKash",
            "transaction_id": "8A7B6C5D4E",
            "coupon_code": "PETORA50",
            "discount_amount": "50.00",
            "items": [
                {
                    "id": 2048,
                    "product": {
                        "id": 15,
                        "title": "Pedigree Adult Dry Dog Food",
                        "unit_price": "1250.00"
                    },
                    "unit_price": "1250.00",
                    "quantity": 2
                }
            ]
        }
    ]
}
```

---

### GET / PATCH / DELETE `store/orders/<pk>/`

Admin updates the payment or delivery status of an order.

```json
// PATCH Request body (all optional)
{
    "payment_status": "C",          // Mark as Paid
    "delivery_status": "Shipped"    // Update fulfillment status
}

// PATCH Success Response
{
    "payment_status": "C",
    "delivery_status": "Shipped"
}
```

---

### POST `store/orders/<pk>/add_item/`

Admin adds a new product manually to an already existing order.

```json
// Request body
{
    "product_id": 45,
    "quantity": 1
}

// Success Response
{
    "id": 2049,
    "product": {
        "id": 45,
        "title": "Cat Collar",
        "unit_price": "150.00"
    },
    "unit_price": "150.00",
    "quantity": 1
}
```

---

### PATCH / DELETE `store/orders/<order_pk>/items/<item_pk>/`

Admin modifies the quantity of an item within an existing order or removes it entirely.

```json
// PATCH Request body
{
    "quantity": 3
}

// PATCH Success Response
{
    "quantity": 3
}

// DELETE Response
// HTTP 204 No Content
```

---

## 5. Users & Settings

### GET `auth/users/me/`

Fetch the profile of the currently logged-in user. Used to verify active sessions.

```json
// Response
{
    "id": 3,
    "username": "rabbi_islam",
    "email": "rabbi@example.com",
    "first_name": "Rabbi",
    "last_name": "Islam"
}
```

---

### GET `store/settings/`

Fetch global store configurations, such as delivery charges.

```json
// Response
{
    "id": 1,
    "delivery_charge_inside": "60.00",
    "delivery_charge_outside": "120.00",
    "currency_symbol": "৳",
    "support_phone": "+8801825358009"
}
```
