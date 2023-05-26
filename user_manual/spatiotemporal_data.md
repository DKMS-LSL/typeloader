# ![Icon](images/TypeLoader_32.png) Spatiotemporal data

As of June 2023, ENA and the other members of INSDC require spatiotemporal data for each submitted sample. This means that TypeLoader now needs you to provide the provenance and collection date of each sample before you can submit to ENA.

(See [INSDC announcement from November 2021](https://www.insdc.org/news/spatio-temporal-annotation-policy-18-11-2021/) for an explanation.)

## Provenance

This specifies the country where a sample was collected.

There is a controlled vocabulary for the options of this field:

- [possible country options](https://www.insdc.org/submitting-standards/country-qualifier-vocabulary/)

## Collection Date

This specifies when the sample from which this allele stems was collected.

These dates must conform to the ISO8601 standard (e.g. `2023-04-23`) and contain at least the year, e.g. `2023`.

## Missing values

If you cannot provide the provenance or collection date of a sample (which you really should if you can), you need to give a reason. 
The following options exist officially:
- [possible values for missing data](https://www.insdc.org/submitting-standards/missing-value-reporting/)

However, only the following options are implemented in TypeLoader, as the other ones don't seem logical:
- `missing: data agreement established pre-2023`
- `missing: third party data`
- `missing: human-identifiable`

(If you need another option, please [open a GitHub issue](https://github.com/DKMS-LSL/typeloader/issues/new) and explain.)
