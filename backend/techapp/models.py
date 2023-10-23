from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from techapp import engine
from techapp.database import Base

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, autoincrement=True, primary_key=True)
    user_fname = Column(String(100))
    user_lname = Column(String(100))
    user_email = Column(String(100), unique=True)
    user_password = Column(String(200))
    user_hashed_password = Column(String(200))
    user_regdate = Column(DateTime(), default=datetime.utcnow)
    confirmation_token = Column(String(100), nullable=True)

    post_info = relationship("Blog", back_populates="author_info")

class Blog(Base):
    __tablename__ = "blog"
    blog_id = Column(Integer, autoincrement=True, primary_key=True)
    blog_title = Column(String(100), index=True)
    blog_content = Column(Text, index=True, nullable=False)
    blog_category_id = Column(Integer, ForeignKey("blog_category.blog_category_id"), nullable=True) 
    blog_author_id = Column(Integer, ForeignKey("user.user_id"), nullable=False) 
    blog_date = Column(DateTime(), index=True, default=datetime.utcnow)
    blog_img = Column(String(100), index=True, nullable=True)

    author_info = relationship("User", back_populates="post_info")
    post_category = relationship("BlogCategory", back_populates="blog_post")


class BlogCategory(Base):
    __tablename__ = "blog_category"
    blog_category_id = Column(Integer, autoincrement=True, primary_key=True)
    blog_category_name = Column(String(100), index=True)
    blog_category_description = Column(Text, index=True)
    
    blog_post = relationship("Blog", back_populates="post_category")