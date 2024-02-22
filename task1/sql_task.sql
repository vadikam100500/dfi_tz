CREATE DATABASE dfi_tz;

\c dfi_tz;

CREATE TABLE A (
    id SERIAL PRIMARY KEY,
    project VARCHAR(255),
    type VARCHAR(10) CHECK (type IN ('root', 'branch', 'leaf')),
    parent_id INT,
    extra JSON
);

ALTER TABLE A
ADD CONSTRAINT parent_id_fk
FOREIGN KEY (parent_id) REFERENCES A(id);

INSERT INTO A (id, project, type, parent_id, extra) 
VALUES 
    (1, 1, 'root', null, null),
    (2, 1, 'root', null, null),
    (3, 1, 'root', null, null),
    (4, 1, 'branch', 1, null),
    (5, 1, 'branch', 1, null),
    (6, 1, 'branch', 1, null),
    (7, 1, 'branch', 2, null),
    (8, 1, 'branch', null, null),
    (9, 1, 'leaf', 4, '{"color":"green"}'),
    (10, 1, 'leaf', 4, '{"color":"green"}'),
    (11, 1, 'leaf', 4, '{"color":"yellow"}'),
    (12, 1, 'leaf', 5, '{}'),
    (13, 1, 'leaf', 5, '{"color":"green"}'),
    (14, 1, 'leaf', 5, '{"color":"red"}'),
    (15, 1, 'leaf', 7, '{"color":"green"}'),
    (16, 1, 'leaf', 7, null),
    (17, 1, 'leaf', null, '{"color":"green"}'),
    (18, 2, 'leaf', null, '{"color":"green"}'),
    (19, 2, 'leaf', null, '{"color":"green"}'),
    (20, 2, 'leaf', null, '{"color":"green"}'),
    (21, 3, 'leaf', null, '{"color":"green"}'),
    (22, 3, 'leaf', null, '{"color":"green"}'),
    (23, 3, 'leaf', null, '{"color":"green"}');

# I have 2 solutions and don't know how to optimize them for big data

# First solution
SELECT root.project, root.id AS root_id, COUNT(DISTINCT branches.branch_id) AS branch_count, JSONB_AGG(DISTINCT colors ->> 'color') AS leaf_colors
FROM (
	SELECT *
	FROM A
	WHERE project = '1' AND type = 'root'
) AS root
LEFT JOIN (
	SELECT id AS branch_id, parent_id AS root_id
	FROM A
	WHERE project = '1' AND type = 'branch' AND parent_id IS NOT NULL
) AS branches ON root.id = branches.root_id
LEFT JOIN (
	SELECT parent_id AS branch_id, extra AS colors
	FROM A
	WHERE project = '1' AND type = 'leaf' AND extra IS NOT NULL AND parent_id IS NOT NULL
) AS leafs ON branches.branch_id = leafs.branch_id
GROUP BY  root.project, root.id;

-- will return 
-- 1, 1, 3, ["green","yellow", "red", null]
-- 1, 2, 1, ["green"]
-- 1, 3, 0, [null]

# second solution
SELECT a.project, a.id, COALESCE(branches.branch_count, 0), COALESCE(leaf_colors, '[]'::jsonb)
FROM a 
LEFT JOIN (
	SELECT parent_id AS root_id, COUNT(DISTINCT id) AS branch_count, JSONB_AGG(DISTINCT leafs.extra ->> 'color') AS leaf_colors
	FROM a
	LEFT JOIN (
	    SELECT extra, parent_id AS branch_id 
	    FROM a
	    WHERE project = '1' AND a.type = 'leaf' AND extra IS NOT NULL AND parent_id IS NOT NULL AND extra->>'color' IS NOT NULL
	) leafs ON a.id = leafs.branch_id 
	WHERE project = '1' AND a."type" = 'branch' AND parent_id IS NOT null
	GROUP BY parent_id
) branches ON a.id = branches.root_id
WHERE a.project = '1' AND a.type = 'root'

-- will return
-- 1, 1, 3, ["green","yellow", "red", null]
-- 1, 2, 1, ["green"]
-- 1, 3, 0, []
