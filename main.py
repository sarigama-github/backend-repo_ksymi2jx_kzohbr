import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Inquiry

app = FastAPI(title="Sanggar Acara API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Sanggar Acara Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Simple model for capturing inquiry from frontend (validated by Pydantic)
class InquiryIn(BaseModel):
    name: str
    email: str
    phone: str | None = None
    event_type: str
    event_date: str | None = None
    budget_range: str | None = None
    message: str | None = None


@app.post("/api/inquiries")
def create_inquiry(payload: InquiryIn):
    try:
        inquiry = Inquiry(**payload.model_dump())
        inserted_id = create_document("inquiry", inquiry)
        return {"success": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inquiries")
def list_inquiries(limit: int = 20):
    try:
        docs = get_documents("inquiry", limit=limit)
        # Convert ObjectId to string for JSON serialization
        def clean(doc: Dict[str, Any]):
            if doc.get("_id"):
                doc["_id"] = str(doc["_id"])
            return doc
        return {"items": [clean(d) for d in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
