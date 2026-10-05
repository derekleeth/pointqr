"""CLI script to seed or reset the admin user from environment variables.

Usage (inside container or venv):
    python -m app.scripts.seed_admin
"""

import asyncio
import sys
from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password, verify_password
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole


async def seed_admin() -> None:
    settings = get_settings()
    email = settings.admin_email
    password = settings.admin_password

    if not email or not password:
        print("ERROR: ADMIN_EMAIL and ADMIN_PASSWORD must be set in your .env file.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to database to seed/sync admin: {email}...")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if user is None:
                admin = User(
                    email=email,
                    hashed_password=hash_password(password),
                    role=UserRole.admin,
                    is_active=True,
                    is_verified=True,
                )
                session.add(admin)
                print(f"SUCCESS: Admin account created for {email} with role={UserRole.admin.value}.")
            else:
                changed = []
                if user.role != UserRole.admin:
                    user.role = UserRole.admin
                    changed.append("promoted role to admin")
                if not user.is_active:
                    user.is_active = True
                    changed.append("activated account")
                if not user.is_verified:
                    user.is_verified = True
                    changed.append("marked as verified")
                if not verify_password(password, user.hashed_password):
                    user.hashed_password = hash_password(password)
                    changed.append("updated password from ADMIN_PASSWORD")

                if changed:
                    print(f"SUCCESS: Admin account {email} updated: {', '.join(changed)}.")
                else:
                    print(f"OK: Admin account {email} already exists and credentials match .env.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
