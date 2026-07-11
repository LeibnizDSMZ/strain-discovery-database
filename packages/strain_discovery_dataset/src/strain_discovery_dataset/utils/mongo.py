# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from pymongo.collection import Collection
from pathlib import Path
import os
from pymongo import MongoClient
from urllib.parse import quote_plus


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

    encoded_user = quote_plus(mongo_user)
    encoded_password = quote_plus(mongo_password)
    encoded_db = quote_plus(mongo_database)
    if isinstance(mongo_socket, str) and Path(mongo_socket).is_socket():
        connection_uri = f"mongodb://{encoded_user}:{encoded_password}"
        connection_uri += f"@{quote_plus(mongo_socket)}/{encoded_db}"
    else:
        connection_uri = f"mongodb://{encoded_user}:{encoded_password}"
        connection_uri += f"@{quote_plus(mongo_host)}:{mongo_port}/{encoded_db}"

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
