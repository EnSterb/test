from typing import List, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, \
    Table, Text, UniqueConstraint, text, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime

class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    email: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)

    collections: Mapped[List['Collections']] = relationship('Collections', back_populates='user')
    links: Mapped[List['Links']] = relationship('Links', back_populates='user')
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")


class Collections(Base):
    __tablename__ = 'collections'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_user'),
        PrimaryKeyConstraint('id', name='collections_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    user: Mapped['Users'] = relationship('Users', back_populates='collections')
    links: Mapped[List['Links']] = relationship('Links', secondary='collection_links', back_populates='collections', lazy='selectin')


class Links(Base):
    __tablename__ = 'links'
    __table_args__ = (
        CheckConstraint("type = ANY (ARRAY['website'::text, 'book'::text, 'article'::text, 'music'::text, 'video'::text])", name='links_type_check'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_user'),
        PrimaryKeyConstraint('id', name='links_pkey'),
        UniqueConstraint('url', name='links_url_key')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'website'::text"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    collections: Mapped[List['Collections']] = relationship('Collections', secondary='collection_links', back_populates='links')
    user: Mapped['Users'] = relationship('Users', back_populates='links')


t_collection_links = Table(
    'collection_links', Base.metadata,
    Column('collection_id', Integer, primary_key=True, nullable=False),
    Column('link_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE', name='fk_collection'),
    ForeignKeyConstraint(['link_id'], ['links.id'], ondelete='CASCADE', name='fk_link'),
    PrimaryKeyConstraint('collection_id', 'link_id', name='collection_links_pkey')
)


class PasswordResetToken(Base):
    __tablename__ = "password_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255), unique=True, index=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("Users", back_populates="password_reset_tokens")


class TempUsers(Base):
    __tablename__ = "temp_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
