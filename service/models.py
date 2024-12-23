import typing as tp

from pydantic import BaseModel


class Error(BaseModel):
    """
    Base error model for all errors in the API.
    """
    error_key: str
    error_message: str
    error_loc: tp.Optional[tp.Any] = None


class UserInit(BaseModel):
    """
    Model for initializing a user.
    """
    username: str
    chat_id: str
    system_prompt: str


class UserPrompt(BaseModel):
    """
    Model to call a AICryptoPulse
    """
    username: str
    prompt: str


class UserNewPrompt(BaseModel):
    """
    Model to update a user's prompt.
    """
    username: str
    new_prompt: str
