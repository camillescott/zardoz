--name: create_schema#
CREATE TABLE IF NOT EXISTS rolls (
    member_id INTEGER NOT NULL,
    member_nick TEXT,
    member_name TEXT,
    roll TEXT NOT NULL,
    tag TEXT,
    result TEXT NOT NULL,
    time real NOT NULL
);

CREATE TABLE IF NOT EXISTS user_vars (
    member_id INTEGER NOT NULL,
    var TEXT NOT NULL,
    val INTEGER NOT NULL,
    PRIMARY KEY (member_id, var)
);

CREATE TABLE IF NOT EXISTS guild_vars (
    member_id INTEGER NOT NULL,
    var TEXT not NULL,
    val INTEGER not NULL,
    PRIMARY KEY (var)
);
