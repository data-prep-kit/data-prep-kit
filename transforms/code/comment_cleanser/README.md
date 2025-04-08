# Comment Cleanser Transform 
The Comment cleanser transforms 
Detect and remove commented code of input data.

This module detects commented code for following:
* C
* C++/C#
* Go
* HTML
* JAVA
* JavaScript
* Python
* Ruby
* Shell
* XML
Note : This module use [comment_cleanser](https://pypi.org/project/comment-parser/) which only support this many languages.

Per the set of 
[transform project conventions](../../README.md#transform-project-conventions)
the following runtimes are available:

* [python](python/README.md) - provides the base python-based transformation 
implementation.
* [ray](ray/README.md) - enables the running of the base python transformation
in a Ray runtime.
* [kfp_ray](kfp_ray/README.md) - enables running the ray docker image 
in a kubernetes cluster using a generated `yaml` file.