

CREATE TABLE t_user (
    id INTEGER NOT NULL, 
    username VARCHAR NOT NULL, 
    password VARCHAR NOT NULL, 
    user_status INTEGER DEFAULT 0, 
    email VARCHAR DEFAULT '', 
    phone VARCHAR DEFAULT '', 
    created_at DATETIME DEFAULT (DATETIME('now')), 
    updated_at DATETIME DEFAULT (DATETIME('now')), 
    PRIMARY KEY (id), 
    UNIQUE (username)
);


INSERT INTO t_user (username, password, user_status, email, phone, created_at, updated_at)
VALUES
    ('tbb', '123', 1, 'tbb@example.com', '1234567890', '2023-09-02 12:00:00', '2023-09-02 12:00:00'),
    ('yzy', '123', 0, 'yzy@example.com', '9876543210', '2023-09-02 13:00:00', '2023-09-02 13:00:00'),
    ('admin', 'admin', 0, 'admin@example.com', '9876543210', '2023-09-02 13:00:00', '2023-09-02 13:00:00');
