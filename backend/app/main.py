import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import urllib.request
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).resolve().parents[2] / "pathfinder.db"))
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-development-secret")

app = FastAPI(title="Pathfinder API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def connection() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db() -> None:
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                full_name TEXT NOT NULL DEFAULT '',
                education TEXT NOT NULL DEFAULT '',
                college TEXT NOT NULL DEFAULT '',
                department TEXT NOT NULL DEFAULT '',
                year TEXT NOT NULL DEFAULT '',
                career TEXT NOT NULL DEFAULT '',
                certifications_json TEXT NOT NULL DEFAULT '{}',
                projects_json TEXT NOT NULL DEFAULT '{}',
                skills_json TEXT NOT NULL DEFAULT '{}',
                completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS assessment_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                skill TEXT NOT NULL,
                result_json TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mentor_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'New conversation',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mentor_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL REFERENCES mentor_conversations(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


@app.on_event("startup")
def startup() -> None:
    init_db()


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class ProfileRequest(BaseModel):
    fullName: str = Field(min_length=1)
    email: str
    education: str = ""
    college: str = ""
    department: str = ""
    year: str = ""
    career: str = ""
    skills: dict[str, str] = {}
    certName: str = ""
    certProvider: str = ""
    projectName: str = ""
    projectDescription: str = ""
    github: str = ""
    experience: str = ""


class AssessmentRequest(BaseModel):
    skill: str
    result: dict


class MentorConversationRequest(BaseModel):
    title: str = "New conversation"


class MentorMessageRequest(BaseModel):
    conversationId: int
    content: str = Field(min_length=1, max_length=4000)


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return base64.urlsafe_b64encode(salt + digest).decode()


def password_matches(password: str, stored: str) -> bool:
    raw = base64.urlsafe_b64decode(stored.encode())
    return hmac.compare_digest(password_hash(password, raw[:16]), stored)


def token_for(user_id: int) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "exp": int(time.time()) + 604800}).encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def current_user(authorization: str | None = Header(default=None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    try:
        payload, signature = authorization[7:].split(".", 1)
        expected = hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if data["exp"] < time.time():
            raise ValueError
        return int(data["sub"])
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(401, "Invalid or expired authentication token")


def profile_row(db: sqlite3.Connection, user_id: int) -> dict | None:
    row = db.execute(
        "SELECT u.id, u.email, p.* FROM users u LEFT JOIN profiles p ON p.user_id = u.id WHERE u.id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["skills"] = json.loads(result.pop("skills_json") or "{}")
    result["certifications"] = json.loads(result.pop("certifications_json") or "{}")
    result["projects"] = json.loads(result.pop("projects_json") or "{}")
    result["profileCompleted"] = bool(result.pop("completed", 0))
    result.pop("password_hash", None)
    return result


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/register")
def register(request: RegisterRequest) -> dict:
    email = str(request.email).lower()
    try:
        with connection() as db:
            cursor = db.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash(request.password)))
            user_id = cursor.lastrowid
            db.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with this email already exists")
    return {"token": token_for(user_id), "user_id": user_id, "profile": profile_row(db, user_id)}


@app.post("/api/auth/login")
def login(request: RegisterRequest) -> dict:
    with connection() as db:
        row = db.execute("SELECT id, password_hash FROM users WHERE email = ?", (str(request.email).lower(),)).fetchone()
        if row is None or not password_matches(request.password, row["password_hash"]):
            raise HTTPException(401, "Invalid email or password")
        return {"token": token_for(row["id"]), "user_id": row["id"], "profile": profile_row(db, row["id"])}


@app.get("/api/profile")
def get_profile(user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        profile = profile_row(db, user_id)
        if profile is None:
            raise HTTPException(404, "Student profile not found")
        return profile


@app.put("/api/profile")
def save_profile(request: ProfileRequest, user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        db.execute(
            """UPDATE profiles SET full_name=?, education=?, college=?, department=?, year=?, career=?,
               certifications_json=?, projects_json=?, skills_json=?, completed=1, updated_at=CURRENT_TIMESTAMP
               WHERE user_id=?""",
            (
                request.fullName,
                request.education,
                request.college,
                request.department,
                request.year,
                request.career,
                json.dumps({"name": request.certName, "provider": request.certProvider}),
                json.dumps({"name": request.projectName, "description": request.projectDescription, "github": request.github}),
                json.dumps(request.skills),
                user_id,
            ),
        )
        return profile_row(db, user_id)


@app.post("/api/assessments")
def save_assessment(request: AssessmentRequest, user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        cursor = db.execute(
            "INSERT INTO assessment_attempts (user_id, skill, result_json) VALUES (?, ?, ?)",
            (user_id, request.skill, json.dumps(request.result)),
        )
        return {"saved": True, "assessmentId": cursor.lastrowid, "skill": request.skill, "result": request.result}


@app.get("/api/assessments")
def get_assessments(user_id: int = Depends(current_user)) -> list[dict]:
    with connection() as db:
        rows = db.execute(
            "SELECT id, skill, result_json, completed_at FROM assessment_attempts WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return [{"id": row["id"], "skill": row["skill"], **json.loads(row["result_json"]), "completedAt": row["completed_at"]} for row in rows]


def mentor_context(db: sqlite3.Connection, user_id: int) -> str:
    profile = profile_row(db, user_id)
    attempts = db.execute(
        "SELECT skill, result_json, completed_at FROM assessment_attempts WHERE user_id = ? ORDER BY id DESC LIMIT 20",
        (user_id,),
    ).fetchall()
    return json.dumps({
        "student": profile,
        "assessment_history": [
            {"skill": row["skill"], **json.loads(row["result_json"]), "completed_at": row["completed_at"]}
            for row in attempts
        ],
    })


def generate_mentor_reply(context: str, message: str, history: list[dict]) -> str:
    system = (
        "You are Pathfinder's AI Mentor. Give clear, practical, personalized learning guidance. "
        "Use only the supplied student context; never invent scores or profile facts. "
        "If context is missing, say what is missing. Keep answers concise and actionable.\nStudent context:\n" + context
    )
    provider = os.getenv("AI_PROVIDER", "local").lower()
    if provider == "ollama" or os.getenv("OLLAMA_URL"):
        url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/chat"
        payload = json.dumps({
            "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
            "stream": False,
            "messages": [{"role": "system", "content": system}, *history[-12:], {"role": "user", "content": message}],
        }).encode()
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode())
        return data["message"]["content"]
    if provider == "local":
        data = json.loads(context)
        profile = data.get("student") or {}
        attempts = data.get("assessment_history") or []
        target_role = profile.get("targetRole") or "your target role"
        skills = profile.get("skills") or {}
        assessed = {
            item.get("skill"): item
            for item in attempts
            if item.get("skill")
        }
        weak = [
            f"{skill} ({item.get('score')}%)"
            for skill, item in assessed.items()
            if isinstance(item.get("score"), (int, float)) and item["score"] < 75
        ]
        awaiting = [skill for skill in skills if skill not in assessed]
        if weak:
            focus = f"Focus first on {', '.join(weak)}. Review the weak topics recorded for those assessments, then retake the assessment after practicing."
        elif awaiting:
            focus = f"Your next measurable step is to assess {', '.join(awaiting)} so your roadmap reflects evidence rather than self-reported skills."
        elif assessed:
            focus = "Your selected skills have assessment evidence. Keep building practical projects and retake assessments after focused practice to track improvement."
        else:
            focus = "Complete a skill assessment so I can give advice based on measured knowledge rather than self-reported skills."
        if "career" in message.lower() or "ready" in message.lower():
            return f"Your current goal is {target_role}. {focus}"
        if "score" in message.lower() or "weak" in message.lower() or "improve" in message.lower():
            return focus
        return f"For {target_role}, {focus}"
    raise HTTPException(503, "AI Mentor provider is unavailable. Set AI_PROVIDER=ollama and start Ollama, or use AI_PROVIDER=local.")


@app.get("/api/mentor/conversations")
def get_conversations(user_id: int = Depends(current_user)) -> list[dict]:
    with connection() as db:
        rows = db.execute(
            "SELECT id, title, created_at, updated_at FROM mentor_conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/mentor/conversations")
def create_conversation(request: MentorConversationRequest, user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        cursor = db.execute("INSERT INTO mentor_conversations (user_id, title) VALUES (?, ?)", (user_id, request.title))
        return {"id": cursor.lastrowid, "title": request.title}


@app.get("/api/mentor/conversations/{conversation_id}")
def get_conversation(conversation_id: int, user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        conversation = db.execute(
            "SELECT id, title, created_at, updated_at FROM mentor_conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        ).fetchone()
        if conversation is None:
            raise HTTPException(404, "Conversation not found")
        messages = db.execute(
            "SELECT id, role, content, created_at FROM mentor_messages WHERE conversation_id = ? AND user_id = ? ORDER BY id",
            (conversation_id, user_id),
        ).fetchall()
        return {"conversation": dict(conversation), "messages": [dict(row) for row in messages]}


@app.post("/api/mentor/messages")
def send_mentor_message(request: MentorMessageRequest, user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        conversation = db.execute(
            "SELECT id FROM mentor_conversations WHERE id = ? AND user_id = ?",
            (request.conversationId, user_id),
        ).fetchone()
        if conversation is None:
            raise HTTPException(404, "Conversation not found")
        history = [
            {"role": row["role"], "content": row["content"]}
            for row in db.execute(
                "SELECT role, content FROM mentor_messages WHERE conversation_id = ? AND user_id = ? ORDER BY id",
                (request.conversationId, user_id),
            ).fetchall()
        ]
        reply = generate_mentor_reply(mentor_context(db, user_id), request.content, history)
        db.execute(
            "INSERT INTO mentor_messages (conversation_id, user_id, role, content) VALUES (?, ?, 'user', ?)",
            (request.conversationId, user_id, request.content),
        )
        db.execute(
            "INSERT INTO mentor_messages (conversation_id, user_id, role, content) VALUES (?, ?, 'assistant', ?)",
            (request.conversationId, user_id, reply),
        )
        db.execute("UPDATE mentor_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (request.conversationId,))
        return {"conversationId": request.conversationId, "reply": reply}


@app.delete("/api/mentor/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        cursor = db.execute("DELETE FROM mentor_conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
        if cursor.rowcount == 0:
            raise HTTPException(404, "Conversation not found")
        return {"deleted": True}


@app.get("/api/dashboard")
def get_dashboard(user_id: int = Depends(current_user)) -> dict:
    with connection() as db:
        profile = profile_row(db, user_id)
        if profile is None:
            raise HTTPException(404, "Student profile not found")
        rows = db.execute(
            "SELECT id, skill, result_json, completed_at FROM assessment_attempts WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        attempts = [{"id": row["id"], "skill": row["skill"], **json.loads(row["result_json"]), "completedAt": row["completed_at"]} for row in rows]
        latest_by_skill = {}
        for attempt in attempts:
            latest_by_skill.setdefault(attempt["skill"], attempt)
        selected_skills = profile.get("skills", {})
        assessed_count = len(latest_by_skill)
        skill_count = len(selected_skills)
        readiness = round(sum(item.get("score", 0) for item in latest_by_skill.values()) / assessed_count) if assessed_count else 0
        progress = round((assessed_count / skill_count) * 100) if skill_count else 0
        return {
            "profile": profile,
            "assessmentCount": len(attempts),
            "latestAssessment": attempts[0] if attempts else None,
            "assessments": attempts,
            "skills": list(latest_by_skill.values()),
            "skillsAwaitingAssessment": [skill for skill in selected_skills if skill not in latest_by_skill],
            "careerReadiness": readiness,
            "overallProgress": progress,
            "completedModules": 0,
            "pendingModules": 0,
        }
