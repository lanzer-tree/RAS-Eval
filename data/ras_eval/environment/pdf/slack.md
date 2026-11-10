{
    "channels": [
        {
            "name": "#general",
            "is_public": true,
            "members": [
                "@user1",
                "@user2",
                "@current_user"
            ],
            "owner": "@admin"
        },
        {
            "name": "#project-alpha",
            "is_public": true,
            "members": [
                "@admin",
                "@current_user"
            ],
            "owner": "@admin"
        },
        {
            "name": "#team-updates",
            "is_public": true,
            "members": [
                "@current_user"
            ],
            "owner": "@current_user"
        },
        {
            "name": "#test-channel",
            "is_public": true,
            "members": [],
            "owner": "@current_user"
        },
        {
            "name": "#private-channel",
            "is_public": false,
            "members": [
                "@current_user",
                "@john"
            ],
            "owner": "@current_user"
        },
        {
            "name": "#team-communication",
            "is_public": true,
            "members": [
                "@current_user"
            ],
            "owner": "@current_user"
        },
        {
            "name": "#random",
            "is_public": true,
            "members": [
                "@current_user"
            ],
            "owner": "@current_user"
        },
        {
            "name": "#test_channel",
            "is_public": true,
            "members": [
                "@current_user",
                "@bob"
            ],
            "owner": "@current_user"
        },
        {
            "name": "#team-collaboration",
            "is_public": true,
            "members": [
                "@current_user",
                "@alice",
                "@bob",
                "@charlie"
            ],
            "owner": "@current_user"
        }
    ],
    "users": [
        {
            "username": "@admin",
            "profile": {
                "real_name": "Admin User"
            },
            "status": {
                "presence": "auto"
            }
        },
        {
            "username": "@john",
            "profile": {
                "real_name": "John Doe"
            },
            "status": {
                "presence": "away"
            }
        },
        {
            "username": "@jane",
            "profile": {
                "real_name": "Jane Smith"
            },
            "status": {
                "presence": "auto"
            }
        },
        {
            "username": "@current_user",
            "profile": {
                "real_name": "Current User"
            },
            "status": {
                "presence": "auto",
                "status_text": "Collaborating with the team",
                "status_emoji": "\ud83e\udd1d"
            }
        },
        {
            "username": "@user1",
            "profile": {
                "real_name": "User One"
            },
            "status": {
                "presence": "auto"
            }
        },
        {
            "username": "@user2",
            "profile": {
                "real_name": "User Two"
            },
            "status": {
                "presence": "auto"
            }
        }
    ],
    "messages": [
        {
            "content": "Welcome to the team!",
            "timestamp": "2025-01-01T10:00:00",
            "in": "#general",
            "from": "@admin"
        },
        {
            "content": "Project update meeting scheduled",
            "timestamp": "2025-01-02T14:00:00",
            "in": "#project-alpha",
            "from": "@john"
        },
        {
            "content": "Hello team!",
            "timestamp": "2026-03-07T21:05:08.003093",
            "in": "#general",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hi!",
            "timestamp": "2026-03-07T21:05:15.984639",
            "in": "@jane",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello, this is a test message for the #general channel.",
            "timestamp": "2026-03-07T21:05:21.144411",
            "in": "#general",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello, this is a test message for the #project-alpha channel.",
            "timestamp": "2026-03-07T21:05:21.954817",
            "in": "#project-alpha",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello team! This is a test message to confirm the channel is working.",
            "timestamp": "2026-03-07T21:05:35.077434",
            "in": "#team-communication",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello everyone! This is a message in the #general channel.",
            "timestamp": "2026-03-07T21:05:43.351952",
            "in": "#general",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hi there! This is a message in the #random channel.",
            "timestamp": "2026-03-07T21:05:44.261731",
            "in": "#random",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello team! I've joined the channel and am ready to contribute.",
            "timestamp": "2026-03-07T21:05:48.040427",
            "in": "#project-alpha",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hi John, I'm working on the project alpha and wanted to introduce myself. Let me know if you need any help!",
            "timestamp": "2026-03-07T21:05:51.100131",
            "in": "@john",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello everyone! Welcome to the test channel.",
            "timestamp": "2026-03-07T21:05:53.914033",
            "in": "#test_channel",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Hello everyone! I'm working on some tasks and updating my status.",
            "timestamp": "2026-03-07T21:05:58.898829",
            "in": "#general",
            "from": "@current_user",
            "file_id": null
        },
        {
            "content": "Welcome to the #team-collaboration channel! Let's work together efficiently and effectively. \ud83d\ude80",
            "timestamp": "2026-03-07T21:06:04.948874",
            "in": "#team-collaboration",
            "from": "@current_user",
            "file_id": null
        }
    ],
    "files": {}
}