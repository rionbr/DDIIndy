# DDI Indy - Data Management

This file traces commands used to create and give permission and handle the raw data.
This file will provide little information to users without the necessary permissions to the Indiana University UITS systems.


## MySQL Enterprise information


Project schema: `casci_ddi_indy`.


### Database Tables

See `script.sql` for MySQL table creation.


### MySQL Management


Show help on creating schemas and users:

```
CALL api.help('me');
```

Code used to create the 'ddi_indy' MySQL schemas and the `rionbr` user.

```
CALL api.createSchema('ddi_indy');
CALL api.createUser('rionbr', '%', '<password>', false, false);
CALL api.grant('casci_rionbr', '%', 'ALL PRIVILEGES', 'casci_ddi_indy', '*');
```


## Raw data access information

Raw data is stored at IU's Scholarly Data Archive (SDA).
To access it you need to login in to an IU's supercomputer, i.e. Carbonate.

`> ssh carbonate.uits.iu.edu`

Then you need to load the `hpss` module to be able to access the SDA.

`> module load hpss`

Then you can enter the `hsi` module to access the data and navigate to the files location.

```
> hsi
> Kerberos Principal: <username>
> cd /hpss/c/a/casci/ddiindy
> get
```

The following files are part of the raw data

```
     size filename
105935521 p2876_demographics.csv
 34118970 p2876_meds_01_t.csv
 59543922 p2876_meds_01_u.csv
 31783367 p2876_meds_02_t.csv
 59695353 p2876_meds_02_u.csv
 32735246 p2876_meds_03_t.csv
 57181584 p2876_meds_03_u.csv
 32526927 p2876_meds_04_t.csv
 54424638 p2876_meds_04_u.csv
 33106270 p2876_meds_05_t.csv
 54732334 p2876_meds_05_u.csv
 31400220 p2876_meds_06_t.csv
 54325254 p2876_meds_06_u.csv
 33560108 p2876_meds_07_t.csv
 57880374 p2876_meds_07_u.csv
 32354787 p2876_meds_08_t.csv
 55122996 p2876_meds_08_u.csv
 33349672 p2876_meds_09_t.csv
 54049346 p2876_meds_09_u.csv
 34286775 p2876_meds_10_t.csv
 55274803 p2876_meds_10_u.csv
 33235309 p2876_meds_11_t.csv
 57319335 p2876_meds_11_u.csv
 32352764 p2876_meds_12_t.csv
 56510580 p2876_meds_12_u.csv
   679458 p2876_ndc.csv
```
