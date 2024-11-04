# app/main.py

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from datetime import timedelta
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist
from contextlib import asynccontextmanager

from app import auth, models
from app.user_manager import get_current_user
from app.config import (
    INVITE_CODE_ENABLED,
    INVITE_CODE,
    REGISTRATION_ENABLED,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    DB_URL,
    EMAIL_AUTH_ENABLED,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Tortoise ORM
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["app.models"]}
    )
    await Tortoise.generate_schemas()

    # Create default admin and administrators group
    await create_default_admin_and_group()

    yield

    # Close Tortoise ORM connections
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)


# Create default admin and administrators group
async def create_default_admin_and_group():
    admin_username = "admin"
    admin_password = "admin"  # Change this in production
    admin_email = "admin@example.com"  # Set a default email

    # Create default admin user
    try:
        user = await models.User.get(username=admin_username)
        logger.info("Admin user already exists.")
    except DoesNotExist:
        hashed_password = auth.get_password_hash(admin_password)
        user = await models.User.create(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            full_name="Administrator"
        )
        logger.info("Default admin user created.")

    # Create default "administrators" group
    group_name = "administrators"
    group, created = await models.Group.get_or_create(name=group_name)
    if created:
        logger.info("Default 'administrators' group created.")

    # Add the admin user to the "administrators" group if not already added
    if user not in await group.users.all():
        await group.users.add(user)
        logger.info("Admin user added to 'administrators' group.")


# Authenticate user
async def authenticate_user(identifier: str, password: str):
    try:
        # Support email-based authentication if enabled
        if EMAIL_AUTH_ENABLED:
            user = await models.User.get(email=identifier)
        else:
            user = await models.User.get(username=identifier)
    except DoesNotExist:
        logger.warning(f"Authentication failed for identifier: {identifier} (User does not exist)")
        return None
    if not auth.verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed for identifier: {identifier} (Incorrect password)")
        return None
    logger.info(f"User authenticated successfully: {user.username}")
    return user


# Login page
@app.get("/admin", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Handle login form submission
@app.post("/admin", response_class=HTMLResponse)
async def login(request: Request, identifier: str = Form(...), password: str = Form(...)):
    user = await authenticate_user(identifier, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"Creating access token for user: {user.username}")
    response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",  # Include "Bearer " prefix
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax"
    )
    logger.info("Access token set in cookie")
    return response


# Registration page
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    if not REGISTRATION_ENABLED:
        logger.warning("Registration is disabled")
        raise HTTPException(status_code=404, detail="Registration is disabled")
    return templates.TemplateResponse(
        "register.html", {"request": request, "invite_code_enabled": INVITE_CODE_ENABLED}
    )


# Handle registration form submission
@app.post("/register", response_class=HTMLResponse)
async def register(
        request: Request,
        username: str = Form(...),
        email: str = Form(None),
        password: str = Form(...),
        full_name: str = Form(None),
        invite_code: str = Form(None),
):
    if not REGISTRATION_ENABLED:
        logger.warning("Registration is disabled")
        raise HTTPException(status_code=404, detail="Registration is disabled")
    if INVITE_CODE_ENABLED and invite_code != INVITE_CODE:
        logger.warning("Invalid invite code provided during registration")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Invalid invite code", "invite_code_enabled": True},
        )
    try:
        existing_user = await models.User.get(username=username)
        logger.warning(f"Registration attempt with existing username: {username}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already taken", "invite_code_enabled": INVITE_CODE_ENABLED},
        )
    except DoesNotExist:
        hashed_password = auth.get_password_hash(password)
        user = await models.User.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        logger.info(f"New user registered: {username}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "info": "Registration successful, please log in"}
        )


# Check if user is in "administrators" group
async def is_administrator(user: models.User):
    groups = await user.groups.all()
    return any(group.name == "administrators" for group in groups)


