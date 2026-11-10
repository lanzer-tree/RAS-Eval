{
    "merchants": [
        {
            "merchant_id": "merchant_001",
            "name": "Golden Dragon Restaurant",
            "category": "Chinese",
            "category_en": "Chinese",
            "category_aliases": [
                "中餐",
                "川菜"
            ],
            "rating": 4.5,
            "delivery_fee": 5.0,
            "distance": 2.5,
            "address": "123 Food Street, Beijing",
            "description": "Authentic Chinese cuisine",
            "average_price": 40,
            "estimate": "30 mins",
            "filters": [
                "fast_delivery",
                "free_delivery_over_50"
            ],
            "menu": [
                {
                    "product_id": "product_001",
                    "name": "Kung Pao Chicken",
                    "price": 35
                },
                {
                    "product_id": "product_002",
                    "name": "Sweet and Sour Pork",
                    "price": 38
                }
            ],
            "reviews": []
        },
        {
            "merchant_id": "merchant_002",
            "name": "Noodle House",
            "category": "Chinese",
            "category_en": "Chinese",
            "category_aliases": [
                "面馆"
            ],
            "rating": 4.3,
            "delivery_fee": 3.0,
            "distance": 1.5,
            "address": "456 Noodle Lane, Shanghai",
            "description": "Fresh handmade noodles",
            "average_price": 30,
            "estimate": "25 mins",
            "filters": [
                "fast_delivery"
            ],
            "menu": [],
            "reviews": []
        }
    ],
    "products": [
        {
            "product_id": "product_001",
            "name": "Kung Pao Chicken",
            "description": "Spicy stir-fried chicken with peanuts",
            "merchant_id": "merchant_001",
            "price": 35,
            "rating": 4.5,
            "sales": 100,
            "stock": 48,
            "specs": [
                {
                    "label": "Spicy",
                    "price": 35
                },
                {
                    "label": "Mild",
                    "price": 35
                }
            ],
            "promotions": []
        },
        {
            "product_id": "product_002",
            "name": "Sweet and Sour Pork",
            "description": "Classic sweet and sour pork dish",
            "merchant_id": "merchant_001",
            "price": 38,
            "rating": 4.3,
            "sales": 80,
            "stock": 40,
            "specs": [],
            "promotions": []
        },
        {
            "product_id": "product_003",
            "name": "Beef Noodles",
            "description": "Handmade noodles with beef broth",
            "merchant_id": "merchant_002",
            "price": 28,
            "rating": 4.6,
            "sales": 150,
            "stock": 58,
            "specs": [
                {
                    "label": "Large",
                    "price": 33
                },
                {
                    "label": "Regular",
                    "price": 28
                }
            ],
            "promotions": []
        }
    ],
    "users": [
        {
            "user_id": "user_001",
            "name": "John Doe",
            "phone": "123456789",
            "address": "123 Main St, Beijing"
        },
        {
            "user_id": "user_002",
            "name": "Jane Smith",
            "phone": "987654321",
            "address": "456 Oak Ave, Shanghai"
        },
        {
            "user_id": "user_003",
            "name": "Bob Johnson",
            "phone": "555123456",
            "address": "789 Pine St, Guangzhou"
        }
    ],
    "coupons": [
        {
            "coupon_id": "coupon_001",
            "discount": 10,
            "min_amount": 50,
            "merchant_id": "merchant_001"
        }
    ],
    "orders": [
        {
            "order_id": "ORD1001",
            "user_id": "user_001",
            "merchant_id": "merchant_001",
            "products": [
                {
                    "product_id": "product_001",
                    "name": "Kung Pao Chicken",
                    "price": 35,
                    "quantity": 1
                }
            ],
            "delivery_address": {
                "name": "John Doe",
                "phone": "123456789",
                "address": "123 Main St, Beijing"
            },
            "notes": "Extra spicy please",
            "coupon_id": null,
            "payment_method": "WeChat",
            "scheduled_delivery": null,
            "delivery_fee": 5.0,
            "discount": 0,
            "items_total": 35,
            "total_amount": 40.0,
            "status": "pending_payment",
            "created_at": "2026-03-07T10:00:00Z",
            "estimated_arrival": "2026-03-07T10:30:00Z"
        },
        {
            "order_id": "ORD1002",
            "user_id": "user_001",
            "merchant_id": "merchant_001",
            "products": [
                {
                    "product_id": "product_002",
                    "name": "Sweet and Sour Pork",
                    "price": 38,
                    "quantity": 1
                }
            ],
            "delivery_address": {
                "name": "John Doe",
                "phone": "123456789",
                "address": "123 Main St, Beijing"
            },
            "notes": "No onions please",
            "coupon_id": null,
            "payment_method": "WeChat",
            "scheduled_delivery": null,
            "delivery_fee": 5.0,
            "discount": 0,
            "items_total": 38,
            "total_amount": 43.0,
            "status": "pending",
            "created_at": "2026-03-07T11:00:00Z",
            "estimated_arrival": "2026-03-07T11:30:00Z"
        },
        {
            "order_id": "ORD1003",
            "user_id": "user_001",
            "merchant_id": "merchant_001",
            "products": [
                {
                    "product_id": "product_001",
                    "name": "Kung Pao Chicken",
                    "price": 35,
                    "quantity": 2
                }
            ],
            "delivery_address": {
                "name": "John Doe",
                "phone": "123456789",
                "address": "123 Main St, Beijing"
            },
            "notes": "Lunch order",
            "coupon_id": null,
            "payment_method": "WeChat",
            "scheduled_delivery": null,
            "delivery_fee": 5.0,
            "discount": 0,
            "items_total": 70,
            "total_amount": 75.0,
            "status": "delivering",
            "created_at": "2026-03-07T09:00:00Z",
            "estimated_arrival": "2026-03-07T09:30:00Z"
        },
        {
            "order_id": "ORD1004",
            "user_id": "user_001",
            "merchant_id": "merchant_001",
            "products": [
                {
                    "product_id": "product_002",
                    "name": "Sweet and Sour Pork",
                    "price": 38,
                    "quantity": 1
                },
                {
                    "product_id": "product_001",
                    "name": "Kung Pao Chicken",
                    "price": 35,
                    "quantity": 1
                }
            ],
            "delivery_address": {
                "name": "John Doe",
                "phone": "123456789",
                "address": "123 Main St, Beijing"
            },
            "notes": "Dinner order",
            "coupon_id": "coupon_001",
            "payment_method": "WeChat",
            "scheduled_delivery": null,
            "delivery_fee": 5.0,
            "discount": 10,
            "items_total": 73,
            "total_amount": 68.0,
            "status": "delivered",
            "created_at": "2026-03-06T18:00:00Z",
            "estimated_arrival": "2026-03-06T18:30:00Z"
        },
        {
            "order_id": "TA-1006",
            "user_id": "user_001",
            "merchant_id": "merchant_001",
            "products": [
                {
                    "product_id": "product_001",
                    "name": "Kung Pao Chicken",
                    "quantity": 1,
                    "unit_price": 35,
                    "spec": "Spicy"
                }
            ],
            "delivery_address": {
                "name": "John Doe",
                "phone": "13800138000",
                "address": "123 Main St, Beijing"
            },
            "notes": "Please include extra peanuts",
            "coupon_id": null,
            "payment_method": "WeChat",
            "scheduled_delivery": null,
            "delivery_fee": 5.0,
            "discount": 0.0,
            "items_total": 35.0,
            "total_amount": 40.0,
            "status": "pending_payment",
            "created_at": "2026-03-07T13:07:07.809558",
            "estimated_arrival": "2026-03-07T13:22:00"
        },
        {
            "order_id": "TA-1007",
            "user_id": "user_001",
            "merchant_id": "merchant_001",
            "products": [
                {
                    "product_id": "product_001",
                    "name": "Kung Pao Chicken",
                    "quantity": 1,
                    "unit_price": 35,
                    "spec": "Spicy"
                }
            ],
            "delivery_address": {
                "name": "Alice Smith",
                "phone": "+8613800138000",
                "address": "456 Central Park Avenue, Beijing"
            },
            "notes": "Extra spicy",
            "coupon_id": null,
            "payment_method": "WeChat",
            "scheduled_delivery": null,
            "delivery_fee": 5.0,
            "discount": 0.0,
            "items_total": 35.0,
            "total_amount": 40.0,
            "status": "pending_payment",
            "created_at": "2026-03-07T13:07:41.878013",
            "estimated_arrival": "2026-03-07T13:22:00"
        },
        {
            "order_id": "TA-1008",
            "user_id": "user_001",
            "merchant_id": "merchant_002",
            "products": [
                {
                    "product_id": "product_003",
                    "name": "Beef Noodles",
                    "quantity": 2,
                    "unit_price": 28,
                    "spec": "Regular"
                }
            ],
            "delivery_address": {
                "name": "Alice Smith",
                "phone": "13800138000",
                "address": "789 Flower Street, Shanghai"
            },
            "notes": "Extra sauce on the side",
            "coupon_id": null,
            "payment_method": "WeChat",
            "scheduled_delivery": "2023-04-15T18:30:00Z",
            "delivery_fee": 3.0,
            "discount": 0.0,
            "items_total": 56.0,
            "total_amount": 59.0,
            "status": "pending_payment",
            "created_at": "2026-03-07T13:08:34.264927",
            "estimated_arrival": "2023-04-15T18:30:00Z"
        }
    ],
    "order_sequence": 1008
}