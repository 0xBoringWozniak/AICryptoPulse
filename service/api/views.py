import boto3
from datetime import datetime, timedelta
from typing import List, Dict


from fastapi import APIRouter, FastAPI, Depends

from service.api.response import JSONResponse, create_response
from service.mongo.app_database import AppDatabase
from service.models import UserPrompt, UserInit, UserNewPrompt
from service.rag_pipeline import RagPipeline

from service.creds import DB_USER, DB_PASS, DB_HOST, DB_PORT
from service.creds import AWS_S3_API_KEY, AWS_S3_API_SECRET


router = APIRouter()

#
# Define the dependencies for the FastAPI endpoints
#

def get_s3_client() -> boto3.client:
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_S3_API_KEY,
        aws_secret_access_key=AWS_S3_API_SECRET,
    )

def get_rag_pipeline() -> RagPipeline:
    return RagPipeline()

def get_db() -> AppDatabase:
    return AppDatabase(
        db_host=DB_HOST,
        db_port=int(DB_PORT),
        db_user=DB_USER,
        db_user_password=DB_PASS,
    )

#
# Define the FastAPI endpoints
#

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
async def create_user(
    user: UserInit, db: AppDatabase = Depends(get_db)
) -> JSONResponse:
    """
    Create a new user.
    """
    try:
        db.add_user(
            username=user.username,
            chat_id=user.chat_id,
            system_prompt=user.system_prompt,
        )
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
async def set_prompt(
    user: UserNewPrompt, db: AppDatabase = Depends(get_db)
) -> JSONResponse:
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
async def predict(
    user: UserPrompt, s3_client = Depends(get_s3_client),
    db: AppDatabase = Depends(get_db), rag = Depends(get_rag_pipeline),) -> JSONResponse:
    """
    Predict a response for a user.
    """
    try:
        user_info = db.get_user_info(user.username)
        prompt = user_info["system_prompt"] + '\n' + user.prompt

        # use short index for daily report
        if user.daily_report:
            start_time = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            end_time = datetime.now().strftime('%Y-%m-%d')
            object_key = f"llama_feed_index_{start_time}_{end_time}"
        else:
            start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_time = datetime.now().strftime('%Y-%m-%d')
            object_key = f"llama_feed_index_{start_time}_{end_time}"

        rag.initialize_faiss_index(
            s3_client=s3_client,
            bucket_name='ai-embeddings-bucket',
            object_key=object_key
        )
        response = rag.run(prompt)
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
