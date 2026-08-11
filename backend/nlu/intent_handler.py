import logging
from sqlalchemy.orm import Session
from nlu import llm_parser, rule_parser
from nlu.llm_parser import LLMParseError
import crud

# Configure a named logger so output is easy to spot in the VS Code terminal
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)s]  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("chatbot.nlu")


def process_message(db: Session, message: str) -> dict:
    """Hybrid pipeline: try the LLM first, fall back to rules if it fails."""
    source = "llm"
    try:
        intents = llm_parser.parse(message)          # always returns a list
        logger.debug("LLM parsed %d intent(s): %s", len(intents), intents)
    except LLMParseError as e:
        logger.error("LLM failed — falling back to rule parser. Reason: %s", e)
        source = "rule"
        intents = [rule_parser.parse(message)]       # wrap single dict in list
        logger.debug("Rule parser parsed intent: %s", intents[0])

    replies = []
    all_success = True
    last_action = "unknown"

    for intent in intents:
        reply, success = _execute_intent(db, intent)
        replies.append(reply)
        if not success:
            all_success = False
        last_action = intent.get("action", "unknown")

    return {
        "reply": "  \n".join(replies),          # newline-separated in chat UI
        "action": last_action,
        "success": all_success,
        "source": source,
    }


def _execute_intent(db: Session, intent: dict):
    action = intent.get("action")
    email = intent.get("email")
    name = intent.get("name")
    fields = intent.get("fields") or {}

    if action == "add":
        if not email:
            return "I couldn't find an email address to add. Please include one.", False
        try:
            user = crud.create_user(db, email=email, fields=fields)
            return f"User '{user.email}' was registered successfully.", True
        except crud.UserAlreadyExistsError:
            return f"A user with email '{email}' already exists.", False

    if action == "delete":
        identifier = email or name
        if not identifier:
            return "I couldn't tell which user to remove. Please give an email or name.", False
        try:
            crud.delete_user(db, identifier=identifier)
            return f"User '{identifier}' was removed successfully.", True
        except crud.UserNotFoundError:
            return f"No user found matching '{identifier}'.", False

    if action == "update":
        identifier = email or name
        if not identifier or not fields:
            return "I couldn't tell what to update. Please specify the user and the field.", False
        try:
            user = crud.update_user(db, identifier=identifier, fields=fields)
            changed = ", ".join(f"{k} -> {v}" for k, v in fields.items())
            return f"Updated {user.email}: {changed}.", True
        except crud.UserNotFoundError:
            return f"No user found matching '{identifier}'.", False

    return (
        'Sorry, I didn\'t understand that. Try something like: '
        'add the user "email@x.com" with phone "+92332".',
        False,
    )