from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    status: str = Field("success", description="응답 상태 ('success' or 'failure')")
    data: Optional[T] = Field(None, description="응답 데이터")
    message: Optional[str] = Field(None, description="추가 메시지")
