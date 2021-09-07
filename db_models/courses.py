from typing import List

from . import db


class Courses(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    is_primary = db.Column(db.Boolean(), nullable=True, unique=True)

    @classmethod
    async def get_courses(cls) -> List['Courses']:
        return await cls.query.gino.all()
