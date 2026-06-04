from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchResult(BaseModel):
    model_config = ConfigDict(strict=True)

    text: str
    document: str
    distance: float | None = None


class SearchRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def query_must_not_be_whitespace(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("query cannot be empty or whitespace")
        return v


class UpsertItem(BaseModel):
    model_config = ConfigDict(strict=True)

    text: str = Field(min_length=1)
    document: str = Field(min_length=1)


class DocumentRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    items: list[UpsertItem] = Field(min_length=1, max_length=1000)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    status: str = "ok"
    chunks_created: int = Field(ge=0)
