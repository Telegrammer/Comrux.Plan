from pydantic import BaseModel


class UserCreated(BaseModel):
    user_id: str
    name: str
    email: str

    model_config = {"extra": "ignore"}


class ProjectCreated(BaseModel):
    project_id: str
    owner_id: str

    model_config = {"extra": "ignore"}


class ProjectMemberAdded(BaseModel):
    project_id: str
    member_id: str

    model_config = {"extra": "ignore"}
