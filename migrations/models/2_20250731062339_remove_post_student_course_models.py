from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "students";
        DROP TABLE IF EXISTS "posts";
        DROP TABLE IF EXISTS "courses";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