# Admin dashboard
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user: models.User = Depends(get_current_user)):
    logger.info(f"Fetching all users for admin: {current_user.username}")

    # Check if current_user is in "administrators" group
    is_admin = await is_administrator(current_user)

    # Fetch all users
    users = await models.User.all().prefetch_related("groups").order_by("username")
    logger.info(f"Number of users fetched: {len(users)}")

    # Fetch all groups
    groups = await models.Group.all().prefetch_related("users")

    # Count of users in each group
    group_user_counts = {group.name: len(await group.users.all()) for group in groups}

    # Total user count
    total_users = len(users)

    # Count of users in "administrators" group
    admin_group_count = group_user_counts.get("administrators", 0)

    # Pass data to template
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "users": users,
        "groups": groups,
        "is_admin": is_admin,
        "total_users": total_users,
        "admin_group_count": admin_group_count,
        "group_user_counts": group_user_counts,
    })


# Edit user's full name
@app.post("/admin/edit_user")
async def edit_user(
        username: str = Form(...),
        full_name: str = Form(...),
        current_user: models.User = Depends(get_current_user)):
    # Only administrators can edit users
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        user = await models.User.get(username=username)
        user.full_name = full_name
        await user.save()
        logger.info(f"User {username}'s full name updated to: {full_name}")
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")


# Add user to a group
@app.post("/admin/add_user_to_group")
async def add_user_to_group(
        username: str = Form(...),
        group_name: str = Form(...),
        current_user: models.User = Depends(get_current_user)):
    # Only administrators can add users to groups
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        user = await models.User.get(username=username)
        group = await models.Group.get(name=group_name)
        await user.groups.add(group)
        logger.info(f"User {username} added to group {group_name}")
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User or group not found")


# Remove user from a group
@app.post("/admin/remove_user_from_group")
async def remove_user_from_group(
        data: dict = Body(...),
        current_user: models.User = Depends(get_current_user)):
    # Only administrators can remove users from groups
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    username = data.get("username")
    group_name = data.get("group_name")
    if not username or not group_name:
        return JSONResponse(content={"success": False, "error": "Username and group_name are required"})
    try:
        user = await models.User.get(username=username)
        group = await models.Group.get(name=group_name)
        await user.groups.remove(group)
        logger.info(f"User {username} removed from group {group_name}")
        return JSONResponse(content={"success": True})
    except DoesNotExist:
        return JSONResponse(content={"success": False, "error": "User or group not found"})


# Create a new group
@app.post("/admin/create_group")
async def create_group(group_name: str = Form(...), current_user: models.User = Depends(get_current_user)):
    # Only administrators can create groups
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    group, created = await models.Group.get_or_create(name=group_name)
    if created:
        logger.info(f"Group created: {group_name}")
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Group already exists")


# Rename an existing group
@app.post("/admin/rename_group")
async def rename_group(group_id: int = Form(...), new_name: str = Form(...), current_user: models.User = Depends(get_current_user)):
    # Only administrators can rename groups
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        group = await models.Group.get(id=group_id)
        group.name = new_name
        await group.save()
        logger.info(f"Group renamed to: {new_name}")
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Group not found")


# Delete a group
@app.post("/admin/delete_group")
async def delete_group(name: str = Body(...), current_user: models.User = Depends(get_current_user)):
    # Only administrators can delete groups
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        group = await models.Group.get(name=name)
        await group.delete()
        logger.info(f"Group deleted: {name}")
        return JSONResponse(content={"success": True})
    except DoesNotExist:
        return JSONResponse(content={"success": False, "error": "Group not found"})


# Handle user deletion
@app.post("/admin/delete_user")
async def delete_user(username: str = Form(...), current_user: models.User = Depends(get_current_user)):
    # Only administrators can delete users
    if not await is_administrator(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    # Prevent admins from deleting themselves
    if username == current_user.username:
        logger.warning("Admin attempted to delete themselves")
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    try:
        user_to_delete = await models.User.get(username=username)
        await user_to_delete.delete()
        logger.info(f"User deleted: {username}")
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    except DoesNotExist:
        logger.warning(f"Attempted to delete non-existent user: {username}")
        raise HTTPException(status_code=404, detail="User not found")


# Logout route
@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    logger.info("User logged out and access_token cookie deleted")
    return response
