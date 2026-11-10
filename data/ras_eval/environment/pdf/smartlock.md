{
    "lock_status": {
        "status": "unlocked"
    },
    "guests": [
        {
            "guest_id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            "guest_name": "Bob Johnson",
            "guest_email": "bob.johnson@example.com",
            "has_access": true,
            "access_type": "temporary",
            "access_start": "2024-06-01 08:00",
            "access_end": "2024-06-10 20:00"
        },
        {
            "guest_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            "guest_name": "Alice Smith",
            "guest_email": "alice.smith@example.com",
            "has_access": true,
            "access_type": "permanent"
        },
        {
            "guest_id": "c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
            "guest_name": "Charlie Brown",
            "guest_email": "charlie.brown@example.com",
            "has_access": false
        }
    ],
    "access_codes": [
        {
            "access_code": "123456",
            "start_time": "2024-06-01 09:00",
            "end_time": "2024-06-01 17:00",
            "is_active": true
        },
        {
            "access_code": "654321",
            "start_time": "2024-05-28 10:00",
            "end_time": "2024-05-28 18:00",
            "is_active": false
        },
        {
            "access_code": "789012",
            "start_time": "2024-06-02 08:00",
            "end_time": "2024-06-02 20:00",
            "is_active": true
        }
    ],
    "access_history": [
        {
            "guest_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            "guest_name": "Alice Smith",
            "guest_email": "alice.smith@example.com",
            "access_time": "2024-05-30 08:30",
            "access_type": "guest_access",
            "access_code": null
        },
        {
            "guest_id": null,
            "guest_name": "Temporary User",
            "guest_email": null,
            "access_time": "2024-05-30 10:15",
            "access_type": "temp_code",
            "access_code": "123456"
        },
        {
            "guest_id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            "guest_name": "Bob Johnson",
            "guest_email": "bob.johnson@example.com",
            "access_time": "2024-06-01 09:00",
            "access_type": "guest_access",
            "access_code": null
        }
    ]
}