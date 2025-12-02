import logging

from sqlmodel import Session, select

from app.db.session import engine
from app.models.category import Category
from app.models.transaction import Source

logger = logging.getLogger(__name__)


def get_default_categories() -> list[Category]:
    """
    Returns the list of default global categories.

    Returns:
        List of Category instances with default categories for the application
    """
    return [
        # Income
        Category(name="Salario", description="Ingresos por empleo", is_default=True),
        Category(
            name="Bono", description="Ingresos extra por trabajo", is_default=True
        ),
        Category(
            name="Ingresos por Intereses",
            description="Ingresos por intereses",
            is_default=True,
        ),
        Category(
            name="Ingresos por Inversiones",
            description="Ingresos por inversiones",
            is_default=True,
        ),
        Category(
            name="Ingresos por Alquiler",
            description="Ingresos por alquiler de propiedad",
            is_default=True,
        ),
        Category(
            name="Ingresos Empresariales",
            description="Ingresos por negocio",
            is_default=True,
        ),
        Category(
            name="Regalo Recibido", description="Regalos recibidos", is_default=True
        ),
        Category(
            name="Reembolsos", description="Reembolsos recibidos", is_default=True
        ),
        Category(
            name="Otros Ingresos",
            description="Otros tipos de ingresos",
            is_default=True,
        ),
        # Expenses
        Category(
            name="Compras de Supermercado",
            description="Comida y compras en supermercado",
            is_default=True,
        ),
        Category(
            name="Comer Fuera",
            description="Restaurantes y cafés",
            is_default=True,
        ),
        Category(
            name="Servicios Públicos",
            description="Electricidad, agua, gas, etc.",
            is_default=True,
        ),
        Category(
            name="Alquiler",
            description="Pagos mensuales de alquiler",
            is_default=True,
        ),
        Category(
            name="Hipoteca",
            description="Pagos de hipoteca",
            is_default=True,
        ),
        Category(
            name="Transporte",
            description="Transporte público, taxis, etc.",
            is_default=True,
        ),
        Category(
            name="Combustible",
            description="Gasolina y combustible",
            is_default=True,
        ),
        Category(
            name="Seguro",
            description="Pagos de seguros",
            is_default=True,
        ),
        Category(
            name="Salud",
            description="Gastos generales de salud",
            is_default=True,
        ),
        Category(
            name="Gastos Médicos",
            description="Médico, hospital, farmacia",
            is_default=True,
        ),
        Category(
            name="Educación",
            description="Matrícula, cursos, libros",
            is_default=True,
        ),
        Category(
            name="Cuidado Infantil",
            description="Guardería, niñera",
            is_default=True,
        ),
        Category(
            name="Entretenimiento",
            description="Películas, conciertos, eventos",
            is_default=True,
        ),
        Category(
            name="Suscripciones",
            description="Streaming, revistas, etc.",
            is_default=True,
        ),
        Category(name="Ropa", description="Ropa y zapatos", is_default=True),
        Category(
            name="Cuidado Personal",
            description="Cortes de cabello, belleza, higiene",
            is_default=True,
        ),
        Category(
            name="Viajes",
            description="Vuelos, hoteles, gastos de viaje",
            is_default=True,
        ),
        Category(
            name="Vacaciones",
            description="Viajes de vacaciones",
            is_default=True,
        ),
        Category(
            name="Teléfono e Internet",
            description="Facturas de telecomunicaciones",
            is_default=True,
        ),
        Category(
            name="Impuestos",
            description="Pagos de impuestos",
            is_default=True,
        ),
        Category(
            name="Donaciones",
            description="Caridad y donaciones",
            is_default=True,
        ),
        Category(
            name="Cuidado de Mascotas",
            description="Comida para mascotas, veterinario, aseo",
            is_default=True,
        ),
        Category(
            name="Mantenimiento del Hogar",
            description="Reparaciones, limpieza, mejoras",
            is_default=True,
        ),
        Category(
            name="Electrónicos",
            description="Gadgets y dispositivos",
            is_default=True,
        ),
        Category(name="Compras", description="Compras generales", is_default=True),
        Category(
            name="Varios",
            description="Otros gastos",
            is_default=True,
        ),
        # Savings
        Category(
            name="Fondo de Emergencia",
            description="Ahorros para emergencias",
            is_default=True,
        ),
        Category(
            name="Ahorros para Jubilación",
            description="Cuentas de jubilación",
            is_default=True,
        ),
        Category(
            name="Fondo para Universidad",
            description="Ahorros para educación",
            is_default=True,
        ),
        Category(
            name="Ahorros para Inversiones",
            description="Ahorros para inversiones",
            is_default=True,
        ),
        Category(
            name="Ahorros a Corto Plazo",
            description="Metas a corto plazo",
            is_default=True,
        ),
        # Investments
        Category(
            name="Acciones",
            description="Inversiones en acciones",
            is_default=True,
        ),
        Category(
            name="Bonos",
            description="Inversiones en bonos",
            is_default=True,
        ),
        Category(
            name="Fondos Mutuos",
            description="Inversiones en fondos mutuos",
            is_default=True,
        ),
        Category(
            name="Bienes Raíces",
            description="Inversiones en bienes raíces",
            is_default=True,
        ),
        Category(
            name="Criptomonedas",
            description="Inversiones en cripto",
            is_default=True,
        ),
        Category(
            name="Otras Inversiones",
            description="Otros tipos de inversiones",
            is_default=True,
        ),
        # Debt
        Category(
            name="Pago de Tarjeta de Crédito",
            description="Facturas de tarjeta de crédito",
            is_default=True,
        ),
        Category(
            name="Pago de Préstamo",
            description="Pagos de préstamos",
            is_default=True,
        ),
        Category(
            name="Pago de Hipoteca",
            description="Pagos de hipoteca",
            is_default=True,
        ),
        Category(
            name="Préstamo Estudiantil",
            description="Pagos de préstamo estudiantil",
            is_default=True,
        ),
        Category(
            name="Préstamo de Auto",
            description="Pagos de préstamo de auto",
            is_default=True,
        ),
        Category(
            name="Otras Deudas",
            description="Otras deudas",
            is_default=True,
        ),
        # Other
        Category(
            name="Sin Categorizar",
            description="Transacciones sin categorizar",
            is_default=True,
        ),
        Category(
            name="Transferencias",
            description="Transferencias entre cuentas",
            is_default=True,
        ),
        Category(
            name="Comisiones",
            description="Comisiones bancarias y de servicios",
            is_default=True,
        ),
        Category(
            name="Ajustes",
            description="Ajustes de saldo",
            is_default=True,
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
            # Get all existing category names to avoid UNIQUE constraint violations
            # Since name is unique across all categories, check all names
            existing_categories = session.exec(select(Category.name)).all()
            existing_names = set(existing_categories)

            # Filter out categories that already exist
            categories_to_create = [
                category
                for category in default_categories
                if category.name not in existing_names
            ]

            if not categories_to_create:
                logger.info(
                    "All default categories already exist. Skipping initialization."
                )
                return

            # Use bulk insert for better performance
            session.add_all(categories_to_create)
            session.commit()

            logger.info(
                f"Successfully initialized {len(categories_to_create)} default categories. "
                f"Skipped {len(existing_names)} existing categories."
            )

    except Exception as e:
        logger.error(f"Error initializing default global categories: {str(e)}")
        raise


def get_default_sources() -> list[Source]:
    """
    Returns the list of default global sources.

    Returns:
        List of Source instances with default sources for the application
    """
    return [
        # Banking
        Source(
            name="Cuenta Bancaria",
            description="Cuenta bancaria principal",
            is_default=True,
        ),
        Source(
            name="Cuenta de Ahorros",
            description="Cuenta de ahorros",
            is_default=True,
        ),
        Source(
            name="Cuenta Corriente",
            description="Cuenta corriente",
            is_default=True,
        ),
        Source(
            name="Tarjeta de Crédito",
            description="Cuenta de tarjeta de crédito",
            is_default=True,
        ),
        Source(
            name="Tarjeta de Débito",
            description="Cuenta de tarjeta de débito",
            is_default=True,
        ),
        # Digital Wallets
        Source(
            name="PayPal",
            description="Cuenta PayPal",
            is_default=True,
        ),
        Source(
            name="Venmo",
            description="Cuenta Venmo",
            is_default=True,
        ),
        Source(name="Cash App", description="Cuenta Cash App", is_default=True),
        Source(
            name="Apple Pay",
            description="Apple Pay",
            is_default=True,
        ),
        Source(
            name="Google Pay",
            description="Google Pay",
            is_default=True,
        ),
        # Cryptocurrency
        Source(
            name="Billetera Bitcoin",
            description="Billetera de criptomoneda Bitcoin",
            is_default=True,
        ),
        Source(
            name="Billetera Ethereum",
            description="Billetera de criptomoneda Ethereum",
            is_default=True,
        ),
        Source(
            name="Exchange de Cripto",
            description="Cuenta de exchange de criptomonedas",
            is_default=True,
        ),
        # Investment
        Source(
            name="Cuenta de Correduría",
            description="Cuenta de correduría de inversiones",
            is_default=True,
        ),
        Source(
            name="Cuenta de Jubilación",
            description="Cuenta 401k o IRA",
            is_default=True,
        ),
        Source(
            name="App de Inversiones",
            description="Cuenta de aplicación de inversiones",
            is_default=True,
        ),
        # Cash and Physical
        Source(name="Efectivo", description="Efectivo físico", is_default=True),
        Source(
            name="Cheque",
            description="Pagos con cheque",
            is_default=True,
        ),
        # Business
        Source(
            name="Cuenta Empresarial",
            description="Cuenta bancaria empresarial",
            is_default=True,
        ),
        Source(
            name="Pago de Cliente",
            description="Pagos de clientes",
            is_default=True,
        ),
        # Other
        Source(
            name="Otro",
            description="Otras fuentes de pago",
            is_default=True,
        ),
        Source(
            name="Desconocido",
            description="Fuente de pago desconocida",
            is_default=True,
        ),
    ]


def init_sources() -> None:
    """
    Initialize default global sources in the database.

    This function is idempotent - it will only create sources that don't exist yet,
    based on the source name. Global sources are identified by having
    is_default=True and user_id=None. It's safe to call multiple times.

    Raises:
        Exception: If there's a database error during source initialization
    """
    default_sources = get_default_sources()

    try:
        with Session(engine) as session:
            # Get all existing source names to avoid UNIQUE constraint violations
            # Since name is unique across all sources, check all names
            existing_sources = session.exec(select(Source.name)).all()
            existing_names = set(existing_sources)

            # Filter out sources that already exist
            sources_to_create = [
                source
                for source in default_sources
                if source.name not in existing_names
            ]

            if not sources_to_create:
                logger.info(
                    "All default sources already exist. Skipping initialization."
                )
                return

            # Use bulk insert for better performance
            session.add_all(sources_to_create)
            session.commit()

            logger.info(
                f"Successfully initialized {len(sources_to_create)} default sources. "
                f"Skipped {len(existing_names)} existing sources."
            )

    except Exception as e:
        logger.error(f"Error initializing default global sources: {str(e)}")
        raise
