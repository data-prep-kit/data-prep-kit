# Language Identification Transform 
The Language Identification transforms serves as a simple exemplar to demonstrate the development
of a simple 1:1 transform.  
Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions, transform configuration, testing and IDE set up.

## Summary 
This transform will identify language of each text with confidence score with fasttext language identification model. [ref](https://huggingface.co/facebook/fasttext-language-identification)

## Contributors

- Daiki Tsuzuku (dtsuzuku@jp.ibm.com)
- Maroun Touma (touma@us.ibm.com)

## Configuration and command line Options

The set of dictionary keys holding [LangIdentificationTransform](dpk_lang_id/transform.py) 
configuration for values are as follows:

| Key name  | Default  | Description |
|------------|----------|--------------|
| _lang_id_model_credential_ | _unset_ | specifies the credential you use to get model. This will be huggingface token. [Guide to get huggingface token](https://huggingface.co/docs/hub/security-tokens) |
| _lang_id_model_kind_ | _unset_ | specifies what kind of model you want to use for language identification. Currently, only `fasttext` is available. |
| _lang_id_model_url_ | _unset_ |  specifies url that model locates. For fasttext, this will be repo nme of the model, like `facebook/fasttext-language-identification` |
| _lang_id_content_column_name_ | `contents` | specifies name of the column containing documents |
| _lang_id_output_lang_column_name_ | `lang` | specifies name of the output column to hold predicted language code |
| _lang_id_output_score_column_name_ | `score` | specifies name of the output column to hold score of prediction |

## Running

### Launched Command Line Options 
The following command line arguments are available in addition to 
the options provided by 
the [launcher](../../../data-processing-lib/doc/launcher-options.md).
```
  --lang_id_model_credential LANG_ID_MODEL_CREDENTIAL   the credential you use to get model. This will be huggingface token.
  --lang_id_model_kind LANG_ID_MODEL_KIND   what kind of model you want to use for language identification. Currently, only `fasttext` is available.
  --lang_id_model_url LANG_ID_MODEL_URL   url that model locates. For fasttext, this will be repo name of the model, like `facebook/fasttext-language-identification`
  --lang_id_content_column_name LANG_ID_CONTENT_COLUMN_NAME   A name of the column containing documents
  --lang_id_output_lang_column_name LANG_ID_OUTPUT_LANG_COLUMN_NAME   Column name to store identified language
  --lang_id_output_score_column_name LANG_ID_OUTPUT_SCORE_COLUMN_NAME   Column name to store the score of language identification
```
These correspond to the configuration keys described above.

### Code example
Here is a sample [notebook](lang_id.ipynb)

## Troubleshooting guide

For M1 Mac user, if you see following error during make command, `error: command '/usr/bin/clang' failed with exit code 1`, you should follow [this step](https://freeman.vc/notes/installing-fasttext-on-an-m1-mac)


### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.



# Language Identification Ray Transform 
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
This project wraps the language identification transform with a Ray runtime.

## Configuration and command line Options

Language Identification configuration and command line options are the same as for the base python transform. 

### Launched Command Line Options 
In addition to those available to the transform as defined here,
the set of 
[launcher options](../../../data-processing-lib/doc/launcher-options.md) are available.

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

# Supported Languages
|                     |                     |                     |            |            |    |  |  |
| :-----------------: | :-----------------: | :-----------------: | :-----------------: | :-----------------: | :-----------------: | :-----------------: | :-----------------: |
|Afrikaans|Albanian|Alemannic|Amharic|Arabic|Aragonese|Armenian|Asaro'o
|Assamese|Asturian|Avaric|Azerbaijani|Bashkir|Basque|Bavarian|Belarusian
|Bengali|Bihari languages|Bishnupriya Manipuri|Bosnian|Breton|Bulgarian|Buriat|Burmese
|Catalan|Cebuano|Central Bikol|Central Khmer|Central Kurdish|Chavacano|Chechen|Chinese
|Chuvash|Cornish|Corsican|Croatian|Czech|Danish|Dimli|Divehi
|Doteli|Dutch|Eastern Mari|Egyptian Arabic|Emilian-Romagnol|English|Esperanto|Estonian
|Fiji Hindi|Finnish|French|Galician|Georgian|German|Goan Konkani|Greek
Guarani|Gujarati|Haitian Creole|Hebrew|Hill Mari|Hindi|Hungarian|Icelandic
Ido|Ilokano|Indonesian|Interlingua|Interlingue|Irish|Italian|Japanese
Javanese|Kalmyk|Kannada|Kapampangan|Karachay-Balkar|Kazakh|Komi|Korean
Kurdish|Kyrgyz|Lao|Latin|Latvian|Lezgian|Limburgish|Lithuanian
Lojban|Lombard|Low German|Lower Sorbian|Luxembourgish|Macedonian|Maithili|Malagasy
Malay|Malayalam|Maltese|Manx|Marathi|Mazandarani|Min|Mirandese
Mongolian|Nahuatl|Neapolitan|Nepal Bhasa|Nepali|Northern Frisian|Northern Luri|Norwegian
Norwegian Nynorsk|Occitan|Odia|Ossetian|Palatine|Pashto|Persian|Piedmontese
Polish|Portuguese|Punjabi|Quechua|Romanian|Romansh|Russian|Rusyn
Sanskrit|Sardinian|Scots|Scottish Gaelic|Serbian|Serbo-Croatian|Sicilian|Sindhi
Sinhala|Slovak|Slovenian|Somali|South Azerbaijani|Spanish|Sundanese|Swahili
Swedish|Tagalog|Tajik|Tamil|Tatar|Telugu|Thai|Tibetan
Turkish|Turkmen|Tuvan|Uighur|Ukrainian|Upper Sorbian|Urdu|Uzbek
Venetian|Veps|Vietnamese|Volapük|Walloon|Waray|Welsh|West Flemish
Western Frisian|Western Punjabi|Wu Chinese|Yakut|Yiddish|Yoruba|Yue
