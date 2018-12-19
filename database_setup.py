import os
import sys
from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String)


class Categories(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return{
            "id": self.id,
            "name": self.name}


class BooksMenu(Base):
    __tablename__ = "book"
    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(50))
    rating = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))
    categories = relationship(Categories)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return{
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rating": self.rating}


engine = create_engine('sqlite:///categories.db')
Base.metadata.create_all(engine)

print 'done'
