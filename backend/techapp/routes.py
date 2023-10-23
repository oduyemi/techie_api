import bcrypt, os
from datetime import timedelta, datetime
from .database import SessionLocal
from .authorize import create_access_token, verify_token, authenticate_user
from fastapi import APIRouter, Request, status, Depends, HTTPException, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from techapp import starter, models, schemas
from techapp.schemas import UserResponse, Token, BlogResponse, BlogCategoryResponse, BlogCategoryPutResponse, BlogPutResponse, UserRequest
from techapp import dependencies
from techapp.dependencies import get_db, get_user_from_session, get_current_user, create_jwt_token
from typing import Optional, List
from techapp.models import User, Blog, BlogCategory
from sqlalchemy import func
from typing import List

tech_starter = APIRouter()



def format_blog_date(blog_date):
    return blog_date.isoformat() if blog_date else None


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


upload_folder_path = Path(__file__).parent.parent / "frontend" / "public" / "assets" / "uploads"

os.makedirs(upload_folder_path, exist_ok=True)

starter.mount("/uploads", StaticFiles(directory=upload_folder_path), name="uploads")





#     --   G E T   R E Q U E S T S   --

@starter.get("/")
async def get_index():
    return {"message": "Welcome to Techie API"}


@starter.get("/about")
async def about():
    return {"message": "Welcome to our About page! We are here to provide valuable information."}


@starter.get("/contact")
async def contact():
    return {"message": "Have questions or concerns? Feel free to contact us! Email: support@techie.org"}


@starter.get("/users", response_model=List[schemas.UserResponse])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    if not users:
        raise HTTPException(status_code=404, detail="Users not available!")

    user_responses = [
        UserResponse(
            id = user.user_id,
            user_fname = user.user_fname,
            user_lname = user.user_lname,
            user_email = user.user_email,
            user_hashed_password = user.user_hashed_password,
        )
        for user in users
    ]

    return user_responses


@starter.get("/user/id", response_model=schemas.UserResponse)
async def get_user(ID: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == ID).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not available!")

    user_response = schemas.UserResponse(
        id = user.user_id,
        user_fname = user.user_fname,
        user_lname = user.user_lname,
        user_email = user.user_email,
        user_hashed_password = user.user_hashed_password
    )

    return user_response


@starter.get("/blog-categories", response_model=List[schemas.BlogCategoryResponse])
async def get_blog_categories(db: Session = Depends(get_db)):
    categories = db.query(BlogCategory).all()

    if not categories:
        raise HTTPException(status_code=404, detail="No blog categories available")

    category_data = [
        {
            "id": category.blog_category_id,
            "blog_category": category.blog_category_name,
            "blog_category_description": category.blog_category_description,
            "blog_posts": [{
                "blog_category": category.blog_category_name, 
                "blog_title": blog.blog_title,
                "blog_img": f"/assets/uploads/{blog.blog_img}",
                "blog_content": blog.blog_content,
                "author_first_name": blog.author_info.user_fname,
                "author_last_name": blog.author_info.user_lname,
                "blog_date": format_blog_date(blog.blog_date)
            } for blog in category.blog_post]
        } for category in categories
    ]

    return category_data


