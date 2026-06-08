from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean


class SoftDelete:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        self.deleted = True
        self.deleted_at = datetime.utcnow()