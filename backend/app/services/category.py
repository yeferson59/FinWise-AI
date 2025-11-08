from fastapi import UploadFile

from app.core.agent import AgentDeps, get_agent, react_agent
from app.db.session import SessionDep
from app.models.category import Category
from app.schemas.category import CreateCategory, UpdateCategory
from app.services.file import extract_text
from app.utils import db
from app.utils.crud import CRUDService

# Initialize CRUD service for Category
_category_crud = CRUDService[Category, CreateCategory, UpdateCategory](Category)


async def get_all_categories(session: SessionDep, offset: int = 0, limit: int = 100):
    """Get all categories with pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns:
        List of Category objects
    """
    return await _category_crud.get_all(session, offset, limit)


async def create_category(session: SessionDep, create_category: CreateCategory):
    return await _category_crud.create(session, create_category)


async def get_category(session: SessionDep, id: int):
    return await _category_crud.get_by_id(session, id)


async def update_category(
    session: SessionDep, id: int, update_category: UpdateCategory
):
    return await _category_crud.update(session, id, update_category)


async def delete_category(session: SessionDep, id: int):
    return await _category_crud.delete(session, id)


async def classification(session: SessionDep, document_type: str, file: UploadFile):
    category_count = db.get_total_count(Category, session)

    if category_count == 0:
        raise ValueError(
            "No categories found in the database. Please create categories before classifying documents."
        )

    data = await extract_text(document_type, file)
    text = str(data["raw_text"]).strip()
    agent = get_agent()
    prompt = """Eres un asistente experto en extracción de palabras clave. Analiza detenidamente el texto que se te proporciona como entrada (el texto se pasa como entrada del usuario) y devuelve SOLO un objeto JSON válido, sin explicaciones ni texto adicional. Piensa detenidamente sobre el contenido antes de generar la salida y asegúrate de que el JSON sea consistente con lo extraído del texto.

    El JSON debe seguir exactamente esta estructura:

    {
      "language": "idioma detectado (ej. es, en)",
      "summary": "Resumen muy breve del texto (1-2 frases)",
      "keywords": [
        {
          "keyword": "palabra o frase clave",
          "score": número entre 0 y 100 (relevancia respecto al tema),
          "occurrences": número entero (veces que aparece la palabra/frase),
          "context": "frase corta o fragmento donde aparece para justificar la selección"
        }
        ...
      ]
    }

    Reglas detalladas:
    - Identifica entre 5 y 20 palabras o frases clave relevantes (si el texto es muy corto, incluye las más importantes).
    - Asigna a cada palabra/frase una puntuación entre 0 y 100 según su relevancia temática.
    - Cuenta cuántas veces aparece cada palabra/frase en el texto (occurrences).
    - Extrae una 'context' breve: una frase o fragmento donde la palabra/frase aparezca que justifique su selección.
    - Ordena el arreglo "keywords" de mayor a menor por "score".
    - Asegúrate de usar comillas dobles y producir JSON estrictamente válido (sin comentarios ni texto extra).
    - No incluyas ningún campo adicional ni metadatos fuera de la estructura especificada.

    Devuelve únicamente el JSON final."""
    keywords = (await agent.run(text, instructions=prompt)).output

    deps = AgentDeps(session)

    # Fetch current categories from the database to validate the agent's output later
    categories = await _category_crud.get_all(session, 0, max(100, category_count))
    category_names = [c.name for c in categories]

    prompt = (
        "You are an expert document categorization assistant. Your task is to compare the provided text "
        "against the existing categories and determine the best fit. Use any available tools to retrieve "
        "the exact list of categories from the database. Then, for each category, provide a short comparison "
        "to the text and a numeric confidence score from 0 to 100 indicating how well the text matches that "
        "category. The comparison helps ensure you actually considered the text against each category.\n\n"
        "Important output requirements:\n"
        "1) For each category, show a one-line entry with the category name, a score (0-100), and a one-sentence reason.\n"
        "2) On the very last non-empty line of your output, return ONLY the exact name of the single category that "
        "you judge is the best fit (exactly as it is stored in the database). That final line must contain nothing else "
        "— no punctuation, no quotes, no explanation. This final line is the definitive answer.\n\n"
        "Follow the steps: (a) retrieve categories using the tools, (b) compare each category to the text and give a score, "
        "(c) choose the best category and put its exact name on the final line only. Begin."
    )

    response = await react_agent.run(
        user_prompt=keywords, instructions=prompt, deps=deps, output_type=str
    )

    response_text = (
        response.output.strip()
        if hasattr(response, "output")
        else str(response).strip()
    )

    # Extract the final non-empty line as the candidate category name
    candidate_name = None
    for line in reversed(response_text.splitlines()):
        if line.strip():
            candidate_name = line.strip()
            break

    # Clean candidate (remove surrounding quotes/backticks if present)
    if candidate_name:
        candidate_name = candidate_name.strip(" \"'`")

    # Validate candidate against existing category names (exact match)
    matched_name = None
    if candidate_name and candidate_name in category_names:
        matched_name = candidate_name
    else:
        # Try case-insensitive exact match
        lower_to_name = {n.lower(): n for n in category_names}
        if candidate_name and candidate_name.lower() in lower_to_name:
            matched_name = lower_to_name[candidate_name.lower()]
        else:
            # As a fallback, try to find any category name that appears somewhere in the agent output
            found = None
            rt_lower = response_text.lower()
            for name in category_names:
                if name.lower() in rt_lower:
                    found = name
                    break
            if found:
                matched_name = found

    if not matched_name:
        raise ValueError(
            "Unable to classify the document: the agent's output did not match any existing category.\n"
            f"Agent output:\n{response_text}"
        )

    category = db.get_entity_by_field(Category, "name", matched_name, session)
    if not category:
        raise ValueError(
            f"The classified category '{matched_name}' does not exist in the database."
        )

    return category
