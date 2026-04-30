from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Student Management API")

Instrumentator().instrument(app).expose(app)

students_db: dict[int, dict] = {}
_next_id = 1


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    major: str
    gpa: float = Field(..., ge=0.0, le=4.0)
    year: int = Field(..., ge=1, le=6)


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[float] = Field(default=None, ge=0.0, le=4.0)
    year: Optional[int] = Field(default=None, ge=1, le=6)


def _next_student_id() -> int:
    global _next_id
    sid = _next_id
    _next_id += 1
    return sid


@app.get("/")
def root():
    return {"message": "Student Management API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Student CRUD ---

@app.get("/students", summary="List all students")
def list_students(
    major: Optional[str] = Query(default=None),
    min_gpa: Optional[float] = Query(default=None, ge=0.0, le=4.0),
):
    results = list(students_db.values())
    if major:
        results = [s for s in results if s["major"].lower() == major.lower()]
    if min_gpa is not None:
        results = [s for s in results if s["gpa"] >= min_gpa]
    return {"students": results, "total": len(results)}


@app.get("/students/{student_id}", summary="Get a student by ID")
def get_student(student_id: int):
    student = students_db.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post("/students", status_code=201, summary="Create a new student")
def create_student(student: StudentCreate):
    sid = _next_student_id()
    entry = {"id": sid, **student.model_dump()}
    students_db[sid] = entry
    return entry


@app.put("/students/{student_id}", summary="Replace a student record")
def replace_student(student_id: int, student: StudentCreate):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    entry = {"id": student_id, **student.model_dump()}
    students_db[student_id] = entry
    return entry


@app.patch("/students/{student_id}", summary="Partially update a student record")
def update_student(student_id: int, student: StudentUpdate):
    existing = students_db.get(student_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")
    updates = student.model_dump(exclude_none=True)
    existing.update(updates)
    return existing


@app.delete("/students/{student_id}", status_code=204, summary="Delete a student")
def delete_student(student_id: int):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    del students_db[student_id]


@app.delete("/students", summary="Delete all students")
def delete_all_students():
    count = len(students_db)
    students_db.clear()
    return {"deleted": count}


@app.get("/students/{student_id}/gpa-status", summary="Check a student's GPA standing")
def gpa_status(student_id: int):
    student = students_db.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    gpa = student["gpa"]
    if gpa >= 3.5:
        standing = "Dean's List"
    elif gpa >= 2.0:
        standing = "Good Standing"
    else:
        standing = "Academic Probation"
    return {"id": student_id, "gpa": gpa, "standing": standing}
