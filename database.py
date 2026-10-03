import sqlite3
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "finance.db"


# ============================================================
# CONEXÃO
# ============================================================

def get_connection():
    """
    Cria e retorna uma conexão com o banco SQLite.
    """

    DB_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def initialize_database():
    """
    Cria todas as tabelas necessárias caso ainda não existam.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # -------------------------
    # TRANSAÇÕES
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)

    # -------------------------
    # INVESTIMENTOS
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            amount REAL NOT NULL,
            profitability REAL DEFAULT 0,
            investment_date TEXT NOT NULL
        )
    """)

    # -------------------------
    # METAS
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            current REAL NOT NULL DEFAULT 0
        )
    """)

    # -------------------------
    # CONFIGURAÇÕES
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# DADOS DE DEMONSTRAÇÃO
# ============================================================

def load_demo_data():
    """
    Insere dados de demonstração.

    Os dados só são inseridos quando essa função é chamada.
    Eles NÃO são recriados automaticamente.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # -------------------------
    # TRANSAÇÕES
    # -------------------------

    transactions = [
        ("2026-01-05", "Salário", "Trabalho", "Receita", 1000),
        ("2026-01-08", "Investimento mensal", "Investimentos", "Despesa", 500),
        ("2026-01-12", "Mercado", "Alimentação", "Despesa", 150),
        ("2026-01-20", "Transporte", "Transporte", "Despesa", 80),

        ("2026-02-05", "Salário", "Trabalho", "Receita", 1000),
        ("2026-02-08", "Investimento mensal", "Investimentos", "Despesa", 500),
        ("2026-02-15", "Mercado", "Alimentação", "Despesa", 130),
        ("2026-02-20", "Lazer", "Lazer", "Despesa", 100),

        ("2026-03-05", "Salário", "Trabalho", "Receita", 1000),
        ("2026-03-08", "Investimento mensal", "Investimentos", "Despesa", 500),
        ("2026-03-15", "Mercado", "Alimentação", "Despesa", 170),
        ("2026-03-25", "Transporte", "Transporte", "Despesa", 90),

        ("2026-04-05", "Salário", "Trabalho", "Receita", 1000),
        ("2026-04-08", "Investimento mensal", "Investimentos", "Despesa", 500),
        ("2026-04-16", "Mercado", "Alimentação", "Despesa", 160),
        ("2026-04-23", "Lazer", "Lazer", "Despesa", 120),

        ("2026-05-05", "Salário", "Trabalho", "Receita", 1000),
        ("2026-05-08", "Investimento mensal", "Investimentos", "Despesa", 500),
        ("2026-05-18", "Mercado", "Alimentação", "Despesa", 180),

        ("2026-06-05", "Salário", "Trabalho", "Receita", 1000),
    ]

    cursor.executemany("""
        INSERT INTO transactions
        (
            transaction_date,
            description,
            category,
            transaction_type,
            amount
        )
        VALUES (?, ?, ?, ?, ?)
    """, transactions)

    # -------------------------
    # INVESTIMENTOS
    # -------------------------

    investments = [
        ("CDB", "Renda fixa", 5000, 12.5, "2026-01-10"),
        ("Tesouro Direto", "Renda fixa", 2000, 10.8, "2026-02-10"),
        ("ETF", "ETF", 1500, 8.4, "2026-03-10"),
        ("FII", "FII", 1200, 9.2, "2026-03-15"),
        ("Ações", "Ações", 1000, 14.3, "2026-04-10"),
    ]

    cursor.executemany("""
        INSERT INTO investments
        (
            name,
            asset_type,
            amount,
            profitability,
            investment_date
        )
        VALUES (?, ?, ?, ?, ?)
    """, investments)

    # -------------------------
    # METAS
    # -------------------------

    goals = [
        ("Reserva de emergência", 10000, 3500),
        ("Faculdade", 20000, 8000),
        ("Primeiros R$ 50 mil", 50000, 12000),
    ]

    cursor.executemany("""
        INSERT INTO goals
        (
            name,
            target,
            current
        )
        VALUES (?, ?, ?)
    """, goals)

    # Marca que os dados de demonstração já foram carregados
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('demo_loaded', '1')
    """)

    connection.commit()
    connection.close()


def demo_data_exists():
    """
    Verifica se existem dados no banco.
    """

    connection = get_connection()
    cursor = connection.cursor()

    transaction_count = cursor.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    investment_count = cursor.execute(
        "SELECT COUNT(*) FROM investments"
    ).fetchone()[0]

    goal_count = cursor.execute(
        "SELECT COUNT(*) FROM goals"
    ).fetchone()[0]

    connection.close()

    return (
        transaction_count > 0
        or investment_count > 0
        or goal_count > 0
    )


# ============================================================
# TRANSAÇÕES
# ============================================================

def get_transactions():
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM transactions
        ORDER BY transaction_date DESC, id DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def add_transaction(
    transaction_date,
    description,
    category,
    transaction_type,
    amount
):
    connection = get_connection()

    connection.execute("""
        INSERT INTO transactions
        (
            transaction_date,
            description,
            category,
            transaction_type,
            amount
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        transaction_date,
        description,
        category,
        transaction_type,
        amount
    ))

    connection.commit()
    connection.close()


