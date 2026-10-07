import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone


DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "analytics.db"
)


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                period_days INTEGER NOT NULL,
                total_messages INTEGER NOT NULL,
                unique_members INTEGER NOT NULL,
                provider TEXT,
                analysis_json TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS server_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                occurrences INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS server_objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                objective TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'normal',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS objective_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objective_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                assessment TEXT NOT NULL,
                evidence TEXT NOT NULL,
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


def record_analysis_report(
    guild_id: int,
    period_days: int,
    total_messages: int,
    unique_members: int,
    provider: str | None,
    analysis_json: str,
):
    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO analysis_reports (
                guild_id,
                created_at,
                period_days,
                total_messages,
                unique_members,
                provider,
                analysis_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                datetime.now(
                    timezone.utc
                ).isoformat(),
                period_days,
                total_messages,
                unique_members,
                provider,
                analysis_json,
            ),
        )

        connection.commit()

    finally:

        connection.close()


def get_analysis_reports(
    guild_id: int,
    limit: int = 10,
):
    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                id,
                guild_id,
                created_at,
                period_days,
                total_messages,
                unique_members,
                provider,
                analysis_json
            FROM analysis_reports
            WHERE guild_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                guild_id,
                limit,
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_previous_analysis_report(
    guild_id: int,
):
    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                guild_id,
                created_at,
                period_days,
                total_messages,
                unique_members,
                provider,
                analysis_json
            FROM analysis_reports
            WHERE guild_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                guild_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(
            row
        )

    finally:

        connection.close()


def get_message_count(
    guild_id: int,
    days: int | None = None,
):
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

        activity_by_date = {
            row["date"]: row["message_count"]
            for row in rows
        }

        now = datetime.now(
            timezone.utc
        )

        start_date = (
            now - timedelta(
                days=days - 1
            )
        ).date()

        results = []

        for offset in range(days):

            current_date = (
                start_date
                + timedelta(
                    days=offset
                )
            )

            date_string = current_date.isoformat()

            results.append(
                {
                    "date": date_string,
                    "message_count": activity_by_date.get(
                        date_string,
                        0,
                    ),
                }
            )

        return results

    finally:

        connection.close()


