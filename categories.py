from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, BooksMenu, User

engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


user1 = User(name='meshal', email='meshal.aneze@gmail.com', picture=' ')
session.add(user1)
session.commit()


category1 = Categories(user_id=1, name='Education')
session.add(category1)
session.commit()


category2 = Categories(user_id=1, name='Sports')
session.add(category2)
session.commit()

category3 = Categories(user_id=1, name='Math')
session.add(category3)
session.commit()

category4 = Categories(user_id=1, name='Languages')
session.add(category4)
session.commit()

category5 = Categories(user_id=1, name='Live')
session.add(category5)
session.commit()


book1 = BooksMenu(
    user_id=1,
    name='sport in KSA',
    description='this book explain sporst in KSA',
    rating='5'
    categories=category2)
session.add(book1)
session.commit()

book2 = BooksMenu(
    user_id=1,
    name='high School',
    description='this book explain high school',
    rating='3',
    categories=category1)
session.add(book2)
session.commit()

book3 = BooksMenu(
    user_id=1,
    name='555',
    description='Math axplaination',
    rating='5',
    categories=category3)
session.add(book3)
session.commit()

book4 = BooksMenu(
    user_id=1,
    name='Arabic Language',
    description='this book explain Arabic Language',
    rating='3',
    categories=category4)
session.add(book4)
session.commit()

book5 = BooksMenu(
    user_id=1,
    name='breath helthy',
    description='this book explain breath',
    rating='5',
    categories=category5)
session.add(book5)
session.commit()

print 'categories and books added'
