from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Union, Any



class Token(BaseModel):
    access_token: str
    token_type: str

class UserRequest(BaseModel):
    user_fname: str
    user_lname: str
    user_email: str
    user_password: str

class UserResponse(BaseModel):
    id: int
    user_fname: str
    user_lname: str
    user_email: str
    user_hashed_password: str

class BlogRequest(BaseModel):
    blog_title: str
    blog_category_id: int
    blog_content: str
    blog_author: Optional[int]
    blog_date: datetime
    blog_img: str

class BlogPostResponse(BaseModel):
    blog_title: str
    blog_img: str
    blog_content: str
    author_first_name: str
    author_last_name: str
    blog_date: str
    blog_category: str
    

class BlogCategoryResponse(BaseModel):
    id: int
    blog_category: str
    blog_posts: List[BlogPostResponse]
    

class BlogCategoryRequest(BaseModel):
    blog_category_name: str
    blog_category_description: str

class BlogCategoryPutResponse(BaseModel):
    message: str
    data: dict

class BlogPutResponse(BaseModel):
    message: str
    data: dict



class BlogResponse(BaseModel):
    id: int
    blog_title: str
    blog_author: str
    blog_date: datetime
    blog_content: str
    blog_img: str
    blog_category_name: str


class BlogIdResponse(BaseModel):
    id: int
    blog_title: str
    blog_img: str
    author_first_name: Optional[str]
    author_last_name: Optional[str]  
    blog_content: str
    blog_date: datetime
    blog_category_name: str











