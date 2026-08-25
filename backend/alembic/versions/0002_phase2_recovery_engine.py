"""Phase 2 Recovery Engine Tables & Columns

Revision ID: 0002_phase2_recovery_engine
Revises: 0001_initial_schema
Create Date: 2026-08-25 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_phase2_recovery_engine'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create recovery_workflows table
    op.create_table(
        'recovery_workflows',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='INITIATED'),
        sa.Column('failure_category', sa.String(length=50), nullable=False, server_default='unknown_failure'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_workflows_transaction_id'), 'recovery_workflows', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_recovery_workflows_status'), 'recovery_workflows', ['status'], unique=False)
    op.create_index(op.f('ix_recovery_workflows_failure_category'), 'recovery_workflows', ['failure_category'], unique=False)

    # 2. Create recovery_decisions table
    op.create_table(
        'recovery_decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workflow_id', sa.String(length=36), nullable=False),
        sa.Column('failure_category', sa.String(length=50), nullable=False),
        sa.Column('recommended_strategy', sa.String(length=50), nullable=False),
        sa.Column('final_strategy', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('policy_result', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=False, server_default='1.00'),
        sa.Column('explanation_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['recovery_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_decisions_workflow_id'), 'recovery_decisions', ['workflow_id'], unique=False)

    # 3. Create recovery_attempts table
    op.create_table(
        'recovery_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recovery_action_id', sa.String(length=36), nullable=False),
        sa.Column('workflow_id', sa.String(length=36), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('amount_recovered', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('response_metadata', sa.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['recovery_action_id'], ['recovery_actions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['recovery_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_attempts_recovery_action_id'), 'recovery_attempts', ['recovery_action_id'], unique=False)
    op.create_index(op.f('ix_recovery_attempts_workflow_id'), 'recovery_attempts', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_recovery_attempts_success'), 'recovery_attempts', ['success'], unique=False)

    # 4. Add workflow_id to recovery_actions table
    op.add_column('recovery_actions', sa.Column('workflow_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_recovery_actions_workflow_id', 'recovery_actions', 'recovery_workflows', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_recovery_actions_workflow_id'), 'recovery_actions', ['workflow_id'], unique=False)

    # 5. Add workflow_id, action, status_result to audit_logs table
    op.add_column('audit_logs', sa.Column('workflow_id', sa.String(length=36), nullable=True))
    op.add_column('audit_logs', sa.Column('action', sa.String(length=255), nullable=True))
    op.add_column('audit_logs', sa.Column('status_result', sa.String(length=100), nullable=True))
    op.create_foreign_key('fk_audit_logs_workflow_id', 'audit_logs', 'recovery_workflows', ['workflow_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_audit_logs_workflow_id'), 'audit_logs', ['workflow_id'], unique=False)

def downgrade() -> None:
    op.drop_constraint('fk_audit_logs_workflow_id', 'audit_logs', type_='foreignkey')
    op.drop_column('audit_logs', 'status_result')
    op.drop_column('audit_logs', 'action')
    op.drop_column('audit_logs', 'workflow_id')

    op.drop_constraint('fk_recovery_actions_workflow_id', 'recovery_actions', type_='foreignkey')
    op.drop_column('recovery_actions', 'workflow_id')

    op.drop_table('recovery_attempts')
    op.drop_table('recovery_decisions')
    op.drop_table('recovery_workflows')
