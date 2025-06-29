
CREATE TABLE db_product.imgrel_categories (
    category_id INT UNIQUE PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    vertical VARCHAR(100) DEFAULT NULL,
    p_flag TINYINT DEFAULT 0,
    created_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE db_product.imgrel_verticals (
    docid VARCHAR(50) NOT NULL UNIQUE PRIMARY KEY,
    vertical VARCHAR(100) NOT NULL,
    categories json DEFAULT NULL,
    cat_process TINYINT DEFAULT 0,
    created_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE db_product.imgrel_scores (
    product_id INT NOT NULL UNIQUE PRIMARY KEY,
    docid VARCHAR(50) NOT NULL,
    product_url text DEFAULT NULL,
    desc_api TEXT DEFAULT NULL,
    desc_llama32 TEXT DEFAULT NULL,
    api_created_datetime TIMESTAMP,
    llama32_created_datetime TIMESTAMP,
    cat_score_01 json DEFAULT NULL,
    cat_score_02 json DEFAULT NULL,
    cat_map_v1 JSON DEFAULT NULL,
    v1_flag TINYINT DEFAULT 0,
    cat_map_v2 JSON DEFAULT NULL,
    v2_flag TINYINT DEFAULT 0,
    created_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

ALTER TABLE `db_product`.`imgrel_scores`
CHANGE COLUMN `llama32_created_datetime` `llama32_updated_datetime` TIMESTAMP;

ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `api_flag` TINYINT NOT NULL DEFAULT 0;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `llama32_flag` TINYINT NOT NULL DEFAULT 0;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `desc_llava15` TEXT NULL DEFAULT NULL;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `llava15_flag` TINYINT NOT NULL DEFAULT 0;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `llava15_updated_datetime` TIMESTAMP NULL DEFAULT NULL;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `cat_score_llava` JSON NULL DEFAULT NULL;

ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `cat_map_llava` JSON NULL DEFAULT NULL;

ALTER TABLE `db_product`.`imgrel_verticals`
ADD COLUMN `city` VARCHAR(20) NULL;

UPDATE imgrel_verticals
SET city = 'bangalore'
WHERE docid!='1';

SELECT * FROM db_product.imgrel_scores;
SELECT COUNT(1) FROM db_product.imgrel_verticals WHERE cat_process=0;
SELECT * FROM db_product.imgrel_verticals LIMIT 10 OFFSET 0;
DESCRIBE db_product.imgrel_scores;
DESCRIBE db_product.imgrel_verticals;
SELECT COUNT(1) FROM db_product.imgrel_verticals;
SELECT COUNT(1) FROM db_product.imgrel_scores;
SELECT DISTINCT docid AS docid_count FROM imgrel_scores;
SELECT COUNT(DISTINCT docid) AS docid_count FROM imgrel_verticals;


SELECT * FROM db_product.tbl_catalogue_details WHERE docid  = '080PXX80.XX80.100503164155.I7X4';
SELECT * FROM db_product.tbl_catalogue_details LIMIT 10 OFFSET 0;
SELECT * FROM db_product.imgrel_scores WHERE product_id = 265907089;

SELECT * FROM db_product.imgrel_scores WHERE desc_llama32 is not null and desc_api is not null;
SELECT desc_api FROM db_product.imgrel_scores WHERE api_flag = 3;

DESC imgrel_scores;
DESC tbl_catalogue_details;
select contractid from db_product.tbl_catalogue_details WHERE contractid IS NOT NULL LIMIT 10;
select * from db_product.tbl_catalogue_details LIMIT 10;
SELECT * FROM db_product.imgrel_verticals LIMIT 10;
SELECT COUNT(*) FROM db_product.imgrel_scores WHERE api_flag =1;
SELECT distinct api_flag FROM db_product.imgrel_scores;

SELECT docid
FROM imgrel_scores 
GROUP BY docid 
HAVING COUNT(*) = SUM(api_flag = 3) LIMIT 10;

SELECT COUNT(*)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(api_flag = 3)
) AS unique_docids;


ALTER TABLE imgrel_scores 
MODIFY contractid VARCHAR(45) DEFAULT NULL;
DESC imgrel_scores;
ALTER TABLE imgrel_scores 
ADD COLUMN `cat_score_01_tfidf` JSON DEFAULT NULL;

ALTER TABLE imgrel_scores 
ADD COLUMN desc_api_tfidf TINYINT DEFAULT 0;


ALTER TABLE imgrel_scores 
CHANGE COLUMN `desc_api_tfidf` `api_flag_tfidf` TINYINT DEFAULT 0;


SELECT COUNT(contractid) FROM imgrel_scores WHERE contractid IS NOT NULL;
247122
SELECT COUNT(contractid) FROM imgrel_scores WHERE contractid IS NULL;


SELECT COUNT(1) FROM imgrel_scores WHERE contractid='' OR contractid IS NULL;
SELECT contractid FROM imgrel_scores  LIMIT 100;
SELECT COUNT(1) FROM imgrel_scores WHERE contractid IS NULL;

SELECT distinct api_flag, count(*)
FROM imgrel_scores 
WHERE contractid='' OR contractid IS NULL
GROUP BY api_flag;


SELECT count(distinct docid)
FROM imgrel_scores 
WHERE contractid='' OR contractid IS NULL;



SELECT COUNT(*) 
FROM imgrel_scores 
WHERE LENGTH(TRIM(contractid)) = 0;

SELECT DISTINCT contractid, HEX(contractid) 
FROM imgrel_scores 
LIMIT 100;
SHOW CREATE TABLE imgrel_scores;

desc imgrel_scores;
select * from imgrel_scores limit 10;

SELECT COUNT(*) FROM imgrel_scores WHERE api_flag_tfidf = 0;
4510
248333

SHOW VARIABLES LIKE 'max_allowed_packet';

select COUNT(1) from imgrel_scores where api_flag = 4;
SELECT COUNT(1) FROM db_product.imgrel_scores where api_flag = 4;

SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 0;210187
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 1;4556
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 2;31651
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 3;5316
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 4;1413
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag_tfidf = 0;248333
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag_tfidf = 1;4510;


SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 1 and api_flag_tfidf = 0;91;
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 1 and api_flag_tfidf = 1;4465;
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 3 and api_flag_tfidf = 0;5282;
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 4 and api_flag_tfidf = 0;1144
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 3 and api_flag_tfidf = 1;41
SELECT COUNT(*) FROM imgrel_scores WHERE api_flag = 4 and api_flag_tfidf = 1;0

select distinct api_flag

SELECT docid FROM imgrel_scores WHERE api_flag = 1 and api_flag_tfidf = 1;
SELECT * FROM imgrel_scores WHERE cat_score_01 IS NOT NULL LIMIT 10;
SELECT COUNT(distinct docid) FROM imgrel_scores WHERE cat_score_01 IS NOT NULL;


select distinct docid from imgrel_scores where cat_score_01 IS NOT NULL and cat_score_01_tfidf IS NOT NULL;

ALTER TABLE db_product.imgrel_scores
MODIFY COLUMN api_flag_tfidf TINYINT DEFAULT 0;

UPDATE db_product.imgrel_scores
SET api_flag_tfidf=0
WHERE product_id!='1'; 

select docid, cat_score_01_tfidf from imgrel_scores where api_flag_tfidf=1;
select product_id cat_score_01_tfidf from imgrel_scores where docid = '022P1000506';


SELECT distinct docid, count(*)
FROM imgrel_scores 
WHERE api_flag_tfidf=1
GROUP BY docid;


SELECT COUNT(distinct docid) FROM imgrel_scores WHERE api_flag in (3,1);
SELECT COUNT(1) FROM imgrel_scores WHERE api_flag in (3,1);114772
SELECT COUNT(1) FROM imgrel_scores WHERE api_flag in (1); 4556
SELECT COUNT(distinct docid) FROM imgrel_scores WHERE api_flag in (1,3);5625
SELECT COUNT(1) FROM imgrel_scores WHERE api_flag in (4);1413
SELECT COUNT(1) FROM imgrel_scores WHERE api_flag in ( 2);67287+69652= 136939
208700
114772 desc done


select docid, cat_score_01_tfidf from imgrel_scores where api_flag_tfidf=1;



SELECT docid
FROM imgrel_scores 
GROUP BY docid 
HAVING COUNT(*) = SUM(api_flag = 3) LIMIT 10;

SELECT docid
FROM (
    SELECT distinct docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(api_flag in (1, 3) and api_flag_tfidf=1)
) AS unique_docids;

select * from imgrel_scores where product_id=234774075;


        SELECT COUNT(*)
        FROM imgrel_scores 
        WHERE api_flag = 0
        ORDER BY docid DESC;
        
177287

        SELECT COUNT(1)
        FROM imgrel_scores 
        WHERE api_flag = 0
        ORDER BY docid DESC
        
        
040PXX40.XX40.200126171604.K4A2
040PXX40.XX40.230822160642.J3W1        
040PXX40.XX40.180606132314.W6S5
040PXX40.XX40.250122113023.H8P2
040PXX40.XX40.220315125622.Y8D8
040PXX40-XX40-240711003537-F9I8
040PXX40.XX40.170301100845.Q1I7
040PXX40.XX40.190503222012.Q1Y4
040PXX40.XX40.181001114101.F6L7
040PXX40.XX40.190302182025.A1U3

;

SELECT * FROM temp_category_synonym_data_20250212 LIMIT 10;
SELECT COUNT(1) FROM temp_category_synonym_data_20250212;
SELECT COUNT(1) FROM temp_category_synonym_data_20250212 where active_flag = 1;
SELECT COUNT(distinct national_catid) FROM temp_category_synonym_data_20250212 where active_flag = 1;

SELECT * FROM temp_category_synonym_data_20250212 where active_flag = 1 ORDER BY national_catid;
# 3.23.49.622 
# 1.14.49.045 active_category non unique
# 16.09.083  active_category unique




SELECT national_catid,main_catname,category_name,active_flag FROM temp_category_synonym_data_20250212 LIMIT 10;
SELECT docid, national_catid FROM bangalore_docid_updated_norma LIMIT 10;

select A.docid, A.national_catid,B.national_catid,B.main_catname,B.category_name,B.active_flag from bangalore_docid_updated_norma A 
join temp_category_synonym_data_20250212 B 
on  B.national_catid = A.national_catid
Where B.active_flag = 1;

CREATE VIEW category_docid_view AS
select A.docid, A.national_catid,B.main_catname,B.category_name,B.active_flag from bangalore_docid_updated_norma A 
join temp_category_synonym_data_20250212 B 
on  B.national_catid = A.national_catid
Where B.active_flag = 1;

select COUNT(distinct A.national_catid) from bangalore_docid_updated_norma A 
join temp_category_synonym_data_20250212 B 
on  B.national_catid = A.national_catid
Where B.active_flag = 1;

# 3929
# 35.94.716

DESC temp_category_synonym_data_20250212;

ALTER TABLE `db_product`.`temp_category_synonym_data_20250212`
ADD COLUMN `main_catname_oovs` TEXT DEFAULT NULL;

ALTER TABLE `db_product`.`temp_category_synonym_data_20250212`
MODIFY COLUMN `main_catname_oovs_sbert` VARCHAR(255) DEFAULT NULL;


ALTER TABLE `db_product`.`temp_category_synonym_data_20250212`
ADD COLUMN `main_catname_oovs` TEXT DEFAULT NULL;

SELECT * FROM temp_category_synonym_data_20250212 where main_catname!=category_name and active_flag = 1 ORDER BY national_catid;

SELECT * 
FROM bangalore_docid_updated_norma A
JOIN temp_category_synonym_data_20250212 B 
ON A.national_catid = B.national_catid
WHERE A.docid='040PXX40.XX40.190208134331.S9X6';


040PXX40.XX40.190208134331.S9X6;
SELECT * FROM category_docid_view;



desc temp_category_synonym_data_20250212;
select * from imgrel_scores where docid = "022P1000844";
select main_catname_oovs_sbert from temp_category_synonym_data_20250212 where  main_catname_oovs_sbert is not null limit 10;

desc imgrel_scores;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `cat_score_01_tfidf_finetune` JSON NULL;
ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `api_flag_tfidf_finetune` TINYINT NULL;


select cat_score_01_tfidf from imgrel_scores where docid = "022P1000844" LIMIT 1;


SELECT docid
FROM imgrel_scores
GROUP BY docid
HAVING COUNT(*) = SUM(CASE WHEN api_flag in (1,3) THEN 1 ELSE 0 END);



SELECT count(docid)
FROM imgrel_scores
GROUP BY docid
HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1, 3) THEN 1 ELSE 0 END);
SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1, 3) THEN 1 ELSE 0 END)
) AS subquery;

