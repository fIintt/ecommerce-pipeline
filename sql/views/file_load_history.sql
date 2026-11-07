CREATE OR REPLACE VIEW file_load_history AS
    SELECT 
        id,
        file_name,
        row_count,
        TO_CHAR (loaded_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') AS loaded_at
    FROM
        loaded_files;