def save_memory(
    guild_id: int,
    memory_type: str,
    content: str,
):
    connection = get_connection()

    try:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        existing = connection.execute(
            """
            SELECT
                id,
                occurrences
            FROM server_memory
            WHERE guild_id = ?
            AND memory_type = ?
            AND content = ?
            """,
            (
                guild_id,
                memory_type,
                content,
            ),
        ).fetchone()

        if existing is not None:

            connection.execute(
                """
                UPDATE server_memory
                SET
                    last_seen_at = ?,
                    occurrences = ?
                WHERE id = ?
                """,
                (
                    now,
                    existing["occurrences"] + 1,
                    existing["id"],
                ),
            )

        else:

            connection.execute(
                """
                INSERT INTO server_memory (
                    guild_id,
                    memory_type,
                    content,
                    created_at,
                    last_seen_at,
                    occurrences
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    memory_type,
                    content,
                    now,
                    now,
                    1,
                ),
            )

        connection.commit()

    finally:

        connection.close()


def get_memories(
    guild_id: int,
    memory_type: str | None = None,
    limit: int = 20,
):
    connection = get_connection()

    try:

        if memory_type is None:

            rows = connection.execute(
                """
                SELECT
                    id,
                    guild_id,
                    memory_type,
                    content,
                    created_at,
                    last_seen_at,
                    occurrences
                FROM server_memory
                WHERE guild_id = ?
                ORDER BY last_seen_at DESC
                LIMIT ?
                """,
                (
                    guild_id,
                    limit,
                ),
            ).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT
                    id,
                    guild_id,
                    memory_type,
                    content,
                    created_at,
                    last_seen_at,
                    occurrences
                FROM server_memory
                WHERE guild_id = ?
                AND memory_type = ?
                ORDER BY last_seen_at DESC
                LIMIT ?
                """,
                (
                    guild_id,
                    memory_type,
                    limit,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def create_objective(
    guild_id: int,
    objective: str,
    description: str = "",
    priority: str = "normal",
):
    connection = get_connection()

    try:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        cursor = connection.execute(
            """
            INSERT INTO server_objectives (
                guild_id,
                objective,
                description,
                priority,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                objective,
                description,
                priority,
                "active",
                now,
                now,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:

        connection.close()


def get_objectives(
    guild_id: int,
    status: str | None = None,
    limit: int = 20,
):
    connection = get_connection()

    try:

        if status is None:

            rows = connection.execute(
                """
                SELECT
                    id,
                    guild_id,
                    objective,
                    description,
                    priority,
                    status,
                    created_at,
                    updated_at
                FROM server_objectives
                WHERE guild_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (
                    guild_id,
                    limit,
                ),
            ).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT
                    id,
                    guild_id,
                    objective,
                    description,
                    priority,
                    status,
                    created_at,
                    updated_at
                FROM server_objectives
                WHERE guild_id = ?
                AND status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (
                    guild_id,
                    status,
                    limit,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_objective(
    objective_id: int,
    guild_id: int,
):
    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                guild_id,
                objective,
                description,
                priority,
                status,
                created_at,
                updated_at
            FROM server_objectives
            WHERE id = ?
            AND guild_id = ?
            """,
            (
                objective_id,
                guild_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(
            row
        )

    finally:

        connection.close()


def update_objective(
    objective_id: int,
    guild_id: int,
    status: str | None = None,
    priority: str | None = None,
    description: str | None = None,
):
    connection = get_connection()

    try:

        existing = connection.execute(
            """
            SELECT
                id,
                status,
                priority,
                description
            FROM server_objectives
            WHERE id = ?
            AND guild_id = ?
            """,
            (
                objective_id,
                guild_id,
            ),
        ).fetchone()

        if existing is None:
            return False

        new_status = (
            status
            if status is not None
            else existing["status"]
        )

        new_priority = (
            priority
            if priority is not None
            else existing["priority"]
        )

        new_description = (
            description
            if description is not None
            else existing["description"]
        )

        updated_at = datetime.now(
            timezone.utc
        ).isoformat()

        connection.execute(
            """
            UPDATE server_objectives
            SET
                status = ?,
                priority = ?,
                description = ?,
                updated_at = ?
            WHERE id = ?
            AND guild_id = ?
            """,
            (
                new_status,
                new_priority,
                new_description,
                updated_at,
                objective_id,
                guild_id,
            ),
        )

        connection.commit()

        return True

    finally:

        connection.close()


def delete_objective(
    objective_id: int,
    guild_id: int,
):
    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            DELETE FROM server_objectives
            WHERE id = ?
            AND guild_id = ?
            """,
            (
                objective_id,
                guild_id,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:

        connection.close()


def save_objective_assessment(
    objective_id: int,
    guild_id: int,
    status: str,
    assessment: str,
    evidence: str,
):
    connection = get_connection()

    try:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        cursor = connection.execute(
            """
            INSERT INTO objective_assessments (
                objective_id,
                guild_id,
                status,
                assessment,
                evidence,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                objective_id,
                guild_id,
                status,
                assessment,
                evidence,
                now,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:

        connection.close()


def get_objective_assessments(
    objective_id: int,
    guild_id: int,
    limit: int = 10,
):
    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                id,
                objective_id,
                guild_id,
                status,
                assessment,
                evidence,
                created_at
            FROM objective_assessments
            WHERE objective_id = ?
            AND guild_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                objective_id,
                guild_id,
                limit,
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_latest_objective_assessment(
    objective_id: int,
    guild_id: int,
):
    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                objective_id,
                guild_id,
                status,
                assessment,
                evidence,
                created_at
            FROM objective_assessments
            WHERE objective_id = ?
            AND guild_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                objective_id,
                guild_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(
            row
        )

    finally:

        connection.close()