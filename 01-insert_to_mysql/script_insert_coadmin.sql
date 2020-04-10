/*
 * Author: Rion B. Correia
 * Date: April 10, 2020
 * Description: Populates coadministration table
*/

/*
 * Co-Administration
*/
INSERT INTO coadministration (id_medication_drug_i, id_medication_drug_j, length, is_ddi)
EXPLAIN SELECT
    mdi.id_medication_drug AS 'medication_drug_i',
    mdj.id_medication_drug AS 'medication_drug_j',
    DATEDIFF(GREATEST(mi.dt_start, mi.dt_end), LEAST(mi.dt_start, mi.dt_end)) AS 'length',
    CASE WHEN EXISTS (
        SELECT * FROM drugbank_interaction dbi
        WHERE (dbi.id_drug_i = di.id_drug AND dbi.id_drug_j = dj.id_drug) OR (dbi.id_drug_i = dj.id_drug) AND (dbi.id_drug_j = di.id_drug)
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
    AND NOT (GREATEST(mi.dt_start, mi.dt_end) < mj.dt_start OR LEAST(mi.dt_start, mi.dt_end) > mj.dt_end) /* medication ij overlap */
    /* excludes topic, ophthalmo & vaccines */
    AND (mi.is_topic = FALSE AND mj.is_topic = FALSE)
    AND (mi.is_ophthalmo = FALSE AND mj.is_ophthalmo = FALSE)
    AND (mi.is_vaccine = FALSE AND mj.is_vaccine = FALSE);
