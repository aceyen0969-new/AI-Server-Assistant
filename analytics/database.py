import sqlite3
from pathlib import Path


DATABASE_PATH = Path("analytics") / "analytics.db"


def get_connection():
    """Create a connection to the analytics database."""

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create the analytics tables if they do not exist."""

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS message_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def record_message(
    guild_id: int,
    channel_id: int,
    user_id: int,
    created_at: str,
):
    """Record one Discord message as an activity event."""

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO message_activity (
                guild_id,
                channel_id,
                user_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                guild_id,
                channel_id,
                user_id,
                created_at,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_message_count(
    guild_id: int,
):
    """Return the total number of recorded messages for a server."""

    connection = get_connection()

    try:
        result = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM message_activity
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

        return result["count"]

    finally:
        connection.close()


def get_unique_member_count(
    guild_id: int,
):
    """Return the number of unique members who sent messages."""

    connection = get_connection()

    try:
        result = connection.execute(
            """
            SELECT COUNT(DISTINCT user_id) AS count
            FROM message_activity
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

        return result["count"]

    finally:
        connection.close()


def get_channel_activity(
    guild_id: int,
):
    """Return message counts grouped by channel."""

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                channel_id,
                COUNT(*) AS message_count
            FROM message_activity
            WHERE guild_id = ?
            GROUP BY channel_id
            ORDER BY message_count DESC
            """,
            (guild_id,),
        ).fetchall()

        return [
            {
                "channel_id": row["channel_id"],
                "message_count": row["message_count"],
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_member_activity(
    guild_id: int,
):
    """Return message counts grouped by member."""

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                user_id,
                COUNT(*) AS message_count
            FROM message_activity
            WHERE guild_id = ?
            GROUP BY user_id
            ORDER BY message_count DESC
            """,
            (guild_id,),
        ).fetchall()

        return [
            {
                "user_id": row["user_id"],
                "message_count": row["message_count"],
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_hourly_activity(
    guild_id: int,
):
    """Return message counts grouped by UTC hour."""

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                substr(created_at, 12, 2) AS hour,
                COUNT(*) AS message_count
            FROM message_activity
            WHERE guild_id = ?
            GROUP BY hour
            ORDER BY hour
            """,
            (guild_id,),
        ).fetchall()

        return [
            {
                "hour": int(row["hour"]),
                "message_count": row["message_count"],
            }
            for row in rows
        ]

    finally:
        connection.close()