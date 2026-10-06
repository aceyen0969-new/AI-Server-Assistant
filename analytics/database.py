import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone


DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "analytics.db"
)


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


def get_start_time(
    days: int,
):
    """Return the UTC timestamp for the beginning of a time window."""

    now = datetime.now(
        timezone.utc
    )

    start = now - timedelta(
        days=days
    )

    return start.isoformat()


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
    days: int | None = None,
):
    """Return the number of messages in a time window."""

    connection = get_connection()

    try:

        if days is None:

            result = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM message_activity
                WHERE guild_id = ?
                """,
                (guild_id,),
            ).fetchone()

        else:

            start_time = get_start_time(
                days
            )

            result = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM message_activity
                WHERE guild_id = ?
                AND created_at >= ?
                """,
                (
                    guild_id,
                    start_time,
                ),
            ).fetchone()

        return result["count"]

    finally:
        connection.close()


def get_unique_member_count(
    guild_id: int,
    days: int | None = None,
):
    """Return unique active members in a time window."""

    connection = get_connection()

    try:

        if days is None:

            result = connection.execute(
                """
                SELECT COUNT(DISTINCT user_id) AS count
                FROM message_activity
                WHERE guild_id = ?
                """,
                (guild_id,),
            ).fetchone()

        else:

            start_time = get_start_time(
                days
            )

            result = connection.execute(
                """
                SELECT COUNT(DISTINCT user_id) AS count
                FROM message_activity
                WHERE guild_id = ?
                AND created_at >= ?
                """,
                (
                    guild_id,
                    start_time,
                ),
            ).fetchone()

        return result["count"]

    finally:
        connection.close()


def get_channel_activity(
    guild_id: int,
    days: int | None = None,
):
    """Return message counts grouped by channel."""

    connection = get_connection()

    try:

        if days is None:

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

        else:

            start_time = get_start_time(
                days
            )

            rows = connection.execute(
                """
                SELECT
                    channel_id,
                    COUNT(*) AS message_count
                FROM message_activity
                WHERE guild_id = ?
                AND created_at >= ?
                GROUP BY channel_id
                ORDER BY message_count DESC
                """,
                (
                    guild_id,
                    start_time,
                ),
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
    days: int | None = None,
):
    """Return message counts grouped by member."""

    connection = get_connection()

    try:

        if days is None:

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

        else:

            start_time = get_start_time(
                days
            )

            rows = connection.execute(
                """
                SELECT
                    user_id,
                    COUNT(*) AS message_count
                FROM message_activity
                WHERE guild_id = ?
                AND created_at >= ?
                GROUP BY user_id
                ORDER BY message_count DESC
                """,
                (
                    guild_id,
                    start_time,
                ),
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
    days: int | None = None,
):
    """Return message counts grouped by UTC hour."""

    connection = get_connection()

    try:

        if days is None:

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

        else:

            start_time = get_start_time(
                days
            )

            rows = connection.execute(
                """
                SELECT
                    substr(created_at, 12, 2) AS hour,
                    COUNT(*) AS message_count
                FROM message_activity
                WHERE guild_id = ?
                AND created_at >= ?
                GROUP BY hour
                ORDER BY hour
                """,
                (
                    guild_id,
                    start_time,
                ),
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

def get_daily_activity(
    guild_id: int,
    days: int = 7,
):
    """Return message counts grouped by UTC date."""

    connection = get_connection()

    try:

        start_time = get_start_time(
            days
        )

        rows = connection.execute(
            """
            SELECT
                substr(created_at, 1, 10) AS date,
                COUNT(*) AS message_count
            FROM message_activity
            WHERE guild_id = ?
            AND created_at >= ?
            GROUP BY date
            ORDER BY date
            """,
            (
                guild_id,
                start_time,
            ),
        ).fetchall()

        return [
            {
                "date": row["date"],
                "message_count": row["message_count"],
            }
            for row in rows
        ]

    finally:

        connection.close()