@starter.get("/blog-category/{id}", response_model=schemas.BlogCategoryResponse)
async def get_blog_category(id: int, db: Session = Depends(get_db)):
    category = db.query(BlogCategory).filter(BlogCategory.blog_category_id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Blog category not available!")

    blog_data = db.query(Blog).filter(Blog.blog_category_id == id).all()
    category_data = {
    "id": category.blog_category_id,
    "blog_category": category.blog_category_name,
    "blog_category_description": category.blog_category_description,
    "blog_posts": [
        {
            "blog_category": category.blog_category_name,
            "blog_title": blog.blog_title,
            "blog_img": f"/assets/uploads/{blog.blog_img}",
            "blog_content": blog.blog_content,
            "author_first_name": blog.author_info.user_fname,
            "author_last_name": blog.author_info.user_lname,
            "blog_date": format_blog_date(blog.blog_date),
        }
        for blog in blog_data
        ],
    }

    return category_data

@starter.get("/blogs", response_model=List[schemas.BlogResponse])
async def get_blog_posts(db: Session = Depends(get_db)):
    blogs = db.query(Blog).options(joinedload(Blog.author_info)).all()
    if not blogs:
        raise HTTPException(status_code=404, detail="Blog posts not available!!")

    result = []
    for blog_deets in blogs:
        user_data = blog_deets.author_info 

        blog_response = BlogResponse(
            id = blog_deets.blog_id,
            blog_title = blog_deets.blog_title,
            blog_author = f"{user_data.user_fname} {user_data.user_lname}", 
            blog_date = blog_deets.blog_date, 
            blog_content = blog_deets.blog_content,
            blog_img = f"/assets/uploads/{blog_deets.blog_img}",
            blog_category_name = blog_deets.post_category.blog_category_name
        )
        result.append(blog_response)

    return result
    

@starter.get("/blog/id", response_model=schemas.BlogIdResponse)
async def get_blog_post(id: int, db: Session = Depends(get_db)):
    blog_post = db.query(Blog).get(id)
    if not blog_post:
        raise HTTPException(status_code=404, detail="Blog post not available!")

    author_data = db.query(User, BlogCategory).\
        join(Blog, User.user_id == Blog.blog_author_id).\
        join(BlogCategory, Blog.blog_category_id == BlogCategory.blog_category_id).\
        filter(User.user_id == blog_post.blog_author_id).all()
    if not author_data or not author_data[0]:
        raise HTTPException(status_code=404, detail="Author data not available!")

    author = author_data[0][0]
    blogpost = schemas.BlogIdResponse(
        id = blog_post.blog_id,
        blog_title = blog_post.blog_title,
        blog_img = f"/assets/uploads/{blog_post.blog_img}",
        author_first_name = author.user_fname,
        author_last_name = author.user_lname,
        blog_content = blog_post.blog_content,
        blog_date = format_blog_date(blog_post.blog_date),
        blog_category_name = blog_post.post_category.blog_category_name
        )
    return blogpost




@starter.get("/blogs-by-category/{category_id}", response_model=List[schemas.BlogResponse])
async def get_blogs_post_by_category(category_id: int, db: Session = Depends(get_db)):
    blogs = db.query(Blog).filter(Blog.blog_category_id == category_id).all()
    
    if not blogs:
        raise HTTPException(status_code=404, detail=f"No blog posts found for category with ID {category_id}")

    result = []
    for blog_deets in blogs:
        user_data = db.query(User).filter(User.user_id == blog_deets.blog_author_id).first()
        post_info = {
            "id": blog_deets.blog_id,
            "blog_title": blog_deets.blog_title,
            "blog_author": f"{user_data.user_fname} {user_data.user_lname}",
            "blog_category": blog_deets.post_category.blog_category_name,
            "blog_date": format_blog_date(blog_deets.blog_date),
            "blog_content": blog_deets.blog_content,  
            "blog_img": f"/assets/uploads/{blog_deets.blog_img}",         
            "blog_category_name": blog_deets.post_category.blog_category_name  
        }

        result.append(post_info)
    return result

#     --   P R O T E C T E D   R O U T E S   --

@starter.get("/dashboard")
async def dashboard(user_id: int = Depends(get_user_from_session), db: Session = Depends(get_db)):
    db: Session = get_db()
    if not user_id:
        raise HTTPException(status_code=302, detail="Redirect to /login")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    return {"message": f"Welcome to the dashboard, {user.fname}!"}






#     --   C R E A T E   R E Q U E S T S   --        

@starter.post("/blog", response_model=schemas.BlogRequest)
async def create_blog_post(
    blog: schemas.BlogRequest,
    user_id: int = Depends(get_user_from_session),
    db: Session = Depends(dependencies.get_db),
    blog_img: UploadFile = File(...)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be signed in to create a blog post")

    available_article = db.query(models.Blog).filter(func.lower(models.Blog.blog_title) == func.lower(blog.blog_title)).first()
    
    if available_article:
        raise HTTPException(status_code=400, detail="This blog post has been published already!")

    image_path = f"assets/uploads/{blog_img.filename}"
    with open(upload_folder_path / blog_img.filename, "wb") as image_file:
        image_file.write(blog_img.file.read())

    db_blogger = models.Blog(
        blog_title = blog.blog_title,
        blog_category_id = blog.blog_category_id,
        blog_content = blog.blog_content,
        blog_author = user_id, 
        blog_date = blog.blog_date,
        blog_img = image_path 
    )

    if blog.blog_title and blog.blog_category_id and blog.blog_content and user_id:
        try:
            db.add(db_blogger)
            db.commit()
            db.refresh(db_blogger)
            return db_blogger
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="All fields are required!")



@starter.post("/blog-category", response_model=schemas.BlogCategoryResponse)
async def create_blog_category(
    Name: str = Form("category"),
    Description: str = Form("desc"),
    db: Session = Depends(dependencies.get_db)
):
    available_category = db.query(models.BlogCategory).filter(func.lower(models.BlogCategory.blog_category_name) == func.lower(Name)).first()

    if available_category:
        raise HTTPException(status_code=400, detail="This category already exists!")

    new_category = models.BlogCategory(blog_category_name=Name, blog_category_description=Description)

    if Name and Description:
        try:
            db.add(new_category)
            db.commit()
            db.refresh(new_category)
            return {
                "id": new_category.blog_category_id,
                "blog_category": new_category.blog_category_name,
                "blog_posts": [],
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="All fields are required!")


@tech_starter.post("/register", response_model=UserRequest)
async def register_user(
    first_name: str = Form("fname"),
    last_name: str = Form("lname"),
    email: str = Form("mail"),
    password: str = Form("pwd"),
    confirm_password: str = Form("cpwd"),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = hash_password(password)
    existing_user = db.query(models.User).filter(models.User.user_email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already taken")

    if not all([first_name, last_name, email, password, confirm_password]):
        raise HTTPException(status_code=400, detail="All fields are required")

    db_user = models.User(
        user_fname=first_name,
        user_lname=last_name,
        user_email=email,
        user_password=password,
        user_hashed_password=hashed_password
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user_id = db_user.user_id
        jwt_token = create_jwt_token(user_id, email)

        return {"user_fname": db_user.user_fname, "user_lname": db_user.user_lname, "user_email": db_user.user_email, "user_password": db_user.user_hashed_password, "token": jwt_token}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@tech_starter.post("/login")
async def login_user(
    email: str = Form("mail"),
    password: str = Form("pwd"),
    db: Session = Depends(get_db)
    ):
    print(f"Received email: {email}, password: {password}")

    if not all([email, password]):
        raise HTTPException(status_code=400, detail="All fields are required")

    user = db.query(models.User).filter(models.User.user_email == email).first()
    if not user or not verify_password(password, user.user_hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.user_email})
    print(f"Generated access_token: {access_token}")

    return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})






@tech_starter.post("/logout")
async def logout_user():
    user_id = get_user_from_session()
    if user_id:
        remove_user_from_session(user_id)
        return {"message": "Logout successful"}
    else:
        raise HTTPException(status_code=401, detail="User not in session")







#     --   U P D A T E   R E Q U E S T S   --

@starter.put("/profile", response_model=schemas.UserResponse)
async def edit_profile(
    user_id: int = Depends(get_user_from_session),
    email: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    if not user_id:
        raise HTTPException(status_code=302, detail="Redirect to /login")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if email is not None and user.email != email:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this email")

    if email is not None:
        user.email = email

    if password is not None:
        user.hashed_password = hash_password(password)

    db.commit()

    return user


@starter.put("/blog-category/id", response_model=schemas.BlogCategoryRequest)
async def update_category(id: int, category: str, description: Optional[str] = None, db: Session = Depends(get_db)):
    category_check = db.query(BlogCategory).filter(BlogCategory.blog_category_id == id).first()

    if not category_check:
        raise HTTPException(status_code=404, detail=f"Category with ID {id} not found")

    category_check.blog_category_name = category
    if description is not None:
        category_check.blog_category_description = description

    db.commit()
    return {"blog_category_name": category_check.blog_category_name, "blog_category_description": category_check.blog_category_description}


@starter.put("/blog/{blog_id}", response_model=schemas.BlogResponse)
async def update_blog_post(
    blog_id: int,
    blog_title: str = Form("title"),
    blog_content: str = Form("content"),
    blog_img: UploadFile = File("img"),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_blog = db.query(models.Blog).filter(models.Blog.blog_id == blog_id).first()
    if not existing_blog:
        raise HTTPException(status_code=404, detail="Blog post not found")

    if existing_blog.blog_author_id != user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to update this blog post")

    if blog_img:
        image_path = f"assets/uploads/{blog_img.filename}"
        with open(upload_folder_path / blog_img.filename, "wb") as image_file:
            image_file.write(blog_img.file.read())
        existing_blog.blog_img = image_path 

    existing_blog.blog_title = blog_title
    existing_blog.blog_content = blog_content  
    db.commit()
    db.refresh(existing_blog) 
    return existing_blog









#     --   D E L E T E   R E Q U E S T S   --

@starter.delete("/blog/{id}", response_model=schemas.BlogPutResponse)
async def delete_blog(
    blog_id: int,
    user_id: int = Depends(get_user_from_session),
    db: Session = Depends(get_db)
):
    existing_blog = db.query(models.Blog).filter(models.Blog.blog_id == id).first()
    if not existing_blog:
        raise HTTPException(status_code=404, detail="Blog post not found")

    if existing_blog.blog_author_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this blog post")

    db.delete(existing_blog)
    db.commit()

    return existing_blog


@starter.delete("/blog-category/{id}", response_model=schemas.BlogCategoryPutResponse)
async def delete_blog_category(blog_category_id: int, db: Session = Depends(dependencies.get_db)):
    existing_category = db.query(models.BlogCategory).filter(models.BlogCategory.blog_category_id == blog_category_id).first()
    if not existing_category:
        raise HTTPException(status_code=404, detail="Blog category not found")

    db.query(models.Blog).filter(models.Blog.blog_category_id == blog_category_id).delete()
    db.delete(existing_category)
    db.commit()
    return {
        "id": existing_category.blog_category_id,
        "blog_category": existing_category.blog_category_name,
        "blog_posts": [],
        }
