"""Initial Schema Setup

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-25 13:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Customers Table
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('total_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lifetime_value', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('risk_score', sa.Numeric(precision=3, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=True)

    # 2. Transactions Table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_customer_id'), 'transactions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_created_at'), 'transactions', ['created_at'], unique=False)

    # 3. Recovery Actions Table
    op.create_table(
        'recovery_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('ai_confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('policy_result', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_actions_transaction_id'), 'recovery_actions', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_recovery_actions_status'), 'recovery_actions', ['status'], unique=False)

    # 4. Recovery Outcomes Table
    op.create_table(
        'recovery_outcomes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recovery_action_id', sa.String(length=36), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('amount_recovered', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['recovery_action_id'], ['recovery_actions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_outcomes_recovery_action_id'), 'recovery_outcomes', ['recovery_action_id'], unique=False)
    op.create_index(op.f('ix_recovery_outcomes_success'), 'recovery_outcomes', ['success'], unique=False)

    # 5. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_transaction_id'), 'audit_logs', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('recovery_outcomes')
    op.drop_table('recovery_actions')
    op.drop_table('transactions')
    op.drop_table('customers')
