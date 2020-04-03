/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Patient Tables
*/


/*
 * Drop Views/Tables before creation
*/
DROP TABLE IF EXISTS patient;


/*
 * Patient
*/
CREATE TABLE patient (
	id_patient INT PRIMARY KEY,
	gender VARCHAR(7) COMMENT "Male; Female",
	dob DATE,
	age_today INT(3) GENERATED ALWAYS AS (TIMESTAMPDIFF(YEAR, dob, '2020-01-01')) VIRTUAL,
	ethnicity VARCHAR(50) COMMENT "Not Hispanic/Latino; Not Hispanic/Latino/Spanish; Hispanic/Latino; Unknown",
	race VARCHAR(25) COMMENT "White; Black; Hispanic; Asian; Indian; Islander; Bi-racial; Unknown",
	zip5 INT(5) COMMENT "First 5 ZIP numbers",
	zip4 INT(4) COMMENT "Last 4 ZIP numbers"
) ENGINE=InnoDB;
