CREATE TABLE employees (
  emp_id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(32) NOT NULL,
  username varchar(32) NOT NULL,
  password varchar(32) NOT NULL DEFAULT 'defaultPassword',
  userlevel int(11) NOT NULL,
  is_approved tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (emp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci AUTO_INCREMENT=1;

CREATE TABLE programs (
  prog_id int(11) NOT NULL AUTO_INCREMENT,
  program varchar(32) NOT NULL,
  program_release varchar(32) NOT NULL,
  program_version varchar(32) NOT NULL,
  PRIMARY KEY (prog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci AUTO_INCREMENT=1;


CREATE TABLE areas (
  area_id int(11) NOT NULL AUTO_INCREMENT,
  prog_id int(11) NOT NULL,
  area varchar(32) NOT NULL,
  PRIMARY KEY (area_id),
  KEY FK_progid (prog_id),
  CONSTRAINT FK_progid FOREIGN KEY (prog_id) REFERENCES programs (prog_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci AUTO_INCREMENT=1;


CREATE TABLE bug (
  bug_id int(32) NOT NULL AUTO_INCREMENT,
  program varchar(32) NOT NULL,
  report_type varchar(32) NOT NULL,
  severity varchar(32) NOT NULL,
  problem_summary varchar(32) NOT NULL,
  reproducible tinyint(1) NOT NULL,
  problem varchar(32) NOT NULL,
  reported_by varchar(32) NOT NULL,
  date_reported date NOT NULL,
  functional_area varchar(32) DEFAULT NULL,
  assigned_to varchar(32) DEFAULT NULL,
  comments varchar(32) DEFAULT NULL,
  status varchar(32) DEFAULT 'Open',
  priority int(32) DEFAULT NULL,
  resolution varchar(32) DEFAULT NULL,
  resolution_version int(32) DEFAULT NULL,
  resolution_by varchar(255) DEFAULT NULL,
  date_resolved date DEFAULT NULL,
  tested_by varchar(32) DEFAULT NULL,
  prog_id int(32) NOT NULL,
  area_id int(32) DEFAULT NULL,
  attachment longblob DEFAULT NULL,
  filename varchar(255) DEFAULT NULL,
  is_deleted TINYINT(1) DEFAULT 0,
  deleted_at DATETIME DEFAULT NULL,
  PRIMARY KEY (bug_id),
  KEY FK_prog_id (prog_id),
  KEY FK_area_id (area_id),
  CONSTRAINT FK_prog_id FOREIGN KEY (prog_id) REFERENCES programs (prog_id) ON DELETE CASCADE,
  CONSTRAINT FK_area_id FOREIGN KEY (area_id) REFERENCES areas (area_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci AUTO_INCREMENT=17;


INSERT INTO employees (emp_id, name, username, password, userlevel, is_approved)
VALUES (101, 'admin', 'admin', 'password', 3, 1);

ALTER TABLE bug
ADD COLUMN suggested_fix VARCHAR(255) DEFAULT NULL;

ALTER TABLE bug
MODIFY COLUMN problem TEXT,
MODIFY COLUMN problem_summary TEXT,
MODIFY COLUMN suggested_fix TEXT,
MODIFY COLUMN comments TEXT;
