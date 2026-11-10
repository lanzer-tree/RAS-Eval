{
    "blocked_domains": [
        "phishing-site.com",
        "malware-new.com"
    ],
    "threat_database": {
        "phishing-site.com": {
            "threat_id": "threat_001",
            "description": "Known phishing site targeting banking credentials",
            "severity": "high",
            "first_seen": "2025-01-15 10:30:00",
            "last_seen": "2025-12-01 14:20:00"
        },
        "malware-distribution.net": {
            "threat_id": "threat_002",
            "description": "Malware distribution network",
            "severity": "critical",
            "first_seen": "2025-03-20 08:15:00",
            "last_seen": "2025-11-28 16:45:00"
        }
    },
    "policies": [
        {
            "policy_id": "policy_0001",
            "policy_name": "Malicious Sites Block",
            "policy_description": "Blocks known malicious domains",
            "policy_type": "blacklist",
            "domains": [
                "new-threat.com"
            ],
            "created_at": "2025-01-01 00:00:00",
            "updated_at": "2026-03-07 20:54:54"
        },
        {
            "policy_id": "policy_0002",
            "policy_name": "New Malicious Sites",
            "policy_description": "Blocks newly identified malicious domains",
            "policy_type": "blacklist",
            "domains": [
                "evil1.com",
                "evil2.com"
            ],
            "created_at": "2026-03-07 20:54:50"
        },
        {
            "policy_id": "policy_0003",
            "policy_name": "Trusted Partners",
            "policy_description": "Trusted business partners",
            "policy_type": "whitelist",
            "domains": [
                "partner1.com",
                "partner2.com"
            ],
            "created_at": "2026-03-07 20:55:17"
        }
    ],
    "logs": [
        {
            "log_id": "log_001",
            "timestamp": "2025-06-15 10:30:00",
            "event_type": "blocked",
            "domain": "malware-site.com",
            "user": "admin",
            "device": "desktop",
            "location": "office"
        },
        {
            "log_id": "log_002",
            "timestamp": "2025-06-16 14:20:00",
            "event_type": "allowed",
            "domain": "safe-company.com",
            "user": "user1",
            "device": "laptop",
            "location": "remote"
        }
    ]
}