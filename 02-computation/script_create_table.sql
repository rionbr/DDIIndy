/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create CoAdministation Table
*/

/*
 * Drop Views/Tables before creation
*/
DROP TABLE IF EXISTS coadministration;
DROP TABLE IF EXISTS helper_patient_parsed;

/*
 * Co-Administration
*/
CREATE TABLE coadministration (
	id_patient INT NOT NULL,
	id_drug_i VARCHAR(7) NOT NULL,
	id_drug_j VARCHAR(7) NOT NULL,
	qt_i INT(4) UNSIGNED COMMENT "in days",
	qt_j INT(4) UNSIGNED COMMENT "in days",
	len_i INT(4) UNSIGNED COMMENT "in days",
	len_j INT(4) UNSIGNED COMMENT "in days",
	len_ij INT(4) UNSIGNED COMMENT "in days",
	is_ddi BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (id_patient, id_drug_i, id_drug_j)
) ENGINE=InnoDB;

/*
 * helper_coadmin_parsed
*/
CREATE TABLE helper_patient_parsed (
	id_patient INT,
	dt_start DATETIME(2),
	dt_end DATETIME(2),
	PRIMARY KEY (id_patient)
) ENGINE=InnoDB;

/*
SELECT id_patient, TIMEDIFF(dt_end, dt_start) as tmcalc FROM helper_patient_parsed;
SELECT id_patient, TIMEDIFF(dt_end, dt_start) AS tmcalc FROM helper_patient_parsed ORDER BY tmcalc DESC;
*/