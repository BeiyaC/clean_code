truncate_all_tables = """
CREATE OR REPLACE FUNCTION truncate_tables()
	RETURNS void AS
$func$
BEGIN
	EXECUTE (
		SELECT 'TRUNCATE TABLE '
			|| string_agg(format('%I.%I', schemaname, tablename), ', ')
			|| ' CASCADE'
		FROM   pg_tables
		WHERE  schemaname = 'public'
		AND    tablename != 'alembic_version'
	);
END
$func$ LANGUAGE plpgsql;
"""
