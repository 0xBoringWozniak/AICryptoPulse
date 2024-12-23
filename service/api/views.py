from typing import List, Dict

from fastapi import APIRouter, FastAPI, Depends

from service.api.response import JSONResponse, create_response
from service.mongo.app_database import AppDatabase
from service.models import UserPrompt, UserInit, UserNewPrompt
from service.creds import DB_USER, DB_PASS, DB_HOST, DB_PORT


router = APIRouter()


def get_db() -> AppDatabase:
    return AppDatabase(
        db_host=DB_HOST,
        db_port=int(DB_PORT),
        db_user=DB_USER,
        db_user_password=DB_PASS,
    )


@router.get(
    path="/health",
    tags=["Health"],
)
async def health() -> JSONResponse:
    """
    Health service check.
    """
    return create_response(
        status_code=200,
        data={"status": "ok"},
    )


@router.post(
    path="/create_user",
    tags=["User"],
)
async def create_user(user: UserInit, db: AppDatabase = Depends(get_db)) -> JSONResponse:
    """
    Create a new user.
    """
    try:
        db.add_user(username=user.username, chat_id=user.chat_id, system_prompt=user.system_prompt)
        return create_response(
            status_code=200,
            data={"message": "User created successfully."},
        )
    except Exception as e:
        return create_response(
            status_code=400,
            data={"message": str(e)},
        )


@router.get(
    path="/get_user",
    tags=["User"],
)
async def get_user(username: str, db: AppDatabase = Depends(get_db)) -> JSONResponse:
    """
    Get a user by username.
    """
    try:
        user = db.get_user_info(username)
        if user is None:
            return create_response(
                status_code=404,
                data={"message": "User not found."},
            )
        return create_response(
            status_code=200,
            data={
                "username": user["username"],
                "system_prompt": user["system_prompt"],
                "chat_id": user["chat_id"],
            },
        )
    except Exception as e:
        return create_response(
            status_code=400,
            data={"message": str(e)},
        )


@router.post(
    path="/set_prompt",
    tags=["User"],
)
async def set_prompt(user: UserNewPrompt, db: AppDatabase = Depends(get_db)) -> JSONResponse:
    """
    Set a new prompt for a user.
    """
    try:
        db.set_user_prompt(username=user.username, new_prompt=user.new_prompt)
        return create_response(
            status_code=200,
            data={"message": "Prompt updated successfully."},
        )
    except Exception as e:
        return create_response(
            status_code=400,
            data={"message": str(e)},
        )


@router.post(
    path="/predict",
    tags=["User"],
)
async def predict(user: UserPrompt, db: AppDatabase = Depends(get_db)) -> JSONResponse:
    """
    Predict a response for a user.
    """
    try:
        user = db.get_user_info(user.username)
        response = "Today is a good day!"
        return create_response(
            status_code=200,
            data={"response": response},
        )
    except Exception as e:
        return create_response(
            status_code=400,
            data={"message": str(e)},
        )


@router.get(
    path="/get_all_users",
    tags=["User"],
)
async def get_all_users(db: AppDatabase = Depends(get_db)) -> JSONResponse:
    """
    Get all users.
    """
    try:
        users: List[Dict] = db.get_all_users()
        return create_response(
            status_code=200,
            data={"users": users},
        )
    except Exception as e:
        return create_response(
            status_code=400,
            data={"message": str(e)},
        )


def add_views(app: FastAPI) -> None:
    app.include_router(router)
