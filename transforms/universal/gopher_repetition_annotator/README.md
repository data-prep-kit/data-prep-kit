# Gopher Repetition Annotator 
Please see the set of
[transform project conventions](../../README.md)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary
This annotator enables the application of the heuristic rules from Gopher Repetition Removal, as described in [this paper](https://arxiv.org/pdf/2112.11446.pdf). An indicator of poor quality data is excessive repetition of certain words or phrases within a document. This annotator helps identifying documents with a high proportion of repeated lines, paragraphs, or n-grams. 

This annotator follows the [Datatrove reference implementation](https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/gopher_repetition_filter.py). The annotator does not remove any data, subsequently data can be filtered out using a set of thresholds, like those defined in Table A1 from https://arxiv.org/pdf/2112.11446.pdf:

```
    duplicate line fraction                 0.30
    duplicate paragraph fraction            0.30
    duplicate line character fraction       0.20
    duplicate paragraph character fraction  0.20

    top 2-gram character fraction           0.20
    top 3-gram character fraction           0.18
    top 4-gram character fraction           0.16

    duplicate 5-gram character fraction     0.15
    duplicate 6-gram character fraction     0.14
    duplicate 7-gram character fraction     0.13
    duplicate 8-gram character fraction     0.12
    duplicate 9-gram character fraction     0.11
    duplicate 10-gram character fraction    0.10
```
