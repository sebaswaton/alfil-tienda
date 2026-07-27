"""Campos y tablas necesarios para la primera etapa administrativa."""

from alembic import op
import sqlalchemy as sa


revision = "0002_admin_mvp"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "brands",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "brands",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brands_is_active", "brands", ["is_active"])

    op.add_column(
        "categories",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "categories",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_categories_is_active", "categories", ["is_active"])

    op.add_column(
        "products",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column(
        "inquiries",
        sa.Column("is_attended", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("inquiries", sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_inquiries_is_attended", "inquiries", ["is_attended"])

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)
    op.create_index("ix_admin_users_is_active", "admin_users", ["is_active"])

    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_admin_sessions_user_id", "admin_sessions", ["user_id"])
    op.create_index("ix_admin_sessions_token_hash", "admin_sessions", ["token_hash"], unique=True)
    op.create_index("ix_admin_sessions_expires_at", "admin_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_table("admin_sessions")
    op.drop_table("admin_users")
    op.drop_index("ix_inquiries_is_attended", table_name="inquiries")
    op.drop_column("inquiries", "attended_at")
    op.drop_column("inquiries", "is_attended")
    op.drop_column("products", "updated_at")
    op.drop_index("ix_categories_is_active", table_name="categories")
    op.drop_column("categories", "updated_at")
    op.drop_column("categories", "is_active")
    op.drop_index("ix_brands_is_active", table_name="brands")
    op.drop_column("brands", "updated_at")
    op.drop_column("brands", "is_active")
