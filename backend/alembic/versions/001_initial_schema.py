"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.core.database import VectorType

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(length=64), nullable=False, server_default='application/pdf'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_filename', 'documents', ['filename'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'])

    # 2. document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('embedding', VectorType(1536), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_chunks_id', 'document_chunks', ['id'])
    op.create_index('ix_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_chunks_page_number', 'document_chunks', ['page_number'])
    op.create_index('ix_chunks_doc_chunk_idx', 'document_chunks', ['document_id', 'chunk_index'])

    # 3. conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'])

    # 4. messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('retrieved_chunks', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # 5. evaluation_datasets table
    op.create_table(
        'evaluation_datasets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evaluation_datasets_id', 'evaluation_datasets', ['id'])

    # 6. evaluation_questions table
    op.create_table(
        'evaluation_questions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('dataset_id', sa.String(length=36), sa.ForeignKey('evaluation_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('expected_answer', sa.Text(), nullable=False),
        sa.Column('relevant_document_name', sa.String(length=255), nullable=False),
        sa.Column('relevant_page', sa.Integer(), nullable=True),
        sa.Column('expected_supporting_context', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evaluation_questions_id', 'evaluation_questions', ['id'])
    op.create_index('ix_evaluation_questions_dataset_id', 'evaluation_questions', ['dataset_id'])

    # 7. evaluation_runs table
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('dataset_id', sa.String(length=36), sa.ForeignKey('evaluation_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mean_recall_at_k', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mean_mrr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mean_hit_rate_at_k', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mean_faithfulness', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mean_answer_correctness', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mean_citation_correctness', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evaluation_runs_id', 'evaluation_runs', ['id'])
    op.create_index('ix_evaluation_runs_dataset_id', 'evaluation_runs', ['dataset_id'])

    # 8. evaluation_results table
    op.create_table(
        'evaluation_results',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('evaluation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.String(length=36), sa.ForeignKey('evaluation_questions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('generated_answer', sa.Text(), nullable=False),
        sa.Column('retrieved_chunks', sa.JSON(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('recall_at_k', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mrr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('hit_rate_at_k', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('faithfulness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('faithfulness_reason', sa.Text(), nullable=True),
        sa.Column('answer_correctness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('answer_correctness_reason', sa.Text(), nullable=True),
        sa.Column('citation_correctness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('citation_correctness_reason', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evaluation_results_id', 'evaluation_results', ['id'])
    op.create_index('ix_evaluation_results_run_id', 'evaluation_results', ['run_id'])


def downgrade() -> None:
    op.drop_table('evaluation_results')
    op.drop_table('evaluation_runs')
    op.drop_table('evaluation_questions')
    op.drop_table('evaluation_datasets')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('documents')

