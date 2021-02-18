CREATE TABLE `file` (
   `id` INTEGER PRIMARY KEY AUTOINCREMENT,
   `filename` TEXT,
   `size` INTEGER,
   `content_type` TEXT,
   `storage_blocks` TEXT,
   `created` DATETIME DEFAULT CURRENT_TIMESTAMP
);