def delete_transaction(transaction_id):
    connection = get_connection()

    connection.execute("""
        DELETE FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    connection.commit()
    connection.close()


def delete_all_transactions():
    connection = get_connection()

    connection.execute("DELETE FROM transactions")

    connection.commit()
    connection.close()


# ============================================================
# INVESTIMENTOS
# ============================================================

def get_investments():
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM investments
        ORDER BY investment_date DESC, id DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def add_investment(
    name,
    asset_type,
    amount,
    profitability,
    investment_date
):
    connection = get_connection()

    connection.execute("""
        INSERT INTO investments
        (
            name,
            asset_type,
            amount,
            profitability,
            investment_date
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        asset_type,
        amount,
        profitability,
        investment_date
    ))

    connection.commit()
    connection.close()


def delete_investment(investment_id):
    connection = get_connection()

    connection.execute("""
        DELETE FROM investments
        WHERE id = ?
    """, (investment_id,))

    connection.commit()
    connection.close()


def delete_all_investments():
    connection = get_connection()

    connection.execute("DELETE FROM investments")

    connection.commit()
    connection.close()


# ============================================================
# METAS
# ============================================================

def get_goals():
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM goals
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def add_goal(name, target, current):
    connection = get_connection()

    connection.execute("""
        INSERT INTO goals
        (
            name,
            target,
            current
        )
        VALUES (?, ?, ?)
    """, (
        name,
        target,
        current
    ))

    connection.commit()
    connection.close()


def update_goal(goal_id, current):
    connection = get_connection()

    connection.execute("""
        UPDATE goals
        SET current = ?
        WHERE id = ?
    """, (
        current,
        goal_id
    ))

    connection.commit()
    connection.close()


def delete_goal(goal_id):
    connection = get_connection()

    connection.execute("""
        DELETE FROM goals
        WHERE id = ?
    """, (goal_id,))

    connection.commit()
    connection.close()


def delete_all_goals():
    connection = get_connection()

    connection.execute("DELETE FROM goals")

    connection.commit()
    connection.close()


# ============================================================
# LIMPEZA COMPLETA
# ============================================================

def delete_all_data():
    """
    Apaga todas as transações, investimentos e metas.
    """

    connection = get_connection()

    connection.execute("DELETE FROM transactions")
    connection.execute("DELETE FROM investments")
    connection.execute("DELETE FROM goals")

    connection.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('demo_loaded', '0')
    """)

    connection.commit()
    connection.close()


# ============================================================
# ESTATÍSTICAS
# ============================================================

def get_database_stats():
    connection = get_connection()
    cursor = connection.cursor()

    transactions = cursor.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    investments = cursor.execute(
        "SELECT COUNT(*) FROM investments"
    ).fetchone()[0]

    goals = cursor.execute(
        "SELECT COUNT(*) FROM goals"
    ).fetchone()[0]

    connection.close()

    return {
        "transactions": transactions,
        "investments": investments,
        "goals": goals,
    }