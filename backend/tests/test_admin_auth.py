from app import models
from app.auth.security import hash_password


def create_admin(db):
    admin = models.AdminUser(
        email="admin@example.com",
        password_hash=hash_password("correct-password"),
    )
    db.add(admin)
    db.commit()


def test_login_me_csrf_and_logout(client, db):
    create_admin(db)

    invalid = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )
    assert invalid.status_code == 401

    login = client.post(
        "/api/admin/auth/login",
        json={"email": "ADMIN@EXAMPLE.COM", "password": "correct-password"},
    )
    assert login.status_code == 200
    csrf_token = login.json()["csrf_token"]
    assert login.json()["user"]["email"] == "admin@example.com"
    assert "httponly" in login.headers["set-cookie"].lower()

    assert client.get("/api/admin/auth/me").status_code == 200
    assert client.get("/api/admin/products").status_code == 200

    without_csrf = client.post("/api/admin/products")
    assert without_csrf.status_code == 403

    prepared = client.post(
        "/api/admin/products",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert prepared.status_code == 422

    logout = client.post(
        "/api/admin/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout.status_code == 204
    assert client.get("/api/admin/auth/me").status_code == 401


def test_inactive_admin_cannot_login(client, db):
    admin = models.AdminUser(
        email="disabled@example.com",
        password_hash=hash_password("correct-password"),
        is_active=False,
    )
    db.add(admin)
    db.commit()

    response = client.post(
        "/api/admin/auth/login",
        json={"email": "disabled@example.com", "password": "correct-password"},
    )
    assert response.status_code == 403
