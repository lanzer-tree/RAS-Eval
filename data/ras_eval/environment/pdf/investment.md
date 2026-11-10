{
    "accounts": {
        "checking": {
            "cash": 5000.0,
            "holdings": [
                {
                    "type": "etf",
                    "name": "S&P 500 ETF",
                    "amount": 3500,
                    "return": 7.0
                },
                {
                    "type": "mutual_fund",
                    "name": "Growth Fund",
                    "amount": 1500,
                    "return": 8.5
                }
            ]
        },
        "savings": {
            "cash": 50000.0,
            "holdings": []
        },
        "primary": {
            "cash": 10000.0,
            "holdings": []
        },
        "investment": {
            "cash": 25000.0,
            "holdings": []
        },
        "brokerage": {
            "cash": 15000.0,
            "holdings": []
        }
    },
    "investment_options": [
        {
            "type": "mutual_fund",
            "name": "Growth Fund",
            "description": "High growth potential mutual fund",
            "min_purchase_amount": 1000.0,
            "return": 8.5
        },
        {
            "type": "etf",
            "name": "S&P 500 ETF",
            "description": "S&P 500 index fund ETF",
            "min_purchase_amount": 500.0,
            "return": 7.0
        },
        {
            "type": "gic",
            "name": "5-Year GIC",
            "description": "5 year guaranteed investment certificate",
            "min_purchase_amount": 1000.0,
            "return": 4.0
        }
    ],
    "transactions": [
        {
            "date": "2026-03-07",
            "account": "checking",
            "type": "etf",
            "name": "S&P 500 ETF",
            "action": "buy",
            "amount": 2000
        },
        {
            "date": "2026-03-07",
            "account": "checking",
            "type": "mutual_fund",
            "name": "Growth Fund",
            "action": "buy",
            "amount": 1500
        },
        {
            "date": "2026-03-07",
            "account": "checking",
            "type": "etf",
            "name": "S&P 500 ETF",
            "action": "buy",
            "amount": 1000
        },
        {
            "date": "2026-03-07",
            "account": "checking",
            "type": "etf",
            "name": "S&P 500 ETF",
            "action": "sell",
            "amount": 500
        },
        {
            "date": "2026-03-07",
            "account": "checking",
            "type": "etf",
            "name": "S&P 500 ETF",
            "action": "buy",
            "amount": 1000
        }
    ]
}