CREATE OR REPLACE VIEW file_load_history AS
    SELECT
        lf.id                                                    AS load_id,
        lf.file_name,
        lfs.row_count,
        lfs.rejected_count,
        lfs.skipped_count,
        lfs.loaded_count,
        lfs.elapsed_seconds,
        TO_CHAR (lfs.loaded_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') AS loaded_at
    FROM
        loaded_files AS lf
        JOIN loaded_file_summaries AS lfs ON lfs.loaded_file_id = lf.id;