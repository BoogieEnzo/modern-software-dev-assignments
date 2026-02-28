from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "data" / "app.db"


class Base(DeclarativeBase):
    pass


class RepoSnapshot(Base):
    __tablename__ = "repo_snapshots"

    id = Column(Integer, primary_key=True)
    snapshot_date = Column(String(10))
    repos_7d_json = Column(JSON)
    repos_30d_json = Column(JSON)
    repos_agent_json = Column(JSON)
    generated_at = Column(DateTime(timezone=True))
    status = Column(String(20))
    error_msg = Column(String, nullable=True)


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    return SessionLocal()


def save_snapshot(
    snapshot_date: str,
    repos_7d: List[Dict[str, Any]],
    repos_30d: List[Dict[str, Any]],
    repos_agent: List[Dict[str, Any]] = [],
    status: str = "success",
    error_msg: Optional[str] = None,
) -> RepoSnapshot:
    init_db()
    with get_db() as db:
        existing = db.query(RepoSnapshot).filter_by(snapshot_date=snapshot_date).first()

        now = datetime.now(timezone.utc)

        if existing:
            existing.repos_7d_json = repos_7d
            existing.repos_30d_json = repos_30d
            existing.repos_agent_json = repos_agent
            existing.generated_at = now
            existing.status = status
            existing.error_msg = error_msg
            snapshot = existing
        else:
            snapshot = RepoSnapshot(
                snapshot_date=snapshot_date,
                repos_7d_json=repos_7d,
                repos_30d_json=repos_30d,
                repos_agent_json=repos_agent,
                generated_at=now,
                status=status,
                error_msg=error_msg,
            )
            db.add(snapshot)

        db.commit()
        db.refresh(snapshot)

        _cleanup_old_snapshots(db)

        return snapshot


def load_today_snapshot(today: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_db() as db:
        snapshot = db.query(RepoSnapshot).filter_by(snapshot_date=today).first()

        if snapshot and snapshot.status == "success":
            return {
                "date": snapshot.snapshot_date,
                "generated_at": snapshot.generated_at,
                "repos_7d": snapshot.repos_7d_json,
                "repos_30d": snapshot.repos_30d_json,
                "repos_agent": snapshot.repos_agent_json or [],
            }

        return None


def _cleanup_old_snapshots(db: Session) -> None:
    all_snapshots = db.query(RepoSnapshot).all()

    for snap in all_snapshots:
        try:
            snap_date = date.fromisoformat(snap.snapshot_date)
            days_diff = (datetime.now(timezone.utc).date() - snap_date).days
            if days_diff > 30:
                db.delete(snap)
        except (ValueError, TypeError):
            continue

    db.commit()
