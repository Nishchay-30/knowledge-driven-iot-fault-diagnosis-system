"""
Admin Initialization CLI Script.
Safely initializes default administrative and operator credentials without committing plaintext passwords.
"""

import sys
import argparse
from getpass import getpass
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.auth.security import auth_manager
from database.connection import db_manager


def init_default_users(admin_pass: str = None, operator_pass: str = None):
    print("Checking database users table...")
    with db_manager.session() as conn:
        cursor = conn.execute("SELECT username FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone() is not None

    if not admin_exists:
        if not admin_pass:
            admin_pass = getpass("Set administrator password: ")
        if len(admin_pass) < 12:
            raise ValueError("Password must be at least 12 characters")
        auth_manager.create_user("admin", admin_pass, role="admin")
        print("Administrator account created successfully.")
    else:
        print("ℹ️ Admin account already exists.")

    with db_manager.session() as conn:
        cursor = conn.execute("SELECT username FROM users WHERE username = 'operator'")
        op_exists = cursor.fetchone() is not None

    if not op_exists:
        if not operator_pass:
            operator_pass = getpass("Set operator password: ")
        if len(operator_pass) < 12:
            raise ValueError("Password must be at least 12 characters")
        auth_manager.create_user("operator", operator_pass, role="operator")
        print("Operator account created successfully.")
    else:
        print("ℹ️ Operator account already exists.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize default database users")
    parser.add_argument("--admin-pass", default=None, help="Administrator password")
    parser.add_argument("--operator-pass", default=None, help="Operator password")
    args = parser.parse_args()

    init_default_users(args.admin_pass, args.operator_pass)

