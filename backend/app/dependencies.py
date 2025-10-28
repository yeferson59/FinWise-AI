import logging
from app.models.category import Category
from sqlmodel import Session, select
from app.db.session import engine

logger = logging.getLogger(__name__)


def get_default_categories() -> list[Category]:
    """
    Returns the list of default global categories.

    Returns:
        List of Category instances with default categories for the application
    """
    return [
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


def init_categories() -> None:
    """
    Initialize default global categories in the database.

    This function is idempotent - it will only create categories that don't exist yet,
    based on the category name. Global categories are identified by having
    is_default=True and user_id=None. It's safe to call multiple times.

    Raises:
        Exception: If there's a database error during category initialization
    """
    default_categories = get_default_categories()

    try:
        with Session(engine) as session:
            # Get all existing global category names to avoid duplicates
            # Global categories have is_default=True and user_id=None
            # Use .is_(None) instead of == None for better SQL performance
            existing_categories = session.exec(
                select(Category.name).where(
                    Category.is_default.is_(True), Category.user_id.is_(None)
                )
            ).all()
            existing_names = set(existing_categories)

            # Filter out categories that already exist
            categories_to_create = [
                category
                for category in default_categories
                if category.name not in existing_names
            ]

            if not categories_to_create:
                logger.info(
                    "All default global categories already exist. Skipping initialization."
                )
                return

            # Use bulk insert for better performance
            session.add_all(categories_to_create)
            session.commit()

            logger.info(
                f"Successfully initialized {len(categories_to_create)} default global categories. "
                f"Skipped {len(existing_names)} existing categories."
            )

    except Exception as e:
        logger.error(f"Error initializing default global categories: {str(e)}")
        raise
