"""
Migration script to add cliente_nombre and cliente_dni columns to ventas table.
"""
from sqlalchemy import String, Column
from sqlalchemy.sql import table
from alembic import op

def upgrade():
    op.add_column('ventas', Column('cliente_nombre', String(100), nullable=True))
    op.add_column('ventas', Column('cliente_dni', String(20), nullable=True))

def downgrade():
    op.drop_column('ventas', 'cliente_nombre')
    op.drop_column('ventas', 'cliente_dni')
