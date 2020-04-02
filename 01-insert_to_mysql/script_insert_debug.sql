
TRUNCATE TABLE coadministration;
TRUNCATE TABLE medication_drug;
TRUNCATE TABLE drugbank_interaction;
TRUNCATE TABLE drug;
TRUNCATE TABLE medication;
TRUNCATE TABLE patient;
/*
 * Patient
*/
INSERT INTO patient (id_patient, gender, dob, ethnicity, race, zip5, zip4) VALUES (1, 'Male', '1985-01-28', 'Not Hispanic or Latino', 'White', 47408, 1234);
INSERT INTO patient (id_patient, gender, dob, ethnicity, race, zip5, zip4) VALUES (2, 'Female', '1987-07-01', 'Not Hispanic or Latino', 'White', 47408, 4321);

/*
 * Medication
*/
INSERT INTO medication (id_medication, id_patient, dt_start, dt_end, name) VALUES (101, 1, '2020-01-01', '2020-01-31', 'Drug A');
INSERT INTO medication (id_medication, id_patient, dt_start, dt_end, name) VALUES (102, 1, '2020-01-15', '2020-02-15', 'Drug B+Drug C');
INSERT INTO medication (id_medication, id_patient, dt_start, dt_end, name) VALUES (103, 1, '2020-03-01', '2020-03-31', 'Drug D');

/*
 * Drug
*/
INSERT INTO drug (id_drug, name) VALUES ('DB000A', 'Drug A');
INSERT INTO drug (id_drug, name) VALUES ('DB000B', 'Drug B');
INSERT INTO drug (id_drug, name) VALUES ('DB000C', 'Drug C');
INSERT INTO drug (id_drug, name) VALUES ('DB000D', 'Drug D');

/*
 * Medication <-> Drug
*/
INSERT INTO medication_drug (id_medication_drug, id_medication, id_drug) VALUES (301, 101, 'DB000A');
INSERT INTO medication_drug (id_medication_drug, id_medication, id_drug) VALUES (302, 102, 'DB000B');
INSERT INTO medication_drug (id_medication_drug, id_medication, id_drug) VALUES (303, 102, 'DB000C');
INSERT INTO medication_drug (id_medication_drug, id_medication, id_drug) VALUES (304, 103, 'DB000D');

/*
 * DrugBank Interaction
*/
INSERT INTO drugbank_interaction (id_drug_i, id_drug_j, description) VALUES ('DB000A', 'DB000C', 'Interaction A-C');
#INSERT INTO drugbank_interaction (id_drug_i, id_drug_j, description) VALUES ('DB000B', 'DB0002', 'Interaction B-2');
#INSERT INTO drugbank_interaction (id_drug_i, id_drug_j, description) VALUES ('DB000C', 'DB0003', 'Interaction C-3');
#INSERT INTO drugbank_interaction (id_drug_i, id_drug_j, description) VALUES ('DB000D', 'DB0004', 'Interaction D-4');

/*
 * Co-Administration
*/
INSERT INTO coadministration (id_medication_drug_i, id_medication_drug_j, length, is_ddi)
SELECT
	mdi.id_medication_drug AS 'medication_drug_i',
	mdj.id_medication_drug AS 'medication_drug_j',
	DATEDIFF(GREATEST(mi.dt_start, mi.dt_end), LEAST(mi.dt_start, mi.dt_end)) AS 'length',
	CASE WHEN EXISTS (
		SELECT * FROM drugbank_interaction dbi
		WHERE (dbi.id_drug_i = di.id_drug AND dbi.id_drug_j = dj.id_drug) OR (dbi.id_drug_j = di.id_drug) AND (dbi.id_drug_i = dj.id_drug)
	) THEN TRUE ELSE FALSE END AS 'is_ddi'
FROM
	medication_drug AS mdi
	JOIN medication AS mi ON mdi.id_medication = mi.id_medication
	JOIN drug AS di ON mdi.id_drug = di.id_drug
	JOIN patient AS pi ON mi.id_patient = pi.id_patient,
	medication_drug AS mdj
	JOIN medication AS mj ON mdj.id_medication = mj.id_medication
	JOIN drug AS dj ON mdj.id_drug = dj.id_drug
	JOIN patient AS pj ON mj.id_patient = pj.id_patient
WHERE
	pi.id_patient = pj.id_patient /* same patient */
	AND mdi.id_medication_drug != mdj.id_medication_drug /* different medication_drug */
	AND di.id_drug < dj.id_drug /* conbination, not product */
	AND NOT (GREATEST(mi.dt_start, mi.dt_end) < mj.dt_start OR LEAST(mi.dt_start, mi.dt_end) > mj.dt_end); /* medication ij overlap */
	/* excludes topic, ophthalmo & vaccines */
	AND (mi.is_topic = FALSE AND mj.is_topic = FALSE)
	AND (mi.is_ophthalmo = FALSE AND mj.is_ophthalmo = FALSE)
	AND (mi.is_vaccine = FALSE AND mj.is_vaccine = FALSE);