desc imgrel_scores;

SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1) THEN 1 ELSE 0 END) 
) AS subquery;
# 231
SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag_tfidf IN (1) THEN 1 ELSE 0 END) 
) AS subquery;
# 522
SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag_tfidf_finetune IN (1) THEN 1 ELSE 0 END) 
) AS subquery;
# 3071

SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1) THEN 1 ELSE 0 END) 
    AND COUNT(*) = SUM(CASE WHEN api_flag_tfidf IN (1) THEN 1 ELSE 0 END) 
    AND COUNT(*) = SUM(CASE WHEN api_flag_tfidf_finetune IN (1) THEN 1 ELSE 0 END) 
) AS subquery;

SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1) THEN 1 ELSE 0 END) 
    AND COUNT(*) = SUM(CASE WHEN api_flag_tfidf IN (1) THEN 1 ELSE 0 END) 
    AND COUNT(*) = SUM(CASE WHEN api_flag_tfidf_finetune IN (1) THEN 1 ELSE 0 END) 
) AS subquery;
# 229

SELECT docid
FROM imgrel_scores
GROUP BY docid
HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1) THEN 1 ELSE 0 END) 
AND COUNT(*) = SUM(CASE WHEN api_flag_tfidf IN (1) THEN 1 ELSE 0 END) 
AND COUNT(*) = SUM(CASE WHEN api_flag_tfidf_finetune IN (1) THEN 1 ELSE 0 END);

