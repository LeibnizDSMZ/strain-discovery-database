from datetime import datetime
from pymongo.collection import Collection
from pathlib import Path
import os
from pymongo import MongoClient


def get_mongo_connection(
    connect_timeout: int = 5000,
    socket_timeout: int = 30000,
    server_selection_timeout: int = 30000,
    /,
) -> MongoClient:

    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = int(os.getenv("MONGO_PORT", "27017"))
    mongo_socket = os.getenv("MONGO_SOCKET")
    mongo_user = os.getenv("MONGO_SDD_USER")
    mongo_password_file = os.getenv("MONGO_SDD_PASSWORD_FILE")
    mongo_database = os.getenv("MONGO_SDD_DATABASE")

    if not mongo_user:
        raise ValueError("MONGO_SDD_USER environment variable is required")

    if mongo_password_file:
        try:
            with Path(mongo_password_file).open("r") as fhd:
                mongo_password = fhd.read().strip()
        except IOError as exc:
            raise ValueError(f"Failed to read password file: {exc}")
    elif not (mongo_password := os.getenv("MONGO_SDD_PASSWORD")):
        raise ValueError("MONGO_PASSWORD environment variable is required")

    if not mongo_database:
        raise ValueError("MONGO_SDD_DATABASE environment variable is required")

    if isinstance(mongo_socket, str) and Path(mongo_socket).is_file():
        connection_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_socket}/"
        connection_uri += f"{mongo_database}"
    else:
        connection_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:"
        connection_uri += f"{mongo_port}/{mongo_database}"

    client_options = {
        "connectTimeoutMS": connect_timeout,
        "socketTimeoutMS": socket_timeout,
        "serverSelectionTimeoutMS": server_selection_timeout,
        "retryWrites": True,
        "w": "majority",
    }
    return MongoClient(connection_uri, **client_options)


def get_sdd_collection(create: bool = False, /) -> Collection:
    database_name = os.getenv("MONGO_SDD_DATABASE")
    if not database_name:
        raise ValueError("Database name is required")
    collection_name = os.getenv("MONGO_SDD_COLLECTION")
    if not collection_name:
        raise ValueError("Collection name is required")
    if create:
        current_time = datetime.now()
        date_suffix = current_time.strftime("%Y_%m_%d_%H_%M")
        return get_mongo_connection()[database_name][f"{collection_name}_{date_suffix}"]
    return get_mongo_connection()[database_name][collection_name]


def is_collection_empty(collection: Collection, /) -> bool:
    count = collection.count_documents({})
    return count == 0
