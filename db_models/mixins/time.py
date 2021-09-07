from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime

from .. import db


class UtcNow(expression.FunctionElement):
    type = DateTime()


@compiles(UtcNow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class TimeMixin(object):
    created_at = db.Column(db.DateTime(timezone=True), server_default=UtcNow())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=UtcNow(), onupdate=UtcNow())
