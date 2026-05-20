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


class ProjectMemberRemoved(BaseModel):
    project_id: str
    member_id: str

    model_config = {"extra": "ignore"}


class ProjectTaskCreated(BaseModel):
    project_id: str
    task_id: str
    title: str | None = None

    model_config = {"extra": "ignore"}


class ProjectTaskStatusChanged(BaseModel):
    project_id: str
    task_id: str
    status: str
    title: str | None = None

    model_config = {"extra": "ignore"}
