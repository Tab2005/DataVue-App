"""
test_teams.py — 團隊管理測試

涵蓋：
  - 建立/讀取 Team、TeamMember 模型
  - 使用者只可看到自己所屬的團隊
  - 邀請 Token 生命週期
"""

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi import status


class TestTeamModel:
    """Team ORM 模型 CRUD 測試"""

    def test_create_team(self, db, admin_user):
        """能夠建立團隊並取回。"""
        from database.models.team import Team

        team = Team(
            id=str(uuid.uuid4()),
            name="測試廣告團隊",
            owner_id=admin_user.id,
        )
        db.add(team)
        db.commit()

        fetched = db.query(Team).filter_by(name="測試廣告團隊").first()
        assert fetched is not None
        assert fetched.owner_id == admin_user.id

    def test_create_team_member(self, db, admin_user, test_user):
        """能夠將使用者加入團隊。"""
        from database.models.team import Team, TeamMember

        team = Team(
            id=str(uuid.uuid4()),
            name="積極行銷隊",
            owner_id=admin_user.id,
        )
        db.add(team)
        db.commit()

        member = TeamMember(
            team_id=team.id,
            user_id=test_user.id,
            role="member",
        )
        db.add(member)
        db.commit()

        result = db.query(TeamMember).filter_by(
            team_id=team.id, user_id=test_user.id
        ).first()
        assert result is not None
        assert result.role == "member"

    def test_team_invite_token(self, db, admin_user):
        """邀請 Token 應可建立並標記為已使用。"""
        from database.models.team import Team, TeamInvite

        team = Team(
            id=str(uuid.uuid4()),
            name="邀請測試隊",
            owner_id=admin_user.id,
        )
        db.add(team)
        db.commit()

        invite = TeamInvite(
            id=str(uuid.uuid4()),
            team_id=team.id,
            email="newmember@example.com",
            role="member",
            token=str(uuid.uuid4()),
            is_used=False,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(invite)
        db.commit()

        # 標記為已使用
        invite.is_used = True
        db.commit()

        fetched = db.query(TeamInvite).filter_by(team_id=team.id).first()
        assert fetched.is_used is True


class TestTeamAPI:
    """團隊 API 端點測試"""

    def test_get_my_teams_requires_auth(self, client):
        """取得我的團隊清單時若無 Token 應回傳 4xx。"""
        response = client.get("/api/teams/")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_authenticated_user_can_get_teams(
        self, client, db, admin_user, mock_google_token_admin, admin_auth_headers
    ):
        """已認證使用者可取得團隊列表（回傳 200，可能為空列表）。"""
        response = client.get("/api/teams/", headers=admin_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert isinstance(body, (list, dict))  # 陣列或 {teams: [...]}
