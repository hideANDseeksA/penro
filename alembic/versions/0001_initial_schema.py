"""initial schema from ordinance ERD

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-16 15:09:09.602343
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import app.core.types

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

# Applied to every create_table() call below so the schema is InnoDB/utf8mb4
# regardless of the server's or database's default engine/charset. On
# PostgreSQL these mysql_* kwargs are simply ignored by SQLAlchemy, so the
# migration stays portable.
_MYSQL_TABLE_KW = dict(
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
)


def upgrade() -> None:
    """Create the full ordinance-derived schema.

    Portable across PostgreSQL and MySQL: UUID keys go through
    app.core.types.GUID (native uuid on PostgreSQL, CHAR(36) on MySQL) and
    every String column carries an explicit length, which MySQL requires.

    Every table is also created with explicit mysql_engine='InnoDB' and
    utf8mb4 charset/collation (see _MYSQL_TABLE_KW), so the schema is
    correct even if the target database's own defaults are wrong (e.g. an
    older MySQL instance/db still defaulting to latin1 or MyISAM). It's
    still good practice to create the database itself as InnoDB/utf8mb4:
        CREATE DATABASE soiltax CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

    Note: the user table is named ``app_user``. ``system_user`` cannot be used
    because PostgreSQL 16+ reserves SYSTEM_USER as a SQL:2023 keyword, which
    makes an unquoted CREATE TABLE system_user a syntax error.
    """
    op.create_table('document_type',
    sa.Column('document_type_id', app.core.types.GUID(), nullable=False),
    sa.Column('document_name', sa.String(length=255), nullable=False),
    sa.Column('mineral_scope', sa.String(length=50), nullable=False),
    sa.Column('stage', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('document_type_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_document_type_mineral_scope'), 'document_type', ['mineral_scope'], unique=False)
    op.create_index(op.f('ix_document_type_stage'), 'document_type', ['stage'], unique=False)
    op.create_table('extraction_site',
    sa.Column('extraction_site_id', app.core.types.GUID(), nullable=False),
    sa.Column('site_name', sa.String(length=255), nullable=False),
    sa.Column('municipality', sa.String(length=100), nullable=True),
    sa.Column('barangay', sa.String(length=100), nullable=True),
    sa.Column('coordinates', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('extraction_site_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_extraction_site_municipality'), 'extraction_site', ['municipality'], unique=False)
    op.create_index(op.f('ix_extraction_site_site_name'), 'extraction_site', ['site_name'], unique=False)
    op.create_table('mineral',
    sa.Column('mineral_id', app.core.types.GUID(), nullable=False),
    sa.Column('mineral_name', sa.String(length=150), nullable=False),
    sa.Column('mineral_category', sa.String(length=100), nullable=False),
    sa.Column('ordinary_quarry_resource_excluded', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('mineral_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_mineral_mineral_category'), 'mineral', ['mineral_category'], unique=False)
    op.create_index(op.f('ix_mineral_mineral_name'), 'mineral', ['mineral_name'], unique=False)
    op.create_table('mining_operation_type',
    sa.Column('operation_type_id', app.core.types.GUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('operation_type_id'),
    sa.UniqueConstraint('name'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('national_agency',
    sa.Column('national_agency_id', app.core.types.GUID(), nullable=False),
    sa.Column('agency_name', sa.String(length=150), nullable=False),
    sa.PrimaryKeyConstraint('national_agency_id'),
    sa.UniqueConstraint('agency_name'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('provincial_office',
    sa.Column('provincial_office_id', app.core.types.GUID(), nullable=False),
    sa.Column('office_name', sa.String(length=150), nullable=False),
    sa.Column('office_role', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('provincial_office_id'),
    sa.UniqueConstraint('office_name'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('remedy_type',
    sa.Column('remedy_type_id', app.core.types.GUID(), nullable=False),
    sa.Column('remedy_name', sa.String(length=50), nullable=False),
    sa.Column('filing_deadline', sa.String(length=150), nullable=True),
    sa.PrimaryKeyConstraint('remedy_type_id'),
    sa.UniqueConstraint('remedy_name'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('role',
    sa.Column('role_id', app.core.types.GUID(), nullable=False),
    sa.Column('role_name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('role_id'),
    sa.UniqueConstraint('role_name'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('taxpayer',
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_name', sa.String(length=255), nullable=False),
    sa.Column('taxpayer_type', sa.String(length=100), nullable=False),
    sa.Column('tax_identification_details', sa.String(length=100), nullable=True),
    sa.Column('business_address', sa.String(length=255), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('taxpayer_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_taxpayer_tax_identification_details'), 'taxpayer', ['tax_identification_details'], unique=False)
    op.create_index(op.f('ix_taxpayer_taxpayer_name'), 'taxpayer', ['taxpayer_name'], unique=False)
    op.create_table('annual_collection_report',
    sa.Column('report_id', app.core.types.GUID(), nullable=False),
    sa.Column('provincial_office_id', app.core.types.GUID(), nullable=False),
    sa.Column('fiscal_year', sa.Integer(), nullable=False),
    sa.Column('total_collections', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('submission_date', sa.Date(), nullable=True),
    sa.Column('posting_date', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['provincial_office_id'], ['provincial_office.provincial_office_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('report_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_annual_collection_report_fiscal_year'), 'annual_collection_report', ['fiscal_year'], unique=False)
    op.create_index(op.f('ix_annual_collection_report_provincial_office_id'), 'annual_collection_report', ['provincial_office_id'], unique=False)
    op.create_table('books_examination_record',
    sa.Column('examination_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('provincial_office_id', app.core.types.GUID(), nullable=False),
    sa.Column('examination_date', sa.Date(), nullable=False),
    sa.Column('scope', sa.String(length=255), nullable=True),
    sa.Column('findings', sa.Text(), nullable=True),
    sa.Column('confidentiality_status', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['provincial_office_id'], ['provincial_office.provincial_office_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('examination_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_books_examination_record_examination_date'), 'books_examination_record', ['examination_date'], unique=False)
    op.create_index(op.f('ix_books_examination_record_provincial_office_id'), 'books_examination_record', ['provincial_office_id'], unique=False)
    op.create_index(op.f('ix_books_examination_record_taxpayer_id'), 'books_examination_record', ['taxpayer_id'], unique=False)
    op.create_table('extraction_record',
    sa.Column('extraction_record_id', app.core.types.GUID(), nullable=False),
    sa.Column('extraction_site_id', app.core.types.GUID(), nullable=False),
    sa.Column('mineral_id', app.core.types.GUID(), nullable=False),
    sa.Column('extraction_date', sa.Date(), nullable=False),
    sa.Column('volume_extracted', sa.Numeric(precision=18, scale=3), nullable=False),
    sa.Column('grade', sa.String(length=100), nullable=True),
    sa.Column('quality', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['extraction_site_id'], ['extraction_site.extraction_site_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['mineral_id'], ['mineral.mineral_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('extraction_record_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_extraction_record_extraction_date'), 'extraction_record', ['extraction_date'], unique=False)
    op.create_index(op.f('ix_extraction_record_extraction_site_id'), 'extraction_record', ['extraction_site_id'], unique=False)
    op.create_index(op.f('ix_extraction_record_mineral_id'), 'extraction_record', ['mineral_id'], unique=False)
    op.create_table('mining_operation',
    sa.Column('mining_operation_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('operation_type_id', app.core.types.GUID(), nullable=False),
    sa.Column('operation_name', sa.String(length=255), nullable=False),
    sa.Column('legal_basis', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['operation_type_id'], ['mining_operation_type.operation_type_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('mining_operation_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_mining_operation_operation_name'), 'mining_operation', ['operation_name'], unique=False)
    op.create_index(op.f('ix_mining_operation_operation_type_id'), 'mining_operation', ['operation_type_id'], unique=False)
    op.create_index(op.f('ix_mining_operation_status'), 'mining_operation', ['status'], unique=False)
    op.create_index(op.f('ix_mining_operation_taxpayer_id'), 'mining_operation', ['taxpayer_id'], unique=False)
    op.create_table('soil_depletion_tax_return',
    sa.Column('return_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('return_period', sa.String(length=10), nullable=False),
    sa.Column('filing_date', sa.Date(), nullable=True),
    sa.Column('reported_gross_receipts', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('return_status', sa.String(length=30), nullable=False),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('return_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index('ix_return_taxpayer_period', 'soil_depletion_tax_return', ['taxpayer_id', 'return_period'], unique=True)
    op.create_index(op.f('ix_soil_depletion_tax_return_filing_date'), 'soil_depletion_tax_return', ['filing_date'], unique=False)
    op.create_index(op.f('ix_soil_depletion_tax_return_return_period'), 'soil_depletion_tax_return', ['return_period'], unique=False)
    op.create_index(op.f('ix_soil_depletion_tax_return_return_status'), 'soil_depletion_tax_return', ['return_status'], unique=False)
    op.create_index(op.f('ix_soil_depletion_tax_return_taxpayer_id'), 'soil_depletion_tax_return', ['taxpayer_id'], unique=False)
    op.create_table('app_user',
    sa.Column('user_id', app.core.types.GUID(), nullable=False),
    sa.Column('role_id', app.core.types.GUID(), nullable=False),
    sa.Column('provincial_office_id', app.core.types.GUID(), nullable=True),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=True),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('last_login', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['provincial_office_id'], ['provincial_office.provincial_office_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['role_id'], ['role.role_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('username'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_app_user_provincial_office_id'), 'app_user', ['provincial_office_id'], unique=False)
    op.create_index(op.f('ix_app_user_role_id'), 'app_user', ['role_id'], unique=False)
    op.create_index(op.f('ix_app_user_taxpayer_id'), 'app_user', ['taxpayer_id'], unique=False)
    op.create_table('audit_log',
    sa.Column('log_id', app.core.types.GUID(), nullable=False),
    sa.Column('user_id', app.core.types.GUID(), nullable=True),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('entity_name', sa.String(length=100), nullable=False),
    sa.Column('entity_id', app.core.types.GUID(), nullable=True),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('logged_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['app_user.user_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('log_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_audit_log_action'), 'audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_audit_log_entity_id'), 'audit_log', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_log_entity_name'), 'audit_log', ['entity_name'], unique=False)
    op.create_index(op.f('ix_audit_log_logged_at'), 'audit_log', ['logged_at'], unique=False)
    op.create_index(op.f('ix_audit_log_user_id'), 'audit_log', ['user_id'], unique=False)
    op.create_table('mining_operation_extraction_site',
    sa.Column('mining_operation_id', app.core.types.GUID(), nullable=False),
    sa.Column('extraction_site_id', app.core.types.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['extraction_site_id'], ['extraction_site.extraction_site_id'], ),
    sa.ForeignKeyConstraint(['mining_operation_id'], ['mining_operation.mining_operation_id'], ),
    sa.PrimaryKeyConstraint('mining_operation_id', 'extraction_site_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('mining_operation_mineral',
    sa.Column('mining_operation_id', app.core.types.GUID(), nullable=False),
    sa.Column('mineral_id', app.core.types.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['mineral_id'], ['mineral.mineral_id'], ),
    sa.ForeignKeyConstraint(['mining_operation_id'], ['mining_operation.mining_operation_id'], ),
    sa.PrimaryKeyConstraint('mining_operation_id', 'mineral_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_table('permit_authority',
    sa.Column('permit_authority_id', app.core.types.GUID(), nullable=False),
    sa.Column('mining_operation_id', app.core.types.GUID(), nullable=False),
    sa.Column('permit_type', sa.String(length=100), nullable=False),
    sa.Column('permit_number', sa.String(length=100), nullable=False),
    sa.Column('issuing_authority', sa.String(length=150), nullable=True),
    sa.Column('issue_date', sa.Date(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['mining_operation_id'], ['mining_operation.mining_operation_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('permit_authority_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_permit_authority_mining_operation_id'), 'permit_authority', ['mining_operation_id'], unique=False)
    op.create_index(op.f('ix_permit_authority_permit_number'), 'permit_authority', ['permit_number'], unique=False)
    op.create_index(op.f('ix_permit_authority_permit_type'), 'permit_authority', ['permit_type'], unique=False)
    op.create_table('shipment',
    sa.Column('shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('mining_operation_id', app.core.types.GUID(), nullable=False),
    sa.Column('extraction_site_id', app.core.types.GUID(), nullable=False),
    sa.Column('mineral_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_date', sa.Date(), nullable=False),
    sa.Column('estimated_volume', sa.Numeric(precision=18, scale=3), nullable=True),
    sa.Column('final_volume', sa.Numeric(precision=18, scale=3), nullable=True),
    sa.Column('gross_receipts', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('buyer', sa.String(length=255), nullable=True),
    sa.Column('destination', sa.String(length=255), nullable=True),
    sa.Column('shipment_status', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['extraction_site_id'], ['extraction_site.extraction_site_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['mineral_id'], ['mineral.mineral_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['mining_operation_id'], ['mining_operation.mining_operation_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('shipment_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_shipment_buyer'), 'shipment', ['buyer'], unique=False)
    op.create_index(op.f('ix_shipment_extraction_site_id'), 'shipment', ['extraction_site_id'], unique=False)
    op.create_index(op.f('ix_shipment_mineral_id'), 'shipment', ['mineral_id'], unique=False)
    op.create_index(op.f('ix_shipment_mining_operation_id'), 'shipment', ['mining_operation_id'], unique=False)
    op.create_index(op.f('ix_shipment_shipment_date'), 'shipment', ['shipment_date'], unique=False)
    op.create_index(op.f('ix_shipment_shipment_status'), 'shipment', ['shipment_status'], unique=False)
    op.create_index('ix_shipment_taxpayer_date', 'shipment', ['taxpayer_id', 'shipment_date'], unique=False)
    op.create_index(op.f('ix_shipment_taxpayer_id'), 'shipment', ['taxpayer_id'], unique=False)
    op.create_table('national_agency_document',
    sa.Column('national_agency_document_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('national_agency_id', app.core.types.GUID(), nullable=False),
    sa.Column('document_name', sa.String(length=255), nullable=False),
    sa.Column('document_date', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['national_agency_id'], ['national_agency.national_agency_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('national_agency_document_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_national_agency_document_national_agency_id'), 'national_agency_document', ['national_agency_id'], unique=False)
    op.create_index(op.f('ix_national_agency_document_shipment_id'), 'national_agency_document', ['shipment_id'], unique=False)
    op.create_table('provincial_monitoring_record',
    sa.Column('monitoring_record_id', app.core.types.GUID(), nullable=False),
    sa.Column('mining_operation_id', app.core.types.GUID(), nullable=True),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=True),
    sa.Column('provincial_office_id', app.core.types.GUID(), nullable=False),
    sa.Column('monitoring_date', sa.Date(), nullable=False),
    sa.Column('volume', sa.Numeric(precision=18, scale=3), nullable=True),
    sa.Column('findings', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['mining_operation_id'], ['mining_operation.mining_operation_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['provincial_office_id'], ['provincial_office.provincial_office_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('monitoring_record_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_provincial_monitoring_record_mining_operation_id'), 'provincial_monitoring_record', ['mining_operation_id'], unique=False)
    op.create_index(op.f('ix_provincial_monitoring_record_monitoring_date'), 'provincial_monitoring_record', ['monitoring_date'], unique=False)
    op.create_index(op.f('ix_provincial_monitoring_record_provincial_office_id'), 'provincial_monitoring_record', ['provincial_office_id'], unique=False)
    op.create_index(op.f('ix_provincial_monitoring_record_shipment_id'), 'provincial_monitoring_record', ['shipment_id'], unique=False)
    op.create_table('provincial_soil_depletion_tax_clearance',
    sa.Column('clearance_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('application_date', sa.Date(), nullable=False),
    sa.Column('issuance_date', sa.Date(), nullable=True),
    sa.Column('clearance_status', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('clearance_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_provincial_soil_depletion_tax_clearance_application_date'), 'provincial_soil_depletion_tax_clearance', ['application_date'], unique=False)
    op.create_index(op.f('ix_provincial_soil_depletion_tax_clearance_clearance_status'), 'provincial_soil_depletion_tax_clearance', ['clearance_status'], unique=False)
    op.create_index(op.f('ix_provincial_soil_depletion_tax_clearance_shipment_id'), 'provincial_soil_depletion_tax_clearance', ['shipment_id'], unique=True)
    op.create_index(op.f('ix_provincial_soil_depletion_tax_clearance_taxpayer_id'), 'provincial_soil_depletion_tax_clearance', ['taxpayer_id'], unique=False)
    op.create_table('return_shipment',
    sa.Column('return_shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('return_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('reported_volume_shipped', sa.Numeric(precision=18, scale=3), nullable=True),
    sa.Column('otp_reference', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['return_id'], ['soil_depletion_tax_return.return_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('return_shipment_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_return_shipment_otp_reference'), 'return_shipment', ['otp_reference'], unique=False)
    op.create_index(op.f('ix_return_shipment_return_id'), 'return_shipment', ['return_id'], unique=False)
    op.create_index(op.f('ix_return_shipment_shipment_id'), 'return_shipment', ['shipment_id'], unique=False)
    op.create_table('shipment_document',
    sa.Column('shipment_document_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('document_type_id', app.core.types.GUID(), nullable=False),
    sa.Column('document_number', sa.String(length=100), nullable=True),
    sa.Column('document_date', sa.Date(), nullable=True),
    sa.Column('document_status', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['document_type_id'], ['document_type.document_type_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('shipment_document_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_shipment_document_document_status'), 'shipment_document', ['document_status'], unique=False)
    op.create_index(op.f('ix_shipment_document_document_type_id'), 'shipment_document', ['document_type_id'], unique=False)
    op.create_index(op.f('ix_shipment_document_shipment_id'), 'shipment_document', ['shipment_id'], unique=False)
    op.create_table('tax_assessment',
    sa.Column('assessment_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=False),
    sa.Column('estimated_gross_receipts', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('gross_receipts', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('tax_rate', sa.Numeric(precision=9, scale=6), nullable=False),
    sa.Column('tax_due', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('surcharge', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('interest', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('assessment_stage', sa.String(length=20), nullable=False),
    sa.Column('assessment_date', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('assessment_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_tax_assessment_assessment_date'), 'tax_assessment', ['assessment_date'], unique=False)
    op.create_index(op.f('ix_tax_assessment_assessment_stage'), 'tax_assessment', ['assessment_stage'], unique=False)
    op.create_index(op.f('ix_tax_assessment_shipment_id'), 'tax_assessment', ['shipment_id'], unique=False)
    op.create_index(op.f('ix_tax_assessment_taxpayer_id'), 'tax_assessment', ['taxpayer_id'], unique=False)
    op.create_table('violation',
    sa.Column('violation_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('shipment_id', app.core.types.GUID(), nullable=True),
    sa.Column('return_id', app.core.types.GUID(), nullable=True),
    sa.Column('violation_date', sa.Date(), nullable=False),
    sa.Column('violation_type', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.ForeignKeyConstraint(['return_id'], ['soil_depletion_tax_return.return_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.shipment_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('violation_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_violation_return_id'), 'violation', ['return_id'], unique=False)
    op.create_index(op.f('ix_violation_shipment_id'), 'violation', ['shipment_id'], unique=False)
    op.create_index(op.f('ix_violation_status'), 'violation', ['status'], unique=False)
    op.create_index(op.f('ix_violation_taxpayer_id'), 'violation', ['taxpayer_id'], unique=False)
    op.create_index(op.f('ix_violation_violation_date'), 'violation', ['violation_date'], unique=False)
    op.create_index(op.f('ix_violation_violation_type'), 'violation', ['violation_type'], unique=False)
    op.create_table('penalty_or_administrative_sanction',
    sa.Column('sanction_id', app.core.types.GUID(), nullable=False),
    sa.Column('violation_id', app.core.types.GUID(), nullable=False),
    sa.Column('sanction_type', sa.String(length=50), nullable=False),
    sa.Column('fine_amount', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('sanction_date', sa.Date(), nullable=False),
    sa.Column('settled', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['violation_id'], ['violation.violation_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('sanction_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_penalty_or_administrative_sanction_sanction_date'), 'penalty_or_administrative_sanction', ['sanction_date'], unique=False)
    op.create_index(op.f('ix_penalty_or_administrative_sanction_sanction_type'), 'penalty_or_administrative_sanction', ['sanction_type'], unique=False)
    op.create_index(op.f('ix_penalty_or_administrative_sanction_settled'), 'penalty_or_administrative_sanction', ['settled'], unique=False)
    op.create_index(op.f('ix_penalty_or_administrative_sanction_violation_id'), 'penalty_or_administrative_sanction', ['violation_id'], unique=False)
    op.create_table('tax_payment',
    sa.Column('payment_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('assessment_id', app.core.types.GUID(), nullable=False),
    sa.Column('clearance_id', app.core.types.GUID(), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=False),
    sa.Column('amount_paid', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('payment_type', sa.String(length=30), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['tax_assessment.assessment_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['clearance_id'], ['provincial_soil_depletion_tax_clearance.clearance_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('payment_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_tax_payment_assessment_id'), 'tax_payment', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_tax_payment_clearance_id'), 'tax_payment', ['clearance_id'], unique=False)
    op.create_index(op.f('ix_tax_payment_payment_date'), 'tax_payment', ['payment_date'], unique=False)
    op.create_index(op.f('ix_tax_payment_payment_type'), 'tax_payment', ['payment_type'], unique=False)
    op.create_index(op.f('ix_tax_payment_taxpayer_id'), 'tax_payment', ['taxpayer_id'], unique=False)
    op.create_table('taxpayer_remedy',
    sa.Column('remedy_id', app.core.types.GUID(), nullable=False),
    sa.Column('taxpayer_id', app.core.types.GUID(), nullable=False),
    sa.Column('assessment_id', app.core.types.GUID(), nullable=True),
    sa.Column('remedy_type_id', app.core.types.GUID(), nullable=False),
    sa.Column('filing_date', sa.Date(), nullable=False),
    sa.Column('decision_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['tax_assessment.assessment_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['remedy_type_id'], ['remedy_type.remedy_type_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer.taxpayer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('remedy_id'),
    **_MYSQL_TABLE_KW
    )
    op.create_index(op.f('ix_taxpayer_remedy_assessment_id'), 'taxpayer_remedy', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_taxpayer_remedy_filing_date'), 'taxpayer_remedy', ['filing_date'], unique=False)
    op.create_index(op.f('ix_taxpayer_remedy_remedy_type_id'), 'taxpayer_remedy', ['remedy_type_id'], unique=False)
    op.create_index(op.f('ix_taxpayer_remedy_status'), 'taxpayer_remedy', ['status'], unique=False)
    op.create_index(op.f('ix_taxpayer_remedy_taxpayer_id'), 'taxpayer_remedy', ['taxpayer_id'], unique=False)


def downgrade() -> None:
    op.drop_table('taxpayer_remedy')
    op.drop_table('tax_payment')
    op.drop_table('penalty_or_administrative_sanction')
    op.drop_table('violation')
    op.drop_table('tax_assessment')
    op.drop_table('shipment_document')
    op.drop_table('return_shipment')
    op.drop_table('provincial_soil_depletion_tax_clearance')
    op.drop_table('provincial_monitoring_record')
    op.drop_table('national_agency_document')
    op.drop_table('shipment')
    op.drop_table('permit_authority')
    op.drop_table('mining_operation_mineral')
    op.drop_table('mining_operation_extraction_site')
    op.drop_table('audit_log')
    op.drop_table('app_user')
    op.drop_table('soil_depletion_tax_return')
    op.drop_table('mining_operation')
    op.drop_table('extraction_record')
    op.drop_table('books_examination_record')
    op.drop_table('annual_collection_report')
    op.drop_table('taxpayer')
    op.drop_table('role')
    op.drop_table('remedy_type')
    op.drop_table('provincial_office')
    op.drop_table('national_agency')
    op.drop_table('mining_operation_type')
    op.drop_table('mineral')
    op.drop_table('extraction_site')
    op.drop_table('document_type')