SELECT distinct api_flag_tfidf_finetune
FROM imgrel_scores;

SELECT COUNT(docid)
FROM (
    SELECT distinct docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1,3) THEN 1 ELSE 0 END) 
) AS subquery;
# 9214
SELECT COUNT(docid)
FROM (
    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1,3) and api_flag_tfidf_finetune not in (1) THEN 1 ELSE 0 END) 
) AS subquery;
# 0
SELECT COUNT(distinct docid) FROM imgrel_scores;



    SELECT docid
    FROM imgrel_scores
    GROUP BY docid
    HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1, 3) THEN 1 ELSE 0 END) LIMIT 10;
    
desc imgrel_scores;
desc imgrel_categories;
    
SELECT docid
FROM imgrel_scores
GROUP BY docid
HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1, 3) THEN 1 ELSE 0 END) ;


select COUNT(1)
from imgrel_scores 
where api_flag_tfidf_finetune is NULL;

select COUNT(distinct docid)
from imgrel_scores 
where api_flag_tfidf_finetune_15 = 1;


select COUNT(1)
from imgrel_scores 
where api_flag_tfidf_finetune=0;

ALTER TABLE imgrel_scores
ALTER COLUMN api_flag_tfidf_finetune SET DEFAULT 0;

UPDATE imgrel_scores
SET api_flag_tfidf_finetune = 0
WHERE api_flag_tfidf_finetune IS NULL and product_id!='1';

