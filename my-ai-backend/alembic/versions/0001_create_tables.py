"""Initial tables for Health AI Assistant."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_create_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("sex", sa.Enum("M", "F", "O", name="sexenum"), nullable=True),
        sa.Column("chronic_conditions", sa.JSON(), nullable=True),
        sa.Column("allergies", sa.JSON(), nullable=True),
        sa.Column("meds", sa.JSON(), nullable=True),
        sa.Column("habits", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.Enum("NCD", "MH", name="domainenum"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("primary_symptom", sa.String(length=255), nullable=False),
        sa.Column("severity_0_10", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("symptom_scores", sa.JSON(), nullable=True),
        sa.Column("side_effects", sa.JSON(), nullable=True),
        sa.Column("interventions", sa.JSON(), nullable=True),
        sa.Column("vitals", sa.JSON(), nullable=True),
        sa.Column("mh_scales", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "measurements_meta",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "type",
            sa.Enum("bp", "glucose", "weight", "sleep", "mh_scale", name="measurementtypeenum"),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.Enum("manual", "device", "import", name="measurementsourceenum"),
            nullable=False,
        ),
        sa.Column("unit", sa.String(length=50), nullable=False),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "triage_level",
            sa.Enum("self-care", "primary-care", "urgent", "emergency", name="triageenum"),
            nullable=False,
        ),
        sa.Column("condition_hints", sa.JSON(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
    )


def downgrade():
    op.drop_table("recommendations")
    op.drop_table("measurements_meta")
    op.drop_table("observations")
    op.drop_table("episodes")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
