-- 1. Create dedicated read-only role for the BI Agent
CREATE USER olist_readonly WITH PASSWORD 'readonly_secure_password_123';

-- 2. Grant connection rights to the database
GRANT CONNECT ON DATABASE olist_db TO olist_readonly;

-- 3. Grant schema usage
\c olist_db;
GRANT USAGE ON SCHEMA public TO olist_readonly;

-- 4. Grant SELECT on all current and future tables in public schema
GRANT SELECT ON ALL TABLES IN SCHEMA public TO olist_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO olist_readonly;