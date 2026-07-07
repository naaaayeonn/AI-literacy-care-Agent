from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.db import get_db
from ..models.models import ReadingSession, ReadingEvent, User

router = APIRouter(prefix="/api/user", tags=["User Data Management"])

@router.delete("/{user_id}/data")
async def delete_user_data(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    ADR-002: 익명 사용자 데이터 파기 요청 (세션 및 이벤트 일괄 삭제)
    """
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()
    
    if not user:
        return {"status": "success", "message": f"User {user_id} not found or already deleted."}
        
    # 세션 조회
    sessions_result = await db.execute(select(ReadingSession).filter(ReadingSession.user_id == user_id))
    sessions = sessions_result.scalars().all()
    session_ids = [s.id for s in sessions]
    
    # 해당 세션의 모든 이벤트 삭제
    if session_ids:
        for sid in session_ids:
            events_result = await db.execute(select(ReadingEvent).filter(ReadingEvent.session_id == sid))
            events = events_result.scalars().all()
            for ev in events:
                await db.delete(ev)
            
        for s in sessions:
            await db.delete(s)
            
    await db.delete(user)
    await db.commit()
    
    return {"status": "success", "message": f"Data for user {user_id} deleted successfully."}
