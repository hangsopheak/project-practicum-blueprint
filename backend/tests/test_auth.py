import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_auth_and_profile_flow():
    # 1. Register a new user (EP-02)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    reg_res = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": password
    })
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["email"] == unique_email
    assert "token" in reg_data

    # 2. Login (EP-03)
    login_res = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": password
    })
    assert login_res.status_code == 200, login_res.text
    login_data = login_res.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Candidate Profile (EP-04)
    profile_res = client.get("/api/v1/profile", headers=headers)
    assert profile_res.status_code == 200, profile_res.text
    profile_data = profile_res.json()
    assert profile_data["user_id"] == reg_data["user_id"]

    # 4. Update Candidate Profile and Skills (EP-05)
    update_res = client.put("/api/v1/profile", headers=headers, json={
        "full_name": "Sreymom Mean",
        "education": "Computer Science, Year 4",
        "experience_level": "entry",
        "preferred_role": "Junior Flutter Developer",
        "preferred_location": "Phnom Penh",
        "expected_salary": 350.00,
        "skills": ["Flutter", "Dart", "Firebase", "Git"]
    })
    assert update_res.status_code == 200, update_res.text
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Sreymom Mean"
    assert "Flutter" in updated_data["skills"]
    assert "Dart" in updated_data["skills"]

def test_unauthorized_profile_access():
    """Verify endpoint protection without valid token"""
    res = client.get("/api/v1/profile")
    assert res.status_code == 401


def test_email_otp_flow():
    """Verify EP-14 (Send OTP) and EP-15 (Verify OTP) end-to-end"""
    target_email = f"candidate_{uuid.uuid4().hex[:8]}@example.com"

    # 1. Send OTP (EP-14)
    send_res = client.post("/api/v1/auth/otp/send", json={
        "email": target_email,
        "purpose": "login_or_verify"
    })
    assert send_res.status_code == 200, send_res.text
    send_data = send_res.json()
    assert send_data["email"] == target_email
    assert send_data["expires_in_seconds"] == 600
    assert "dev_code" in send_data
    otp_code = send_data["dev_code"]
    assert len(otp_code) == 6

    # 2. Verify with wrong code should fail (400)
    bad_res = client.post("/api/v1/auth/otp/verify", json={
        "email": target_email,
        "code": "000000",
        "purpose": "login_or_verify"
    })
    assert bad_res.status_code == 400
    assert bad_res.json()["detail"]["error"]["code"] == "BAD_REQUEST"

    # 3. Verify with correct code (EP-15)
    verify_res = client.post("/api/v1/auth/otp/verify", json={
        "email": target_email,
        "code": otp_code,
        "purpose": "login_or_verify"
    })
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()
    assert "access_token" in verify_data
    assert verify_data["token_type"] == "bearer"
    assert verify_data["user"]["email"] == target_email

    # 4. Reusing the same code should fail (already used)
    reuse_res = client.post("/api/v1/auth/otp/verify", json={
        "email": target_email,
        "code": otp_code,
        "purpose": "login_or_verify"
    })
    assert reuse_res.status_code == 400


def test_email_otp_invalid_input():
    """Test validation errors on bad inputs"""
    # Bad email format -> 422
    res = client.post("/api/v1/auth/otp/send", json={
        "email": "not-an-email"
    })
    assert res.status_code == 422

    # Code not 6 digits -> 422
    res = client.post("/api/v1/auth/otp/verify", json={
        "email": "test@example.com",
        "code": "123"
    })
    assert res.status_code == 422
