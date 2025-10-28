from app.models.category import Category
from sqlmodel import Session
from app.db.session import engine


def init_categories():
    default_categories = [
        # Income
        Category(name="Salary", description="Income from employment", is_default=True),
        Category(name="Bonus", description="Extra income from work", is_default=True),
        Category(
            name="Interest Income", description="Income from interest", is_default=True
        ),
        Category(
            name="Investment Income",
            description="Income from investments",
            is_default=True,
        ),
        Category(
            name="Rental Income",
            description="Income from property rental",
            is_default=True,
        ),
        Category(
            name="Business Income", description="Income from business", is_default=True
        ),
        Category(name="Gift Received", description="Gifts received", is_default=True),
        Category(name="Refunds", description="Refunds received", is_default=True),
        Category(
            name="Other Income", description="Other types of income", is_default=True
        ),
        # Expenses
        Category(
            name="Groceries",
            description="Food and supermarket purchases",
            is_default=True,
        ),
        Category(
            name="Dining Out", description="Restaurants and cafes", is_default=True
        ),
        Category(
            name="Utilities",
            description="Electricity, water, gas, etc.",
            is_default=True,
        ),
        Category(name="Rent", description="Monthly rent payments", is_default=True),
        Category(name="Mortgage", description="Mortgage payments", is_default=True),
        Category(
            name="Transportation",
            description="Public transport, taxis, etc.",
            is_default=True,
        ),
        Category(name="Fuel", description="Gasoline and fuel", is_default=True),
        Category(name="Insurance", description="Insurance payments", is_default=True),
        Category(
            name="Healthcare",
            description="General healthcare expenses",
            is_default=True,
        ),
        Category(
            name="Medical Expenses",
            description="Doctor, hospital, pharmacy",
            is_default=True,
        ),
        Category(
            name="Education", description="Tuition, courses, books", is_default=True
        ),
        Category(name="Childcare", description="Daycare, babysitting", is_default=True),
        Category(
            name="Entertainment",
            description="Movies, concerts, events",
            is_default=True,
        ),
        Category(
            name="Subscriptions",
            description="Streaming, magazines, etc.",
            is_default=True,
        ),
        Category(name="Clothing", description="Apparel and shoes", is_default=True),
        Category(
            name="Personal Care",
            description="Haircuts, beauty, hygiene",
            is_default=True,
        ),
        Category(
            name="Travel",
            description="Flights, hotels, travel expenses",
            is_default=True,
        ),
        Category(name="Vacation", description="Holiday trips", is_default=True),
        Category(name="Phone & Internet", description="Telecom bills", is_default=True),
        Category(name="Taxes", description="Tax payments", is_default=True),
        Category(
            name="Donations", description="Charity and donations", is_default=True
        ),
        Category(
            name="Pet Care", description="Pet food, vet, grooming", is_default=True
        ),
        Category(
            name="Home Maintenance",
            description="Repairs, cleaning, improvements",
            is_default=True,
        ),
        Category(
            name="Electronics", description="Gadgets and devices", is_default=True
        ),
        Category(name="Shopping", description="General shopping", is_default=True),
        Category(name="Miscellaneous", description="Other expenses", is_default=True),
        # Savings
        Category(
            name="Emergency Fund",
            description="Savings for emergencies",
            is_default=True,
        ),
        Category(
            name="Retirement Savings",
            description="Retirement accounts",
            is_default=True,
        ),
        Category(name="College Fund", description="Education savings", is_default=True),
        Category(
            name="Investment Savings",
            description="Savings for investments",
            is_default=True,
        ),
        Category(
            name="Short-term Savings", description="Short-term goals", is_default=True
        ),
        # Investments
        Category(name="Stocks", description="Stock investments", is_default=True),
        Category(name="Bonds", description="Bond investments", is_default=True),
        Category(
            name="Mutual Funds", description="Mutual fund investments", is_default=True
        ),
        Category(
            name="Real Estate", description="Real estate investments", is_default=True
        ),
        Category(
            name="Cryptocurrency", description="Crypto investments", is_default=True
        ),
        Category(
            name="Other Investments",
            description="Other types of investments",
            is_default=True,
        ),
        # Debt
        Category(
            name="Credit Card Payment", description="Credit card bills", is_default=True
        ),
        Category(name="Loan Payment", description="Loan repayments", is_default=True),
        Category(
            name="Mortgage Payment", description="Mortgage repayments", is_default=True
        ),
        Category(
            name="Student Loan", description="Student loan payments", is_default=True
        ),
        Category(name="Car Loan", description="Car loan payments", is_default=True),
        Category(name="Other Debt", description="Other debts", is_default=True),
        # Other
        Category(
            name="Uncategorized",
            description="Uncategorized transactions",
            is_default=True,
        ),
        Category(name="Transfers", description="Account transfers", is_default=True),
        Category(name="Fees", description="Bank and service fees", is_default=True),
        Category(
            name="Adjustments", description="Balance adjustments", is_default=True
        ),
    ]

    with Session(engine) as session:
        for category in default_categories:
            session.add(category)
        session.commit()
