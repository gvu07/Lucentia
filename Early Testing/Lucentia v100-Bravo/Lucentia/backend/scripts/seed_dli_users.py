from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional

import os
import sys
from pathlib import Path

os.environ.setdefault("PLAID_CLIENT_ID", "seed-script-placeholder")
os.environ.setdefault("PLAID_SECRET", "seed-script-placeholder")
os.environ.setdefault("PLAID_ENV", "sandbox")
os.environ.setdefault("DATABASE_URL", "sqlite:///seed_dli.db")

try:
    from backend.app import models
    from backend.app.database import SessionLocal
    from .seed_sample_data import ensure_account, ensure_user, regenerate_insights
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app import models  # type: ignore
    from app.database import SessionLocal  # type: ignore
    from scripts.seed_sample_data import ensure_account, ensure_user, regenerate_insights  # type: ignore


MONTHS_OF_HISTORY = 6
USER_PROFILES = {
    "struggling": {
        "income": [
            {
                "name": "Retail Shift Payroll",
                "merchant": "Ann Arbor Retail Co",
                "amount": Decimal("-1500.00"),
                "category_primary": "INCOME",
                "category_detailed": "SALARY_WAGES",
            },
            {
                "name": "Rideshare Payout",
                "merchant": "Lyft Driver",
                "amount": Decimal("-320.00"),
                "category_primary": "INCOME",
                "category_detailed": "FREELANCE_INCOME",
            },
        ],
        "spending": [
            {
                "merchant": "CheckSmart Payday",
                "name": "CheckSmart Loan Payment",
                "category_primary": "BANK_FEES",
                "category_detailed": "PAYDAY_LOANS",
                "amount": Decimal("85.00"),
                "frequency": 2,
            },
            {
                "merchant": "Meijer",
                "name": "Meijer Essentials",
                "category_primary": "GENERAL_MERCHANDISE",
                "category_detailed": "DISCOUNT_STORES",
                "amount": Decimal("60.00"),
                "frequency": 4,
            },
            {
                "merchant": "McDonald's Packard",
                "name": "McDonald's",
                "category_primary": "FOOD_AND_DRINK",
                "category_detailed": "FAST_FOOD",
                "amount": Decimal("14.50"),
                "frequency": 6,
            },
            {
                "merchant": "AATA",
                "name": "AATA Bus Pass",
                "category_primary": "TRANSPORTATION",
                "category_detailed": "PUBLIC_TRANSIT",
                "amount": Decimal("25.00"),
                "frequency": 2,
            },
            {
                "merchant": "Rent Payment",
                "name": "Washtenaw Housing",
                "category_primary": "RENT_AND_UTILITIES",
                "category_detailed": "RENT",
                "amount": Decimal("900.00"),
                "frequency": 1,
            },
            {
                "merchant": "Speedway Gas",
                "name": "Gas Station",
                "category_primary": "TRANSPORTATION",
                "category_detailed": "FUEL",
                "amount": Decimal("40.00"),
                "frequency": 3,
            },
            {
                "merchant": "Little Caesars",
                "name": "Little Caesars Ann Arbor",
                "category_primary": "FOOD_AND_DRINK",
                "category_detailed": "FAST_FOOD",
                "amount": Decimal("12.00"),
                "frequency": 4,
            },
        ],
        "baseline_balance": Decimal("600.00"),
    },
    "middle": {
        "income": [
            {
                "name": "Michigan Health Systems Payroll",
                "merchant": "Michigan Health Systems",
                "amount": Decimal("-3400.00"),
                "category_primary": "INCOME",
                "category_detailed": "SALARY_WAGES",
            },
            {
                "name": "Freelance Consulting",
                "merchant": "Midwest Consulting",
                "amount": Decimal("-550.00"),
                "category_primary": "INCOME",
                "category_detailed": "FREELANCE_INCOME",
            },
        ],
        "spending": [
            {
                "merchant": "Zingerman's Roadhouse",
                "name": "Zingerman's",
                "category_primary": "FOOD_AND_DRINK",
                "category_detailed": "DINE_IN_RESTAURANT",
                "amount": Decimal("65.00"),
                "frequency": 3,
            },
            {
                "merchant": "Whole Foods",
                "name": "Whole Foods Ann Arbor",
                "category_primary": "FOOD_AND_DRINK",
                "category_detailed": "GROCERIES",
                "amount": Decimal("140.00"),
                "frequency": 2,
            },
            {
                "merchant": "Ann Arbor Mortgage",
                "name": "Mortgage Payment",
                "category_primary": "RENT_AND_UTILITIES",
                "category_detailed": "MORTGAGE",
                "amount": Decimal("1650.00"),
                "frequency": 1,
            },
            {
                "merchant": "DTE Energy",
                "name": "DTE Energy",
                "category_primary": "RENT_AND_UTILITIES",
                "category_detailed": "UTILITIES",
                "amount": Decimal("140.00"),
                "frequency": 1,
            },
            {
                "merchant": "Comcast",
                "name": "Xfinity Internet",
                "category_primary": "RENT_AND_UTILITIES",
                "category_detailed": "UTILITIES",
                "amount": Decimal("95.00"),
                "frequency": 1,
            },
            {
                "merchant": "Peloton",
                "name": "Peloton Subscription",
                "category_primary": "HEALTHCARE",
                "category_detailed": "GYM_FITNESS",
                "amount": Decimal("44.00"),
                "frequency": 1,
            },
            {
                "merchant": "State Street Boutique",
                "name": "State Street Shopping",
                "category_primary": "GENERAL_MERCHANDISE",
                "category_detailed": "CLOTHING_STORES",
                "amount": Decimal("120.00"),
                "frequency": 2,
            },
            {
                "merchant": "Toyota Financial",
                "name": "Highland Car Payment",
                "category_primary": "TRANSPORTATION",
                "category_detailed": "AUTO_FINANCE",
                "amount": Decimal("410.00"),
                "frequency": 1,
            },
        ],
        "baseline_balance": Decimal("4800.00"),
    },
    "affluent": {
        "income": [
            {
                "name": "Duo Security Payroll",
                "merchant": "Duo Security",
                "amount": Decimal("-9200.00"),
                "category_primary": "INCOME",
                "category_detailed": "SALARY_WAGES",
            },
            {
                "name": "Angel Investment Return",
                "merchant": "Midwest Ventures",
                "amount": Decimal("-2300.00"),
                "category_primary": "INCOME",
                "category_detailed": "INVESTMENT_INCOME",
            },
        ],
        "spending": [
            {
                "merchant": "The Chop House",
                "name": "The Chop House",
                "category_primary": "FOOD_AND_DRINK",
                "category_detailed": "DINE_IN_RESTAURANT",
                "amount": Decimal("185.00"),
                "frequency": 3,
            },
            {
                "merchant": "Delta Air Lines",
                "name": "Delta First Class",
                "category_primary": "TRAVEL",
                "category_detailed": "TRAVEL_FLIGHTS",
                "amount": Decimal("650.00"),
                "frequency": 2,
            },
            {
                "merchant": "Ann Arbor Country Club",
                "name": "Country Club Dues",
                "category_primary": "ENTERTAINMENT",
                "category_detailed": "CLUB_MEMBERSHIPS",
                "amount": Decimal("520.00"),
                "frequency": 1,
            },
            {
                "merchant": "TESLA FINANCE",
                "name": "Model S Lease",
                "category_primary": "TRANSPORTATION",
                "category_detailed": "AUTO_FINANCE",
                "amount": Decimal("1280.00"),
                "frequency": 1,
            },
            {
                "merchant": "IKEA Ann Arbor",
                "name": "IKEA Ann Arbor",
                "category_primary": "GENERAL_MERCHANDISE",
                "category_detailed": "FURNITURE_STORES",
                "amount": Decimal("480.00"),
                "frequency": 1,
            },
            {
                "merchant": "The Wine Seller",
                "name": "Wine Cellar Purchase",
                "category_primary": "FOOD_AND_DRINK",
                "category_detailed": "ALCOHOL_BARS",
                "amount": Decimal("240.00"),
                "frequency": 2,
            },
            {
                "merchant": "Found Gallery",
                "name": "Found Gallery Artwork",
                "category_primary": "GENERAL_MERCHANDISE",
                "category_detailed": "ART_DEALERS",
                "amount": Decimal("900.00"),
                "frequency": 1,
            },
            {
                "merchant": "Equinox",
                "name": "Equinox Elite",
                "category_primary": "HEALTHCARE",
                "category_detailed": "GYM_FITNESS",
                "amount": Decimal("280.00"),
                "frequency": 1,
            },
        ],
        "baseline_balance": Decimal("18500.00"),
    },
}

