{
  "users": {
    "12345": {
      "user_id": "12345",
      "username": "test_user",
      "email": "test@example.com",
      "connected_apps": ["email", "facebook"],
      "flows": []
    }
  },
  "apps": [
    {
      "app_id": "gmail",
      "app_name": "Gmail",
      "app_category": "communication",
      "description": "Google email service",
      "auth_type": "oauth2",
      "supported_triggers": [
        {"trigger_id": "new_email", "trigger_name": "New Email", "trigger_description": "Triggers when a new email arrives"}
      ],
      "supported_actions": [
        {"action_id": "send_email", "action_name": "Send Email", "action_description": "Send an email"},
        {"action_id": "read_email", "action_name": "Read Email", "action_description": "Read an email"}
      ]
    },
    {
      "app_id": "facebook",
      "app_name": "Facebook",
      "app_category": "social",
      "description": "Facebook social media platform",
      "auth_type": "oauth2",
      "supported_triggers": [],
      "supported_actions": [
        {"action_id": "post_to_page", "action_name": "Post to Page", "action_description": "Create a post on a Facebook page"},
        {"action_id": "post_to_timeline", "action_name": "Post to Timeline", "action_description": "Create a post on user's timeline"}
      ]
    }
  ]
}
