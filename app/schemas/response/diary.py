from pydantic import BaseModel

class DiaryResponse(BaseModel):
    is_public: bool
    is_owner: bool
    dream_name: str
    dream: str
    resolution: str
    checklist: str
    image_url: str
    create_date: str
    modified_date: str
    view_count: int
    like_count: int
    is_modified: bool

class DiaryListResponse(BaseModel):
    id: int
    dream_name: str
    image_url: str
    view_count: int
    like_count: int
    comment_count: int
    userNickname: str
    userId: int
    is_liked: bool

class DiaryUserListResponse(DiaryListResponse):
    isMine: bool

class CommentListResponse(BaseModel):
    id: int
    userNickname: str
    userId: int
    comment: str
    create_date: str