ANN_ARBOR_LOCATION = {
    "city": "Ann Arbor",
    "region": "MI",
    "country": "US",
}

DEFAULT_PASSWORD = "password123"

DLI_USERS = [
    {
        "index": 1,
        "email": "dli_test1@example.com",
        "profile": "struggling",
        "variant": {
            "income_multiplier": Decimal("0.92"),
            "spending_multiplier": Decimal("1.12"),
            "balance_delta": Decimal("-260.00"),
            "extra_income": [
                {
                    "name": "Babysitting Cash",
                    "merchant": "Neighbors on Miller",
                    "amount": Decimal("-60.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "OTHER_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Quickie Burger & Dogs",
                    "name": "Quickie Burger Late Night",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "FAST_FOOD",
                    "amount": Decimal("18.50"),
                    "frequency": 3,
                },
                {
                    "merchant": "Bank of Ann Arbor",
                    "name": "Overdraft Fee",
                    "category_primary": "BANK_FEES",
                    "category_detailed": "OVERDRAFT_FEES",
                    "amount": Decimal("35.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Marathon Packard",
                    "name": "Packard Gas Station",
                    "category_primary": "TRANSPORTATION",
                    "category_detailed": "FUEL",
                    "amount": Decimal("38.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Blue Front Ann Arbor",
                    "name": "Convenience Store Beer",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "ALCOHOL_BARS",
                    "amount": Decimal("22.00"),
                    "frequency": 2,
                },
            ],
        },
    },
    {
        "index": 2,
        "email": "dli_test2@example.com",
        "profile": "struggling",
        "variant": {
            "income_multiplier": Decimal("0.98"),
            "spending_multiplier": Decimal("1.05"),
            "balance_delta": Decimal("-180.00"),
            "extra_income": [
                {
                    "name": "Marketplace Sale",
                    "merchant": "Facebook Marketplace",
                    "amount": Decimal("-80.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "OTHER_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "DoorDash Ann Arbor",
                    "name": "DoorDash Takeout",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "FOOD_DELIVERY",
                    "amount": Decimal("28.00"),
                    "frequency": 4,
                },
                {
                    "merchant": "Planet Fitness Washtenaw",
                    "name": "Gym Membership",
                    "category_primary": "HEALTHCARE",
                    "category_detailed": "GYM_FITNESS",
                    "amount": Decimal("25.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Boost Mobile",
                    "name": "Prepaid Phone",
                    "category_primary": "RENT_AND_UTILITIES",
                    "category_detailed": "UTILITIES",
                    "amount": Decimal("55.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "7-Eleven Packard",
                    "name": "7-Eleven Snacks",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "CONVENIENCE_STORES",
                    "amount": Decimal("17.00"),
                    "frequency": 3,
                },
            ],
        },
    },
    {
        "index": 3,
        "email": "dli_test3@example.com",
        "profile": "struggling",
        "variant": {
            "income_multiplier": Decimal("0.95"),
            "spending_multiplier": Decimal("1.15"),
            "balance_delta": Decimal("-140.00"),
            "extra_income": [
                {
                    "name": "Odd Job Cash",
                    "merchant": "Side Work",
                    "amount": Decimal("-45.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "OTHER_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Xbox Live Marketplace",
                    "name": "Gaming Microtransaction",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "DIGITAL_GAMING",
                    "amount": Decimal("9.99"),
                    "frequency": 5,
                },
                {
                    "merchant": "Uber",
                    "name": "Late Night Ride",
                    "category_primary": "TRANSPORTATION",
                    "category_detailed": "RIDESHARE",
                    "amount": Decimal("24.00"),
                    "frequency": 4,
                },
                {
                    "merchant": "Rent-A-Center",
                    "name": "Furniture Payment",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "FURNITURE_STORES",
                    "amount": Decimal("110.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Ypsilanti Coney",
                    "name": "Coney Island Combo",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "FAST_FOOD",
                    "amount": Decimal("15.00"),
                    "frequency": 4,
                },
            ],
        },
    },
    {
        "index": 4,
        "email": "dli_test4@example.com",
        "profile": "middle",
        "variant": {
            "income_multiplier": Decimal("1.03"),
            "spending_multiplier": Decimal("1.02"),
            "balance_delta": Decimal("250.00"),
            "extra_income": [
                {
                    "name": "Clinical Performance Bonus",
                    "merchant": "Michigan Health Systems",
                    "amount": Decimal("-400.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "BONUS",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Ann Arbor YMCA",
                    "name": "YMCA Membership",
                    "category_primary": "HEALTHCARE",
                    "category_detailed": "GYM_FITNESS",
                    "amount": Decimal("72.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Ann Arbor Farmers Market",
                    "name": "Market Produce",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "GROCERIES",
                    "amount": Decimal("85.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Trader Joe's",
                    "name": "Trader Joe's Grocery",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "GROCERIES",
                    "amount": Decimal("160.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Ann Arbor Civic Theatre",
                    "name": "Theatre Donation",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "CULTURE_EVENTS",
                    "amount": Decimal("60.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Arbor Brewing Company",
                    "name": "Arbor Brewing Meetup",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "BARS",
                    "amount": Decimal("48.00"),
                    "frequency": 2,
                },
            ],
        },
    },
    {
        "index": 5,
        "email": "dli_test5@example.com",
        "profile": "middle",
        "variant": {
            "income_multiplier": Decimal("1.01"),
            "spending_multiplier": Decimal("1.08"),
            "balance_delta": Decimal("600.00"),
            "extra_income": [
                {
                    "name": "UX Workshop Honorarium",
                    "merchant": "Ann Arbor Startups",
                    "amount": Decimal("-620.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "FREELANCE_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Michigan Athletics",
                    "name": "Season Tickets",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "SPORTS_EVENTS",
                    "amount": Decimal("220.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "RoosRoast Coffee",
                    "name": "RoosRoast Beans",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "COFFEE",
                    "amount": Decimal("18.00"),
                    "frequency": 4,
                },
                {
                    "merchant": "Ann Arbor Fiber",
                    "name": "Fiber Internet",
                    "category_primary": "RENT_AND_UTILITIES",
                    "category_detailed": "UTILITIES",
                    "amount": Decimal("80.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "REI Ann Arbor",
                    "name": "Outdoor Gear",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "SPORTING_GOODS",
                    "amount": Decimal("190.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Hands-On Museum",
                    "name": "Museum Membership",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "MUSEUMS",
                    "amount": Decimal("45.00"),
                    "frequency": 1,
                },
            ],
        },
    },
    {
        "index": 6,
        "email": "dli_test6@example.com",
        "profile": "middle",
        "variant": {
            "income_multiplier": Decimal("0.98"),
            "spending_multiplier": Decimal("1.06"),
            "balance_delta": Decimal("340.00"),
            "extra_income": [
                {
                    "name": "Partner Commission",
                    "merchant": "Keller Williams Ann Arbor",
                    "amount": Decimal("-850.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "COMMISSION",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Zingerman's Bakehouse",
                    "name": "Bakehouse Breakfast",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "GROCERIES",
                    "amount": Decimal("48.00"),
                    "frequency": 3,
                },
                {
                    "merchant": "OrangeTheory Ann Arbor",
                    "name": "OrangeTheory Class",
                    "category_primary": "HEALTHCARE",
                    "category_detailed": "GYM_FITNESS",
                    "amount": Decimal("32.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Michigan Avenue Montessori",
                    "name": "Childcare Tuition",
                    "category_primary": "GENERAL_SERVICES",
                    "category_detailed": "EDUCATION",
                    "amount": Decimal("540.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "AATA Transit",
                    "name": "Transit Pass",
                    "category_primary": "TRANSPORTATION",
                    "category_detailed": "PUBLIC_TRANSIT",
                    "amount": Decimal("32.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Spotify",
                    "name": "Spotify Family",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "STREAMING_SUBSCRIPTIONS",
                    "amount": Decimal("16.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Ace Hardware Ann Arbor",
                    "name": "Hardware Supplies",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "HOME_IMPROVEMENT",
                    "amount": Decimal("85.00"),
                    "frequency": 1,
                },
            ],
        },
    },
    {
        "index": 7,
        "email": "dli_test7@example.com",
        "profile": "affluent",
        "variant": {
            "income_multiplier": Decimal("1.05"),
            "spending_multiplier": Decimal("1.06"),
            "balance_delta": Decimal("4500.00"),
            "extra_income": [
                {
                    "name": "Quarterly Stock Vest",
                    "merchant": "Cisco RSU",
                    "amount": Decimal("-3200.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "INVESTMENT_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Vinology Wine Bar",
                    "name": "Vinology Wine Club",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "DINE_IN_RESTAURANT",
                    "amount": Decimal("210.00"),
                    "frequency": 3,
                },
                {
                    "merchant": "Ann Arbor Art Center",
                    "name": "Art Center Donation",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "ART_DEALERS",
                    "amount": Decimal("700.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "UM Alumni Association",
                    "name": "Alumni Giving",
                    "category_primary": "GENERAL_SERVICES",
                    "category_detailed": "CHARITY",
                    "amount": Decimal("500.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Lexus Financial",
                    "name": "Lexus Lease",
                    "category_primary": "TRANSPORTATION",
                    "category_detailed": "AUTO_FINANCE",
                    "amount": Decimal("980.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Cherry Republic Kerrytown",
                    "name": "Cherry Republic Treats",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "SPECIALTY_FOOD",
                    "amount": Decimal("80.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Shinola Ann Arbor",
                    "name": "Shinola Watch",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "JEWELRY",
                    "amount": Decimal("450.00"),
                    "frequency": 1,
                },
            ],
        },
    },
    {
        "index": 8,
        "email": "dli_test8@example.com",
        "profile": "affluent",
        "variant": {
            "income_multiplier": Decimal("1.04"),
            "spending_multiplier": Decimal("1.12"),
            "balance_delta": Decimal("5200.00"),
            "extra_income": [
                {
                    "name": "Advisory Retainer",
                    "merchant": "TechTown Detroit",
                    "amount": Decimal("-2300.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "CONSULTING",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Detroit Metro Flights",
                    "name": "DTW Flight Upgrade",
                    "category_primary": "TRAVEL",
                    "category_detailed": "TRAVEL_FLIGHTS",
                    "amount": Decimal("980.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "OM Day Spa",
                    "name": "Luxury Spa Day",
                    "category_primary": "HEALTHCARE",
                    "category_detailed": "SPA_SERVICES",
                    "amount": Decimal("360.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Ann Arbor Symphony",
                    "name": "Symphony Patron",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "CULTURE_EVENTS",
                    "amount": Decimal("280.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Neutral Zone",
                    "name": "Neutral Zone Donation",
                    "category_primary": "GENERAL_SERVICES",
                    "category_detailed": "CHARITY",
                    "amount": Decimal("600.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Bivouac Outdoor",
                    "name": "Bivouac Gear",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "OUTDOOR_RECREATION",
                    "amount": Decimal("450.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "M-Den",
                    "name": "M-Den Gear",
                    "category_primary": "GENERAL_MERCHANDISE",
                    "category_detailed": "CLOTHING_STORES",
                    "amount": Decimal("160.00"),
                    "frequency": 2,
                },
            ],
        },
    },
    {
        "index": 9,
        "email": "dli_test9@example.com",
        "profile": "affluent",
        "variant": {
            "income_multiplier": Decimal("1.08"),
            "spending_multiplier": Decimal("1.10"),
            "balance_delta": Decimal("7200.00"),
            "extra_income": [
                {
                    "name": "Board Compensation",
                    "merchant": "Ann Arbor Innovators",
                    "amount": Decimal("-3800.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "COMMISSION",
                },
                {
                    "name": "Old West Side Rental",
                    "merchant": "Old West Side Rentals",
                    "amount": Decimal("-2100.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "RENTAL_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "All Seasons Travel",
                    "name": "Travel Planning",
                    "category_primary": "TRAVEL",
                    "category_detailed": "TRAVEL_AGENCIES",
                    "amount": Decimal("1200.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Pacific Rim by Kana",
                    "name": "Pacific Rim Chef's Table",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "DINE_IN_RESTAURANT",
                    "amount": Decimal("260.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Matthaei Botanical Gardens",
                    "name": "Gala Donation",
                    "category_primary": "GENERAL_SERVICES",
                    "category_detailed": "CHARITY",
                    "amount": Decimal("750.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "The Ark",
                    "name": "The Ark Patron Pass",
                    "category_primary": "ENTERTAINMENT",
                    "category_detailed": "CULTURE_EVENTS",
                    "amount": Decimal("200.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Tesla Supercharger",
                    "name": "Supercharger Session",
                    "category_primary": "TRANSPORTATION",
                    "category_detailed": "FUEL",
                    "amount": Decimal("28.00"),
                    "frequency": 3,
                },
                {
                    "merchant": "Ann Arbor Dermatology",
                    "name": "Dermatology Visit",
                    "category_primary": "HEALTHCARE",
                    "category_detailed": "DOCTORS",
                    "amount": Decimal("310.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Plum Market",
                    "name": "Plum Market Gourmet",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "GROCERIES",
                    "amount": Decimal("220.00"),
                    "frequency": 2,
                },
            ],
        },
    },
    {
        "index": 11,
        "email": "dli_test11@example.com",
        "profile": "affluent",
        "variant": {
            "income_multiplier": Decimal("1.06"),
            "spending_multiplier": Decimal("0.96"),
            "balance_delta": Decimal("6800.00"),
            "extra_income": [
                {
                    "name": "Performance Bonus",
                    "merchant": "Duo Security Bonus",
                    "amount": Decimal("-1800.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "BONUS",
                },
                {
                    "name": "Quarterly RSU Vest",
                    "merchant": "Midwest Ventures RSU",
                    "amount": Decimal("-2400.00"),
                    "category_primary": "INCOME",
                    "category_detailed": "INVESTMENT_INCOME",
                },
            ],
            "extra_spending": [
                {
                    "merchant": "Plum Market",
                    "name": "Plum Market Healthy Groceries",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "GROCERIES",
                    "amount": Decimal("185.00"),
                    "frequency": 3,
                },
                {
                    "merchant": "Orangetheory Fitness",
                    "name": "Orangetheory Membership",
                    "category_primary": "HEALTHCARE",
                    "category_detailed": "GYM_FITNESS",
                    "amount": Decimal("145.00"),
                    "frequency": 2,
                },
                {
                    "merchant": "Delta Air Lines",
                    "name": "Delta Comfort Upgrade",
                    "category_primary": "TRAVEL",
                    "category_detailed": "TRAVEL_FLIGHTS",
                    "amount": Decimal("420.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Vanguard Investments",
                    "name": "Monthly ETF Contribution",
                    "category_primary": "GENERAL_SERVICES",
                    "category_detailed": "FINANCIAL_ADVICE",
                    "amount": Decimal("650.00"),
                    "frequency": 1,
                },
                {
                    "merchant": "Zingerman's Roadhouse",
                    "name": "Zingerman's Dinner",
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "DINE_IN_RESTAURANT",
                    "amount": Decimal("120.00"),
                    "frequency": 2,
                },
            ],
        },
    },
]

CENT = Decimal("0.01")


def quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(CENT)


def _clone_events(events):
    if not events:
        return []
    return [event.copy() for event in events]


def _apply_multiplier(events, multiplier):
    if multiplier is None:
        return events
    multiplier_value = multiplier if isinstance(multiplier, Decimal) else Decimal(str(multiplier))
    if multiplier_value == Decimal("1"):
        return events
    for event in events:
        event["amount"] = quantize_amount(event["amount"] * multiplier_value)
    return events


def _normalize_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def build_schedule(profile_key: str, variant: Optional[dict] = None):
    profile = USER_PROFILES[profile_key]
    variant = variant or {}
    incomes = _clone_events(profile["income"])
    spending = _clone_events(profile["spending"])

    incomes = _apply_multiplier(incomes, variant.get("income_multiplier"))
    spending = _apply_multiplier(spending, variant.get("spending_multiplier"))
    incomes.extend(_clone_events(variant.get("extra_income")))
    spending.extend(_clone_events(variant.get("extra_spending")))

    baseline_delta = _normalize_decimal(variant.get("balance_delta", Decimal("0.00")))
    baseline_value = quantize_amount(profile["baseline_balance"] + baseline_delta)
    return incomes, spending, baseline_value


def _month_start(base: date, offset: int) -> date:
    year = base.year
    month = base.month - offset
    while month <= 0:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return date(year, month, 1)


def _days_in_month(month_start: date) -> int:
    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)
    return (next_month - month_start).days


def clear_transactions(session, user_id: int):
    session.query(models.Transaction).filter(models.Transaction.user_id == user_id).delete()
    session.commit()


def insert_transactions(session, user, account, profile_key: str, variant: Optional[dict] = None):
    incomes, spending, baseline_balance = build_schedule(profile_key, variant)
    clear_transactions(session, user.id)

    today = datetime.utcnow().date()
    current_month_start = today.replace(day=1)
    created = 0
    for month in range(MONTHS_OF_HISTORY):
        month_start = _month_start(current_month_start, month)
        days_in_month = _days_in_month(month_start)

        # Income deposited early each month
        for idx, income in enumerate(incomes):
            income_day = min(idx * 3 + 1, days_in_month - 1)
            txn_date = datetime.combine(
                month_start + timedelta(days=income_day),
                datetime.min.time(),
            )
            transaction = models.Transaction(
                user_id=user.id,
                account_id=account.id,
                plaid_transaction_id=f"dli-income-{user.id}-{month}-{idx}",
                amount=income["amount"],
                date=txn_date,
                name=income["name"],
                merchant_name=income["merchant"],
                category_primary=income["category_primary"],
                category_detailed=income["category_detailed"],
                payment_channel="direct_deposit",
                location_city=ANN_ARBOR_LOCATION["city"],
                location_region=ANN_ARBOR_LOCATION["region"],
                location_country=ANN_ARBOR_LOCATION["country"],
                is_pending=False,
            )
            session.add(transaction)
            created += 1

        # Structured spending
        for item_idx, spend in enumerate(spending):
            for occurrence in range(spend["frequency"]):
                base_offset = 5 + item_idx * 2 + occurrence * 3
                if days_in_month <= 0:
                    days_offset = 0
                else:
                    days_offset = base_offset % days_in_month
                txn_date = datetime.combine(
                    month_start + timedelta(days=days_offset),
                    datetime.min.time(),
                )
                transaction = models.Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    plaid_transaction_id=f"dli-spend-{user.id}-{month}-{item_idx}-{occurrence}",
                    amount=spend["amount"],
                    date=txn_date,
                    name=spend["name"],
                    merchant_name=spend["merchant"],
                    category_primary=spend["category_primary"],
                    category_detailed=spend["category_detailed"],
                    payment_channel="card",
                    location_city=ANN_ARBOR_LOCATION["city"],
                    location_region=ANN_ARBOR_LOCATION["region"],
                    location_country=ANN_ARBOR_LOCATION["country"],
                    is_pending=False,
                )
                session.add(transaction)
                created += 1

    account.available_balance = baseline_balance
    account.current_balance = baseline_balance
    session.commit()
    print(f"Inserted {created} deterministic transactions for {user.email}")


def seed_profile_user(
    session, email: str, password: str, profile_key: str, variant: Optional[dict] = None
):
    user = ensure_user(session, email=email, password=password)
    account = ensure_account(session, user)
    insert_transactions(session, user, account, profile_key, variant)
    regenerate_insights(session, user)


def main():
    preview_session = SessionLocal()
    try:
        engine_url = preview_session.bind.url
    finally:
        preview_session.close()
    print(f"Seeding against database: {engine_url}")
    session = SessionLocal()
    try:
        for user_cfg in DLI_USERS:
            email = user_cfg["email"]
            profile_key = user_cfg["profile"]
            variant = user_cfg.get("variant")
            print(f"Seeding {email} with {profile_key} profile...")
            seed_profile_user(session, email, DEFAULT_PASSWORD, profile_key, variant)
    finally:
        session.close()


if __name__ == "__main__":
    main()
