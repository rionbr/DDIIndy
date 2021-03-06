/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create (Materialized) Views
*/

/*
 * Drop Materialized Views and Views
*/
DROP TABLE IF EXISTS dw_coadministration;
DROP VIEW IF EXISTS dw_interaction;

/*
 * DW - Co-Administration (materialized view)
*/
CREATE TABLE dw_coadministration (
    id_patient INT NOT NULL,
    gender VARCHAR(7) COMMENT "Male; Female",
    dob DATE,
    age INT(3),
    ethnicity VARCHAR(50),
    race VARCHAR(25),
    zip5 INT(5),
    zip4 INT(4),
    id_drug_i VARCHAR(7),
    id_drug_j VARCHAR(7),
    name_i TEXT,
    name_j TEXT,
    qt_i INT(4),
    qt_j INT(4),
    len_i INT(4),
    len_j INT(4),
    len_ij INT(4),
    is_ddi BOOLEAN,
    ddi_description TEXT,
    ddi_severity VARCHAR(15)
) ENGINE=InnoDB;

/* Insert Select */
INSERT INTO dw_coadministration
    SELECT
        p.id_patient,
        p.gender,
        p.dob,
        p.age_today AS 'age',
        p.ethnicity,
        p.race,
        p.zip5,
        p.zip4,
        c.id_drug_i,
        c.id_drug_j,
        di.name AS 'name_i',
        dj.name AS 'name_j',
        c.qt_i,
        c.qt_j,
        c.len_i,
        c.len_j,
        c.len_ij,
        c.is_ddi,
        dbi.description AS 'ddi_description',
        dbi.severity AS 'ddi_severity'
    FROM coadministration c
        JOIN drug di ON c.id_drug_i = di.id_drug
        JOIN drug dj ON c.id_drug_j = dj.id_drug
        JOIN patient p ON c.id_patient = p.id_patient
        LEFT JOIN drugbank_interaction dbi ON (dbi.id_drug_i = c.id_drug_i AND dbi.id_drug_j = c.id_drug_j);

/*
 * Indexes
*/
CREATE INDEX idx_dw_coadmin_id_patient ON dw_coadministration (id_patient);
CREATE INDEX idx_dw_coadmin_gender ON dw_coadministration (gender);
CREATE INDEX idx_dw_coadmin_age ON dw_coadministration (age);
CREATE INDEX idx_dw_coadmin_race ON dw_coadministration (race);
CREATE INDEX idx_dw_coadmin_id_drug_i ON dw_coadministration (id_drug_i);
CREATE INDEX idx_dw_coadmin_id_drug_j ON dw_coadministration (id_drug_j);
CREATE INDEX idx_dw_coadmin_id_drug_i_j ON dw_coadministration (id_drug_i, id_drug_j);
CREATE INDEX idx_dw_coadmin_is_ddi ON dw_coadministration (is_ddi);

/*
DROP INDEX idx_dw_coadmin_id_patient ON dw_coadministration;
DROP INDEX idx_dw_coadmin_gender ON dw_coadministration;
DROP INDEX idx_dw_coadmin_age ON dw_coadministration;
DROP INDEX idx_dw_coadmin_id_drug_i ON dw_coadministration;
DROP INDEX idx_dw_coadmin_id_drug_j ON dw_coadministration;
DROP INDEX idx_dw_coadmin_is_ddi ON dw_coadministration;
*/


/*
 * DW - Interaction (view)
*/
CREATE VIEW dw_interaction AS
SELECT *
FROM dw_coadministration c
WHERE c.is_ddi = TRUE;