select *
FROM imgrel_scores
WHERE api_flag_tfidf_finetune = 1 LIMIT 100;

select *
FROM imgrel_scores
WHERE docid in ('080PAPP20081229IRO46221920');

SELECT * FROM lg_videos_29L WHERE docid = '011P1217932890L9I4E1';

SELECT COUNT(*)
FROM imgrel_scores
WHERE api_flag = 0


ALTER TABLE `db_product`.`imgrel_scores`
ADD COLUMN `api_flag_tfidf_finetune_15` TINYINT NOT NULL DEFAULT 0;
ALTER TABLE imgrel_scores 
ADD COLUMN `cat_score_01_tfidf_finetune_15` JSON DEFAULT NULL;

select * from imgrel_verticals limit 10;

SELECT * FROM imgrel_scores limit 10;
SELECT product_id, docid, product_url, desc_api, cat_score_01_tfidf_finetune_15, contractid FROM imgrel_scores limit 10;
select count(1) from imgrel_scores where cat_score_01_tfidf_finetune_15 = 0;

    WITH unique_docids AS (
        SELECT docid
        FROM imgrel_scores
        GROUP BY docid
        ORDER BY docid
        LIMIT 4 OFFSET 0
    )
    SELECT i.product_id, i.docid, i.product_url, i.desc_api, i.cat_score_01_tfidf_finetune_15, i.contractid
    FROM imgrel_scores i
    JOIN unique_docids u ON i.docid = u.docid;
    
SELECT  COUNT(1) FROM imgrel_scores where cat_score_01_tfidf_finetune_15 is null;


    WITH unique_docids AS (
        SELECT docid
        FROM imgrel_scores
        WHERE cat_score_01_tfidf_finetune_15 IS NOT NULL
        GROUP BY docid
        ORDER BY docid
    )
    SELECT i.product_id, i.docid, i.product_url, i.desc_api, i.cat_score_01_tfidf_finetune_15, i.contractid
    FROM imgrel_scores i
    JOIN unique_docids u ON i.docid = u.docid
    WHERE cat_score_01_tfidf_finetune_15 IS NULL;
    
    
SELECT *
FROM imgrel_scores
WHERE docid in (
	SELECT docid
	FROM imgrel_scores
	GROUP BY docid
	HAVING COUNT(*) = SUM(CASE WHEN api_flag IN (1) THEN 1 ELSE 0 END)
    );




SELECT *
FROM imgrel_scores
WHERE product_id in (339603624);